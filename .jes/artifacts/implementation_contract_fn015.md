# Implementation Contract — FN-015

> ⛔ **SUPERSEDED by G23 (2026-08-20)** — the FN-015 feature this contract
> implemented was removed in full. See
> [`.jes/artifacts/implementation_contract_g23_remove_fn015.md`](implementation_contract_g23_remove_fn015.md)
> and [`.jes/artifacts/implementation_report_g23_remove_fn015.md`](implementation_report_g23_remove_fn015.md).
> This document is kept as historical audit trail only — do not implement
> or reference it as current behavior.

**Project:** Jarvis  
**Date:** 2026-08-08  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** APPROVED FOR IMPLEMENTATION  

**Plan ref:** Acquisition Fluency Architecture — Corte 2  
**Depends on:** FN-005, FN-013, FN-014 (closed)  
**Does not implement:** FN-016, Conversation Engine, Phase-A copy rewrite (unless needed as minimal hint text for help)  

---

## 1. Intent

When acquisition is already open (`DEFINE_MISSING_PARAMETERS`) — or IDLE with a known next gap — and the user asks for **generic help to define the current value** without naming a block/component, Jarvis must **help with the real pending item**, not call the LLM.

Field-note case:

```text
DEFINE_MISSING, pending=["propellers"]  (or motors then propellers)
User: "ayudame a definir el valor"
  or: "ayudame a definir"

Today:
  intent analyze (regex \bayudame\b) → LLM
  → invents battery_capacity_wh / energy talk

Target:
  0 LLM
  session unchanged (collected_params / pending preserved)
  deterministic help for pending[0] only (propellers hints — NOT battery)
```

---

## 2. Root cause

In `DEFINE_MISSING_PARAMETERS` ([`orchestrator.py`](src/jarvis/core/orchestrator.py) ~723):

```text
if _dm_intent == "analyze" and not is_help_choose_phrase(user_input):
    → _handle_analyze → LLM
```

`is_help_choose_phrase` only covers **motor catalog** help (`elegir`/`escoger`/`motor`/…).  
`"ayudame a definir"` / `"ayudame a definir el valor"` match `ANALYZE_PATTERNS` (`\bayudame\b`) but **not** help-choose → LLM, which ignores `pending_param_definitions`.

FN-013 already handles declare-block re-prompt; FN-014 handles named block/component in IDLE. Neither covers bare “help me define (the value)”.

---

## 3. Scope

### In scope

| Area | Change |
|---|---|
| Help-phrase detection | Recognize generic “help define current pending” phrases (new helper, preferably next to `is_help_choose_phrase` or in `acquisition_target.py`) |
| [`orchestrator.py`](src/jarvis/core/orchestrator.py) DEFINE_MISSING branch | Before analyze→LLM: if generic help-define → deterministic pending help |
| Optional IDLE | If IDLE + user says bare help-define **and** `_next_pending_block` exists: open Bug54 bridge **then** show the same pending help (or open acquisition and re-prompt). Prefer: open acquisition via `_set_pending_next_block` + `start_define_missing_params` then return the help payload for `pending[0]` — **one turn**, 0 LLM |
| Hints for component keys | Small deterministic hint map for `propellers` / `motors` / `battery` / `frame` / … (may reuse `_BLOCK_COMPONENT_HINTS` text or add `COMPONENT_PENDING_HINTS`) |
| Assisted motor params | If `pending[0] ∈ ASSISTED_MOTOR_PARAMS` → delegate to existing `offer_catalog_help()` / FN-005 path |
| Tests | `tests/test_fn015_pending_help.py` |
| Docs | Short FN-015 note in Continuity / IMPLEMENTATION_TASKS |

### Out of scope

- FN-016 (`atrás`, float-as-component)
- Rewriting `ANALYZE_PATTERNS` globally
- Changing LLM prompts
- Auto-jumping to energy/battery when pending is propulsion
- Full humanization of all `param_question` strings (copy cut) — only enough hint text for the help response
- Conversation Engine

---

## 4. Design

### 4.1 Phrase detector: `is_help_define_pending_phrase(user_input) -> bool`

