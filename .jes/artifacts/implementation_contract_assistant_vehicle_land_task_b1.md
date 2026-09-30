# Implementation Contract — Assistant vehicle LAND Task (`B1-assistant-vehicle-land-task`)

**Project:** Jarvis  
**Date:** 2026-09-30  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.15`**

**Status:** ★ **AUTHORIZED** (Engineer 2026-09-30 — ACCEPT T6 + redacta siguiente)  
**Parents:**
- [DC ★ CLOSED](design_contract_assistant_vehicle_land_task_b0.md)
- T6 [`B1-assistant-vehicle-hold-task`](implementation_review_assistant_vehicle_hold_task_b1.md) — ★ ACCEPT CLOSED @ **`v0.6.14`**
- [HOLD INV ★](investigation_report_assistant_vehicle_hold_task_b0.md) — seams reused; no new INV

**Type:** Second vehicle Assistant Task — classify LAND phrases → Task → orchestrator fulfill via autonomy surface + disarmed ArmedAllowlist (mirror HOLD).  
**Opens:** **`0.6.15` / `v0.6.15`** on ACCEPT.  
**Cola:** **T7**

**Not:** GO_TO · `arm()` on product path · `default_safety_gate` change · SoftwareCapabilitySafetyGate for flight · intelligence→FS import · voice · copper · Continuity ranking · collapsing HOLD+LAND into a generic verb framework (thin private helper reuse OK if it does not change HOLD behavior).

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-vehicle-land-task`** |
| 2 | `TASK_KIND_REQUEST_LAND = "request_land"` · `CAPABILITY_FLIGHT_LAND = "flight.land"` |
| 3 | `try_request_land_task(intent) -> Task \| None` in `assistant_task.py` |
| 4 | `VEHICLE_LAND_PHRASES` in `jarvis.config` — finite frozenset; exact match after `_normalize_for_continuity_match`; store pre-normalized. Minimum seed (normative): `land`, `aterrizar`, `aterriza`, `aterrizaje`, `baja`, `bajar`, `descend`, `descender` — accented forms normalize onto accent-free entries (same discipline as HOLD) |
| 5 | Precedence in `_handle_global_commands`: **after** HOLD branch, before `return None`: Intent → `try_request_land_task` → fulfill LAND |
| 6 | Membership only for `flight.land`; **no** `SoftwareCapabilitySafetyGate` / `_software_safety_allows` |
| 7 | Metadata `task_kind=request_land` only after membership pass |
| 8 | Seed **add** (keep all existing rows): capability `flight.land` version `0.6.15`, `availability=not_implemented`, `provider_id=provider.flight_land`, `health=unknown`; provider `provider.flight_land` `kind=vehicle` `offered_capability_ids=["flight.land"]`; skill `skill.request_land` version `0.6.15` `required_capability_ids=["flight.land"]` `availability=stub` |
| 9 | Fulfill: `gate = ArmedAllowlistSafetyGate()` — **do not arm**; `propose_command(AutonomyVerb.LAND, intent_id=...)`; `submit_command(cmd, gate)`; `action=vehicle_land`; Spanish message includes safety outcome/reason + execution — never claim landed/executed. Thin reuse of HOLD message-shape OK |
| 10 | Internal guards in `try_request_land_task`: refuse explain-shaped, Continuity-defer phrases, **and** HOLD phrases (so a direct caller cannot steal HOLD). Orchestrator order already protects the product path |
| 11 | Fences: `assistant_task` still no `flight_software`/`vehicle_profiles`/`jarvis.core`. Adapt cascade skill/cap counts (now four skills / four caps) honestly; keep orchestrator-only allow-list for FS import. HOLD tests must still pass |
| 12 | Version **`0.6.15`**; docs: intelligence README T7 · PLATFORM · CONNECTIONS extend (**no new C-xxx**) · PRIORIDAD · USER_GUIDE one line if needed |
| 13 | GO_TO / `arm()` out |

---

## 1. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/config.py` | `VEHICLE_LAND_PHRASES` |
| `src/jarvis/intelligence/assistant_task.py` | `try_request_land_task` + exports |
| `src/jarvis/core/orchestrator.py` | wire after HOLD; `_handle_vehicle_land` (or shared thin helper) |
| `src/jarvis/capabilities/data/default_registry.json` | `flight.land` + provider + skill |
| `tests/test_assistant_vehicle_land_task_b1.py` | **new** T1–T8 |
| Cascade / hold tests | counts + HOLD regression |
| `pyproject.toml` | `0.6.15` |
| Docs | §0.12 |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | LAND phrase → Task `["flight.land"]`, `task_kind=request_land` |
| T2 | Non-land craft line → `None` |
| T3 | Explain / Continuity / HOLD phrase → LAND try is `None` |
| T4 | `handle_user_text` LAND phrase → message has Safety reject (`disarmed`); never `executed`; exploding LLM ok; HOLD / `estado` / explain precedence intact |
| T5 | Seed: `flight.land` `not_implemented` + vehicle provider + skill stub; HOLD + software rows still present |
| T6 | AST: `assistant_task` no FS / vehicle_profiles / `jarvis.core` |
| T7 | `default_safety_gate()` RejectAll; fulfill uses disarmed ArmedAllowlist |
| T8 | `pyproject` reads `0.6.15` |

Bump stale `0.6.14` checkpoints that this Buy owns.

---

## 3. Acceptance

- [ ] Classify + membership + orchestrator fulfill via `submit_command(LAND)`  
- [ ] Disarmed ArmedAllowlist · honest UX · no FS import in intelligence · HOLD path unchanged  
- [ ] Registry honesty · cascade adapted · tests T1–T8 · docs · `0.6.15`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.15`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-vehicle-land-task (T7)

IC: .jes/artifacts/implementation_contract_assistant_vehicle_land_task_b1.md
DC: .jes/artifacts/design_contract_assistant_vehicle_land_task_b0.md (★ CLOSED)
Parent: T6 HOLD ★ ACCEPT CLOSED @ v0.6.14 (same seam; no new INV)

Add VEHICLE_LAND_PHRASES + try_request_land_task in assistant_task
(Task request_land → flight.land). Membership only — NO SoftwareCapabilitySafetyGate.
Refuse explain / Continuity / HOLD phrases inside the classifier.
intelligence must NOT import flight_software.
Wire orchestrator AFTER HOLD branch: propose_command(LAND) +
submit_command with fresh disarmed ArmedAllowlistSafetyGate (do not arm).
Honest message — never claim landed/executed. action=vehicle_land.
Seed registry: flight.land not_implemented + provider.flight_land vehicle +
skill.request_land stub. Keep all HOLD/software rows.
Precedence: explain > defer > hold > land. Adapt cascade counts.
HOLD regression must stay green. Tests T1–T8. Bump to 0.6.15. Docs + PRIORIDAD. Report.
No ACCEPT claim.
```
