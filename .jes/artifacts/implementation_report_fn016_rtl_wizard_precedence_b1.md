# Implementation Report — FN-016 vs RETURN_HOME wizard precedence (`B1-fn016-rtl-wizard-precedence`, T15)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Implementer:** Claude Code (Engineer authorization paste)  
**Contract:** [`implementation_contract_fn016_rtl_wizard_precedence_b1.md`](implementation_contract_fn016_rtl_wizard_precedence_b1.md)  
**Parents:** [DC ★ CLOSED](design_contract_fn016_rtl_wizard_precedence_b0.md) · [FN-016 cycle close ★](cycle_close_fn016.md) · T10 RETURN_HOME ★ @ **`v0.6.18`** · tip **`v0.6.21`**  
**Status:** Implemented — await Cursor review → Engineer ★ ACCEPT. **No ACCEPT claim.**  
**Package / tag:** `0.6.23` / **`v0.6.23`** (on ACCEPT).

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/core/orchestrator.py` | New early check in `_handle_global_commands`, placed right after the Continuity-defer intercept and **before** every vehicle/Safety-policy intercept (ARM/DISARM/HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME/FOLLOW/PATROL): when `session.mode == DEFINE_MISSING_PARAMETERS` and `is_navigation_back_phrase(stripped)`, clears the session and returns the same `{status: cancelled, action: define_missing_params, message: "Definición cancelada. Puedes retomar cuando quieras."}` shape the existing DEFINE_MISSING-mode FN-016 block already used (kept there too, untouched, as defense in depth for direct callers) |
| `tests/test_fn016_navigation_parse_safety.py` | Strengthened `test_volver_cancels_numeric_wizard_phase_b` (asserts `action == "define_missing_params"` too) + two new tests: `test_vuelve_and_atras_also_cancel_numeric_wizard_phase_b`, `test_idle_volver_still_vehicle_return_home` + new `test_pyproject_version_is_0_6_23` |
| `pyproject.toml` | `0.6.23` |
| Buy-owned active-lineage version checkpoints (the T0–T13 Assistant/vehicle-task chain only — **not** the parked Fase C 0.5.x / early-0.6.x historical pins) | bumped `0.6.21` → `0.6.23` in the 18 files this chain already tracks, same mechanical convention every prior Buy in this chain has used |
| `docs/IMPLEMENTATION_TASKS.md` | PRIORIDAD line + T15 row → "Implemented, await review" |

**Not touched:** `VEHICLE_RETURN_HOME_PHRASES` (still includes `volver`/`vuelve`), `NAVIGATION_BACK_WORDS`, global `ESCAPE_WORDS`, `ParamDefinitionSession.answer`'s own FN-016 fallback, T14 allow-list widen, T16 ESC fence — both separate, still-only-authorized ICs this Buy does not implement.

---

## 2. Behavior

- `DEFINE_MISSING_PARAMETERS` + `volver`/`vuelve`/`atras` → wizard cancels (`status=cancelled`, `action=define_missing_params`), session back to IDLE — same as the pre-T10 FN-016 behavior.
- `IDLE` (no active wizard) + `volver`/`vuelve` → still classifies and fulfills as `vehicle_return_home` via the existing T10 path (honest `disarmed`/`reject`).
- No change to `atras`-only Phase A component-wizard cancel (already worked; now also explicitly covered for Phase B numeric wizard).

---

## 3. Tests executed

```text
pytest tests/test_fn016_navigation_parse_safety.py -q
→ 14 passed

pytest tests/test_fn016_navigation_parse_safety.py \
  tests/test_assistant_vehicle_return_home_task_b1.py \
  tests/test_assistant_vehicle_hold_task_b1.py \
  tests/test_assistant_vehicle_land_task_b1.py \
  tests/test_assistant_vehicle_go_to_task_b1.py \
  tests/test_assistant_vehicle_takeoff_task_b1.py \
  tests/test_assistant_vehicle_arm_ux_b1.py \
  tests/test_assistant_vehicle_follow_task_b1.py \
  tests/test_assistant_vehicle_patrol_task_b1.py -q
→ 82 passed

pytest tests/ -q
→ 3878 passed, 9 skipped, 53 failed
```

The 53 failures are diffed byte-for-byte against this branch's pre-fix tip: **zero new failures**, and exactly one prior failure now fixed (`test_fn016_navigation_parse_safety.py::test_volver_cancels_numeric_wizard_phase_b`). The remaining 53 are the pre-existing, parked Fase C 0.5.x / early-0.6.x historical tip-pin debt — untouched, per DC §0 row 7 / Engineer's explicit "no tip-pin mass cleanup" direction.

---

## 4. Remaining

None for this Buy. T14 (allow-list widen) and T16 (ESC fence) remain separate, already-authorized ICs — not implemented here.
