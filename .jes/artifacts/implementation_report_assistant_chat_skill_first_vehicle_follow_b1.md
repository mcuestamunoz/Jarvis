# Implementation Report — Chat Skill-first vehicle FOLLOW (`B1-assistant-chat-skill-first-vehicle-follow`, T28)

**Project:** Jarvis  
**Date:** 2026-10-02  
**Implementer:** Claude Code (Engineer authorization paste)  
**Contract:** [`implementation_contract_assistant_chat_skill_first_vehicle_follow_b1.md`](implementation_contract_assistant_chat_skill_first_vehicle_follow_b1.md)  
**Parents:** [DC ★ CLOSED — phase B](design_contract_assistant_chat_skill_first_b0.md) · T27 ★ ACCEPT CLOSED @ **`v0.6.36`** · T12 FOLLOW ★ @ `v0.6.20` · T14 allow-list widen ★ · T20 sim copper ★ (FOLLOW **not** in sim tick set)  
**Status:** **Implemented** (Claude Code) — await Cursor review → Engineer ★ ACCEPT.  
**Package / tag:** `0.6.37` / pending **`v0.6.37`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/capabilities/data/default_registry.json` | `skill.request_follow` → `availability=available`, `version` → `0.6.37`. `flight.follow` capability byte-unchanged — still `not_implemented`, provider still `vehicle` |
| `src/jarvis/capabilities/skills_runtime.py` | `SKILL_ID_REQUEST_FOLLOW` added to `_VEHICLE_GATE_SKILL_IDS` (now `{HOLD, LAND, GO_TO, TAKEOFF, RETURN_HOME, FOLLOW}`) — same shared `_vehicle_skill_gate`, still never `SoftwareCapabilitySafetyGate`, still gate-only. Docstrings updated to mention T28 |
| `src/jarvis/core/orchestrator.py` | FOLLOW intercept in `_handle_global_commands`: on a matched `try_request_follow_task`, calls `run_skill("skill.request_follow")` first; non-`ok` → honest `"Skill request_follow no disponible (reason)."`, no silent Task-only fallback; `ok` → existing `_handle_vehicle_follow` unchanged byte-for-byte (empty params, shared ArmedAllowlist, allow/`not_implemented` honesty) — **no sim tick added** |
| `tests/test_assistant_chat_skill_first_vehicle_follow_b1.py` | **new** T1–T5 (+ T1b sub-case) |
| `tests/test_assistant_chat_skill_first_vehicle_hold_b1.py`, `..._land_b1.py`, `..._go_to_b1.py`, `..._takeoff_b1.py`, `..._return_home_b1.py` | each had a "sibling stays stub" probe naming `skill.request_follow` — retargeted to `skill.request_patrol` (still genuinely stub), same pattern used for every prior sibling in this chain |
| `tests/test_capability_skills_runtime_software_b1.py` (T21's own file) | `test_t3_vehicle_and_ops_skills_stay_stub`'s loop no longer includes `skill.request_follow`; `test_t4_seed_exactly_two_available_rest_stub`'s exact-set assertion extended to include it |
| `pyproject.toml` | `0.6.37` |
| Docs | PRIORIDAD · PLATFORM · CONNECTIONS (no new C-xxx) |

**Not touched:** `flight.follow` capability (`not_implemented`, never flipped — IC's own explicit "Not"), any track/target parsing or invention, the T20 sim-copper tick set (FOLLOW deliberately stays outside it), SD-GO_TO (untouched, still OPEN), PATROL/ARM/DISARM/CHARGE/explain/status classify or fulfill, `AutonomyVerb` enum, `SoftwareCapabilitySafetyGate`, live ESC, voice, tip-version pins (T17 guardrail re-verified green). `test_assistant_vehicle_follow_task_b1.py` (T12's own file) needed no retarget — its only `skill.request_follow` reference is a registry-membership check (`<=`), not an availability equality assertion.

---

## 2. Behavior

- Disarmed + `follow` (IDLE) → Skill gate `ok`, then `_handle_vehicle_follow`'s own unchanged Safety path → `reject`/`disarmed`, same as before this Buy.
- Armed + `follow` → Skill gate `ok` → `_handle_vehicle_follow` → Safety `allow`/`not_implemented` — **no** sim-copper attempt at all (verified: no `"Simulación"` substring, matching TAKEOFF/RETURN_HOME's own precedent).
- HOLD, LAND, GO_TO, TAKEOFF, and RETURN_HOME Skill-first behavior is byte-identical to before (regression-tested: T4).
- PATROL (and every other non-flipped vehicle/ops Skill) still `reject`/`skill_stub` via `run_skill`.

---

## 3. Tests executed

```text
pytest tests/test_assistant_chat_skill_first_vehicle_follow_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_go_to_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_hold_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_land_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_takeoff_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_return_home_b1.py \
  tests/test_capability_skills_runtime_software_b1.py \
  tests/test_assistant_vehicle_follow_task_b1.py \
  tests/test_assistant_vehicle_patrol_task_b1.py -q
→ 60 passed

pytest tests/test_suite_no_tip_version_pins_b1.py tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 19 passed (T17 guardrail + T16 ESC fence both still green)

pytest tests/ -q
→ 3937 passed, 9 skipped, 0 failed
```

Diffed against this branch's pre-T28 tip (stash push/pop): baseline was `3931 passed, 9 skipped, 0 failed`. **Zero regressions** — the only delta is the 6 new T28 tests passing.

---

## 4. Remaining

None for this Buy. Next candidates per the DC: remaining vehicle Skill-first siblings (PATROL/ARM/DISARM/CHARGE), then phase C (voice/world, phased CLI migrate). SD-GO_TO still awaits its own, explicit Buy.
