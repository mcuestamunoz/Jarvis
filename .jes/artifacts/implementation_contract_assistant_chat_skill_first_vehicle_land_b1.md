# Implementation Contract — Chat Skill-first vehicle LAND (`B1-assistant-chat-skill-first-vehicle-land`)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Cursor** (Engineer: “Ejecuta”)  
**Reviewer:** Cursor forensic **PASS WITH NOTES** · Engineer ACCEPT → tag **`v0.6.33`**

**Status:** **Implemented** (Cursor) — Cursor review **PASS WITH NOTES** → await Engineer ★ ACCEPT → tag **`v0.6.33`**.  
**Parents:** [DC ★ CLOSED](design_contract_assistant_chat_skill_first_b0.md) · T23 ★ @ **`v0.6.32`** · T7 LAND ★ @ `v0.6.15`  
**Type:** Second vehicle Skill-first slice — **LAND**; generalize shared vehicle gate (T23 N2).  
**Opens:** **`0.6.33` / `v0.6.33`**. **Cola:** **T24**

**Not:** flipping GO_TO/TAKEOFF/…/CHARGE · marking `flight.land` (or `flight.hold`) capability `available` · live ESC · SD-GO_TO · voice · tip pins · SoftwareCapabilitySafetyGate for vehicle Skills.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-chat-skill-first-vehicle-land`** |
| 2 | Flip **only** `skill.request_land` → `availability=available` (version `0.6.33`). **`flight.land` stays `not_implemented`**; provider stays `vehicle`. Every other non-HOLD vehicle/ops Skill stays `stub` (`skill.request_hold` stays `available` from T23) |
| 3 | **Generalize vehicle gate (T23 N2):** `run_skill` MUST route `skill.request_hold` **and** `skill.request_land` through the shared `_vehicle_skill_gate` (membership + provider `kind==vehicle`) — not a second copy of the gate, and **not** `SoftwareCapabilitySafetyGate`. Prefer a finite vehicle-Skill id set or equivalent shared dispatch; HOLD behavior byte-stable. Gate-only `outcome="ok"`; no propose_command / ArmedAllowlist / sim / `jarvis.core` / `flight_software` in `skills_runtime` |
| 4 | **Chat LAND path:** when `try_request_land_task` matches, orch MUST call `run_skill("skill.request_land")` first. On non-ok: honest “Skill … no disponible (reason)” — no silent Task-only fallback. On ok: existing `_handle_vehicle_land` unchanged (ArmedAllowlist + T20 sim copper) |
| 5 | Chat HOLD path stays Skill-first (T23) — regression green |
| 6 | Classify stays. GO_TO / TAKEOFF / RETURN_HOME / FOLLOW / PATROL / ARM / DISARM / CHARGE / explain / status: **unchanged** this Buy |
| 7 | Tests: chat `land` → `run_skill` + `vehicle_land` shape; direct `run_skill("skill.request_land")` → ok; HOLD still ok; other vehicle Skill still stub; tip-pin green |
| 8 | Version **`0.6.33`**; PRIORIDAD · PLATFORM · CONNECTIONS (**no new C-xxx** unless unavoidable) |
| 9 | Out: further siblings · inventing cap `available` · live copper · voice · SD-GO_TO · tip pins |

---

## 1. Files

| Path | Change |
|---|---|
| `capabilities/data/default_registry.json` | `skill.request_land` → `available` @ `0.6.33` |
| `capabilities/skills_runtime.py` | shared vehicle gate for HOLD+LAND |
| `core/orchestrator.py` | LAND intercept: `run_skill` gate then `_handle_vehicle_land` |
| `tests/test_assistant_chat_skill_first_vehicle_land_b1.py` | **new** |
| `pyproject.toml` | `0.6.33` |
| Docs | short |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | chat `land` → `run_skill("skill.request_land")`; `action=vehicle_land` + Safety honesty |
| T2 | direct `run_skill("skill.request_land")` → `outcome=ok`; `flight.land` still `not_implemented` |
| T3 | `run_skill("skill.request_hold")` still ok; `run_skill("skill.request_go_to")` still `skill_stub` |
| T4 | chat `hold` still Skill-first vehicle (regression) |
| T5 | No tip pins |

---

## 3. Acceptance

- [ ] LAND chat gated via `run_skill` · shared vehicle gate · `0.6.33`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.33`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-chat-skill-first-vehicle-land (T24)
Parent tip: T23 ★ ACCEPT CLOSED @ v0.6.32. Implement now → package 0.6.33.

IC: .jes/artifacts/implementation_contract_assistant_chat_skill_first_vehicle_land_b1.md
DC: .jes/artifacts/design_contract_assistant_chat_skill_first_b0.md (★ CLOSED · phase B)

Second vehicle Skill-first — LAND + shared vehicle gate (T23 N2):
- Flip skill.request_land → available (flight.land stays not_implemented)
- run_skill: HOLD+LAND share _vehicle_skill_gate (NO SoftwareCapabilitySafetyGate)
- chat land → run_skill("skill.request_land") then existing _handle_vehicle_land
  (ArmedAllowlist + sim copper unchanged). Hard Skill reject → no silent fallback.
HOLD Skill-first stays green. Other vehicle/ops Skills stay stub / Task-direct.
No tip pins. No ACCEPT claim.
Not live ESC · not SD-GO_TO · not voice · not inventing flight.land=available.
```
