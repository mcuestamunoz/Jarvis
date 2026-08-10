# Implementation Contract — FN-017

**Project:** Jarvis  
**Date:** 2026-08-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** APPROVED FOR IMPLEMENTATION  

**Plan ref:** Acquisition Guided Engineering — Step B (P0 Plumbing)  
**Depends on:** FN-014, FN-015, FN-016 (closed); principle ratified  
**Does not implement:** Acquisition Brief (C), Guided Engineering subsystem (D), Conversation Engine, Corte-4 prose essays  

**Workflow reminder:** Claude Code implements + tests + report. Cursor reviews only after Engineer forwards the report. No commit/push unless Engineer asks separately.

---

## 1. Intent

Fix live plumbing that makes *any* acquisition UX (including future Brief) lie about the current target.

Field-note session (propulsion / propellers pending):

```text
definir propulsión → ¿Cuál es el valor de propellers?          # copy thin — OK for later C
declarar batería / 10x4.5 / 5 / definir hélices
  → "Indica material y masa. Ej: fibra de carbono 450g"       # WRONG — frame fallback
plastico 450g → "Generic component registrado."               # WRONG — silent junk write
declarar motores (IDLE, motors already high, propellers low)
  → wizard per_actuator_torque_nm (terrestrial)               # WRONG domain — verify+fix
```

**Target after FN-017:**

```text
Phase A open on propellers:
  low / unclear input → propellers hint (_COMPONENT_PROMPTS), never frame material/masa
  hélices 10x4.5 (or accepted propeller phrase) → saves propellers
  generic-only match → refuse write; re-prompt pending key
  session.pending_missing_params mirrors pending component keys while wizard active

IDLE aerial, motors complete, propellers incomplete:
  "declarar motores" does NOT open transmission torque wizard
  Prefer: reopen/continue propulsion Phase A (propellers) OR clear mismatch-style message
```

---

## 2. Root causes (do not conflate with Guidance)

1. **`ParamDefinitionSession.start()`** builds a fresh session with `param_definition_reason` + `pending_param_definitions` but **does not set** `pending_missing_params`. `_handle_component_description` reads `expected_keys = session.pending_missing_params` → `[]` on live turns.

2. **Low-completeness fallback** in `_handle_component_description` (~1748–1762) is frame-centric (`mass_kg`/`material` probes + default “Indica material y masa…”) for any non-FC/sensors key — including propellers/battery/motors.

3. **`generic_component` medium** with empty `expected_keys` is applied via `_apply_inferred_component_spec` → “Generic component registrado.”

4. **IDLE `declarar motores`:** FN-014 declines (motors not a gap) → fall-through to Bug41 `define_params` / terrestrial `MISSING_TRANSMISSION_PARAMETERS` → `per_actuator_torque_nm` on a **dron** project.

---

## 3. Scope

### In scope (B only)

| # | Change |
|---|---|
| B1 | Keep `pending_missing_params` coherent for component-definition wizards |
| B2 | `_handle_component_description` uses those keys (or `pending_param_definitions` when reason is `MISSING_COMPONENT_DEFINITION`) as `expected_keys` |
| B3 | Low-completeness / unclear input → **key-aware** prompt from `_COMPONENT_PROMPTS` / `_component_prompt_for_first_missing(expected)`, never frame default when pending is another key |
| B4 | Refuse silent `generic_component` writes when expected keys are set (or always refuse generic write in this path — prefer: no write + re-prompt) |
| B5 | Phase A `start()` first question: if reason is `MISSING_COMPONENT_DEFINITION` and first key ∈ `_COMPONENT_PROMPTS`, use that prompt (not `¿Cuál es el valor de propellers?`) — **minimal**; not full Brief (C) |
| B6 | Aerial / non-terrestrial: do not open transmission torque wizard on `declarar motores` when propulsion still has component gaps (propellers) — route to Phase A or deterministic message |
| Tests | `tests/test_fn017_component_acquisition_plumbing.py` |
| Docs | Short FN-017 note in Continuity / IMPLEMENTATION_TASKS |

