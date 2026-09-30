# Implementation Report — Assistant vehicle FOLLOW Task (`B1-assistant-vehicle-follow-task`, T12)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Implementer:** Cursor (Engineer: “Implementa ic”)  
**Contract:** [`implementation_contract_assistant_vehicle_follow_task_b1.md`](implementation_contract_assistant_vehicle_follow_task_b1.md)  
**Parents:** [DC ★ CLOSED](design_contract_assistant_vehicle_follow_task_b0.md) · T11 ★ ACCEPT CLOSED @ **`v0.6.19`**  
**Status:** Delivered for review → Engineer ACCEPT. **No ACCEPT claimed.**  
**Package:** `0.6.20`. **No tag.**

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/config.py` | `VEHICLE_FOLLOW_PHRASES` |
| `src/jarvis/intelligence/assistant_task.py` | `try_request_follow_task` + FOLLOW refusals in prior try_* |
| `src/jarvis/core/orchestrator.py` | wire after RETURN_HOME; `_handle_vehicle_follow` via shared gate |
| `src/jarvis/capabilities/data/default_registry.json` | `flight.follow` not_implemented + vehicle provider + skill stub |
| `tests/test_assistant_vehicle_follow_task_b1.py` | T1–T9 |
| Cascade + tip version checkpoints | 9 caps / 10 skills; `0.6.20` |
| Docs | PRIORIDAD · PLATFORM · CONNECTIONS · USER_GUIDE · intelligence README |

**Not touched:** `safety.py` `_ALLOWED_VERBS`, person/target parse, PATROL/CHARGE, prior fulfill bodies.

---

## 2. Behavior

- `follow` / `sígueme` → `vehicle_follow` · Safety `reject`/`disarmed` (default).
- After `armar` → FOLLOW `verb_not_allowed`; HOLD still `allow`/`not_implemented`.
- Exact match only — `sigue con el frame` not stolen.
- Shared T11 gate; empty params; never claims following executed.

---

## 3. Tests executed

```text
pytest tests/test_assistant_vehicle_follow_task_b1.py \
  tests/test_assistant_vehicle_arm_ux_b1.py \
  tests/test_assistant_vehicle_{hold,land,go_to,takeoff,return_home}_task_b1.py \
  tests/test_assistant_software_safety_bridge_b1.py \
  tests/test_capability_skills_seed_b1.py \
  tests/test_assistant_task_registry_coherence_b1.py \
  tests/test_capability_registry_product_fill_b1.py -q
→ 89 passed
```

---

## 4. Remaining

- Independent Cursor review of record.
- Engineer ★ ACCEPT → tag `v0.6.20`.
