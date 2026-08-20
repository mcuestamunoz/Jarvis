# Implementation Contract — R3b Real Preempt for DEFINE_MISSING (G7/G11 residual)

**Project:** Jarvis  
**Date:** 2026-08-20  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor (Implementation Review)

**Status:** READY FOR ENGINEER → send to Claude after ratification

**Type:** UX/routing — sub-mode-aware real preempt for `DEFINE_MISSING_PARAMETERS` (closes R3 residual after R3a).

**Investigation:** [`.jes/artifacts/investigation_r3_preempt_policy.md`](investigation_r3_preempt_policy.md) — Option B  
**Prior cut:** [`.jes/artifacts/implementation_contract_r3a_preempt_refuse.md`](implementation_contract_r3a_preempt_refuse.md) (✅ implemented)  
**Checkpoint base:** commit `a918a96` (R3a + CLI-walk fixes + handoff_context preservation)

**Workflow:** Claude implements **Slices 1→2 in order** + tests + report → Engineer → Cursor review → checkpoint only if Engineer asks.

---

## 0. Why this cut

R3a closed the sharpest asymmetry (honest refuse + DSE read-only soft-interrupt) **without** clearing wizard state. Residual from investigation §1.1 / §4:

| Input mid-wizard | Component sub-mode today | Numeric sub-mode today (post-R3a) |
|---|---|---|
| `"aplica la mejor"` | ❌ silent Brief re-show (gate 10d) | ⚠ honest refuse (R3a) — intent never executes |
| bare `"itera material"` | ❌ silent Brief re-show | ⚠ honest refuse |
| `"descartar sugerencia"` / dismiss | ❌ silent Brief re-show | ⚠ honest refuse |
| `"nuevo proyecto"` / create | ❌ silent Brief re-show | ⚠ honest refuse |

R3b implements **Option B** from the investigation: real preempt with sub-mode-aware state handling, mirroring C-052 (`_should_preempt_iterate_wizard`) but respecting §3's asymmetry — **component sub-mode is safe to blind-clear; numeric sub-mode is not when `collected_params` is non-empty.**

**Hard rules:**

- Do **not** regress R3a: soft-interrupts and refuse paths remain unchanged for inputs R3a already handles.
- Do **not** add Option C (confirm-before-discard) — investigation §6 rejected it.
- Components already written to `design_properties.components` must never be reverted.
- **`collected_params` must not be silently lost** in numeric sub-mode.
- Zero weakened tests.

---

## 1. Slices

### Slice 1 — Preempt detector + component sub-mode clear-and-redispatch

**Problem:** Strong intents that mutate project state or switch orchestrator mode are trapped in component sub-mode (silent Brief re-show) or refused but not executed in numeric sub-mode.

**Fix:** Add `_should_preempt_define_missing_wizard(user_input, session) -> bool` and a companion `_preempt_define_missing_message(result, *, partial_apply: bool = False) -> str`, mirroring the iterate wizard pattern (`orchestrator.py:486-564`, `:820-830`).

**Preempt intent set** — `_DEFINE_MISSING_PREEMPT_INTENTS`:

```python
frozenset({
    "apply_exploration_result",
    "iterate",
    "dismiss_suggestion",
    "create_project",
    "define_params",   # only when targeting a *different* block than the active wizard
})
```

**Detection:** Reuse `IntentResolver._resolve_strong_action_intent(normalized)` (same helper C-052 uses). For `define_params`, preempt only when `resolve_declare_block_request(user_input)` names a block **different** from the wizard's active block (same different-block logic `_maybe_refuse_different_target` / R3a already uses). If same-block declare, do **not** preempt — existing FN-013 reprompt handles it upstream.

**Gate placement:** In the `DEFINE_MISSING_PARAMETERS` branch, **after** all existing soft-interrupts and R3a gates (project_status, list_materials, list_motors, FN-013 reprompt, FN-015 help, analyze/help-choose, calculate, simulate, navigation-back, R3a explore soft-interrupt) and **before** the component/numeric sub-mode fork (`MISSING_COMPONENT_DEFINITION` intercept at ~959).

