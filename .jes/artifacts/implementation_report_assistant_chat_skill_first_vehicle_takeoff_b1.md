# Implementation Report — Chat Skill-first vehicle TAKEOFF (`B1-assistant-chat-skill-first-vehicle-takeoff`, T26)

**Project:** Jarvis  
**Date:** 2026-10-02  
**Implementer:** Claude Code (Engineer authorization paste)  
**Contract:** [`implementation_contract_assistant_chat_skill_first_vehicle_takeoff_b1.md`](implementation_contract_assistant_chat_skill_first_vehicle_takeoff_b1.md)  
**Parents:** [DC ★ CLOSED — phase B](design_contract_assistant_chat_skill_first_b0.md) · T25 ★ ACCEPT CLOSED @ **`v0.6.34`** · T9 TAKEOFF ★ @ `v0.6.17` · T14 allow-list widen ★ · T20 sim copper ★ (TAKEOFF **not** in sim tick set)  
**Status:** **★ ACCEPT CLOSED** (Engineer 2026-10-02) — Cursor **PASS WITH NOTES**.  
**Package / tag:** `0.6.35` / **`v0.6.35`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/capabilities/data/default_registry.json` | `skill.request_takeoff` → `availability=available`, `version` → `0.6.35`. `flight.takeoff` capability byte-unchanged — still `not_implemented`, provider still `vehicle` |
| `src/jarvis/capabilities/skills_runtime.py` | `SKILL_ID_REQUEST_TAKEOFF` added to `_VEHICLE_GATE_SKILL_IDS` (now `{HOLD, LAND, GO_TO, TAKEOFF}`) — same shared `_vehicle_skill_gate`, still never `SoftwareCapabilitySafetyGate`, still gate-only. Docstrings updated to mention T26 and explicitly note TAKEOFF stays outside the T20 sim-tick set |
| `src/jarvis/core/orchestrator.py` | TAKEOFF intercept in `_handle_global_commands`: on a matched `try_request_takeoff_task`, calls `run_skill("skill.request_takeoff")` first; non-`ok` → honest `"Skill request_takeoff no disponible (reason)."`, no silent Task-only fallback; `ok` → existing `_handle_vehicle_takeoff` unchanged byte-for-byte (empty params, shared ArmedAllowlist, allow/`not_implemented` honesty) — **no sim tick added**, confirmed by test |
| `tests/test_assistant_chat_skill_first_vehicle_takeoff_b1.py` | **new** T1–T5 |
| `tests/test_assistant_chat_skill_first_vehicle_hold_b1.py`, `..._land_b1.py`, `..._go_to_b1.py` | each had a "sibling stays stub" probe naming `skill.request_takeoff` — retargeted to `skill.request_return_home` (still genuinely stub), same pattern used for every prior sibling in this chain |
| `tests/test_capability_skills_runtime_software_b1.py` (T21's own file) | `test_t3_vehicle_and_ops_skills_stay_stub`'s loop no longer includes `skill.request_takeoff`; `test_t4_seed_exactly_two_available_rest_stub`'s exact-set assertion extended to include it |
| `tests/test_assistant_vehicle_takeoff_task_b1.py` (T9's own file) | its own seed-honesty assertion (`takeoff_skill.availability == STUB`) flipped to `AVAILABLE`, same pattern T24/T25 used for LAND's/GO_TO's own T7/T8 files |
| `pyproject.toml` | `0.6.35` |
| Docs | PRIORIDAD · PLATFORM · CONNECTIONS (no new C-xxx) |

**Not touched:** `flight.takeoff` capability (`not_implemented`, never flipped — IC's own explicit "Not"), any altitude parsing or invention, the T20 sim-copper tick set (TAKEOFF deliberately stays outside it — no tick logic added anywhere for this verb), SD-GO_TO (untouched, still OPEN), RETURN_HOME/FOLLOW/PATROL/ARM/DISARM/CHARGE/explain/status classify or fulfill, `AutonomyVerb` enum, `SoftwareCapabilitySafetyGate`, live ESC, voice, tip-version pins (T17 guardrail re-verified green).

---

## 2. Behavior

- Disarmed + `takeoff` → Skill gate `ok` (TAKEOFF is now a real vehicle-gated Skill), then `_handle_vehicle_takeoff`'s own unchanged Safety path → `reject`/`disarmed`, same as before this Buy.
- Armed + `takeoff` → Skill gate `ok` → `_handle_vehicle_takeoff` → Safety `allow`/`not_implemented` — **no** sim-copper attempt at all (verified: no `"Simulación"` substring in the message, unlike HOLD/LAND/GO_TO).
- HOLD, LAND, and GO_TO Skill-first behavior is byte-identical to before (regression-tested: T4), including GO_TO's own "sin destino" honesty note (T4b) — SD-GO_TO untouched.
- RETURN_HOME (and every other non-flipped vehicle/ops Skill) still `reject`/`skill_stub` via `run_skill`.

---

## 3. Tests executed

```text
pytest tests/test_assistant_chat_skill_first_vehicle_takeoff_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_go_to_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_land_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_hold_b1.py \
  tests/test_capability_skills_runtime_software_b1.py \
  tests/test_assistant_vehicle_takeoff_task_b1.py -q
→ 37 passed

pytest tests/test_suite_no_tip_version_pins_b1.py tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 19 passed (T17 guardrail + T16 ESC fence both still green)

pytest tests/ -q
→ 3923 passed, 9 skipped, 0 failed
```

Diffed against this branch's pre-T26 tip: baseline was `3916 passed, 9 skipped, 0 failed`. **Zero regressions** — the only delta is the 7 new T26 tests passing.

---

## 4. Remaining

None for this Buy. Next candidates per the DC: remaining vehicle Skill-first siblings (RETURN_HOME/FOLLOW/PATROL/ARM/DISARM/CHARGE), then phase C (voice/world, phased CLI migrate). SD-GO_TO still awaits its own, explicit Buy.