Add next to motor help (preferred: [`motor_catalog_assist.py`](src/jarvis/core/motor_catalog_assist.py) **or** `acquisition_target.py` — pick one module and document why).

**Must match** (normalize accents; examples):

```text
ayudame a definir
ayúdame a definir
ayudame a definir el valor
ayudame a definir esto
ayudame con el valor
como lo defino
cómo lo defino
no se que poner
no sé qué poner
```

**Must NOT match** (leave to existing paths):

```text
ayudame a elegir / ayudame a elegir el motor   → FN-005 is_help_choose_phrase
ayudame a declarar propulsión                  → FN-011/013/014 (named target)
definir propellers                             → FN-014
analiza el margen / explicame el warning       → real analyze (keep LLM)
```

Heuristic (suggested, implementer may refine if tests pass):

```text
normalized has "ayudame" (or "como lo defino" / "no se que poner")
AND NOT is_help_choose_phrase(...)
AND NOT resolve_declare_block_request(...)/resolve_acquisition_mention with a concrete target
AND (
  "definir" in phrase OR "valor" in phrase OR "poner" in phrase
  OR phrase is exactly/near "ayudame a definir"
)
```

Do **not** treat every `ayudame` as pending-help — that would steal real analyze questions.

### 4.2 Payload: help for current pending (no session restart)

```text
_help_current_pending_acquisition(session) -> dict
```

Read `pending = session.pending_param_definitions`. If empty → `None` (fall through).

**Branch on `pending[0]`:**

| pending[0] | Behavior |
|---|---|
| `motor_power_w` / `per_motor_max_thrust_n` | `param_definition_session.offer_catalog_help()` (existing FN-005) |
| Component key (`propellers`, `motors`, `battery`, `frame`, …) | `status=interactive`, `action=define_missing_params`, **do not** call `start()` again; message + question with concrete hint for that key; `pending` unchanged; `block_declaration_reprompt` or new flag `pending_help=True` |
| Other numeric params | Re-ask via existing `_question_for_param(pending[0])` plus one short clarifying line; 0 LLM |

**Component hint examples (deterministic):**

```text
propellers → "Describe las hélices. Ej: '10x4.5' o 'hélices 10 pulgadas'."
motors     → "Describe los motores. Ej: '4x 2306 2400KV' o un modelo del catálogo."
battery    → "Describe la batería. Ej: 'LiPo 6S 5000mAh'."
frame      → "Describe el frame. Ej: 'carbono 450g'."
```

Reuse [`_BLOCK_COMPONENT_HINTS`](src/jarvis/core/orchestrator.py) where the pending key maps cleanly to a block; otherwise a small `COMPONENT_PENDING_HINTS` dict in the same module as the detector.

**Critical:** Message must **not** mention `battery_capacity_wh` / energy when pending is `propellers`/`motors`.

### 4.3 Orchestrator wiring — DEFINE_MISSING

Inside `mode == DEFINE_MISSING_PARAMETERS`, **after** FN-013 re-prompt and **before** the analyze→LLM branch:

```text
if is_help_define_pending_phrase(user_input):
    help_result = self._help_current_pending_acquisition(...)
    if help_result is not None:
        track + return
# existing: if analyze and not is_help_choose_phrase → LLM
```

Also: if `is_help_choose_phrase` → keep current behavior (catalog).

Order:

```text
project_status
→ FN-013 declare-block re-prompt
→ FN-015 help-define-pending     ← NEW
→ FN-005 help-choose (analyze exception) / catalog via answer path
→ analyze → LLM (only if not help-define and not help-choose)
→ …
```

### 4.4 Orchestrator wiring — IDLE (minimal)

If IDLE and `is_help_define_pending_phrase` and system has `_next_pending_block`:

```text
_set_pending_next_block()
start_define_missing_params(...)
then return _help_current_pending_acquisition on the new session
```

If no pending block → `None` (existing routing / LLM OK).

Do **not** invent a Continuity-only soft open without `_next_pending_block`.

### 4.5 Interaction with FN-013 / FN-014

- Named block/component phrases stay on FN-013/014 paths (they run first or resolve via mention helpers).
- FN-015 only for **bare** help-define without a resolvable acquisition mention (or with mention that is not a declare-block request).