**Execution — component sub-mode** (`param_definition_reason == MISSING_COMPONENT_DEFINITION`):

1. If `_should_preempt_define_missing_wizard` → True:
2. `self.state_manager.clear_runtime_session()` — safe per investigation §3.1 (accepted components already on disk).
3. Recursive `_handle_user_text_inner(user_input, llm_interface)`.
4. Prefix result with `_preempt_define_missing_message(...)` and set `preempted_define_missing: True` on the result dict (mirror `preempted_iterate`).

**Notice text (component sub-mode):**

```text
He cerrado la definición en curso para atender esta instrucción.
```

**Files changed:**

- `src/jarvis/core/orchestrator.py` — detector, message helper, gate + execution path.

**Tests** (new file `tests/test_r3b_preempt_real.py` recommended):

- `test_r3b_component_submode_apply_exploration_preempts` — component wizard open, `"aplica la mejor"` with `last_exploration_result` seeded → apply executes, wizard cleared, notice present.
- `test_r3b_component_submode_bare_iterate_preempts` — component wizard, `"itera material del frame"` → iterate wizard starts (or iterate action), not silent Brief re-show.
- `test_r3b_component_submode_dismiss_preempts` — component wizard + pending suggestion → dismiss executes.
- `test_r3b_component_submode_create_project_preempts` — component wizard, `"nuevo proyecto"` → create flow starts.
- `test_r3b_component_submode_real_component_description_not_preempted` — `"4x 2306 2400KV 50W"` while defining motors → **no** preempt (regression guard).

---

### Slice 2 — Numeric sub-mode partial-apply-then-preempt

**Problem:** Numeric sub-mode may hold unsaved progress in `session.collected_params` (investigation §3.1). Blind `clear_runtime_session()` loses typed values.

**Fix:** When preempt fires in **numeric sub-mode** (`param_definition_reason != MISSING_COMPONENT_DEFINITION`):

1. If `session.collected_params` is **non-empty**:
   - Call `self.param_definition_session.apply_and_recalculate(session.collected_params)` **first** (same proven path as skip-to-completion at `param_definition_session.py:605-607`).
   - Capture whether partial apply succeeded (status ok vs structural-confirm interrupt).
   - If `begin_structural_confirm` fires (FN-004 structural substitution), **abort preempt** — return the structural-confirm response unchanged; do not clear and redispatch.
2. If `collected_params` is empty OR partial apply completed (session already cleared by `apply_and_recalculate`):
   - If session still open (empty collected path only), `clear_runtime_session()`.
   - Recursive `_handle_user_text_inner(user_input, llm_interface)`.
3. Prefix notice; include partial-apply note when step 1 ran:

```text
He cerrado la definición en curso para atender esta instrucción.
(Se aplicaron los parámetros que ya habías indicado.)
```

**Important:** Partial apply is a **side effect** the user did not explicitly request. The notice MUST mention it when it happens. Do not silent-apply.

**R3a interaction:** Inputs that R3a already handles (`explore_design_space` with resolvable goal → soft-interrupt; engineering-intent/explore without resolvable goal → refuse) must still be handled by R3a gates **before** this preempt gate. The preempt set intentionally **excludes** `explore_design_space`, `calculate`, `simulate` — those already execute inline without clearing.

**Files changed:**

- `src/jarvis/core/orchestrator.py` — numeric sub-mode branch in preempt execution.
- Possibly `src/jarvis/core/param_definition_session.py` — **only if** a small, read-only helper is needed to apply `collected_params` without duplicating `apply_and_recalculate` logic. Prefer calling the existing method.

**Tests:**

- `test_r3b_numeric_submode_preempt_with_empty_collected_params` — wizard open, no collected params, `"aplica la mejor"` → preempt + apply executes.
- `test_r3b_numeric_submode_preempt_partial_apply_then_preempt` — collect 1 of 2 params (e.g. `motor_count=4` typed, second pending), then `"itera material"` → partial apply persists `motor_count`, then iterate starts; notice mentions partial apply.
- `test_r3b_numeric_submode_preempt_aborts_on_structural_confirm` — collected params trigger FN-004 structural confirm → preempt does **not** proceed; wizard state preserved for confirm flow.
- `test_r3b_numeric_submode_real_value_not_preempted` — `"12.0"` → accepted as value (regression).
- `test_r3b_reentry_component_submode_resumes_gap` — preempt from component wizard, re-open same block via `"ayúdame a elegir"` → resumes at correct pending component (already saved components reflected).

