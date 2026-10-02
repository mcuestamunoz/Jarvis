# Implementation Report — Chat Skill-first vehicle RETURN_HOME (`B1-assistant-chat-skill-first-vehicle-return-home`, T27)

**Project:** Jarvis  
**Date:** 2026-10-02  
**Implementer:** Claude Code (Engineer authorization paste)  
**Contract:** [`implementation_contract_assistant_chat_skill_first_vehicle_return_home_b1.md`](implementation_contract_assistant_chat_skill_first_vehicle_return_home_b1.md)  
**Parents:** [DC ★ CLOSED — phase B](design_contract_assistant_chat_skill_first_b0.md) · T26 ★ ACCEPT CLOSED @ **`v0.6.35`** · T10 RETURN_HOME ★ @ `v0.6.18` · T14 allow-list widen ★ · T15 FN-016 wizard precedence ★ · T20 sim copper ★ (RETURN_HOME **not** in sim tick set)  
**Status:** Implemented — await Cursor review → Engineer ★ ACCEPT. **No ACCEPT claim.**  
**Package / tag:** `0.6.36` / **`v0.6.36`** (on ACCEPT).

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/capabilities/data/default_registry.json` | `skill.request_return_home` → `availability=available`, `version` → `0.6.36`. `flight.return_home` capability byte-unchanged — still `not_implemented`, provider still `vehicle` |
| `src/jarvis/capabilities/skills_runtime.py` | `SKILL_ID_REQUEST_RETURN_HOME` added to `_VEHICLE_GATE_SKILL_IDS` (now `{HOLD, LAND, GO_TO, TAKEOFF, RETURN_HOME}`) — same shared `_vehicle_skill_gate`, still never `SoftwareCapabilitySafetyGate`, still gate-only. Docstrings updated to mention T27 and the FN-016 precedence note |
| `src/jarvis/core/orchestrator.py` | RETURN_HOME intercept in `_handle_global_commands`: on a matched `try_request_return_home_task`, calls `run_skill("skill.request_return_home")` first; non-`ok` → honest `"Skill request_return_home no disponible (reason)."`, no silent Task-only fallback; `ok` → existing `_handle_vehicle_return_home` unchanged byte-for-byte (empty params, shared ArmedAllowlist, allow/`not_implemented` honesty) — **no sim tick added**. The FN-016 early wizard-cancel block (T15, lines ~526+) was **not** touched or moved — it still runs well before this branch |
| `tests/test_assistant_chat_skill_first_vehicle_return_home_b1.py` | **new** T1–T5 (+ T1b/T4b/T4c sub-cases, including an explicit FN-016 precedence regression test) |
| `tests/test_assistant_chat_skill_first_vehicle_hold_b1.py`, `..._land_b1.py`, `..._go_to_b1.py`, `..._takeoff_b1.py` | each had a "sibling stays stub" probe naming `skill.request_return_home` — retargeted to `skill.request_follow` (still genuinely stub), same pattern used for every prior sibling in this chain |
| `tests/test_capability_skills_runtime_software_b1.py` (T21's own file) | `test_t3_vehicle_and_ops_skills_stay_stub`'s loop no longer includes `skill.request_return_home`; `test_t4_seed_exactly_two_available_rest_stub`'s exact-set assertion extended to include it |
| `tests/test_assistant_vehicle_return_home_task_b1.py` (T10's own file) | its own seed-honesty assertion (`skill.availability == STUB`) flipped to `AVAILABLE`, same pattern used for T7/T8/T9's own files |
| `pyproject.toml` | `0.6.36` |
| Docs | PRIORIDAD · PLATFORM · CONNECTIONS (no new C-xxx) |

**Not touched:** `flight.return_home` capability (`not_implemented`, never flipped — IC's own explicit "Not"), any home/waypoint parsing or invention, the T20 sim-copper tick set (RETURN_HOME deliberately stays outside it), SD-GO_TO (untouched, still OPEN), the FN-016 early-cancel block's position or logic, FOLLOW/PATROL/ARM/DISARM/CHARGE/explain/status classify or fulfill, `AutonomyVerb` enum, `SoftwareCapabilitySafetyGate`, live ESC, voice, tip-version pins (T17 guardrail re-verified green).

---

## 2. Behavior

- Disarmed + `rtl`/`return home`/`volver` (IDLE) → Skill gate `ok`, then `_handle_vehicle_return_home`'s own unchanged Safety path → `reject`/`disarmed`, same as before this Buy.
- Armed + RETURN_HOME phrase → Skill gate `ok` → `_handle_vehicle_return_home` → Safety `allow`/`not_implemented` — **no** sim-copper attempt at all (verified: no `"Simulación"` substring, matching TAKEOFF's own precedent).
- **FN-016 regression (critical for this Buy):** inside an active `DEFINE_MISSING_PARAMETERS` wizard, `"volver"`/`"vuelve"` still cancel the wizard (`status=cancelled`) and never reach the RETURN_HOME Skill-first gate at all — verified directly (T4b). Outside a wizard (IDLE), the same word still classifies and fulfills as RETURN_HOME, now through the Skill-first gate too (T4c).
- HOLD, LAND, GO_TO, and TAKEOFF Skill-first behavior is byte-identical to before (regression-tested: T4).
- FOLLOW (and every other non-flipped vehicle/ops Skill) still `reject`/`skill_stub` via `run_skill`.

---

## 3. Tests executed

```text
pytest tests/test_assistant_chat_skill_first_vehicle_return_home_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_takeoff_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_go_to_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_land_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_hold_b1.py \
  tests/test_capability_skills_runtime_software_b1.py \
  tests/test_assistant_vehicle_return_home_task_b1.py \
  tests/test_fn016_navigation_parse_safety.py -q
→ 58 passed

pytest tests/test_suite_no_tip_version_pins_b1.py tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 19 passed (T17 guardrail + T16 ESC fence both still green)

pytest tests/ -q
→ 3931 passed, 9 skipped, 0 failed
```

Diffed against this branch's pre-T27 tip: baseline was `3923 passed, 9 skipped, 0 failed`. **Zero regressions** — the only delta is the 8 new T27 tests passing.

---

## 4. Remaining

None for this Buy. Next candidates per the DC: remaining vehicle Skill-first siblings (FOLLOW/PATROL/ARM/DISARM/CHARGE), then phase C (voice/world, phased CLI migrate). SD-GO_TO still awaits its own, explicit Buy.
