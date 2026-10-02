# Implementation Contract — Chat Skill-first vehicle HOLD (`B1-assistant-chat-skill-first-vehicle-hold`)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Author:** JES / Cursor — **IC only**  
**Implementer:** **Cursor** (Engineer: “Ejecuta tu ic t23”)  
**Reviewer:** Cursor forensic **PASS WITH NOTES** · Engineer ACCEPT → tag **`v0.6.32`**

**Status:** **★ ACCEPT CLOSED** (Engineer 2026-10-01) — Cursor review **PASS WITH NOTES** · tag **`v0.6.32`**.  
**Parents:** [DC ★ CLOSED](design_contract_assistant_chat_skill_first_b0.md) · T22 ★ @ **`v0.6.31`** · T6 HOLD ★ @ `v0.6.14`  
**Type:** First Skill-first chat slice for a **vehicle** Skill — **HOLD only**.  
**Opens:** **`0.6.32` / `v0.6.32`**. **Cola:** **T23**

**Not:** flipping LAND/GO_TO/…/CHARGE Skills to `available` · marking `flight.hold` capability `available` · live ESC/copper · SD-GO_TO · voice · tip pins · routing vehicle Skills through `SoftwareCapabilitySafetyGate` as if they were software.

---

## 0. Engineer Buy (locked)

| # | Lock |
|---|---|
| 1 | Buy **`B1-assistant-chat-skill-first-vehicle-hold`** |
| 2 | Flip **only** `skill.request_hold` → `availability=available` in `default_registry.json` (bump that Skill’s `version` to `0.6.32`). **`flight.hold` stays `not_implemented`**; provider stays `vehicle`. Every other vehicle/ops Skill stays `stub` |
| 3 | **`run_skill` vehicle path:** for `skill.request_hold` (and only this Skill this Buy), after lookup + `available`, do **not** call `_software_safety_allows_skill` / `SoftwareCapabilitySafetyGate`. Instead: registry **membership** check that every `required_capability_id` exists and its bound provider `kind == vehicle` (finite reject reasons, e.g. `capability_unknown` / `provider_not_vehicle`). On pass → `outcome="ok"` as a **gate** (message optional/None). **No** `propose_command` / ArmedAllowlist / sim / `jarvis.core` / `flight_software` imports inside `skills_runtime` |
| 4 | **Chat HOLD path:** when `try_request_hold_task` matches, orch MUST call `run_skill("skill.request_hold")` first. On `skill_stub` / `safety_reject` / `unknown_skill` / vehicle-path hard rejects: **do not** silently fall through to Task-only fulfill — honest “Skill … no disponible (reason)” message. On `ok`: call existing `_handle_vehicle_hold` unchanged (shared ArmedAllowlist + T20 sim copper honesty preserved) |
| 5 | Classify stays (`try_request_hold_task` / phrase table). Skill-first = **fulfill gate through `run_skill`**, not delete Tasks |
| 6 | LAND / GO_TO / TAKEOFF / RETURN_HOME / FOLLOW / PATROL / ARM / DISARM / CHARGE / explain / status: **unchanged** this Buy (still their current Task or software Skill-first paths) |
| 7 | Tests: chat `hold` → `run_skill("skill.request_hold")` exercised + same `vehicle_hold` product shape / ArmedAllowlist honesty; `run_skill("skill.request_hold")` alone → ok gate (not `skill_stub`); other vehicle Skill still stub; software Skill-first still green; tip-pin / ESC fences green |
| 8 | Version **`0.6.32`**; PRIORIDAD · PLATFORM · CONNECTIONS note (**no new C-xxx** unless unavoidable). Refresh stale T21 “Skill-first is next block” prose in `skills_runtime.py` docstring if touched |
| 9 | Out: other vehicle Skill-first · inventing `flight.hold=available` · live copper · voice · SD-GO_TO · tip pins |

---

## 1. Files

| Path | Change |
|---|---|
| `capabilities/data/default_registry.json` | `skill.request_hold` → `available` @ `0.6.32` |
| `capabilities/skills_runtime.py` | vehicle HOLD gate path (no SoftwareCapabilitySafetyGate) |
| `core/orchestrator.py` | HOLD intercept: `run_skill` gate then `_handle_vehicle_hold` |
| `tests/test_assistant_chat_skill_first_vehicle_hold_b1.py` | **new** |
| `pyproject.toml` | `0.6.32` |
| Docs | short |

---

## 2. Tests

| ID | Assert |
|---|---|
| T1 | chat `hold` → `run_skill("skill.request_hold")` called; response still `action=vehicle_hold` + Safety honesty (disarmed reject ok) |
| T2 | direct `run_skill("skill.request_hold")` → `outcome=ok` (not `skill_stub`); must **not** use software Safety (vehicle provider) |
| T3 | `run_skill("skill.request_land")` (or another vehicle Skill) still `skill_stub` |
| T4 | chat `explain` / `estado` still Skill-first software (regression) |
| T5 | No tip pins |

---

## 3. Acceptance

- [x] HOLD chat gated via `run_skill` · `flight.hold` still `not_implemented` · other vehicle Skills stub · `0.6.32`  
- [x] Cursor review · Engineer ACCEPT · tag **`v0.6.32`**

---

## 4. Paste for Claude (AUTHORIZED)

```text
★ AUTHORIZED implementation — B1-assistant-chat-skill-first-vehicle-hold (T23)
Parent tip: T22 ★ ACCEPT CLOSED @ v0.6.31. Implement now → package 0.6.32.

IC: .jes/artifacts/implementation_contract_assistant_chat_skill_first_vehicle_hold_b1.md
DC: .jes/artifacts/design_contract_assistant_chat_skill_first_b0.md (★ CLOSED · phase B)

First vehicle Skill-first — HOLD only:
- Flip skill.request_hold → available (flight.hold stays not_implemented)
- run_skill vehicle path: NO SoftwareCapabilitySafetyGate; membership +
  provider kind==vehicle; outcome ok = gate only (no propose_command/sim/core)
- chat hold → run_skill("skill.request_hold") then existing _handle_vehicle_hold
  (ArmedAllowlist + sim copper unchanged). Hard Skill reject → no silent fallback.
Other vehicle/ops Skills stay stub / Task-direct. No tip pins. No ACCEPT claim.
Not live ESC · not SD-GO_TO · not voice · not inventing flight.hold=available.
```
