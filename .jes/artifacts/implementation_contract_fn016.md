# Implementation Contract — FN-016

**Project:** Jarvis  
**Date:** 2026-08-08  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** APPROVED FOR IMPLEMENTATION  

**Plan ref:** Acquisition Fluency Architecture — Corte 3  
**Depends on:** FN-013, FN-014, FN-015 (closed)  
**Does not implement:** Conversation Engine, full step-stack undo, Phase-A copy rewrite, silent cross-block jumps  

---

## 1. Intent

Inside an open acquisition wizard (`DEFINE_MISSING_PARAMETERS`), navigation words and unsafe parses must **never** be absorbed as parameter values.

Field-note cases:

```text
A) DEFINE_MISSING (Phase A or B)
   User: "atrás"  /  "atras"  /  "volver"
   Today: no navigation vocabulary → falls into value parse / "No reconozco … como valor"
          (Phase B: risk of mis-absorption via float/keyword parsers)
   Target: deterministic non-value handling — cancel the wizard (same family as ESCAPE),
           0 LLM, no collected_params mutation from that turn

B) DEFINE_MISSING where pending[0] is a component key
   (motors / propellers / battery / frame / …)
   User: bare number e.g. "10"  or float-shaped input treated as the "value" of that key
   Today: ParamDefinitionSession.answer can zip floats onto pending keys
          → would store propellers=10.0 as a numeric "param" (corruption class)
   Target: never assign raw float to a component-key pending item;
           re-prompt / help for the component instead (0 LLM)
```

Success for the CLI fluency chain after FN-014/015:

```text
… → acquisition open on propellers
→ "atrás" → wizard cancelled cleanly (not a value)
→ reopen / continue acquisition as before
→ "10x4.5" still applies as a real propeller description (unchanged)
```

---

## 2. Root cause

1. **Navigation:** `ESCAPE_WORDS` (`cancelar`, `salir`, …) do **not** include `atrás`/`volver`. Intent resolver has “siguiente …” orientation phrases, not back/cancel. Inside `ParamDefinitionSession.answer`, non-numeric non-skip text becomes `"No reconozco '{input}' como valor"`; with numbers present, bidir/positional float parse can consume input as values.

2. **Component-key float:** `answer()` assumes every `pending[0]` is a numeric engineering parameter. Phase A usually routes via `pending_missing_reason == MISSING_COMPONENT_DEFINITION` → `_handle_component_description`, but defense-in-depth is missing: if a component key ever sits in `pending_param_definitions` on the numeric path (or reason is wrong), `parse_floats_from_input` + `zip(pending, values)` will treat `propellers` like `motor_power_w`.

FN-013/014/015 fix *routing into* help/acquisition; they do not harden *value absorption* once inside the wizard.

---

## 3. Scope

### In scope

| Area | Change |
|---|---|
| Navigation vocabulary | Minimal exact-phrase set: `atrás` / `atras` / `volver` (normalize accents; strip; lower). Optional near-exact: `vuelve` — only if tests keep it unambiguous. **Do not** add free-form “quiero volver al paso anterior” NLP. |
| DEFINE_MISSING / param session | Before float/keyword parse: if navigation word → **cancel session** (same outcome shape as existing ESCAPE handling in `ParamDefinitionSession.answer` / orchestrator escape). Prefer implementing the check inside `ParamDefinitionSession.answer` **and** early in the DEFINE_MISSING branch for `MISSING_COMPONENT_DEFINITION` (component path never hits `answer`). |
| Component-key guard | Shared frozenset of component suggested_keys (reuse `_COMPONENT_PROMPTS` keys and/or all values from `BLOCK_TO_COMPONENTS` — one source of truth, document which). If `pending[0]` ∈ that set → **never** assign floats via positional/bidir parse; return interactive re-prompt / FN-015-style hint (`_COMPONENT_PROMPTS` / `_question` / existing component prompt). |
| Tests | `tests/test_fn016_navigation_parse_safety.py` |
| Docs | Short FN-016 note in Continuity / IMPLEMENTATION_TASKS |

### Out of scope

