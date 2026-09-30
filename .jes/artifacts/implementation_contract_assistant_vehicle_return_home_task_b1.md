# Implementation Contract — Assistant vehicle RETURN_HOME Task (`B1-assistant-vehicle-return-home-task`)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.18`**

**Status:** ★ **AUTHORIZED** (Engineer 2026-09-30 — ACCEPT T9 + redacta IC siguiente)  
**Parents:**
- [DC ★ CLOSED](design_contract_assistant_vehicle_return_home_task_b0.md)
- T9 [`B1-assistant-vehicle-takeoff-task`](implementation_review_assistant_vehicle_takeoff_task_b1.md) — ★ ACCEPT CLOSED @ **`v0.6.17`**
- Engineer cola T10 · HOLD INV ★ — no new INV

**Type:** Fifth vehicle Assistant Task — RETURN_HOME / RTL phrase → Task → orchestrator fulfill via disarmed ArmedAllowlist. Closes basic mando set.  
**Opens:** **`0.6.18` / `v0.6.18`** on ACCEPT.  
**Cola:** **T10**

**Not:** `arm()` · allow-list widen · home/GPS parse · SoftwareCapabilitySafetyGate for flight · intelligence→FS import · voice · copper · edit HOLD/LAND/GO_TO/TAKEOFF fulfill bodies · FOLLOW/PATROL/CHARGE · generic verb framework.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-vehicle-return-home-task`** |
| 2 | `TASK_KIND_REQUEST_RETURN_HOME = "request_return_home"` · `CAPABILITY_FLIGHT_RETURN_HOME = "flight.return_home"` |
| 3 | `try_request_return_home_task(intent) -> Task \| None` |
| 4 | `VEHICLE_RETURN_HOME_PHRASES` — finite frozenset, pre-normalized. Minimum seed: `return home`, `returnhome`, `rtl`, `rth`, `vuelve`, `volver`, `vuelve a casa`, `volver a casa`, `casa`, `home` — accented forms normalize onto accent-free entries |
| 5 | Precedence: **after** TAKEOFF branch, before `return None` |
| 6 | Membership only; **no** `SoftwareCapabilitySafetyGate` |
| 7 | Metadata `task_kind=request_return_home` only after membership |
| 8 | Seed **add**: capability `flight.return_home` v`0.6.18` `not_implemented` `provider.flight_return_home`; provider `kind=vehicle` offers `["flight.return_home"]`; skill `skill.request_return_home` stub requires `["flight.return_home"]` |
| 9 | Fulfill sibling `_handle_vehicle_return_home`: fresh disarmed ArmedAllowlist; `propose_command(AutonomyVerb.RETURN_HOME, intent_id=..., params={})`; `action=vehicle_return_home`; honest Spanish message — never claim returned/RTL executed |
| 10 | Guards: refuse explain / Continuity / HOLD / LAND / GO_TO / TAKEOFF phrases |
| 11 | Do **not** edit prior `_handle_vehicle_*` bodies (hold/land/go_to/takeoff). Cascade → **seven** skills / seven caps. Prior four vehicle suites + regression green |
| 12 | Version **`0.6.18`**; docs README T10 · PLATFORM · CONNECTIONS (**no new C-xxx**) · PRIORIDAD · USER_GUIDE one line if needed |
| 13 | `arm()` / allow-list widen / FOLLOW… out |

**Phrase caution:** `casa` / `home` / `volver` are short — exact-match only (same discipline as other tables). Do **not** steal craft chat like “volver al board”.

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/config.py` | `VEHICLE_RETURN_HOME_PHRASES` |
| `src/jarvis/intelligence/assistant_task.py` | `try_request_return_home_task` |
| `src/jarvis/core/orchestrator.py` | wire after TAKEOFF; `_handle_vehicle_return_home` |
| `src/jarvis/capabilities/data/default_registry.json` | return_home cap/provider/skill |
| `tests/test_assistant_vehicle_return_home_task_b1.py` | **new** T1–T8 |
| Cascade + prior vehicle tests | counts + regression |
| `pyproject.toml` | `0.6.18` |
| Docs | §0.12 |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | RETURN_HOME phrase → Task `["flight.return_home"]`, `task_kind=request_return_home` |
| T2 | Non-RTL craft line (e.g. `volver al board`) → `None` |
| T3 | Explain / Continuity / HOLD / LAND / GO_TO / TAKEOFF → RETURN_HOME try `None`; prior classifiers still match |
| T4 | `handle_user_text` RTL phrase → Safety reject `disarmed`; never `executed`; precedence intact across five vehicle actions |
| T5 | Seed honesty + prior rows present; allow-list still excludes RETURN_HOME |
| T6 | AST fence on `assistant_task` |
| T7 | `default_safety_gate()` RejectAll; fulfill disarmed ArmedAllowlist; empty params |
| T8 | `pyproject` `0.6.18` |

Bump stale `0.6.17` checkpoints this Buy owns.

---

## 3. Acceptance

- [ ] Classify + membership + fulfill `submit_command(RETURN_HOME)`  
- [ ] Disarmed ArmedAllowlist · honest UX · prior verbs unchanged  
- [ ] Registry · cascade · T1–T8 · docs · `0.6.18`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.18`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-vehicle-return-home-task (T10)

IC: .jes/artifacts/implementation_contract_assistant_vehicle_return_home_task_b1.md
DC: .jes/artifacts/design_contract_assistant_vehicle_return_home_task_b0.md (★ CLOSED)
Parent: T9 TAKEOFF ★ ACCEPT CLOSED @ v0.6.17 (same seam; no new INV)

Add VEHICLE_RETURN_HOME_PHRASES + try_request_return_home_task in assistant_task
(Task request_return_home → flight.return_home). Membership only — NO SoftwareCapabilitySafetyGate.
Refuse explain / Continuity / HOLD / LAND / GO_TO / TAKEOFF phrases inside the classifier.
Exact match only — do not steal "volver al board".
intelligence must NOT import flight_software.
Wire orchestrator AFTER TAKEOFF branch: propose_command(RETURN_HOME, params={}) +
submit_command with fresh disarmed ArmedAllowlistSafetyGate (do not arm).
Do NOT widen ArmedAllowlist allow-list. Honest message — never claim RTL/home executed.
action=vehicle_return_home.
Do NOT edit prior _handle_vehicle_hold/land/go_to/takeoff bodies.
Seed registry: flight.return_home not_implemented + provider.flight_return_home vehicle +
skill.request_return_home stub. Keep all prior rows.
Precedence: explain > defer > hold > land > go_to > takeoff > return_home.
Adapt cascade to 7 skills. Prior vehicle suites must stay green.
Tests T1–T8. Bump to 0.6.18. Docs + PRIORIDAD. Report.
No ACCEPT claim. After this tip, basic mando set is complete (TAKEOFF/HOLD/GO_TO/RETURN_HOME/LAND).
```
