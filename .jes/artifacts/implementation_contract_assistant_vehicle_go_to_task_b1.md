# Implementation Contract — Assistant vehicle GO_TO Task (`B1-assistant-vehicle-go-to-task`)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.16`**

**Status:** ★ **AUTHORIZED** (Engineer 2026-09-30 — ACCEPT T7 + procede siguiente IC)  
**Parents:**
- [DC ★ CLOSED](design_contract_assistant_vehicle_go_to_task_b0.md)
- T7 [`B1-assistant-vehicle-land-task`](implementation_review_assistant_vehicle_land_task_b1.md) — ★ ACCEPT CLOSED @ **`v0.6.15`**
- T6 HOLD ★ @ **`v0.6.14`** · HOLD INV ★ — seams reused; **no new INV**

**Type:** Third vehicle Assistant Task — classify GO_TO phrases → Task → orchestrator fulfill via autonomy surface + disarmed ArmedAllowlist (mirror HOLD/LAND).  
**Opens:** **`0.6.16` / `v0.6.16`** on ACCEPT.  
**Cola:** **T8**

**Not:** `arm()` · coordinate/waypoint parsing · `default_safety_gate` change · SoftwareCapabilitySafetyGate for flight · intelligence→FS import · voice · copper · Continuity ranking · generic multi-verb framework (thin sibling of LAND/HOLD OK; do not refactor HOLD/LAND bodies).

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-vehicle-go-to-task`** |
| 2 | `TASK_KIND_REQUEST_GO_TO = "request_go_to"` · `CAPABILITY_FLIGHT_GO_TO = "flight.go_to"` |
| 3 | `try_request_go_to_task(intent) -> Task \| None` in `assistant_task.py` |
| 4 | `VEHICLE_GO_TO_PHRASES` in `jarvis.config` — finite frozenset; exact match after `_normalize_for_continuity_match`; store pre-normalized. Minimum seed: `go to`, `goto`, `go_to`, `ve a`, `ir a`, `dirigete`, `dirigete a`, `navega`, `navigate` — accented forms normalize onto accent-free entries (`dirígete` → `dirigete`) |
| 5 | Precedence in `_handle_global_commands`: **after** LAND branch, before `return None`: Intent → `try_request_go_to_task` → fulfill GO_TO |
| 6 | Membership only for `flight.go_to`; **no** `SoftwareCapabilitySafetyGate` |
| 7 | Metadata `task_kind=request_go_to` only after membership pass |
| 8 | Seed **add** (keep all existing): capability `flight.go_to` version `0.6.16`, `availability=not_implemented`, `provider_id=provider.flight_go_to`, `health=unknown`; provider `provider.flight_go_to` `kind=vehicle` `offered_capability_ids=["flight.go_to"]`; skill `skill.request_go_to` version `0.6.16` `required_capability_ids=["flight.go_to"]` `availability=stub` |
| 9 | Fulfill: fresh disarmed `ArmedAllowlistSafetyGate()`; `propose_command(AutonomyVerb.GO_TO, intent_id=..., params={})` — **empty params**; `submit_command`; `action=vehicle_go_to`; Spanish message with safety outcome/reason + execution — never claim navigated/executed/arrived |
| 10 | Internal guards in `try_request_go_to_task`: refuse explain-shaped, Continuity-defer, **HOLD**, and **LAND** phrases |
| 11 | Fences: `assistant_task` still no FS / vehicle_profiles / `jarvis.core`. Cascade skill/cap counts → **five** skills / five caps. HOLD + LAND regression must stay green. Do not edit `_handle_vehicle_hold` / `_handle_vehicle_land` bodies |
| 12 | Version **`0.6.16`**; docs: intelligence README T8 · PLATFORM · CONNECTIONS extend (**no new C-xxx**) · PRIORIDAD · USER_GUIDE one line if needed |
| 13 | `arm()` / coord parsing / TAKEOFF… out |

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/config.py` | `VEHICLE_GO_TO_PHRASES` |
| `src/jarvis/intelligence/assistant_task.py` | `try_request_go_to_task` |
| `src/jarvis/core/orchestrator.py` | wire after LAND; `_handle_vehicle_go_to` sibling |
| `src/jarvis/capabilities/data/default_registry.json` | `flight.go_to` + provider + skill |
| `tests/test_assistant_vehicle_go_to_task_b1.py` | **new** T1–T8 |
| Cascade / HOLD / LAND tests | counts + regression |
| `pyproject.toml` | `0.6.16` |
| Docs | §0.12 |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | GO_TO phrase → Task `["flight.go_to"]`, `task_kind=request_go_to` |
| T2 | Non-go-to craft line → `None` |
| T3 | Explain / Continuity / HOLD / LAND phrase → GO_TO try is `None`; HOLD/LAND classifiers still match their own phrases |
| T4 | `handle_user_text` GO_TO phrase → Safety reject (`disarmed`); never `executed`; exploding LLM ok; HOLD / LAND / `estado` / explain precedence intact |
| T5 | Seed: `flight.go_to` `not_implemented` + separate vehicle provider + skill stub; HOLD/LAND/software rows still present |
| T6 | AST: `assistant_task` no FS / vehicle_profiles / `jarvis.core` |
| T7 | `default_safety_gate()` RejectAll; fulfill uses disarmed ArmedAllowlist; propose uses empty `params` (or omit → `{}`) |
| T8 | `pyproject` reads `0.6.16` |

Bump stale `0.6.15` checkpoints this Buy owns.

---

## 3. Acceptance

- [ ] Classify + membership + orchestrator fulfill via `submit_command(GO_TO)` with empty params  
- [ ] Disarmed ArmedAllowlist · honest UX · no FS import in intelligence · HOLD/LAND unchanged  
- [ ] Registry honesty · cascade adapted · tests T1–T8 · docs · `0.6.16`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.16`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-vehicle-go-to-task (T8)

IC: .jes/artifacts/implementation_contract_assistant_vehicle_go_to_task_b1.md
DC: .jes/artifacts/design_contract_assistant_vehicle_go_to_task_b0.md (★ CLOSED)
Parent: T7 LAND ★ ACCEPT CLOSED @ v0.6.15 (same seam; no new INV)

Add VEHICLE_GO_TO_PHRASES + try_request_go_to_task in assistant_task
(Task request_go_to → flight.go_to). Membership only — NO SoftwareCapabilitySafetyGate.
Refuse explain / Continuity / HOLD / LAND phrases inside the classifier.
intelligence must NOT import flight_software.
Wire orchestrator AFTER LAND branch: propose_command(GO_TO, params={}) +
submit_command with fresh disarmed ArmedAllowlistSafetyGate (do not arm).
Empty params this Buy — no coordinate parsing. Honest message — never claim
navigated/executed. action=vehicle_go_to.
Do NOT edit _handle_vehicle_hold / _handle_vehicle_land bodies.
Seed registry: flight.go_to not_implemented + provider.flight_go_to vehicle +
skill.request_go_to stub. Keep all prior rows.
Precedence: explain > defer > hold > land > go_to. Adapt cascade to 5 skills.
HOLD+LAND regression must stay green. Tests T1–T8. Bump to 0.6.16. Docs + PRIORIDAD. Report.
No ACCEPT claim.
```
