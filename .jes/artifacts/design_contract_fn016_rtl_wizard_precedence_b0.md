# Design Contract — FN-016 vs RETURN_HOME wizard precedence (`DC-fn016-rtl-wizard-precedence`)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Author:** JES / Cursor  
**Status:** ★ **CLOSED** (Engineer 2026-10-01 — “los 2 tests son buys reales · lanza IC”)  
**Type:** Design lock — restore FN-016 cancel when `volver`/`vuelve` arrive mid–`DEFINE_MISSING`. Regression from T10 RETURN_HOME phrase overlap.  
**Parents:** [FN-016 cycle close ★](cycle_close_fn016.md) · [T10 RETURN_HOME ★](implementation_review_assistant_vehicle_return_home_task_b1.md) @ **`v0.6.18`** · tip parent **`v0.6.21`** · **no new INV**

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Root cause: `_handle_global_commands` vehicle RETURN_HOME intercept runs **before** the DEFINE_MISSING FN-016 cancel. Exact phrases `volver` / `vuelve` sit in **both** `NAVIGATION_BACK_WORDS` and `VEHICLE_RETURN_HOME_PHRASES` → wizard turn becomes `vehicle_return_home` (`status=ok`) instead of cancel |
| 2 | Fix shape: when runtime session mode is **`DEFINE_MISSING_PARAMETERS`** and `is_navigation_back_phrase(user_input)`, cancel the wizard (**same** result shape as existing FN-016 block: `status=cancelled`, `action=define_missing_params`, clear session) **before** any vehicle Task intercept in `_handle_global_commands` |
| 3 | Do **not** remove `volver`/`vuelve` from `VEHICLE_RETURN_HOME_PHRASES` — IDLE/`--chat` RTL phrases must keep working |
| 4 | Do **not** add navigation words to global `ESCAPE_WORDS` |
| 5 | Keep `ParamDefinitionSession.answer` FN-016 fallback; keep DEFINE_MISSING-branch cancel as defense in depth |
| 6 | Regression test: existing `test_volver_cancels_numeric_wizard_phase_b` must go green; add/keep IDLE `volver` → RETURN_HOME still classifies/fulfills |
| 7 | Out: undo stack · tip-pin mass cleanup · allow-list widen · CHARGE · copper · ESC fence (separate Buy) |
| 8 | Next code: IC **`B1-fn016-rtl-wizard-precedence`** (T15) → package **`0.6.23`** |

**Product sentence:** mid-wizard `volver`/`atrás` cancels acquisition again; at idle the same word still means RETURN_HOME.

**Why this Buy:** T10 closed basic mando with short RTL words; FN-016’s wizard cancel silently broke. Real behavior regression, not a tip pin.