- Full undo stack (“pop last collected param / last component write”)
- Adding `atrás` to **global** `ESCAPE_WORDS` for IDLE / iterate / create (scope navigation to acquisition wizards only unless a shared helper is clearly gated by mode)
- Conversation Engine / Decision Engine
- Rewriting `ANALYZE_PATTERNS` / LLM prompts
- Copy polish for `¿Cuál es el valor de X?` (Corte 4 — still deferred)
- Fixing wrong-named-block-while-wizard-open LLM leak (FN-015 residual)
- Changing physics, catalog, Continuity formula

---

## 4. Design

### 4.1 Navigation detector

Preferred location: small helper next to existing escape handling — e.g. in `jarvis.config` as `NAVIGATION_BACK_WORDS` **or** a one-liner in `param_definition_session.py` / `acquisition_target.py`. Pick one module; do not duplicate lists.

```text
is_navigation_back_phrase(user_input) -> bool
```

Rules:

1. Normalize: strip, lower, strip diacritics (same style as other phrase helpers).
2. Match **exact** token/phrase only — entire input after normalize is one of: `atras`, `volver` (and optionally `vuelve`).
3. Must **not** match: `cancelar` (already ESCAPE), `omitir`/`después` (skip), `ayudame a definir`, `definir propulsión`, `10x4.5`, `350`, real analyze phrases.

**Behavior when true (DEFINE_MISSING / ParamDefinitionSession):**

```text
clear_runtime_session()  # or existing cancel path
return {
  status: "cancelled",
  action: "define_missing_params",
  message: <existing cancel message or short equivalent:
            "Definición cancelada. Puedes retomar cuando quieras.">
}
```

Do **not** invent a new Conversation Engine step. Do **not** silently skip the current param (that is `_SKIP_PHRASES`).

Wire also on the **component-description** DEFINE_MISSING path (before `infer_components`), so Phase A `"atrás"` cancels instead of falling into low-completeness follow-ups.

### 4.2 Component-key parse guard

In `ParamDefinitionSession.answer`, **before** `parse_floats_from_input` / bidir assignment:

```text
if current in COMPONENT_KEYS_FOR_ACQUISITION:
    # never zip floats onto this key
    return interactive re-prompt / hint for current
           (reuse _COMPONENT_PROMPTS via orchestrator helper if available,
            or a thin local message + param_question — prefer reusing FN-015
            hint text; do not invent battery when current is propellers)
```

Also refuse the positional `zip(pending, values)` path when **any** consumed pending key in the zip would be a component key (defense if multiple pending).

If `pending_missing_reason == MISSING_COMPONENT_DEFINITION`, orchestrator already avoids `answer()` — guard still required for defense-in-depth and for any future/mis-set reason.

**Must still allow:** real component descriptions with numbers inside text (`"10x4.5"`, `"4 motores 920KV"`) on the **component inference** path — unchanged.

### 4.3 Precedence inside DEFINE_MISSING

Keep existing order; insert navigation cancel early:

```text
project_status / globals (existing)
FN-013 block re-prompt
FN-015 bare help-define
FN-005 help-choose / analyze branch (existing)
… calculate/simulate …
*** NEW: navigation-back → cancel (Phase A component path AND before answer) ***
MISSING_COMPONENT_DEFINITION → _handle_component_description
… battery intercept …
ParamDefinitionSession.answer
  *** NEW: navigation-back (if not already handled)
  *** NEW: component-key guard before float zip
```

FN-013/014/015 must remain first for their phrases; navigation is exact single-word/short phrases and will not steal them.

### 4.4 IDLE

No IDLE change required unless `"atrás"` with no session should stay no-op (current behavior). Do **not** open acquisition on bare `atrás` in IDLE.

---

## 5. Acceptance criteria

