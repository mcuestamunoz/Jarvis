# Implementation Report — Assistant chat → sim copper (`B1-assistant-chat-sim-copper`, T20)

**Project:** Jarvis  
**Date:** 2026-10-01  
**Implementer:** Claude Code (Engineer authorization paste)  
**Contract:** [`implementation_contract_assistant_chat_sim_copper_b1.md`](implementation_contract_assistant_chat_sim_copper_b1.md)  
**Parents:** [DC ★ CLOSED](design_contract_assistant_chat_sim_copper_b0.md) · T14 ★ · T19 ★ ACCEPT CLOSED @ **`v0.6.28`** · C40 sim executor  
**Status:** Implemented — await Cursor review → Engineer ★ ACCEPT. **No ACCEPT claim.**  
**Package / tag:** `0.6.29` / **`v0.6.29`** (on ACCEPT).

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/core/orchestrator.py` | New lazy `_sim_autonomy_executor()` (owns one process-scoped `SimAutonomyExecutor` + `ToyQuad6DofPlant`, mirrors `_vehicle_chat_safety_gate()`'s pattern) + `_sim_autonomy_tick_note(verb)` helper. `_handle_vehicle_hold`/`_handle_vehicle_land`/`_handle_vehicle_go_to` now call the helper and append its note to the message **only when** `result.safety.outcome == "allow"`. `submit_command`'s own `execution` field is untouched — preferred path (a), confirmed byte-stable |
| `tests/test_assistant_chat_sim_copper_b1.py` | **new** T1–T4 (+ T1b/T1c/T2b sub-cases) |
| `tests/test_assistant_vehicle_allowlist_widen_b1.py` | T14's own `test_t7_no_sim_autonomy_executor_wired_from_chat` retargeted — that exact prohibition is now obsolete by this Buy's own explicit design; renamed/rewritten to check the real, still-permanent invariant (T16's AST-honest ESC fence) instead of a stale substring ban |
| `tests/test_fase_c_autonomy_executor_b1.py`, `tests/test_fase_c_controlled_flight_sim_tip_b1.py`, `tests/test_fase_c_sim_6dof_plant_b1.py` | 3 historical core/adapters isolation tests (pre-dating this Buy) that blanket-forbade `SimAutonomyExecutor`/`flight_control.plant`/`ToyQuad6DofPlant` anywhere under `core/`/`adapters/` — each retargeted to exclude `orchestrator.py` by name only; every other file in those directories is still checked exactly as before |
| `pyproject.toml` | `0.6.29` |
| Docs | PRIORIDAD · PLATFORM · CONNECTIONS (no new C-xxx) |

**Not touched:** `submit_command`/`AutonomySubmissionResult`/the C4 surface (`execution` stays `"not_implemented"` byte-unchanged, confirmed by test and by preferred-path choice), `ArmedAllowlistSafetyGate`, any `try_request_*` classifier, `SimulatedEscSink`/ESC HAL (never imported — T16 fence re-verified green), TAKEOFF/RETURN_HOME/FOLLOW/PATROL fulfill bodies (no tick call added — sim executor doesn't support those verbs), CHARGE, Skills, tip-version pins (T17 guardrail re-verified green).

---

## 2. Behavior

- Armed + HOLD/LAND → Safety `allow`, `execution=not_implemented` (unchanged), **plus** one real sim tick — message includes `"Simulación (no vuelo real, sin ESC/motores): tick en t=…s, colectivo=…"`.
- Armed + GO_TO → same `allow`/`not_implemented`, but the sim executor's own contract requires `x_m`/`y_m` and chat GO_TO never supplies them (T8 — no coordinate parsing). Caught and reported honestly: `"Simulación no disponible sin destino…"` — never a crash, never an invented destination.
- Armed + TAKEOFF/RETURN_HOME/FOLLOW/PATROL → `allow`/`not_implemented`, **no** tick, no `"Simulación"` text — unchanged from before this Buy.
- Disarmed (any verb) → `reject`/`disarmed`, no tick — unchanged.
- Never claims copper flight, live motors, or ESC arm at any point.

**One design note for reviewers:** the IC's own test table (§2) doesn't enumerate a GO_TO-specific case, and the sim executor (`C40`) hard-requires `x_m`/`y_m` for `GO_TO` by contract — which chat's own `GO_TO` fulfill never supplies (T8's own lock: no coordinate parsing). I resolved this by catching the resulting `ValueError` and reporting it as an honest "simulation unavailable without a target" note, rather than inventing coordinates or letting the call crash. Flagging this explicitly in case Cursor/Engineer want a different resolution on review.

---

## 3. Tests executed

```text
pytest tests/test_assistant_chat_sim_copper_b1.py -q
→ 7 passed

pytest tests/test_assistant_vehicle_allowlist_widen_b1.py tests/test_fase_c_esc_pwm_stub_rung_b1.py \
  tests/test_suite_no_tip_version_pins_b1.py -q
→ 26 passed

pytest tests/ -q
→ 3888 passed, 9 skipped, 0 failed
```

Diffed against this branch's pre-T20 tip: baseline was `3881 passed, 9 skipped, 0 failed`. **Zero regressions** — the only delta is the 7 new T20 tests passing.

---

## 4. Remaining

**This Buy:** none blocking.  
**Listed debt (not in this Buy):** **SD-GO_TO** — chat GO_TO still has no destination (T8) while C40 requires `x_m`/`y_m`. T20 leaves the allow→tick seam ready and reports honest “sin destino”. SoT: [`engineer_note_t20_goto_chat_sim_destination_debt.md`](engineer_note_t20_goto_chat_sim_destination_debt.md).  
**Next cola:** T21 Skills runtime software.