---

## 2. Scope boundaries

### In scope

- `_should_preempt_define_missing_wizard` detector.
- Component sub-mode: clear + redispatch (Slice 1).
- Numeric sub-mode: partial-apply + clear + redispatch (Slice 2).
- Notice messages + `preempted_define_missing` result flag.
- Regression tests mirroring `tests/test_orchestrator.py` iterate-preempt tests (~689-807).

### Out of scope (do not implement)

- Option C confirm-before-discard interaction state.
- Changes to R3a refuse / explore soft-interrupt / `_maybe_refuse_numeric_submode`.
- Changes to `_maybe_refuse_different_target` (component ★2 refuse for engineering-intent — stays as refuse unless preempt intent matches).
- `engineering_intent` plan display via preempt (e.g. `"reducir payload"` executing the plan) — remains R3a refuse unless it also matches a preempt intent above.
- G9-A catalog_ref blind spot (separate IC).
- G12 retarget paths (separate).
- ITERATE_INTERACTIVE preempt changes (C-052 already closed).

---

## 3. Acceptance criteria

1. `"aplica la mejor"` mid component wizard → exploration result applied, wizard cleared, notice shown — **not** silent Brief re-show.
2. bare `"itera X"` mid component wizard → iterate flow starts — **not** silent Brief re-show.
3. `"descartar sugerencia"` / dismiss mid wizard → suggestion dismissed.
4. `"nuevo proyecto"` mid wizard → create-project flow starts.
5. Numeric wizard with non-empty `collected_params` + preempt → partial apply runs first, notice mentions it, then original intent executes.
6. Numeric wizard with empty `collected_params` + preempt → direct clear + redispatch, no partial-apply notice.
7. FN-004 structural confirm intercepts preempt when partial apply would trigger substitution confirm.
8. Real component descriptions and numeric values still accepted normally (regression).
9. R3a tests (`tests/test_r3a_preempt_refuse.py`) unchanged and passing.
10. Full suite green (1867+ baseline).

---

## 4. Decision log

| # | Decision | Rationale |
|---|---|---|
| ★1 | Option B only (investigation §6) | Closes G7/G11 residual; Option A already shipped as R3a |
| ★2 | Sub-mode-aware execution | §3.1: blind clear safe for component, lossy for numeric with collected_params |
| ★3 | Partial apply before clear (numeric) | Reuses proven `apply_and_recalculate` path; investigation §3.3 option (a) |
| ★4 | Abort preempt on structural confirm | FN-004 is a real interrupt — do not bypass with preempt |
| ★5 | Exclude explore/calculate/simulate from preempt set | Already soft-interrupt inline in DEFINE_MISSING; R3a adds explore read-only |
| ★6 | Mirror C-052 structure, not copy ownership guards | DEFINE_MISSING has no iterate-style "strategy selection ownership" ambiguity |
| ★7 | `preempted_define_missing` flag on result | Parallel to `preempted_iterate` for CLI/test observability |

---

## 5. Review checklist (Cursor — mandatory)

1. Verify gate ordering: R3a soft-interrupts/refuses run **before** R3b preempt.
2. Verify numeric partial-apply notice appears when and only when `collected_params` was non-empty and apply succeeded.
3. Verify FN-004 structural confirm blocks preempt (no silent state loss).
4. Verify component sub-mode preempt does not revert `design_properties.components` already saved.
5. Verify `_should_preempt_define_missing_wizard` does **not** fire on real component specs or numeric floats.
6. Run `tests/test_r3b_preempt_real.py` + full suite.
7. Confirm zero regressions in `tests/test_r3a_preempt_refuse.py`.

---

**End of contract.**