### Out of scope

- Acquisition Brief template (qué / por qué / opciones / consecuencia) — **C**  
- Guided Engineering subsystem — **D**  
- Conversation Engine  
- Registry change to accept bare `10x4.5` without “hélices” — **optional stretch**; if easy and tested, OK; otherwise document as follow-up (key-aware prompt alone fixes the misleading frame message)  
- Propulsion-vs-battery product priority  
- Rewriting Continuity formula / LLM prompts / 13 checkpoints  

---

## 4. Design

### 4.1 B1 — Populate `pending_missing_params` on start

In `ParamDefinitionSession.start(missing_params, reason=...)`:

When `reason == MISSING_COMPONENT_DEFINITION`, set on the new `InteractiveSessionState`:

```text
pending_missing_params = list(missing_params)
pending_missing_reason = MISSING_COMPONENT_DEFINITION   # optional but recommended for symmetry
```

(Keep `pending_param_definitions` as today.)

Alternatively (also acceptable): in `_handle_component_description`, if `param_definition_reason == MISSING_COMPONENT_DEFINITION` and `pending_missing_params` empty, use `pending_param_definitions` as `expected_keys`. Prefer **both**: populate on start + defensive read.

Prove with assertion in tests / optional snapshot shape: after opening Phase A, `pending_missing_params == ["propellers"]` (or current missing keys).

### 4.2 B2–B3 — Key-aware low path

Replace frame-default branch when `expected_keys` non-empty:

```text
if completeness low / no processable in-scope specs:
  return interactive prompt = _component_prompt_for_first_missing(expected_keys)
  # which already uses _COMPONENT_PROMPTS
```

Frame-specific mass/material follow-ups **only** when the pending/expected key is `frame` (or inferred spec is frame with partial props).

### 4.3 B4 — Generic write protection

If the only processable/inferred spec is `generic_component` (or no in-scope match):

- **Do not** call `_apply_inferred_component_spec` / do not persist `generic_component`.
- Return interactive re-prompt for expected pending key (+ short message that the description was not recognized as that component).

### 4.4 B5 — Opening question for Phase A

In `start()` (or orchestrator wrapper that surfaces the first question): if component-definition reason and first key in `_COMPONENT_PROMPTS`, question/message = that prompt string.

Still **not** a multi-paragraph Brief.

### 4.5 B6 — Aerial motors ≠ transmission torque

Smallest safe fix (pick one, document which):

**Preferred:** In IDLE acquisition / define_params path: if vehicle is aerial (or architecture has `propulsion` composite) and `_next_pending_block` is propulsion with propellers still incomplete, and user mention resolves to motors (already high): open/continue Phase A for remaining propulsion components (same Bug54 bridge) **or** return deterministic “motores ya declarados; falta definir hélices” + start propellers acquisition — **0 LLM**, no `per_actuator_torque_nm`.

**Do not** broaden Bug41 terrestrial keywords globally without an aerial gate.

If full B6 proves entangled with intent_resolver, minimum bar for FN-017: **prove with test** that aerial + motors high + propellers low + `declarar motores` does not ask torque; implement the smallest gate that passes. Flag residual in report if intent_resolver change was required.

### 4.6 Precedence

Do not break FN-013/014/015/016. Plumbing sits inside existing DEFINE_MISSING / start / component handler.

---

## 5. Acceptance criteria

