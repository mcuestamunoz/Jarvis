# Implementation Contract — FN-021

**Project:** Jarvis  
**Date:** 2026-08-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)  

**Status:** APPROVED FOR IMPLEMENTATION  

**Plan ref:** Audit `audit_2026-08-10_engineering_intent_vs_sticky_session.md` — session hygiene first  
**Depends on:** FN-017–020 (closed)  
**Does not implement:** Engineering Intent → goal/DSE bridge; “ayúdame con el siguiente paso” → Continuity; Create→BOM; Conversation Engine; Step D  

**Workflow:** Claude implements + tests + report → Engineer forwards → Cursor reviews. No commit/push unless asked.

**Hard constraint — EVERYTHING GENERIC:**  
Implement architecture-complete / no-next-block cleanup for **any** last acquisition path. Do **not** special-case thrust, empuje, flight_controller, control, or a single field-note phrase as the design center. Field phrases are **acceptance probes only**.

---

## 1. Intent

After architecture acquisition finishes (no next pending block), the runtime session must return to **IDLE** with pending acquisition fields cleared.

Field evidence (probe only):

```text
Arch 4/4 complete, Continuity PASS, user later: "Aumentar el empuje"
Today: still mode=define_missing_params with stale pending_missing_params
       → _handle_component_description → wrong component prompt
If IDLE: intent=iterate (correct class of turn)
```

**Target:** when there is nothing left to acquire for architecture, Jarvis must not keep a zombie `DEFINE_MISSING` session that steals later engineering / iterate / analyze turns.

---

## 2. Root cause

On component (or param) acquisition completion, when `still_missing` is empty:

```text
_set_pending_next_block()
  → _next_pending_block() is None
  → return   // without clear_runtime_session()
```

Session keeps `mode=DEFINE_MISSING_PARAMETERS` and stale `pending_*` / `param_definition_reason`. DEFINE_MISSING branch in `_handle_user_text_inner` runs before iterate.

Same class of bug for **any** final block completion (not control-specific).

---

## 3. Scope

### In scope

| # | Change |
|---|---|
| 1 | When acquisition completes a step and `_next_pending_block` is `None`, **clear** the runtime session to IDLE (not a silent no-op) |
| 2 | Prefer implementing inside `_set_pending_next_block` when `pending is None` **while** current mode is an acquisition wizard (`DEFINE_MISSING_PARAMETERS`), **and/or** at the call sites that finish a wizard when there is no next block — one clear rule, document it |
| 3 | Also clear (or refuse DEFINE_MISSING handling) if somehow still in DEFINE_MISSING with no next block and pending targets already satisfied — defense in depth optional but welcome if tiny |
| 4 | Optional but recommended: `simulate` / `calculate` (and similar strong actions) must not leave the user trapped — if they run while DEFINE_MISSING is stale with arch complete, clear after or before so the next turn is IDLE. Prefer: clear on arch-complete so simulate never sees zombie mode |
| 5 | Tests: generic fixture that completes last architecture gap → IDLE; probe that a post-complete engineering/iterate-class phrase is **not** answered with a component-description prompt for a stale expected key |
| Docs | Short Continuity / IMPLEMENTATION_TASKS note |

### Out of scope

- Mapping “aumentar empuje” (or any intent) to `goal_planner` / DSE  
- Changing iterate wizard behavior beyond receiving the turn  
- “ayúdame con el siguiente paso” → Continuity (follow-up FN)  
- Create→BOM handoff  
- Conversation Engine / Step D  
- Continuity copy / `_BLOCK_COMPONENT_HINTS` “batería y motores”  

---

## 4. Design

### 4.1 Primary rule (normative)

```text
After successfully finishing the current acquisition unit
(component keys for active expected set, or numeric pending list),
if _next_pending_block(project_state) is None:
    clear_runtime_session()  # → IDLE, pending_* empty
else:
    existing _set_pending_next_block / start next wizard behavior
```

`_set_pending_next_block` today:

```text
pending = self._next_pending_block(...)
if pending is None:
    return   # BUG: leaves zombie DEFINE_MISSING
```

**Required change:** if `pending is None` and session is in acquisition mode (`DEFINE_MISSING_PARAMETERS` or equivalent pending flags), call `clear_runtime_session()` (or equivalent reset to IDLE) instead of bare `return`.

