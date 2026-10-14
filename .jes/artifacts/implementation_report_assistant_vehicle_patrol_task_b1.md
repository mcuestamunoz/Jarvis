# Implementation Report — Assistant vehicle PATROL Task (`B1-assistant-vehicle-patrol-task`, T13)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Implementer:** Claude Code (Engineer: "procede con patrol")  
**Contract:** [`implementation_contract_assistant_vehicle_patrol_task_b1.md`](implementation_contract_assistant_vehicle_patrol_task_b1.md)  
**Parents:** [DC ★ CLOSED](design_contract_assistant_vehicle_patrol_task_b0.md) · T12 ★ ACCEPT CLOSED @ **`v0.6.20`**  
**Status:** **★ ACCEPT CLOSED** (Engineer 2026-10-01) — Cursor review PASS WITH NOTES.  
**Package / tag:** `0.6.21` / **`v0.6.21`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/config.py` | `VEHICLE_PATROL_PHRASES` |
| `src/jarvis/intelligence/assistant_task.py` | `try_request_patrol_task` + PATROL refusals in all 8 prior try_* |
| `src/jarvis/core/orchestrator.py` | wire after FOLLOW; `_handle_vehicle_patrol` via shared gate |
| `src/jarvis/capabilities/data/default_registry.json` | `flight.patrol` not_implemented + vehicle provider + skill stub |
| `tests/test_assistant_vehicle_patrol_task_b1.py` | **new** T1–T9 |
| Prior vehicle / arm / follow / cascade tests | version checkpoints bumped to `0.6.21`; FOLLOW's own registry seed-honesty counts bumped 9→10 caps / 10→11 skills; 39 Fase C cascade tests (`capability_registry_default_still_empty` family) extended with `skill.request_patrol` |
| Cascade | 10 caps / 11 skills; `0.6.21` |
| Docs | PRIORIDAD · PLATFORM · CONNECTIONS · USER_GUIDE · intelligence README · `.jes/state/engineering_state.json` |

**Not touched:** `safety.py` `_ALLOWED_VERBS` (still `{HOLD, LAND, GO_TO}`), waypoint/route parse, CHARGE/copper, prior `_handle_vehicle_*`/`_handle_arm_policy`/`_handle_disarm_policy` fulfill bodies (byte-unchanged — only new PATROL-refusal guard lines added to the 8 prior `try_*` classifiers).

---

## 2. Behavior

- `patrol` / `patrulla` / `patrullar` / `hacer patrulla` / `start patrol` / `iniciar patrulla` → `vehicle_patrol` · Safety `reject`/`disarmed` (default).
- After `armar` → PATROL `verb_not_allowed`; HOLD still `allow`/`not_implemented`.
- Exact match only — `patrulla del catalogo` / `patrol the board layout` not stolen.
- Shared T11 gate (`self._vehicle_chat_safety_gate()`) — not a fresh gate, `gate.arm()` never called from this fulfill.
- Empty `params={}` — no waypoint/route parse.
- Honest Spanish — never claims a patrol/circuit/route was executed.
- Last C4 `AutonomyVerb` without a chat Task — closes the vehicle-verb cola (HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME/FOLLOW/PATROL all now have a Task).

---

## 3. Tests executed

```text
pytest tests/test_assistant_vehicle_patrol_task_b1.py \
  tests/test_assistant_vehicle_follow_task_b1.py \
  tests/test_assistant_vehicle_arm_ux_b1.py \
  tests/test_assistant_vehicle_{hold,land,go_to,takeoff,return_home}_task_b1.py -q
→ 68 passed

pytest tests/ -q
→ 3874 passed, 9 skipped, 54 failed
```

The 54 failures are a **pre-existing baseline**, byte-identical (same test ids) to the failure set on the pristine `origin/main` tip (`843b77d`) before this Buy's changes — verified by diffing the full-suite failure list before vs. after this implementation. They are historical version-checkpoint/package-count assertions unrelated to this Buy (e.g. `test_fase_c_*::test_tN_pyproject_version_is_0_5_XX`, `test_library_cameras_seed_b1.py::test_t8_package_checkpoint_version`) plus the already-known, separately-tracked FN-016 bug (`test_fn016_navigation_parse_safety.py::test_volver_cancels_numeric_wizard_phase_b`). **Zero new regressions** introduced by this Buy.

---

## 4. Remaining

None for this Buy. Next candidates: allow-list widen · CHARGE · copper.
