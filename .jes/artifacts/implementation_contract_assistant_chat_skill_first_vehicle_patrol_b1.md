# Implementation Contract — Chat Skill-first vehicle PATROL (`B1-assistant-chat-skill-first-vehicle-patrol`)

**Project:** Jarvis  
**Date:** 2026-10-02  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.38`**

**Status:** **★ ACCEPT CLOSED** (Engineer 2026-10-02) — Cursor review **PASS WITH NOTES** · tag **`v0.6.38`**.  
**Parents:** [DC ★ CLOSED](design_contract_assistant_chat_skill_first_b0.md) · T28 ★ @ **`v0.6.37`** · T13 PATROL ★ @ `v0.6.21` · T14 allow-list widen ★ · T20 sim copper ★ (PATROL **not** in sim tick set)  
**Type:** Seventh vehicle Skill-first slice — **PATROL**; grow shared vehicle gate; **closes the seven chat AutonomyVerb Skill-first set**.  
**Opens:** **`0.6.38` / `v0.6.38`**. **Cola:** **T29**

**Not:** inventing route/circuit parse · adding PATROL to T20 sim copper tick set · flipping CHARGE/ARM/DISARM · marking `flight.patrol` capability `available` · live ESC · SD-GO_TO · voice · tip pins · `SoftwareCapabilitySafetyGate` for vehicle Skills.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-chat-skill-first-vehicle-patrol`** |
| 2 | Flip **only** `skill.request_patrol` → `availability=available` (version `0.6.38`). **`flight.patrol` stays `not_implemented`**; provider stays `vehicle`. HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME/FOLLOW Skills stay `available`. Every other vehicle/ops Skill stays `stub` (CHARGE / ARM / DISARM remain stub) |
| 3 | **Grow shared vehicle gate:** add `skill.request_patrol` to `_VEHICLE_GATE_SKILL_IDS` (same `_vehicle_skill_gate` — membership + provider `kind==vehicle`). **No** `SoftwareCapabilitySafetyGate`. Prior six vehicle Skills behavior byte-stable. Gate-only `outcome="ok"`; no propose_command / ArmedAllowlist / sim / `jarvis.core` / `flight_software` in `skills_runtime` |
| 4 | **Chat PATROL path:** when `try_request_patrol_task` matches, orch MUST call `run_skill("skill.request_patrol")` first. On non-ok: honest “Skill … no disponible (reason)” — no silent Task-only fallback. On ok: existing `_handle_vehicle_patrol` **unchanged** (empty params · ArmedAllowlist · allow/`not_implemented` honesty — **no** sim tick; T20 only ticks HOLD/LAND/GO_TO). Exact-match `VEHICLE_PATROL_PHRASES` / classify unchanged |
| 5 | Chat HOLD / LAND / GO_TO / TAKEOFF / RETURN_HOME / FOLLOW Skill-first stay green (regression). FN-016 precedence + GO_TO “sin destino” / **SD-GO_TO OPEN** untouched |
| 6 | Classify stays. ARM / DISARM / CHARGE / explain / status: **unchanged** this Buy |
| 7 | Tests: chat PATROL phrase (e.g. `patrol` / known `VEHICLE_PATROL_PHRASES` entry) → `run_skill` + `vehicle_patrol` shape; direct `run_skill("skill.request_patrol")` → ok; six prior vehicle Skills still ok; CHARGE (or sibling) still stub; tip-pin green. Retarget prior “sibling stays stub” probes that named PATROL (T21/T23–T28 own files) to CHARGE |
| 8 | Version **`0.6.38`**; PRIORIDAD · PLATFORM · CONNECTIONS (**no new C-xxx**). SD-GO_TO row stays **OPEN**. Note: this Buy closes AutonomyVerb vehicle Skill-first (HOLD…PATROL); remaining Skill-first candidates are policy/ops (ARM/DISARM/CHARGE), not further AutonomyVerbs |
| 9 | Out: sim PATROL tick · route invent · CHARGE/ARM/DISARM · inventing cap `available` · live copper · SD-GO_TO · voice · tip pins |

---

## 1. Files

| Path | Change |
|---|---|
| `capabilities/data/default_registry.json` | `skill.request_patrol` → `available` @ `0.6.38` |
| `capabilities/skills_runtime.py` | add PATROL to `_VEHICLE_GATE_SKILL_IDS` |
| `core/orchestrator.py` | PATROL intercept: `run_skill` gate then `_handle_vehicle_patrol` |
| `tests/test_assistant_chat_skill_first_vehicle_patrol_b1.py` | **new** |
| Retargets | T21/T23–T28 “sibling stub” probes that still name PATROL → CHARGE |
| `pyproject.toml` | `0.6.38` |
| Docs | short · SD-GO_TO still OPEN |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | chat PATROL phrase (e.g. `patrol`) → `run_skill("skill.request_patrol")`; `action=vehicle_patrol`; Safety honesty (disarmed reject / armed allow+`not_implemented`); **no** invented route; **no** new sim-tick claim |
| T2 | direct `run_skill("skill.request_patrol")` → `outcome=ok`; `flight.patrol` still `not_implemented` |
| T3 | `run_skill` HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME/FOLLOW still ok; `run_skill("skill.request_charge")` still `skill_stub` |
| T4 | chat `hold` / `land` / `go to` / `takeoff` / `rtl` / `follow` still Skill-first vehicle (regression) |
| T5 | No tip pins |

---

## 3. Acceptance

- [x] PATROL chat gated via `run_skill` · shared vehicle gate · seven AutonomyVerb Skills available · `flight.patrol` still `not_implemented` · `0.6.38`  
- [x] Cursor review · Engineer ACCEPT · tag **`v0.6.38`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-chat-skill-first-vehicle-patrol (T29)
Parent tip: T28 ★ ACCEPT CLOSED @ v0.6.37. Implement now → package 0.6.38.

IC: .jes/artifacts/implementation_contract_assistant_chat_skill_first_vehicle_patrol_b1.md
DC: .jes/artifacts/design_contract_assistant_chat_skill_first_b0.md (★ CLOSED · phase B)
SD-GO_TO: .jes/artifacts/engineer_note_t20_goto_chat_sim_destination_debt.md (stays OPEN)

Seventh vehicle Skill-first — PATROL (gate only; no route invent; no sim tick).
Closes the seven chat AutonomyVerb Skill-first set (HOLD…PATROL):
- Flip skill.request_patrol → available (flight.patrol stays not_implemented)
- Add skill.request_patrol to _VEHICLE_GATE_SKILL_IDS (shared gate; NO
  SoftwareCapabilitySafetyGate)
- chat patrol phrase → run_skill("skill.request_patrol") then existing
  _handle_vehicle_patrol (empty params + ArmedAllowlist + allow/not_implemented
  honesty). PATROL is NOT in T20 sim copper tick set — do not add a tick.
  Hard Skill reject → no silent fallback.
HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME/FOLLOW Skill-first stay green.
CHARGE/ARM/DISARM stay stub. Retarget sibling-stub probes that still name
PATROL → CHARGE.
SD-GO_TO remains OPEN. No tip pins. No ACCEPT claim.
Not live ESC · not voice · not inventing flight.patrol=available · not sim PATROL.
```
