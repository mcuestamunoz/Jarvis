# Implementation Report — Chat Skill-first software Skills (`B1-assistant-chat-skill-first-software`, T22)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Implementer:** Cursor (Engineer: “ejecutalo tú”)  
**Contract:** [`implementation_contract_assistant_chat_skill_first_software_b1.md`](implementation_contract_assistant_chat_skill_first_software_b1.md)  
**Parents:** [DC ★ CLOSED](design_contract_assistant_chat_skill_first_b0.md) · T21 ★ @ **`v0.6.30`**  
**Status:** Implemented — await Cursor review of record is same-session; Engineer may treat as PASS pending ★ ACCEPT. **No ACCEPT claim.**  
**Package / tag:** `0.6.31` / **`v0.6.31`** (on ACCEPT).

---

## 1. What landed

| Area | Change |
|---|---|
| `intelligence/assistant_task.py` | `handle_explain_intent` fulfills via `run_skill("skill.explain_concept", …)` — Skill-first on chat explain seam |
| `core/orchestrator.py` | Continuity defer: `run_skill("skill.project_status", provider=build_startup_context)` gate; on hard reject honest message; on ok/`no_project` → existing `_handle_project_status` shape + side effects |
| `capabilities/skills_runtime.py` | optional `ontology_root` passthrough to `fulfill_ontology_explain` |
| `tests/test_assistant_chat_skill_first_software_b1.py` | **new** T1–T5 |
| `tests/test_capability_skills_runtime_software_b1.py` | T5 retargeted (classify still Skill-agnostic; fulfill may import `run_skill` post-T22) |
| `pyproject.toml` | `0.6.31` |
| Docs | PRIORIDAD · PLATFORM · CONNECTIONS |

**Not touched:** vehicle/arm/ops/CHARGE/sim copper Task paths · Skill availability of vehicle Skills · Continuity ranking · tip pins.

---

## 2. Behavior

- `explain c-rate-de-bateria` → same cite honesty; path goes through `run_skill`.
- `estado` → `run_skill` gated; response still `action=project_status` + `startup_context`.
- `hold` / `charge` → still Task-direct.

---

## 3. Tests executed

```text
pytest tests/test_assistant_chat_skill_first_software_b1.py \
  tests/test_capability_skills_runtime_software_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py \
  tests/test_assistant_ops_charge_task_b1.py \
  tests/test_assistant_vehicle_hold_task_b1.py -q
→ 28 passed
```

---

## 4. Remaining

None for this Buy. Next phase B (candidate): vehicle Skill-first where Skills become `available`.
