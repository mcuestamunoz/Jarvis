# Implementation Contract — Chat Skill-first vehicle TAKEOFF (`B1-assistant-chat-skill-first-vehicle-takeoff`)

**Project:** Jarvis  
**Date:** 2026-10-02  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.35`**

**Status:** Cursor **PASS WITH NOTES** — await Engineer ★ ACCEPT → tag **`v0.6.35`**.  
**Parents:** [DC ★ CLOSED](design_contract_assistant_chat_skill_first_b0.md) · T25 ★ @ **`v0.6.34`** · T9 TAKEOFF ★ @ `v0.6.17` · T14 allow-list widen ★ · T20 sim copper ★ (TAKEOFF **not** in sim tick set)  
**Type:** Fourth vehicle Skill-first slice — **TAKEOFF**; grow shared vehicle gate.  
**Opens:** **`0.6.35` / `v0.6.35`**. **Cola:** **T26**

**Not:** inventing altitude parse · adding TAKEOFF to T20 sim copper tick set · flipping RETURN_HOME/FOLLOW/PATROL/CHARGE · marking `flight.takeoff` capability `available` · live ESC · SD-GO_TO · voice · tip pins · `SoftwareCapabilitySafetyGate` for vehicle Skills.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-chat-skill-first-vehicle-takeoff`** |
| 2 | Flip **only** `skill.request_takeoff` → `availability=available` (version `0.6.35`). **`flight.takeoff` stays `not_implemented`**; provider stays `vehicle`. HOLD/LAND/GO_TO Skills stay `available`. Every other vehicle/ops Skill stays `stub` |
| 3 | **Grow shared vehicle gate:** add `skill.request_takeoff` to `_VEHICLE_GATE_SKILL_IDS` (same `_vehicle_skill_gate` — membership + provider `kind==vehicle`). **No** `SoftwareCapabilitySafetyGate`. HOLD/LAND/GO_TO behavior byte-stable. Gate-only `outcome="ok"`; no propose_command / ArmedAllowlist / sim / `jarvis.core` / `flight_software` in `skills_runtime` |
| 4 | **Chat TAKEOFF path:** when `try_request_takeoff_task` matches, orch MUST call `run_skill("skill.request_takeoff")` first. On non-ok: honest “Skill … no disponible (reason)” — no silent Task-only fallback. On ok: existing `_handle_vehicle_takeoff` **unchanged** (empty params · ArmedAllowlist · allow/`not_implemented` honesty — **no** sim tick; T20 only ticks HOLD/LAND/GO_TO) |
| 5 | Chat HOLD / LAND / GO_TO Skill-first stay green (regression). GO_TO “sin destino” honesty + **SD-GO_TO OPEN** untouched |
| 6 | Classify stays. RETURN_HOME / FOLLOW / PATROL / ARM / DISARM / CHARGE / explain / status: **unchanged** this Buy |
| 7 | Tests: chat TAKEOFF phrase → `run_skill` + `vehicle_takeoff` shape; direct `run_skill("skill.request_takeoff")` → ok; HOLD/LAND/GO_TO still ok; RETURN_HOME (or sibling) still stub; tip-pin green. Retarget prior “sibling stays stub” probes that named TAKEOFF (T21/T23/T24/T25 own files) to RETURN_HOME |
| 8 | Version **`0.6.35`**; PRIORIDAD · PLATFORM · CONNECTIONS (**no new C-xxx**). SD-GO_TO row stays **OPEN** |
| 9 | Out: sim TAKEOFF tick · altitude parse · further siblings · inventing cap `available` · live copper · SD-GO_TO · voice · tip pins |

---

## 1. Files

| Path | Change |
|---|---|
| `capabilities/data/default_registry.json` | `skill.request_takeoff` → `available` @ `0.6.35` |
| `capabilities/skills_runtime.py` | add TAKEOFF to `_VEHICLE_GATE_SKILL_IDS` |
| `core/orchestrator.py` | TAKEOFF intercept: `run_skill` gate then `_handle_vehicle_takeoff` |
| `tests/test_assistant_chat_skill_first_vehicle_takeoff_b1.py` | **new** |
| Retargets | T21/T23/T24/T25 “sibling stub” probes that still name TAKEOFF → RETURN_HOME |
| `pyproject.toml` | `0.6.35` |
| Docs | short · SD-GO_TO still OPEN |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | chat TAKEOFF phrase (e.g. known `VEHICLE_TAKEOFF_PHRASES` entry) → `run_skill("skill.request_takeoff")`; `action=vehicle_takeoff`; Safety honesty (disarmed reject / armed allow+`not_implemented`); **no** invented altitude; **no** new sim-tick claim |
| T2 | direct `run_skill("skill.request_takeoff")` → `outcome=ok`; `flight.takeoff` still `not_implemented` |
| T3 | `run_skill` HOLD/LAND/GO_TO still ok; `run_skill("skill.request_return_home")` still `skill_stub` |
| T4 | chat `hold` / `land` / `go to` still Skill-first vehicle (regression) |
| T5 | No tip pins |

---

## 3. Acceptance

- [ ] TAKEOFF chat gated via `run_skill` · shared vehicle gate · `flight.takeoff` still `not_implemented` · `0.6.35`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.35`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-chat-skill-first-vehicle-takeoff (T26)
Parent tip: T25 ★ ACCEPT CLOSED @ v0.6.34. Implement now → package 0.6.35.

IC: .jes/artifacts/implementation_contract_assistant_chat_skill_first_vehicle_takeoff_b1.md
DC: .jes/artifacts/design_contract_assistant_chat_skill_first_b0.md (★ CLOSED · phase B)
SD-GO_TO: .jes/artifacts/engineer_note_t20_goto_chat_sim_destination_debt.md (stays OPEN)

Fourth vehicle Skill-first — TAKEOFF (gate only; no altitude invent; no sim tick):
- Flip skill.request_takeoff → available (flight.takeoff stays not_implemented)
- Add skill.request_takeoff to _VEHICLE_GATE_SKILL_IDS (shared gate; NO
  SoftwareCapabilitySafetyGate)
- chat takeoff phrase → run_skill("skill.request_takeoff") then existing
  _handle_vehicle_takeoff (empty params + ArmedAllowlist + allow/not_implemented
  honesty). TAKEOFF is NOT in T20 sim copper tick set — do not add a tick.
  Hard Skill reject → no silent fallback.
HOLD/LAND/GO_TO Skill-first stay green. Other vehicle/ops Skills stay stub.
Retarget sibling-stub probes that still name TAKEOFF → RETURN_HOME.
SD-GO_TO remains OPEN. No tip pins. No ACCEPT claim.
Not live ESC · not voice · not inventing flight.takeoff=available · not sim TAKEOFF.
```
