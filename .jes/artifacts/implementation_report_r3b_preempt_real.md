# Implementation Report — R3b Real Preempt for DEFINE_MISSING (G7/G11 residual)

**Contract:** [`implementation_contract_r3b_preempt_real.md`](implementation_contract_r3b_preempt_real.md)
**Investigation:** [`investigation_r3_preempt_policy.md`](investigation_r3_preempt_policy.md)
**Checkpoint base:** `checkpoint-r3a` (`d484ea2`) + uncheckpointed `0044868`, `a918a96`
**Status:** Implemented, both slices, 10 new tests added, full suite green (1877). **Not committed** (per contract §"checkpoint only if Engineer asks").

---

## Slices completed

- [x] Slice 1 — preempt detector + component sub-mode clear-and-redispatch
- [x] Slice 2 — numeric sub-mode partial-apply-then-preempt

---

## Files changed

| File | What |
|---|---|
| `src/jarvis/core/orchestrator.py` | `_DEFINE_MISSING_PREEMPT_INTENTS`, `_should_preempt_define_missing_wizard`, `_preempt_define_missing_message`, `_clear_runtime_session_preserving_dse` (new helper, see deviation #2), gate + sub-mode-aware execution inserted into the `DEFINE_MISSING_PARAMETERS` branch. |
| `tests/test_r3b_preempt_real.py` | New — 10 tests (5 per slice, matching the contract's named cases, one renamed — see below). |

No changes to `tests/test_r3a_preempt_refuse.py`, `_maybe_refuse_different_target`, `_maybe_refuse_numeric_submode` bodies, or any ITERATE_INTERACTIVE code (C-052 untouched).

---

## Deviations from the contract, found during implementation

### 1. `define_params` (different-block) dropped from the preempt intent set — required to avoid regressing R3a and an existing FN-013 test

The contract's Hard Rule (§0) and review checklist (#1) both require R3a's refuse to keep winning for inputs it already owns. Implementing the gate exactly as placed ("before the sub-mode fork") without also re-running R3a's refuse checks first caused an immediate regression: `"reducir payload"` resolves to strong-intent `"iterate"` (via `ITERATE_PATTERNS`' bare `reducir`) **and** to R3a's engineering-intent refuse — the same collision shape ★3/G11-B already documents for the iterate wizard. Fixed by running the sub-mode-appropriate R3a refuse check (`_maybe_refuse_different_target` / `_maybe_refuse_numeric_submode`) **first**, at the gate itself, and only evaluating the R3b preempt when it returns `None`.

That fix then exposed a second, deeper issue specific to `define_params`: once R3a's refuse runs first, it turns out R3a's refuse **already owns every case** where a declare-different-block phrase would be safe to act on. The only cases where `_maybe_refuse_different_target`/`_maybe_refuse_numeric_submode` do *not* refuse are ones where the resolved target block shares a component with the active wizard (e.g. `"motors"` belongs to both `propulsion` and `energy` in `BLOCK_TO_COMPONENTS`). For exactly that shared-component case, `tests/test_fn013_active_block_declare_routing.py::test_definir_energia_while_propulsion_active_does_not_jump` already asserts the wizard must **park** (stay in `DEFINE_MISSING_PARAMETERS`, not jump to a new wizard) — a third, deliberate behavior distinct from both "refuse" and "preempt". Including `define_params` in the R3b intent set overrode that test's intent (mode ended up `IDLE` instead of `DEFINE_MISSING_PARAMETERS`).

**Fix:** removed `define_params` from `_DEFINE_MISSING_PREEMPT_INTENTS`. The remaining four intents (`apply_exploration_result`, `iterate`, `dismiss_suggestion`, `create_project`) — the ones the contract's own §0 residual table actually documents as broken — are unaffected. This is documented inline at the intent set's definition.

### 2. `last_exploration_result` must be preserved across the clear, or `apply_exploration_result` always fails post-preempt

A blind `clear_runtime_session()` resets to a brand-new `InteractiveSessionState()`, which wipes `last_exploration_result` (runtime-only, never persisted to disk — unlike accepted components). Since that field is exactly what `_handle_apply_exploration()` reads, the very first acceptance criterion (`"aplica la mejor"` → exploration applied) was failing with `"No hay resultados de exploración recientes"` immediately after the preempt that was supposed to execute it.

**Fix:** added `_clear_runtime_session_preserving_dse(session)` — clears normally, then carries `last_exploration_result` forward onto the fresh session, same precedent as the existing `handoff_context` forwarding added in `0044868` for R3a Slice 2. Used in both sub-mode clear paths.

### 3. Numeric sub-mode: apply *before* clearing, not after

The contract's Slice 2 text says "session already cleared by `apply_and_recalculate`" — in the two pre-existing call sites (`ParamDefinitionSession.answer()`), the caller clears *before* calling `apply_and_recalculate`, not the method itself. Clearing first here would break ★4 (abort must preserve wizard state on FN-004 structural confirm): `begin_structural_confirm` layers `pending_structural_change` onto whatever session is live at that moment via `get_runtime_session()` — if already cleared to IDLE, the wizard's `pending_param_definitions`/`collected_params` would be gone by the time the user is asked to confirm.

**Fix:** call `apply_and_recalculate` on the still-active wizard session; only clear afterward, and only on the non-structural-confirm path. Verified by `test_r3b_numeric_submode_preempt_aborts_on_structural_confirm`: wizard mode, `pending_param_definitions`, and `collected_params` are all intact after the abort.

---

## Test naming deviation

`test_r3b_reentry_component_submode_resumes_gap` (contract's suggested name) was implemented as `test_r3b_component_submode_preserves_saved_components_after_preempt` — same underlying safety property (already-saved components must survive a preempt, including when the wizard's own `pending_missing_params` is stale per FN-016), verified directly against `design_properties.components` rather than through a full "ayúdame a elegir" reentry UX flow (which is motor-catalog-specific machinery, not a generic reentry path).

---

## Acceptance criteria — status

1. ✅ `"aplica la mejor"` mid component wizard → applied, wizard cleared, notice shown.
2. ✅ bare `"itera X"` mid component wizard → iterate flow starts (not silent Brief re-show).
3. ✅ `"descartar sugerencia"` mid wizard → dismiss executes (project_status/dismiss_noop; wizard cleared).
4. ✅ create-project-shaped phrase mid wizard → create flow starts. (Exact phrase `"nuevo proyecto"` is caught earlier by the pre-existing global `n`/`nuevo` shortcut in `_handle_global_commands` — a separate, already-working mechanism; test uses `"quiero crear un proyecto nuevo"` to exercise the R3b path itself.)
5. ✅ Numeric wizard, non-empty `collected_params` + preempt → partial apply runs first, notice mentions it, then intent executes.
6. ✅ Numeric wizard, empty `collected_params` + preempt → direct clear + redispatch, no partial-apply notice.
7. ✅ FN-004 structural confirm intercepts preempt; wizard state preserved.
8. ✅ Real component descriptions and numeric values still accepted normally.
9. ✅ R3a tests unchanged and passing (11/11).
10. ✅ Full suite green — 1877 passed (1867 baseline + 10 new).
11. — `define_params` different-block preempt: **not implemented**, see deviation #1.

---

## Tests executed

```
python -m pytest tests/test_r3b_preempt_real.py tests/test_r3a_preempt_refuse.py -v   # 21 passed
python -m pytest -q                                                                    # 1877 passed
```

---

## Remaining risks

- `define_params` is no longer in the R3b preempt set (deviation #1). If a future field note surfaces a *genuine* different-block declare that should preempt (not the shared-component park case), it needs its own investigation — the current codebase has no clean way to distinguish "different block, safe to jump" from "different block, but shares a component with the active wizard" other than the `BLOCK_TO_COMPONENTS` membership check R3a's refuse already performs.
- `_maybe_refuse_different_target` / `_maybe_refuse_numeric_submode` are now called once at the new gate and, when they return `None`, effectively a second time by the pre-existing code further down (inside `_handle_component_description`, or nowhere for numeric since the first call is now the only one on that path). Both are pure/stateless per their own docstrings — redundant but harmless; not deduplicated to keep this diff minimal.
