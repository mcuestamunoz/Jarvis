# Implementation Report — Assistant vehicle RETURN_HOME Task (`B1-assistant-vehicle-return-home-task`, T10)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Implementer:** Claude Code (partial) + **Cursor** (completion — Engineer: Claude limit; “revisa qué hizo y sigue”)  
**Contract:** [`implementation_contract_assistant_vehicle_return_home_task_b1.md`](implementation_contract_assistant_vehicle_return_home_task_b1.md)  
**Parents:** [DC ★ CLOSED](design_contract_assistant_vehicle_return_home_task_b0.md) · T9 ★ ACCEPT CLOSED @ **`v0.6.17`**  
**Status:** Delivered for Cursor review → Engineer ACCEPT. **No ACCEPT claimed.**  
**Package:** `0.6.18`. **No tag.**

---

## 1. What Claude had already done (before limit)

- `src/jarvis/config.py` — `VEHICLE_RETURN_HOME_PHRASES` (10 entries, IC seed)
- `src/jarvis/intelligence/assistant_task.py` — `CAPABILITY_FLIGHT_RETURN_HOME`, `TASK_KIND_REQUEST_RETURN_HOME`, `try_request_return_home_task` with full ahead-of-it guards
- `src/jarvis/capabilities/data/default_registry.json` — `flight.return_home` / `provider.flight_return_home` / `skill.request_return_home`

## 2. What Cursor completed

- `src/jarvis/core/orchestrator.py` — wire after TAKEOFF; `_handle_vehicle_return_home` sibling (prior fulfill bodies untouched)
- `tests/test_assistant_vehicle_return_home_task_b1.py` — T1–T8
- 39-file cascade → 7 skill ids; version checkpoints + `pyproject` → **`0.6.18`**
- Docs: intelligence README T10 · PLATFORM · CONNECTIONS (no new C-xxx) · USER_GUIDE · PRIORIDAD
- This report

**Not touched:** `safety.py` allow-list, `flight_software/`, Continuity, schemas/registry code.

---

## 3. Verification

Live: `rtl` / `casa` / `return home` → `action=vehicle_return_home`, message contains `reject`/`disarmed`/`not_attempted`.  
`volver al board` → no RETURN_HOME Task.  
Prior verbs HOLD/LAND/GO_TO/TAKEOFF still classify and fulfill.  
`ArmedAllowlistSafetyGate._ALLOWED_VERBS` still `{HOLD,LAND,GO_TO}`.

---

## 4. Tests

```text
tests/test_assistant_vehicle_return_home_task_b1.py + prior four vehicle suites
(see pytest run in delivery)
```

T1–T8 as IC §2.

---

## 5. IC checklist self-check

- [x] Classify + membership + fulfill `submit_command(RETURN_HOME)`  
- [x] Disarmed ArmedAllowlist · honest UX · prior verbs unchanged  
- [x] Registry · cascade · T1–T8 · docs · `0.6.18`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.18`**

**No ACCEPT claim.** Basic mando set in chat code: TAKEOFF · HOLD · GO_TO · RETURN_HOME · LAND.