If both could match, prefer more specific: mention/declare > help-choose > help-define-pending > analyze.

---

## 5. Acceptance criteria

| # | Scenario | Expected |
|---|---|---|
| A | DEFINE_MISSING, pending=`["propellers"]`, `"ayudame a definir el valor"` | interactive help for propellers; **0 LLM**; pending unchanged; message must not push battery as the next action |
| B | Same, `"ayudame a definir"` | Same as A |
| C | DEFINE_MISSING, pending assisted motor param, `"ayudame a definir"` | Catalog help path (same family as FN-005); 0 LLM |
| D | DEFINE_MISSING, `"ayudame a elegir el motor"` | FN-005 unchanged |
| E | DEFINE_MISSING, `"definir propulsión"` | FN-013 re-prompt unchanged |
| F | DEFINE_MISSING, `"analiza el margen de seguridad"` (or similar real analyze) | Still allowed to reach analyze/LLM |
| G | IDLE, propulsion Phase A pending, `"ayudame a definir"` | Opens acquisition + help for real pending (propellers/motors); 0 LLM; **not** iterate |
| H | collected_params non-empty before help | Still non-empty after (no session restart) |

---

## 6. Tests (required)

File: `tests/test_fn015_pending_help.py`

Reuse fixtures from FN-011/014 (motors declared, propellers pending).

`_RefuseLLM` on A–E, G, H.

Minimum:

1. `test_ayudame_definir_el_valor_helps_propellers_no_llm`
2. `test_ayudame_definir_bare_helps_propellers_no_llm`
3. `test_help_does_not_mention_battery_when_pending_propellers`
4. `test_ayudame_elegir_motor_still_catalog` (regression FN-005)
5. `test_definir_propulsion_still_fn013` (regression)
6. `test_collected_params_preserved_on_help`
7. `test_idle_ayudame_definir_opens_acquisition_help` (criterion G)
8. `test_real_analyze_phrase_still_may_use_llm` — use `_StubLLM` and assert analyze path **or** document if a specific phrase still routes elsewhere; must prove FN-015 does not swallow all `ayudame*`

Run also: FN-011, FN-013, FN-014 test files. Full suite required.

---

## 7. Files allowed

| File | Allowed |
|---|---|
| `src/jarvis/core/motor_catalog_assist.py` and/or `acquisition_target.py` | Detector + optional hints |
| `src/jarvis/core/orchestrator.py` | Wire FN-015 before analyze in DEFINE_MISSING; optional IDLE |
| `src/jarvis/core/param_definition_session.py` | Only if help reuses `_question_for_param` / `offer_catalog_help` publicly — avoid deep rewrites |
| `tests/test_fn015_pending_help.py` | **Create** |
| `docs/PROJECT_CONTINUITY.md` | FN-015 note |
| `docs/IMPLEMENTATION_TASKS.md` | Mark complete when done |

**Forbidden:** expanding `ANALYZE_PATTERNS` removal of `ayudame`; LLM prompt edits; FN-016 navigation; silent energy jump.

---

## 8. Implementation report (Claude Code must return)

1. Diff summary per file  
2. Exact phrase detector rules + non-matches  
3. Where DEFINE_MISSING / IDLE are wired (line-level description)  
4. Proof battery is not suggested when pending is propellers  
5. Test commands + counts  
6. Confirmation: no FN-016 / no Conversation Engine  
7. Residual risks  

---

## 9. Review checklist (Cursor)

- [ ] 0 LLM on field-note help phrases with pending propellers  
- [ ] No energy/battery diversion  
- [ ] Session not restarted (`collected_params` safe)  
- [ ] FN-005 / FN-013 / FN-014 regressions green  
- [ ] Real analyze not entirely stolen  

**Verdict scale:** PASS / PASS WITH NOTES / FAIL  

---

## 10. Non-goals reminder

FN-015 does **not** finish Acquisition Fluency. Next contract remains **FN-016** (navigation / parse safety). Copy polish for all questions stays deferred unless the hint map above is insufficient for acceptance A.
