# Implementation Report — Assistant vehicle Safety arm UX (`B1-assistant-vehicle-arm-ux`, T11)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Implementer:** Cursor (Engineer: “implementa tú”)  
**Contract:** [`implementation_contract_assistant_vehicle_arm_ux_b1.md`](implementation_contract_assistant_vehicle_arm_ux_b1.md)  
**Parents:** [DC ★ CLOSED](design_contract_assistant_vehicle_arm_ux_b0.md) · T10 ★ ACCEPT CLOSED @ **`v0.6.18`**  
**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-30) — Cursor review PASS WITH NOTES.  
**Package / tag:** `0.6.19` / **`v0.6.19`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/config.py` | `VEHICLE_ARM_PHRASES` · `VEHICLE_DISARM_PHRASES` |
| `src/jarvis/intelligence/assistant_task.py` | `try_request_arm_policy_task` / `try_request_disarm_policy_task` (T3+T4); vehicle try_* refuse arm/disarm |
| `src/jarvis/core/orchestrator.py` | `_vehicle_chat_safety_gate()` shared latch; ARM/DISARM wire+fulfill; five vehicle fulfills retargeted |
| `src/jarvis/capabilities/data/default_registry.json` | `safety.chat_armed_allowlist` available + software provider + 2 skill stubs |
| `tests/test_assistant_vehicle_arm_ux_b1.py` | T1–T10 |
| Cascade + tip version checkpoints | 9 skills; `0.6.19` |
| Docs | PRIORIDAD · PLATFORM · CONNECTIONS · USER_GUIDE · intelligence README |

**Not touched:** `safety.py` `_ALLOWED_VERBS` (still `{HOLD,LAND,GO_TO}`), `flight_software/` autonomy surface, Continuity, ESC/`SimulatedEscSink.arm()`.

---

## 2. Behavior

- Default: vehicle verbs still `reject`/`disarmed` (shared gate starts disarmed).
- `armar` → latch armed; honest “política Safety / software” message; never ESC/motors.
- Then `hold`/`land`/`go to` → `allow`/`not_implemented`.
- Then `takeoff`/`rtl` → `verb_not_allowed`.
- `desarmar` → latch clear; next `hold` → `disarmed` again.

---

## 3. Tests executed

```text
pytest tests/test_assistant_vehicle_arm_ux_b1.py \
  tests/test_assistant_vehicle_hold_task_b1.py \
  tests/test_assistant_vehicle_land_task_b1.py \
  tests/test_assistant_vehicle_go_to_task_b1.py \
  tests/test_assistant_vehicle_takeoff_task_b1.py \
  tests/test_assistant_vehicle_return_home_task_b1.py \
  tests/test_assistant_software_safety_bridge_b1.py \
  tests/test_assistant_task_registry_coherence_b1.py \
  tests/test_capability_registry_product_fill_b1.py \
  tests/test_capability_skills_seed_b1.py -q
→ 80 passed

pytest tests/test_assistant_*.py \
  tests/test_chat_explain_intercept_b1.py \
  tests/test_continuity_explain_topics_expand_b1.py -q
→ 102 passed, 1 failed (pre-existing tip pin:
   test_assistant_terminal_canal_b1.py expects 0.6.3 — not owned by this Buy;
   IC only bumps stale 0.6.18 checkpoints)
```

---

## 4. Remaining

None for this Buy. Next candidates: FOLLOW · PATROL · allow-list widen · CHARGE.