| # | Scenario | Expected |
|---|---|---|
| A | DEFINE_MISSING Phase A (pending propellers), `"atrás"` | `status=cancelled`; session cleared / IDLE; **0 LLM**; no component write |
| B | DEFINE_MISSING Phase B (numeric pending e.g. `per_motor_max_thrust_n`), `"atrás"` / `"volver"` | Same cancel; **0 LLM**; `collected_params` not updated by that turn |
| C | DEFINE_MISSING Phase B, `"350"` (or valid bare watts when assisted) | Still accepted as value (regression — navigation must not break numeric entry) |
| D | DEFINE_MISSING Phase A, `"10x4.5"` (or existing propeller description fixture) | Still saves / advances component path (regression) |
| E | If `answer()` is entered with `pending[0]=="propellers"` (force via test harness), input `"10"` | **Must not** store `collected_params["propellers"]=10`; interactive re-prompt/help instead |
| F | DEFINE_MISSING, `"definir propulsión"` | FN-013 unchanged |
| G | DEFINE_MISSING, `"ayudame a definir"` | FN-015 unchanged |
| H | DEFINE_MISSING, `"cancelar"` | Existing ESCAPE unchanged |
| I | IDLE, `"atrás"` | Does **not** open DEFINE_MISSING; no crash |

---

## 6. Tests (required)

File: `tests/test_fn016_navigation_parse_safety.py`

Reuse FN-011/013/015 fixture patterns (`_RefuseLLM`, propulsion with propellers pending).

Minimum:

1. `test_atras_cancels_component_acquisition_phase_a`
2. `test_volver_cancels_numeric_wizard_phase_b`
3. `test_numeric_value_still_accepted_phase_b` (criterion C)
4. `test_propeller_description_still_works_phase_a` (criterion D)
5. `test_bare_float_not_assigned_to_component_key_pending` (criterion E — may call `ParamDefinitionSession.answer` with a crafted session)
6. `test_definir_propulsion_still_fn013` (regression)
7. `test_ayudame_definir_still_fn015` (regression)
8. `test_cancelar_still_escape` (criterion H)
9. `test_idle_atras_does_not_open_acquisition` (criterion I)

Run also: `tests/test_fn013_*.py`, `tests/test_fn014_*.py`, `tests/test_fn015_*.py`, plus a focused slice of `tests/test_assisted_acquisition.py` / `tests/test_define_*` if touched. Full suite required before report.

---

## 7. Files allowed

| File | Allowed |
|---|---|
| `src/jarvis/config.py` | Optional `NAVIGATION_BACK_WORDS` frozenset |
| `src/jarvis/core/param_definition_session.py` | Navigation cancel + component-key float guard |
| `src/jarvis/core/orchestrator.py` | Phase-A navigation cancel before `_handle_component_description`; thin wiring only |
| `src/jarvis/core/acquisition_target.py` | Optional detector helper if preferred over config |
| `tests/test_fn016_navigation_parse_safety.py` | **Create** |
| `docs/PROJECT_CONTINUITY.md` | FN-016 note |
| `docs/IMPLEMENTATION_TASKS.md` | Mark complete when done |

**Forbidden:** Conversation Engine; global iterate/IDLE behavior changes beyond no-op IDLE `atrás`; ANALYZE_PATTERNS edits; LLM prompt edits; silent energy diversion; full undo stack.

---

## 8. Implementation report (Claude Code must return)

1. Diff summary per file  
2. Exact navigation word list + match rules  
3. Component-key set used for the float guard + where checked  
4. Where Phase A vs Phase B cancel is wired (line-level)  
5. Proof bare float does not land on `propellers` in collected_params  
6. Test commands + counts (include pre-FN-016 baseline if known: **1485**)  
7. Confirmation: no Conversation Engine / no Corte-4 copy rewrite / no FN-015 regressions  
8. Residual risks  

---

## 9. Review checklist (Cursor)

- [ ] `"atrás"`/`"volver"` cancel DEFINE_MISSING; 0 LLM; no value write  
- [ ] Bare float cannot become `collected_params[component_key]`  
- [ ] Phase A description + Phase B numeric entry regressions green  
- [ ] FN-013 / FN-015 regressions green  
- [ ] IDLE `"atrás"` does not open acquisition  
- [ ] No Conversation Engine / no global ESCAPE expansion that breaks iterate  

**Verdict scale:** PASS / PASS WITH NOTES / FAIL  

---

## 10. Non-goals reminder

FN-016 finishes Acquisition Fluency Corte 3 (navigation + parse safety).  
**Corte 4 (copy)** remains deferred unless `¿Cuál es el valor de X?` still hurts after this cut.  
Wrong-block-while-wizard LLM leak remains a known residual, not this contract.
