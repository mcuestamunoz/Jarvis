# Implementation Report — Chat Skill-first vehicle HOLD (`B1-assistant-chat-skill-first-vehicle-hold`, T23)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Implementer:** Cursor (Engineer: “Ejecuta tu ic t23”)  
**Contract:** [`implementation_contract_assistant_chat_skill_first_vehicle_hold_b1.md`](implementation_contract_assistant_chat_skill_first_vehicle_hold_b1.md)  
**Parents:** [DC ★ CLOSED](design_contract_assistant_chat_skill_first_b0.md) · T22 ★ @ **`v0.6.31`** · T6 HOLD ★  
**Status:** Implemented — await Cursor review of record / Engineer ★ ACCEPT. **No ACCEPT claim.**  
**Package / tag:** `0.6.32` / **`v0.6.32`** (on ACCEPT).

---

## 1. What landed

| Area | Change |
|---|---|
| `capabilities/data/default_registry.json` | `skill.request_hold` → `available` @ `0.6.32`; `flight.hold` stays `not_implemented` |
| `capabilities/skills_runtime.py` | vehicle HOLD gate (membership + provider `kind==vehicle`); **no** `SoftwareCapabilitySafetyGate`; refreshed docstring |
| `core/orchestrator.py` | HOLD intercept: `run_skill("skill.request_hold")` gate then `_handle_vehicle_hold` |
| `tests/test_assistant_chat_skill_first_vehicle_hold_b1.py` | **new** T1–T5 |
| Prior suites retargeted | T21 T3/T4 · T6 T5 seed · T22 T3 charge-only |
| `pyproject.toml` | `0.6.32` |
| Docs | PRIORIDAD · PLATFORM · CONNECTIONS |

**Not touched:** other vehicle/ops Skill availability · `flight.hold=available` · live ESC · SD-GO_TO · ArmedAllowlist / sim copper fulfill bodies.

---

## 2. Behavior

- `hold` → `run_skill("skill.request_hold")` ok gate → existing `_handle_vehicle_hold` (disarmed reject / armed allow+sim honesty unchanged).
- Direct `run_skill("skill.request_hold")` → `outcome=ok` (not `skill_stub`, not software Safety reject).
- `skill.request_land` / `skill.request_charge` still `skill_stub`.
- explain / estado still software Skill-first.

---

## 3. Tests executed

```text
pytest tests/test_assistant_chat_skill_first_vehicle_hold_b1.py \
  tests/test_capability_skills_runtime_software_b1.py \
  tests/test_assistant_vehicle_hold_task_b1.py \
  tests/test_assistant_chat_skill_first_software_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py -q
→ 25 passed
```

---

## 4. Remaining

None for this Buy. Next phase B candidate: Skill-first siblings (LAND…).
