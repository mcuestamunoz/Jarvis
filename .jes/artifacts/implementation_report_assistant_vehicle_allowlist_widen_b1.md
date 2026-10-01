# Implementation Report — Assistant chat ArmedAllowlist widen (`B1-assistant-vehicle-allowlist-widen`, T14)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Implementer:** Claude Code (Engineer authorization paste)  
**Contract:** [`implementation_contract_assistant_vehicle_allowlist_widen_b1.md`](implementation_contract_assistant_vehicle_allowlist_widen_b1.md)  
**Parents:** [DC ★ CLOSED](design_contract_assistant_vehicle_allowlist_widen_b0.md) · T16 ESC fence ★ ACCEPT CLOSED @ **`v0.6.24`** · T13 PATROL ★ @ **`v0.6.21`** · T11 arm UX ★  
**Status:** **★ ACCEPT CLOSED** (Engineer 2026-10-01).  
**Package / tag:** `0.6.25` / **`v0.6.25`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/capabilities/safety.py` | `ArmedAllowlistSafetyGate._ALLOWED_VERBS` widened from `{HOLD,LAND,GO_TO}` to `{HOLD,LAND,GO_TO,TAKEOFF,RETURN_HOME,FOLLOW,PATROL}`; class docstring updated; new module-docstring paragraph documenting the T14 widen |
| `src/jarvis/core/orchestrator.py` | `_handle_arm_policy`'s Spanish message updated — no longer claims TAKEOFF/RETURN_HOME stay `verb_not_allowed` after `armar`. No fulfill-method rewiring |
| `src/jarvis/capabilities/data/default_registry.json` | `safety.chat_armed_allowlist` capability `version` → `0.6.25` |
| `tests/test_assistant_vehicle_allowlist_widen_b1.py` | **new** T1–T8 |
| Retargeted (armed → `verb_not_allowed` for TAKEOFF/RETURN_HOME/FOLLOW/PATROL, or the old 3-verb frozenset) | `test_assistant_vehicle_arm_ux_b1.py`, `test_assistant_vehicle_follow_task_b1.py`, `test_assistant_vehicle_patrol_task_b1.py`, `test_assistant_vehicle_return_home_task_b1.py`, `test_assistant_vehicle_takeoff_task_b1.py`, `test_assistant_software_safety_bridge_b1.py`, `test_fase_c_safety_real_policy_b1.py`, `test_fase_c_safety_sim_policy_b1.py`, `test_fase_c_crsf_dual_role_bridge_b1.py` (the last three are the original C17/C41 Fase C gate tests — real, live assertions against the shared gate class, not frozen version pins, so they had to be retargeted too; their "not allowed" probe now uses `CHARGE`, a verb that was never a chat Task kind, instead of a now-allowed one) |
| Buy-owned active-lineage version checkpoints | bumped `0.6.24` → `0.6.25` in the 20 files this chain tracks |
| Docs | PRIORIDAD · PLATFORM (new T14 paragraph) · CONNECTIONS (new T14 paragraph, no new C-xxx) · intelligence README (new T14 section + 5 stale "allow-list still {HOLD,LAND,GO_TO}" lines corrected to past tense) · USER_GUIDE_EXPLAIN (T11/T12/T13 notes corrected + new T14 note) |

**Not touched:** `_handle_vehicle_*` fulfill method bodies/docstrings (still say "verb_not_allowed when armed" — out of IC scope, same restraint as T13's own precedent), any phrase table, any Task kind, `SimAutonomyExecutor` (never wired from chat — verified by new T7), CHARGE/copper, FN-016, historical Fase C 0.5.x tip pins.

---

## 2. Behavior

- After `armar`: all seven chat vehicle verbs (HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME/FOLLOW/PATROL) → Safety `allow` + execution `not_implemented` — never `"executed"`.
- Disarmed (default): all seven still `reject`/`disarmed`, unchanged.
- `armar` → `desarmar` → any verb: back to `reject`/`disarmed`, unchanged.
- Allow ≠ execute: `SimAutonomyExecutor` stays HOLD/LAND/GO_TO-only in sim; nothing in `orchestrator.py` references it.

---

## 3. Tests executed

```text
pytest tests/test_assistant_vehicle_allowlist_widen_b1.py -q
→ 8 passed

pytest tests/test_assistant_vehicle_allowlist_widen_b1.py tests/test_assistant_vehicle_arm_ux_b1.py \
  tests/test_assistant_vehicle_follow_task_b1.py tests/test_assistant_vehicle_patrol_task_b1.py \
  tests/test_assistant_vehicle_takeoff_task_b1.py tests/test_assistant_vehicle_return_home_task_b1.py \
  tests/test_assistant_vehicle_hold_task_b1.py tests/test_assistant_vehicle_land_task_b1.py \
  tests/test_assistant_vehicle_go_to_task_b1.py tests/test_assistant_software_safety_bridge_b1.py \
  tests/test_fase_c_safety_real_policy_b1.py tests/test_fase_c_safety_sim_policy_b1.py \
  tests/test_fase_c_crsf_dual_role_bridge_b1.py -q
→ 120 passed, 3 failed (pre-existing Fase C 0.5.x historical pins only — untouched, expected)

pytest tests/ -q
→ 3889 passed, 9 skipped, 52 failed
```

The 52 failures are diffed byte-for-byte against this branch's pre-T14 tip: **zero new failures, zero fixed** (T14 widens a feature rather than fixing a previously-failing regression test, so the pre-existing historical-pin failure count is unchanged at 52). All 52 are the pre-existing, parked Fase C 0.5.x / early-0.6.x historical tip-pin debt — untouched, per DC §0 row 9 / Engineer's explicit "no tip-pin mass cleanup" direction.

---

## 4. Remaining

None for this Buy. Next candidates: CHARGE · copper.
