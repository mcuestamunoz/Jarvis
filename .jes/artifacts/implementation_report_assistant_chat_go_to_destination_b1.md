# Implementation Report — Chat GO_TO destination (`B1-assistant-chat-go-to-destination`, T32)

**Project:** Jarvis  
**Date:** 2026-10-03  
**Implementer:** Claude Code (Engineer authorization paste)  
**Contract:** [`implementation_contract_assistant_chat_go_to_destination_b1.md`](implementation_contract_assistant_chat_go_to_destination_b1.md)  
**Parents:** [DC ★ CLOSED](design_contract_assistant_chat_go_to_destination_b0.md) · [SD-GO_TO note](engineer_note_t20_goto_chat_sim_destination_debt.md) · T31 ★ ACCEPT CLOSED @ **`v0.6.40`** · T20 ★ @ `v0.6.29` · T25 Skill-first GO_TO ★ @ `v0.6.34`  
**Status:** Cursor **PASS WITH NOTES** — await Engineer ★ ACCEPT.  
**Package / tag:** `0.6.41` / pending **`v0.6.41`**.

---

## 1. What landed

| Area | Change |
|---|---|
| `src/jarvis/intelligence/assistant_task.py` | New `parse_go_to_destination(raw_text) -> tuple[float, float] \| None` — exact, finite-only match on `go to\|goto\|ir a\|ve a <x> <y>` after the same minimal normalize every classify function here already uses. `try_request_go_to_task`'s acceptance guard widened: `normalized not in VEHICLE_GO_TO_PHRASES and parse_go_to_destination(...) is None` (was bare-phrase-only). All seven sibling `try_request_*_task` functions that already refuse bare GO_TO phrases (ARM, DISARM, TAKEOFF, RETURN_HOME, FOLLOW, PATROL, CHARGE) now also refuse the destination-bearing pattern: `normalized in VEHICLE_GO_TO_PHRASES or parse_go_to_destination(...) is not None` |
| `src/jarvis/core/orchestrator.py` | New `_resolve_go_to_destination(intent) -> tuple[float, float] \| None` method: (1) `intent.metadata["go_to_x_m"]`/`["go_to_y_m"]` connect plug (cast from string, `math.isfinite` guarded) — the seam future GPS/world/voice providers fill; (2) else `parse_go_to_destination(intent.raw_text)`; (3) else `None`. `_handle_vehicle_go_to` now resolves a destination, builds `params={}` or `params={"x_m": str(x), "y_m": str(y)}` for `propose_command`, and after Safety `allow` calls `_sim_autonomy_tick_note(AutonomyVerb.GO_TO, x_m=…, y_m=…)` when a destination exists, else the unchanged no-arg call. `_sim_autonomy_tick_note` gained optional keyword-only `x_m`/`y_m` (default `None`) — HOLD/LAND callers pass neither, byte-identical to before; `SimAutonomyParams(x_m=x_m, y_m=y_m)` replaces the old always-empty `SimAutonomyParams()` |
| `tests/test_assistant_chat_go_to_destination_b1.py` | **new** T1–T5 |
| `tests/test_assistant_chat_sim_copper_b1.py` | T1c's docstring updated to point at the new suite; its own bare-phrase assertion is untouched and still passes byte-for-byte (resolver returns `None` for a bare phrase, same sin-destino path as before) |
| `pyproject.toml` | `0.6.41` |
| Docs | PRIORIDAD · PLATFORM · CONNECTIONS (no new C-xxx) |

**Not touched:** the SD-GO_TO debt note (`engineer_note_t20_goto_chat_sim_destination_debt.md`) — stays "Buy AUTHORIZED" per the IC's own explicit instruction; marking it CLOSED is reserved for Engineer ★ ACCEPT, not this impl commit. `flight.go_to` capability (`not_implemented`, never flipped), live ESC/copper, voice ingress, real GPS hardware, a second sim stack, `AutonomyVerb` enum, TAKEOFF/RETURN_HOME/FOLLOW/PATROL sim ticks (still outside the T20 tick set), `VEHICLE_GO_TO_PHRASES` itself (bare-phrase membership unchanged), Skill-first gating (`run_skill("skill.request_go_to")` still runs first, unchanged), tip-version pins (T17 guardrail re-verified green), ESC fence (T16, re-verified green).

---

## 2. Behavior

- Disarmed + any GO_TO-shaped line (bare or destination-bearing) → unchanged `disarmed`/`reject`, no tick, same as before.
- Armed + bare `go to` → `allow` + honest sin-destino note (`"Simulación no disponible sin destino (falta x_m/y_m;…)"` — N1 polish).
- Armed + `go to 1.0 2.0` / `goto -3.5 4` / `ir a 10 -2.25` / `ve a 0.5 0.5` → `allow` + a real sim tick note (`"Simulación (no vuelo real, sin ESC/motores): tick en t=…, colectivo=…."`), same shape HOLD/LAND already produce.
- Metadata connect plug: a manually constructed `Intent` with `metadata={"go_to_x_m": "5.5", "go_to_y_m": "-1.25"}` resolves to `(5.5, -1.25)` via `_resolve_go_to_destination` directly — the chat path itself never populates this today (`TerminalIntentAdapter.parse` always starts with empty metadata), so this is exercised as a direct unit test of the seam, per the IC's own suggestion. A non-finite metadata value (e.g. `"inf"`) is rejected, never silently used.
- A destination-bearing GO_TO line (`"go to 1.0 2.0"`) is refused by every later sibling classify function (TAKEOFF/RETURN_HOME/FOLLOW/PATROL/CHARGE, and defensively ARM/DISARM) — verified directly.
- `"ve a comprar pan"` and other payload/craft lines still never match (the regex requires exactly two trailing floats, anchored).
- HOLD, LAND still tick (no change); PATROL still doesn't tick; GO_TO Skill-first (`run_skill("skill.request_go_to")`) still gates first, verified via the spy pattern used throughout the Skill-first chain.

---

## 3. Tests executed

```text
pytest tests/test_assistant_chat_go_to_destination_b1.py \
  tests/test_assistant_chat_sim_copper_b1.py \
  tests/test_assistant_vehicle_go_to_task_b1.py \
  tests/test_assistant_vehicle_takeoff_task_b1.py \
  tests/test_assistant_vehicle_return_home_task_b1.py \
  tests/test_assistant_vehicle_follow_task_b1.py \
  tests/test_assistant_vehicle_patrol_task_b1.py \
  tests/test_assistant_ops_charge_task_b1.py \
  tests/test_assistant_vehicle_arm_ux_b1.py \
  tests/test_assistant_chat_skill_first_vehicle_go_to_b1.py -q
→ 72 passed

pytest tests/test_suite_no_tip_version_pins_b1.py tests/test_fase_c_esc_pwm_stub_rung_b1.py -q
→ 19 passed (T17 guardrail + T16 ESC fence both still green)

pytest tests/ -q
→ 3958 passed, 9 skipped, 0 failed
```

Diffed against this branch's pre-T32 tip (stash push/pop): baseline was `3953 passed, 9 skipped, 0 failed`. **Zero regressions** — the only delta is the 5 new T32 tests passing.

---

## 4. Remaining

None for this Buy. On Engineer ★ ACCEPT: mark the SD-GO_TO note Status → **CLOSED** and close its PRIORIDAD debt row (not done in this commit, per the IC). Next horizon per the DC/PRIORIDAD: phase C (voice/world, phased CLI migrate) — explicitly not immediate.
