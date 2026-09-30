# Implementation Contract — Assistant vehicle TAKEOFF Task (`B1-assistant-vehicle-takeoff-task`)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.17`**

**Status:** ★ **ACCEPT CLOSED** (Engineer 2026-09-30) — Cursor review PASS; package/tag **`0.6.17` / `v0.6.17`**.
**Parents:**
- [DC ★ CLOSED](design_contract_assistant_vehicle_takeoff_task_b0.md)
- T8 [`B1-assistant-vehicle-go-to-task`](implementation_review_assistant_vehicle_go_to_task_b1.md) — ★ ACCEPT CLOSED @ **`v0.6.16`**
- Engineer cola: T9 TAKEOFF → T10 RETURN_HOME · HOLD INV ★ — no new INV

**Type:** Fourth vehicle Assistant Task — TAKEOFF phrase → Task → orchestrator fulfill via disarmed ArmedAllowlist (mirror HOLD/LAND/GO_TO).  
**Opens:** **`0.6.17` / `v0.6.17`** on ACCEPT.  
**Cola:** **T9**

**Not:** RETURN_HOME (T10) · `arm()` · allow-list widen · altitude parse · SoftwareCapabilitySafetyGate for flight · intelligence→FS import · voice · copper · edit HOLD/LAND/GO_TO fulfill bodies · generic verb framework.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-vehicle-takeoff-task`** |
| 2 | `TASK_KIND_REQUEST_TAKEOFF = "request_takeoff"` · `CAPABILITY_FLIGHT_TAKEOFF = "flight.takeoff"` |
| 3 | `try_request_takeoff_task(intent) -> Task \| None` |
| 4 | `VEHICLE_TAKEOFF_PHRASES` — finite frozenset, pre-normalized. Minimum seed: `takeoff`, `take off`, `despegar`, `despega`, `despegue`, `levanta`, `levantar`, `sube`, `ascender` |
| 5 | Precedence: **after** GO_TO branch, before `return None` |
| 6 | Membership only; **no** `SoftwareCapabilitySafetyGate` |
| 7 | Metadata `task_kind=request_takeoff` only after membership |
| 8 | Seed **add**: capability `flight.takeoff` v`0.6.17` `not_implemented` `provider.flight_takeoff`; provider `kind=vehicle` offers `["flight.takeoff"]`; skill `skill.request_takeoff` stub requires `["flight.takeoff"]` |
| 9 | Fulfill sibling `_handle_vehicle_takeoff`: fresh disarmed ArmedAllowlist; `propose_command(AutonomyVerb.TAKEOFF, intent_id=..., params={})`; `action=vehicle_takeoff`; honest Spanish message — never claim airborne/executed |
| 10 | Guards: refuse explain / Continuity / HOLD / LAND / GO_TO phrases |
| 11 | Do **not** edit `_handle_vehicle_hold` / `_handle_vehicle_land` / `_handle_vehicle_go_to` bodies. Cascade → **six** skills / six caps. HOLD+LAND+GO_TO regression green |
| 12 | Version **`0.6.17`**; docs README T9 · PLATFORM · CONNECTIONS (**no new C-xxx**) · PRIORIDAD · USER_GUIDE one line if needed |
| 13 | RETURN_HOME / `arm()` / allow-list widen out |

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/config.py` | `VEHICLE_TAKEOFF_PHRASES` |
| `src/jarvis/intelligence/assistant_task.py` | `try_request_takeoff_task` |
| `src/jarvis/core/orchestrator.py` | wire after GO_TO; `_handle_vehicle_takeoff` |
| `src/jarvis/capabilities/data/default_registry.json` | takeoff cap/provider/skill |
| `tests/test_assistant_vehicle_takeoff_task_b1.py` | **new** T1–T8 |
| Cascade + prior vehicle tests | counts + regression |
| `pyproject.toml` | `0.6.17` |
| Docs | §0.12 |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | TAKEOFF phrase → Task `["flight.takeoff"]`, `task_kind=request_takeoff` |
| T2 | Non-takeoff craft line → `None` |
| T3 | Explain / Continuity / HOLD / LAND / GO_TO → TAKEOFF try `None`; prior classifiers still match |
| T4 | `handle_user_text` TAKEOFF → Safety reject `disarmed`; never `executed`; precedence intact |
| T5 | Seed honesty + prior rows present |
| T6 | AST fence on `assistant_task` |
| T7 | `default_safety_gate()` RejectAll; fulfill disarmed ArmedAllowlist; empty params |
| T8 | `pyproject` `0.6.17` |

Bump stale `0.6.16` checkpoints this Buy owns.

---

## 3. Acceptance

- [ ] Classify + membership + fulfill `submit_command(TAKEOFF)`  
- [ ] Disarmed ArmedAllowlist · honest UX · prior verbs unchanged  
- [ ] Registry · cascade · T1–T8 · docs · `0.6.17`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.17`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-vehicle-takeoff-task (T9)

IC: .jes/artifacts/implementation_contract_assistant_vehicle_takeoff_task_b1.md
DC: .jes/artifacts/design_contract_assistant_vehicle_takeoff_task_b0.md (★ CLOSED)
Parent: T8 GO_TO ★ ACCEPT CLOSED @ v0.6.16 (same seam; no new INV)

Add VEHICLE_TAKEOFF_PHRASES + try_request_takeoff_task in assistant_task
(Task request_takeoff → flight.takeoff). Membership only — NO SoftwareCapabilitySafetyGate.
Refuse explain / Continuity / HOLD / LAND / GO_TO phrases inside the classifier.
intelligence must NOT import flight_software.
Wire orchestrator AFTER GO_TO branch: propose_command(TAKEOFF, params={}) +
submit_command with fresh disarmed ArmedAllowlistSafetyGate (do not arm).
Honest message — never claim airborne/executed. action=vehicle_takeoff.
Do NOT edit _handle_vehicle_hold / _handle_vehicle_land / _handle_vehicle_go_to bodies.
Seed registry: flight.takeoff not_implemented + provider.flight_takeoff vehicle +
skill.request_takeoff stub. Keep all prior rows.
Precedence: explain > defer > hold > land > go_to > takeoff. Adapt cascade to 6 skills.
HOLD+LAND+GO_TO regression must stay green. Tests T1–T8. Bump to 0.6.17. Docs + PRIORIDAD. Report.
No ACCEPT claim. T10 RETURN_HOME remains next after this tip.
```
