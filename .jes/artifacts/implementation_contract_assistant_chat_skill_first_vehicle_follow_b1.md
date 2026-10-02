# Implementation Contract — Chat Skill-first vehicle FOLLOW (`B1-assistant-chat-skill-first-vehicle-follow`)

**Project:** Jarvis  
**Date:** 2026-10-02  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.37`**

**Status:** **Implemented** (Claude Code) — await Cursor review → Engineer ★ ACCEPT → tag `v0.6.37`.  
**Parents:** [DC ★ CLOSED](design_contract_assistant_chat_skill_first_b0.md) · T27 ★ @ **`v0.6.36`** · T12 FOLLOW ★ @ `v0.6.20` · T14 allow-list widen ★ · T20 sim copper ★ (FOLLOW **not** in sim tick set)  
**Type:** Sixth vehicle Skill-first slice — **FOLLOW**; grow shared vehicle gate.  
**Opens:** **`0.6.37` / `v0.6.37`**. **Cola:** **T28**

**Not:** inventing target/track parse · adding FOLLOW to T20 sim copper tick set · flipping PATROL/CHARGE/ARM/DISARM · marking `flight.follow` capability `available` · live ESC · SD-GO_TO · voice · tip pins · `SoftwareCapabilitySafetyGate` for vehicle Skills.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-chat-skill-first-vehicle-follow`** |
| 2 | Flip **only** `skill.request_follow` → `availability=available` (version `0.6.37`). **`flight.follow` stays `not_implemented`**; provider stays `vehicle`. HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME Skills stay `available`. Every other vehicle/ops Skill stays `stub` |
| 3 | **Grow shared vehicle gate:** add `skill.request_follow` to `_VEHICLE_GATE_SKILL_IDS` (same `_vehicle_skill_gate` — membership + provider `kind==vehicle`). **No** `SoftwareCapabilitySafetyGate`. HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME behavior byte-stable. Gate-only `outcome="ok"`; no propose_command / ArmedAllowlist / sim / `jarvis.core` / `flight_software` in `skills_runtime` |
| 4 | **Chat FOLLOW path:** when `try_request_follow_task` matches, orch MUST call `run_skill("skill.request_follow")` first. On non-ok: honest “Skill … no disponible (reason)” — no silent Task-only fallback. On ok: existing `_handle_vehicle_follow` **unchanged** (empty params · ArmedAllowlist · allow/`not_implemented` honesty — **no** sim tick; T20 only ticks HOLD/LAND/GO_TO). Exact-match `VEHICLE_FOLLOW_PHRASES` / classify unchanged |
| 5 | Chat HOLD / LAND / GO_TO / TAKEOFF / RETURN_HOME Skill-first stay green (regression). FN-016 precedence + GO_TO “sin destino” / **SD-GO_TO OPEN** untouched |
| 6 | Classify stays. PATROL / ARM / DISARM / CHARGE / explain / status: **unchanged** this Buy |
| 7 | Tests: chat FOLLOW phrase (e.g. `follow` / known `VEHICLE_FOLLOW_PHRASES` entry) → `run_skill` + `vehicle_follow` shape; direct `run_skill("skill.request_follow")` → ok; HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME still ok; PATROL (or sibling) still stub; tip-pin green. Retarget prior “sibling stays stub” probes that named FOLLOW (T21/T23/T24/T25/T26/T27 own files) to PATROL |
| 8 | Version **`0.6.37`**; PRIORIDAD · PLATFORM · CONNECTIONS (**no new C-xxx**). SD-GO_TO row stays **OPEN** |
| 9 | Out: sim FOLLOW tick · target/track invent · further siblings · inventing cap `available` · live copper · SD-GO_TO · voice · tip pins |

---

## 1. Files

| Path | Change |
|---|---|
| `capabilities/data/default_registry.json` | `skill.request_follow` → `available` @ `0.6.37` |
| `capabilities/skills_runtime.py` | add FOLLOW to `_VEHICLE_GATE_SKILL_IDS` |
| `core/orchestrator.py` | FOLLOW intercept: `run_skill` gate then `_handle_vehicle_follow` |
| `tests/test_assistant_chat_skill_first_vehicle_follow_b1.py` | **new** |
| Retargets | T21/T23/T24/T25/T26/T27 “sibling stub” probes that still name FOLLOW → PATROL |
| `pyproject.toml` | `0.6.37` |
| Docs | short · SD-GO_TO still OPEN |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | chat FOLLOW phrase (e.g. `follow`) → `run_skill("skill.request_follow")`; `action=vehicle_follow`; Safety honesty (disarmed reject / armed allow+`not_implemented`); **no** invented track/target; **no** new sim-tick claim |
| T2 | direct `run_skill("skill.request_follow")` → `outcome=ok`; `flight.follow` still `not_implemented` |
| T3 | `run_skill` HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME still ok; `run_skill("skill.request_patrol")` still `skill_stub` |
| T4 | chat `hold` / `land` / `go to` / `takeoff` / `rtl` still Skill-first vehicle (regression) |
| T5 | No tip pins |

---

## 3. Acceptance

- [ ] FOLLOW chat gated via `run_skill` · shared vehicle gate · `flight.follow` still `not_implemented` · `0.6.37`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.37`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-chat-skill-first-vehicle-follow (T28)
Parent tip: T27 ★ ACCEPT CLOSED @ v0.6.36. Implement now → package 0.6.37.

IC: .jes/artifacts/implementation_contract_assistant_chat_skill_first_vehicle_follow_b1.md
DC: .jes/artifacts/design_contract_assistant_chat_skill_first_b0.md (★ CLOSED · phase B)
SD-GO_TO: .jes/artifacts/engineer_note_t20_goto_chat_sim_destination_debt.md (stays OPEN)

Sixth vehicle Skill-first — FOLLOW (gate only; no track invent; no sim tick):
- Flip skill.request_follow → available (flight.follow stays not_implemented)
- Add skill.request_follow to _VEHICLE_GATE_SKILL_IDS (shared gate; NO
  SoftwareCapabilitySafetyGate)
- chat follow phrase → run_skill("skill.request_follow") then existing
  _handle_vehicle_follow (empty params + ArmedAllowlist + allow/not_implemented
  honesty). FOLLOW is NOT in T20 sim copper tick set — do not add a tick.
  Hard Skill reject → no silent fallback.
HOLD/LAND/GO_TO/TAKEOFF/RETURN_HOME Skill-first stay green. Other vehicle/ops
Skills stay stub. Retarget sibling-stub probes that still name FOLLOW → PATROL.
SD-GO_TO remains OPEN. No tip pins. No ACCEPT claim.
Not live ESC · not voice · not inventing flight.follow=available · not sim FOLLOW.
```
