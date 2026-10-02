# Implementation Contract — Chat Skill-first vehicle GO_TO (`B1-assistant-chat-skill-first-vehicle-go-to`)

**Project:** Jarvis  
**Date:** 2026-10-02  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.34`**

**Status:** ★ **AUTHORIZED — Claude implement now** (T24 ★ @ `v0.6.33`).  
**Parents:** [DC ★ CLOSED](design_contract_assistant_chat_skill_first_b0.md) · T24 ★ @ **`v0.6.33`** · T8 GO_TO ★ @ `v0.6.16` · T20 ★ (sim copper) · [SD-GO_TO OPEN](engineer_note_t20_goto_chat_sim_destination_debt.md)  
**Type:** Third vehicle Skill-first slice — **GO_TO**; grow shared vehicle gate.  
**Opens:** **`0.6.34` / `v0.6.34`**. **Cola:** **T25**

**Not:** closing **SD-GO_TO** · inventing destination / `x_m`/`y_m` parse · flipping TAKEOFF/RH/FOLLOW/PATROL/CHARGE · marking `flight.go_to` capability `available` · live ESC · voice · tip pins · `SoftwareCapabilitySafetyGate` for vehicle Skills.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-chat-skill-first-vehicle-go-to`** |
| 2 | Flip **only** `skill.request_go_to` → `availability=available` (version `0.6.34`). **`flight.go_to` stays `not_implemented`**; provider stays `vehicle`. HOLD/LAND Skills stay `available`. Every other vehicle/ops Skill stays `stub` |
| 3 | **Grow shared vehicle gate:** add `skill.request_go_to` to `_VEHICLE_GATE_SKILL_IDS` (same `_vehicle_skill_gate` — membership + provider `kind==vehicle`). **No** `SoftwareCapabilitySafetyGate`. HOLD/LAND behavior byte-stable. Gate-only `outcome="ok"`; no propose_command / ArmedAllowlist / sim / `jarvis.core` / `flight_software` in `skills_runtime` |
| 4 | **Chat GO_TO path:** when `try_request_go_to_task` matches, orch MUST call `run_skill("skill.request_go_to")` first. On non-ok: honest “Skill … no disponible (reason)” — no silent Task-only fallback. On ok: existing `_handle_vehicle_go_to` **unchanged** (empty params · ArmedAllowlist · T20 sim honesty / “sin destino” note — **SD-GO_TO stays OPEN**) |
| 5 | Chat HOLD / LAND Skill-first stay green (regression) |
| 6 | Classify stays. TAKEOFF / RETURN_HOME / FOLLOW / PATROL / ARM / DISARM / CHARGE / explain / status: **unchanged** this Buy |
| 7 | Tests: chat GO_TO phrase → `run_skill` + `vehicle_go_to` shape + honest empty-params / sin-destino behavior preserved; direct `run_skill("skill.request_go_to")` → ok; HOLD/LAND still ok; TAKEOFF (or sibling) still stub; tip-pin green |
| 8 | Version **`0.6.34`**; PRIORIDAD · PLATFORM · CONNECTIONS (**no new C-xxx**). SD-GO_TO row stays **OPEN** |
| 9 | Out: SD-GO_TO close · destination parse · further siblings · inventing cap `available` · live copper · voice · tip pins |

---

## 1. Files

| Path | Change |
|---|---|
| `capabilities/data/default_registry.json` | `skill.request_go_to` → `available` @ `0.6.34` |
| `capabilities/skills_runtime.py` | add GO_TO to `_VEHICLE_GATE_SKILL_IDS` |
| `core/orchestrator.py` | GO_TO intercept: `run_skill` gate then `_handle_vehicle_go_to` |
| `tests/test_assistant_chat_skill_first_vehicle_go_to_b1.py` | **new** |
| `pyproject.toml` | `0.6.34` |
| Docs | short · SD-GO_TO still OPEN |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | chat GO_TO phrase (e.g. `go to` / known `VEHICLE_GO_TO_PHRASES` entry) → `run_skill("skill.request_go_to")`; `action=vehicle_go_to`; Safety honesty; empty-params / sin-destino note still honest (not invented coords) |
| T2 | direct `run_skill("skill.request_go_to")` → `outcome=ok`; `flight.go_to` still `not_implemented` |
| T3 | `run_skill("skill.request_hold")` / `skill.request_land` still ok; `run_skill("skill.request_takeoff")` still `skill_stub` |
| T4 | chat `hold` / `land` still Skill-first vehicle (regression) |
| T5 | No tip pins |

---

## 3. Acceptance

- [ ] GO_TO chat gated via `run_skill` · shared vehicle gate · SD-GO_TO still OPEN · `0.6.34`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.34`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-chat-skill-first-vehicle-go-to (T25)
Parent tip: T24 ★ ACCEPT CLOSED @ v0.6.33. Implement now → package 0.6.34.

IC: .jes/artifacts/implementation_contract_assistant_chat_skill_first_vehicle_go_to_b1.md
DC: .jes/artifacts/design_contract_assistant_chat_skill_first_b0.md (★ CLOSED · phase B)
SD-GO_TO: .jes/artifacts/engineer_note_t20_goto_chat_sim_destination_debt.md (stays OPEN)

Third vehicle Skill-first — GO_TO (gate only; no destination invent):
- Flip skill.request_go_to → available (flight.go_to stays not_implemented)
- Add skill.request_go_to to _VEHICLE_GATE_SKILL_IDS (shared gate; NO
  SoftwareCapabilitySafetyGate)
- chat go-to phrase → run_skill("skill.request_go_to") then existing
  _handle_vehicle_go_to (empty params + ArmedAllowlist + T20 “sin destino”
  honesty). Hard Skill reject → no silent fallback.
HOLD/LAND Skill-first stay green. Other vehicle/ops Skills stay stub.
SD-GO_TO remains OPEN — do NOT parse/invent x_m/y_m this Buy.
No tip pins. No ACCEPT claim.
Not live ESC · not voice · not inventing flight.go_to=available.
```