| # | Scenario | Expected |
|---|---|---|
| A | Open Phase A propellers; inspect session | `pending_missing_params` contains `propellers` (non-empty) |
| B | Phase A open; input that yields low/unclear (`definir hélices`, `5`, `declarar batería`) | Message uses **propellers** prompt family (`_COMPONENT_PROMPTS["propellers"]` / hélices), **not** “Indica material y masa” / frame |
| C | Phase A; `hélices 10x4.5` (registry-known phrase) | Saves propellers; not generic |
| D | Phase A; `plastico 450g` (or similar generic) | **No** `generic_component` in components; interactive re-prompt; propellers still pending |
| E | Phase A start question | Not `¿Cuál es el valor de propellers?` — uses component prompt |
| F | Aerial project, motors high, propellers low, IDLE `declarar motores` | Does **not** open `per_actuator_torque_nm` wizard |
| G | FN-013 `definir propulsión` / FN-015 `ayudame a definir` / FN-016 `atrás` | Regressions green |
| H | Real frame acquisition still asks material/masa when pending/expected is `frame` | Unbroken |

---

## 6. Tests (required)

File: `tests/test_fn017_component_acquisition_plumbing.py`

Reuse FN-011/016 fixture patterns (`_RefuseLLM`, motors high / propellers pending).

Minimum:

1. `test_phase_a_session_has_pending_missing_params`  
2. `test_unclear_input_prompts_propellers_not_frame`  
3. `test_helices_description_saves_propellers`  
4. `test_generic_description_does_not_write_generic_component`  
5. `test_phase_a_start_question_uses_component_prompt`  
6. `test_declarar_motores_aerial_does_not_open_torque_wizard`  
7. `test_frame_pending_still_asks_material_masa` (or equivalent structure fixture)  
8. FN-013 / FN-015 / FN-016 smoke regressions (1 each or import-style calls)

Run also: `test_fn014_*`, `test_fn015_*`, `test_fn016_*`, focused component tests if touched. Full suite before report. Baseline pre-FN-017: **1496**.

---

## 7. Files allowed

| File | Allowed |
|---|---|
| `src/jarvis/core/param_definition_session.py` | Populate pending_missing_* on start; Phase A question |
| `src/jarvis/core/orchestrator.py` | expected_keys fallback; key-aware low path; generic refuse; B6 aerial gate wiring |
| `src/jarvis/core/acquisition_target.py` | Only if B6 needs a tiny helper |
| `src/jarvis/core/intent_resolver.py` | Only if B6 requires aerial gate — **minimize**; document in report |
| `tests/test_fn017_component_acquisition_plumbing.py` | **Create** |
| `docs/PROJECT_CONTINUITY.md` | FN-017 note |
| `docs/IMPLEMENTATION_TASKS.md` | Mark complete |

**Forbidden:** Guidance Brief multi-section copy; Conversation Engine; Continuity redesign; silent energy jump; large orchestrator rewrite.

---

## 8. Implementation report (Claude Code must return)

1. Diff summary per file  
2. How `pending_missing_params` is kept coherent (start + read path)  
3. Exact low-path prompt rule (when frame vs `_COMPONENT_PROMPTS`)  
4. Generic write protection rule  
5. B6 approach + proof no torque on aerial `declarar motores`  
6. Whether bare `10x4.5` was included or deferred  
7. Test commands + counts (expect 1496 + N)  
8. Confirmation: no Brief (C) / no Guided Engineering (D) / no Conversation Engine  
9. Residual risks  

**No commit, no push** unless Engineer asks.

---

## 9. Review checklist (Cursor)

- [ ] Live Phase A: `pending_missing_params` non-empty  
- [ ] Unclear input ≠ frame material/masa when pending propellers  
- [ ] No silent `generic_component`  
- [ ] Opening question uses component prompt  
- [ ] Aerial `declarar motores` ≠ torque wizard  
- [ ] Frame path still works  
- [ ] FN-013/015/016 green  
- [ ] No C/D scope creep  

**Verdict scale:** PASS / PASS WITH NOTES / FAIL  

---

## 10. Non-goals reminder

FN-017 is **Step B only**. After PASS, Engineer may authorize **C — Acquisition Brief**. Do not start C inside this cut.
