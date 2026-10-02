# Implementation Report — Chat Skill-first vehicle PATROL (`B1-assistant-chat-skill-first-vehicle-patrol`, T29)

**Project:** Jarvis  
**Date:** 2026-10-02  
**Implementer:** Claude Code (Engineer authorization paste)  
**Contract:** [`implementation_contract_assistant_chat_skill_first_vehicle_patrol_b1.md`](implementation_contract_assistant_chat_skill_first_vehicle_patrol_b1.md)  
**Parents:** [DC ★ CLOSED — phase B](design_contract_assistant_chat_skill_first_b0.md) · T28 ★ ACCEPT CLOSED @ **`v0.6.37`** · T13 PATROL ★ @ `v0.6.21` · T14 allow-list widen ★ · T20 sim copper ★ (PATROL **not** in sim tick set)  
**Status:** **Implemented** (Claude Code) — await Cursor review → Engineer ★ ACCEPT.  
**Package / tag:** `0.6.38` / pending **`v0.6.38`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/capabilities/data/default_registry.json` | `skill.request_patrol` → `availability=available`, `version` → `0.6.38`. `flight.patrol` capability byte-unchanged — still `not_implemented`, provider still `vehicle` |
| `src/jarvis/capabilities/skills_runtime.py` | `SKILL_ID_REQUEST_PATROL` added to `_VEHICLE_GATE_SKILL_IDS` (now `{HOLD, LAND, GO_TO, TAKEOFF, RETURN_HOME, FOLLOW, PATROL}`) — same shared `_vehicle_skill_gate`, still never `SoftwareCapabilitySafetyGate`, still gate-only. Docstrings updated to mention T29 and that this closes the full seven-verb AutonomyVerb Skill-first set |
| `src/jarvis/core/orchestrator.py` | PATROL intercept in `_handle_global_commands`: on a matched `try_request_patrol_task`, calls `run_skill("skill.request_patrol")` first; non-`ok` → honest `"Skill request_patrol no disponible (reason)."`, no silent Task-only fallback; `ok` → existing `_handle_vehicle_patrol` unchanged byte-for-byte (empty params, shared ArmedAllowlist, allow/`not_implemented` honesty) — **no sim tick added** |
| `tests/test_assistant_chat_skill_first_vehicle_patrol_b1.py` | **new** T1–T5 (+ T1b sub-case) |
| `tests/test_assistant_chat_skill_first_vehicle_hold_b1.py`, `..._land_b1.py`, `..._go_to_b1.py`, `..._takeoff_b1.py`, `..._return_home_b1.py`, `..._follow_b1.py` | each had a "sibling stays stub" probe naming `skill.request_patrol` — retargeted to `skill.request_charge` (still genuinely stub). In `..._hold_b1.py` this collapsed a now-redundant duplicate CHARGE assertion back down to one check (that file already probed CHARGE separately before this Buy) |
| `tests/test_capability_skills_runtime_software_b1.py` (T21's own file) | `test_t3_vehicle_and_ops_skills_stay_stub`'s loop no longer includes `skill.request_patrol`; `test_t4_seed_exactly_two_available_rest_stub`'s exact-set assertion extended to include it |
| `pyproject.toml` | `0.6.38` |
| Docs | PRIORIDAD · PLATFORM · CONNECTIONS (no new C-xxx) |

**Not touched:** `flight.patrol` capability (`not_implemented`, never flipped — IC's own explicit "Not"), any route/circuit parsing or invention, the T20 sim-copper tick set (PATROL deliberately stays outside it), SD-GO_TO (untouched, still OPEN), ARM/DISARM/CHARGE/explain/status classify or fulfill, `AutonomyVerb` enum, `SoftwareCapabilitySafetyGate`, live ESC, voice, tip-version pins (T17 guardrail re-verified green). `test_assistant_vehicle_patrol_task_b1.py` (T13's own file) needed no retarget — its only `skill.request_patrol` reference besides the `flight.patrol` capability check is a registry-membership check (`<=`), not an availability equality assertion.

---

## 2. Behavior

- Disarmed + `patrol` (IDLE) → Skill gate `ok`, then `_handle_vehicle_patrol`'s own unchanged Safety path → `reject`/`disarmed`, same as before this Buy.
- Armed + `patrol` → Skill gate `ok` → `_handle_vehicle_patrol` → Safety `allow`/`not_implemented` — **no** sim-copper attempt at all (verified: no `"Simulación"` substring, matching TAKEOFF/RETURN_HOME/FOLLOW's own precedent).
- HOLD, LAND, GO_TO, TAKEOFF, RETURN_HOME, and FOLLOW Skill-first behavior is byte-identical to before (regression-tested: T4).
- CHARGE (and ARM/DISARM) still `reject`/`skill_stub` via `run_skill`. **This Buy closes the full seven-verb chat AutonomyVerb Skill-first set** (HOLD…PATROL) — remaining Skill-first candidates per the DC are policy/ops Skills (ARM/DISARM/CHARGE), not further AutonomyVerbs.

---

## 3. Tests executed

```text
pytest tests/test_assistant_chat_skill_first_vehicle_patrol_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_go_to_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_hold_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_land_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_takeoff_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_return_home_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_follow_b1.py \
  tests/test_capability_skills_runtime_software_b1.py \
  tests/test_assistant_vehicle_patrol_task_b1.py \
  tests/test_assistant_ops_charge_task_b1.py -q
→ 66 passed

pytest tests/test_suite_no_tip_version_pins_b1.py tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 19 passed (T17 guardrail + T16 ESC fence both still green)

pytest tests/ -q
→ 3943 passed, 9 skipped, 0 failed
```

Diffed against this branch's pre-T29 tip (stash push/pop): baseline was `3937 passed, 9 skipped, 0 failed`. **Zero regressions** — the only delta is the 6 new T29 tests passing.

---

## 4. Remaining

None for this Buy. Next candidates per the DC: policy/ops Skill-first siblings (ARM/DISARM/CHARGE — no further AutonomyVerbs remain), then phase C (voice/world, phased CLI migrate). SD-GO_TO still awaits its own, explicit Buy.