If clearing from `_set_pending_next_block` is too broad (e.g. called from IDLE Bug54 prep), gate:

```text
if pending is None:
    if session.mode == DEFINE_MISSING_PARAMETERS:
        clear_runtime_session()
    return
```

Document the gate. Callers that only pre-load from IDLE must keep working.

### 4.2 What “clear” means

Same as existing cancel/escape paths: `mode=IDLE`, empty `pending_param_definitions`, empty `pending_missing_params`, clear `param_definition_reason` / `pending_define_missing` / related acquisition flags. Reuse `clear_runtime_session()` — do not invent a parallel clearer.

### 4.3 Genericity

- Trigger = **no next architecture block**, not “sensors just saved” or “control block”.  
- Acceptance may use the live-shaped drone walk or a minimal N-block fixture.  
- Do not add `if key == "flight_controller"` or thrust-specific branches.

---

## 5. Acceptance criteria

| # | Scenario | Expected |
|---|---|---|
| A | Complete the **last** architecture acquisition gap (any block that makes `_next_pending_block` None) | Session `mode == IDLE`; pending acquisition fields empty |
| B | After A, user phrase that resolves to **iterate** (probe: `"Aumentar el empuje"` or another iterate-class phrase) | Must **not** return `component_description_prompt` / COMPONENT_PROMPTS for a stale expected key; must enter iterate path or documented IDLE handling — **0** zombie DEFINE_MISSING |
| C | Mid-architecture: complete a **non-final** block (next block still exists) | Still opens / pending next block as today (`_set_pending_next_block` / Bug54 behavior preserved) |
| D | FN-016 `atrás` / cancel still clears | Unchanged |
| E | FN-019 bare propeller / FN-018 brief / FN-020 continuity | Regressions green |
| F | No Conversation Engine / no goal_planner keyword expansion in this cut | Confirmed in report |

---

## 6. Tests (required)

File: `tests/test_fn021_session_hygiene.py`

Minimum:

1. `test_last_architecture_gap_clears_to_idle`  
2. `test_after_arch_complete_iterate_phrase_not_stale_component_prompt` (use `_RefuseLLM` / stub as needed; assert not flight_controller / not component_description for stale keys)  
3. `test_non_final_block_still_sets_next_pending`  
4. Smoke: FN-016 cancel or atrás still IDLE  

Reuse existing multi-block fixtures where possible. Full suite. Baseline: **1529** (post count-fix).

---

## 7. Files allowed

| File | Allowed |
|---|---|
| `src/jarvis/core/orchestrator.py` | `_set_pending_next_block` + any finish-path that must clear |
| `src/jarvis/core/state_manager.py` | Only if `clear_runtime_session` needs a tiny helper — prefer existing API |
| `tests/test_fn021_session_hygiene.py` | **Create** |
| `docs/PROJECT_CONTINUITY.md` | FN-021 note |
| `docs/IMPLEMENTATION_TASKS.md` | Mark complete |

**Forbidden:** goal_planner / DSE / intent_resolver edits (unless a one-line prove-out is impossible without — default **no**); Engineering Intent; LLM prompts; Conversation Engine.

---

## 8. Implementation report (Claude)

1. Diff per file  
2. Exact clear rule + gate (when `_set_pending_next_block` clears vs returns)  
3. Proof mid-architecture next-block still works  
4. Proof post-complete iterate-class phrase not stolen by component prompt  
5. Test commands + suite count  
6. Confirmation: generic only; no Engineering Intent / no next-step-help FN / no Conversation Engine  
7. Residuals  

No commit/push unless asked.

---

## 9. Review checklist (Cursor)

- [ ] Arch complete → IDLE, no stale pending  
- [ ] Iterate-class phrase after complete ≠ stale component prompt  
- [ ] Non-final block chaining intact  
- [ ] No thrust/FC special cases  
- [ ] Suite green  

**Verdict:** PASS / PASS WITH NOTES / FAIL  

---

## 10. Queue after PASS

1. **Generic Engineering Intent → goal_planner / DSE** (separate contract; all goals)  
2. Generic next-step help → Continuity / Acquisition Target  
3. Create→BOM handoff  
4. Step D — blocked  
