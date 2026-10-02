# Implementation Contract — Chat Skill-first vehicle RETURN_HOME (`B1-assistant-chat-skill-first-vehicle-return-home`)

**Project:** Jarvis  
**Date:** 2026-10-02  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Claude Code** — ★ AUTHORIZED with this delivery  
**Reviewer:** Cursor on request · Engineer ACCEPT → tag **`v0.6.36`**

**Status:** **Implemented** (Claude Code) — await Cursor review → Engineer ★ ACCEPT → tag **`v0.6.36`**.  
**Parents:** [DC ★ CLOSED](design_contract_assistant_chat_skill_first_b0.md) · T26 ★ @ **`v0.6.35`** · T10 RETURN_HOME ★ @ `v0.6.18` · T14 allow-list widen ★ · T15 FN-016 wizard precedence ★ · T20 sim copper ★ (RETURN_HOME **not** in sim tick set)  
**Type:** Fifth vehicle Skill-first slice — **RETURN_HOME**; grow shared vehicle gate.  
**Opens:** **`0.6.36` / `v0.6.36`**. **Cola:** **T27**

**Not:** inventing home/waypoint parse · adding RETURN_HOME to T20 sim copper tick set · reordering FN-016 wizard cancel vs RETURN_HOME · flipping FOLLOW/PATROL/CHARGE/ARM/DISARM · marking `flight.return_home` capability `available` · live ESC · SD-GO_TO · voice · tip pins · `SoftwareCapabilitySafetyGate` for vehicle Skills.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-chat-skill-first-vehicle-return-home`** |
| 2 | Flip **only** `skill.request_return_home` → `availability=available` (version `0.6.36`). **`flight.return_home` stays `not_implemented`**; provider stays `vehicle`. HOLD/LAND/GO_TO/TAKEOFF Skills stay `available`. Every other vehicle/ops Skill stays `stub` |
| 3 | **Grow shared vehicle gate:** add `skill.request_return_home` to `_VEHICLE_GATE_SKILL_IDS` (same `_vehicle_skill_gate` — membership + provider `kind==vehicle`). **No** `SoftwareCapabilitySafetyGate`. HOLD/LAND/GO_TO/TAKEOFF behavior byte-stable. Gate-only `outcome="ok"`; no propose_command / ArmedAllowlist / sim / `jarvis.core` / `flight_software` in `skills_runtime` |
| 4 | **Chat RETURN_HOME path:** when `try_request_return_home_task` matches, orch MUST call `run_skill("skill.request_return_home")` first. On non-ok: honest “Skill … no disponible (reason)” — no silent Task-only fallback. On ok: existing `_handle_vehicle_return_home` **unchanged** (empty params · ArmedAllowlist · allow/`not_implemented` honesty — **no** sim tick; T20 only ticks HOLD/LAND/GO_TO) |
| 5 | **FN-016 precedence stays:** when mode is `DEFINE_MISSING_PARAMETERS`, nav-back cancel (`is_navigation_back_phrase`) still runs **before** the RETURN_HOME Skill-first intercept. Do **not** reorder. Exact-match `VEHICLE_RETURN_HOME_PHRASES` / classify unchanged |
| 6 | Chat HOLD / LAND / GO_TO / TAKEOFF Skill-first stay green (regression). GO_TO “sin destino” honesty + **SD-GO_TO OPEN** untouched |
| 7 | Classify stays. FOLLOW / PATROL / ARM / DISARM / CHARGE / explain / status: **unchanged** this Buy |
| 8 | Tests: chat RETURN_HOME phrase (prefer unambiguous e.g. `rtl` / `return home`) → `run_skill` + `vehicle_return_home` shape; direct `run_skill("skill.request_return_home")` → ok; HOLD/LAND/GO_TO/TAKEOFF still ok; FOLLOW (or sibling) still stub; tip-pin green. Retarget prior “sibling stays stub” probes that named RETURN_HOME (T21/T23/T24/T25/T26 own files) to FOLLOW |
| 9 | Version **`0.6.36`**; PRIORIDAD · PLATFORM · CONNECTIONS (**no new C-xxx**). SD-GO_TO row stays **OPEN** |
| 10 | Out: sim RETURN_HOME tick · home/waypoint invent · FN-016 reorder · further siblings · inventing cap `available` · live copper · SD-GO_TO · voice · tip pins |

---

## 1. Files

| Path | Change |
|---|---|
| `capabilities/data/default_registry.json` | `skill.request_return_home` → `available` @ `0.6.36` |
| `capabilities/skills_runtime.py` | add RETURN_HOME to `_VEHICLE_GATE_SKILL_IDS` |
| `core/orchestrator.py` | RETURN_HOME intercept: `run_skill` gate then `_handle_vehicle_return_home` (after existing FN-016 early cancel) |
| `tests/test_assistant_chat_skill_first_vehicle_return_home_b1.py` | **new** |
| Retargets | T21/T23/T24/T25/T26 “sibling stub” probes that still name RETURN_HOME → FOLLOW |
| `pyproject.toml` | `0.6.36` |
| Docs | short · SD-GO_TO still OPEN |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | chat RETURN_HOME phrase (e.g. `rtl` / `return home`) → `run_skill("skill.request_return_home")`; `action=vehicle_return_home`; Safety honesty (disarmed reject / armed allow+`not_implemented`); **no** invented home coords; **no** new sim-tick claim |
| T2 | direct `run_skill("skill.request_return_home")` → `outcome=ok`; `flight.return_home` still `not_implemented` |
| T3 | `run_skill` HOLD/LAND/GO_TO/TAKEOFF still ok; `run_skill("skill.request_follow")` still `skill_stub` |
| T4 | chat `hold` / `land` / `go to` / `takeoff` still Skill-first vehicle (regression) |
| T5 | No tip pins |

---

## 3. Acceptance

- [ ] RETURN_HOME chat gated via `run_skill` · shared vehicle gate · FN-016 precedence untouched · `flight.return_home` still `not_implemented` · `0.6.36`  
- [ ] Cursor review · Engineer ACCEPT · tag **`v0.6.36`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-chat-skill-first-vehicle-return-home (T27)
Parent tip: T26 ★ ACCEPT CLOSED @ v0.6.35. Implement now → package 0.6.36.

IC: .jes/artifacts/implementation_contract_assistant_chat_skill_first_vehicle_return_home_b1.md
DC: .jes/artifacts/design_contract_assistant_chat_skill_first_b0.md (★ CLOSED · phase B)
SD-GO_TO: .jes/artifacts/engineer_note_t20_goto_chat_sim_destination_debt.md (stays OPEN)
FN-016: wizard nav-back cancel still BEFORE RETURN_HOME intercept — do not reorder.

Fifth vehicle Skill-first — RETURN_HOME (gate only; no home invent; no sim tick):
- Flip skill.request_return_home → available (flight.return_home stays not_implemented)
- Add skill.request_return_home to _VEHICLE_GATE_SKILL_IDS (shared gate; NO
  SoftwareCapabilitySafetyGate)
- chat return-home phrase → run_skill("skill.request_return_home") then existing
  _handle_vehicle_return_home (empty params + ArmedAllowlist + allow/not_implemented
  honesty). RETURN_HOME is NOT in T20 sim copper tick set — do not add a tick.
  Hard Skill reject → no silent fallback.
HOLD/LAND/GO_TO/TAKEOFF Skill-first stay green. Other vehicle/ops Skills stay stub.
Retarget sibling-stub probes that still name RETURN_HOME → FOLLOW.
SD-GO_TO remains OPEN. No tip pins. No ACCEPT claim.
Not live ESC · not voice · not inventing flight.return_home=available · not sim RTL.
```
