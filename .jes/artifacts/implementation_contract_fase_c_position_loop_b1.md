# Implementation Contract — Fase C position loop (`B1-fase-c-position-loop`)

**Project:** Jarvis  
**Date:** 2026-09-26  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — ★ AUTHORIZED: **implement now**  
**Reviewer:** Cursor against this IC · Engineer spot-check (sim GPS ≠ live GPS · xy→tilt ≠ flying ≠ GO_TO on copper · plant outside `step`)

**Status:** ★ **ACCEPT CLOSED** @ tag **`v0.5.40`** (Engineer 2026-09-26) · Cursor review PASS WITH NOTES  
**Parents:**
- [C38 ★ ACCEPT](implementation_contract_fase_c_altitude_loop_b1.md) — sim altitude + z→collective @ **`v0.5.39`**  
- [C37 ★ ACCEPT](implementation_contract_fase_c_mag_yaw_rung_b1.md) — sim mag + RC yaw @ **`v0.5.38`**  
- [C36 ★ ACCEPT](implementation_contract_fase_c_sim_6dof_plant_b1.md) — `ToyQuad6DofPlant` pose ENU @ **`v0.5.37`**  
- [C24 ★ ACCEPT](implementation_contract_fase_c_control_loop_tick_b1.md) — `step(sample, setpoint, collective)` @ **`v0.5.22`**  
- [Month note](engineer_note_software_month_until_bench_2026_09_26.md) — C39 after C38  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — add a **simulated horizontal position sensor** (GPS/flow-shaped *port*) and an **xy → tilt** controller so the 6-DoF plant can chase a documented ENU point in sim.  
**Package:** bump **`0.5.39` → `0.5.40`**; git tag **`v0.5.40`** only after Engineer ACCEPT.

**Not** live GPS/flow chip · not house map · not AutonomyVerb `GO_TO` executor (C40) · not Safety deepen · not craft↔FS · not Assistant · not live baro · not folding plant into `step` · not claiming position hold in air · not rewriting C38 altitude law.

**Outputs (required):**
1. Python: position sample type + `SimulatedPositionHal` (preferred name) + position controller producing an **`AttitudeSetpoint`** (roll/pitch tilt; yaw held documented)  
2. C++ twin under `native/flight_control/`  
3. Thin smoke: `ToyQuad6DofPlant` + position loop (+ C38 altitude for z) → horizontal distance to `(x_des, y_des)` **strictly decreases** over N steps, chaining `pos.compute` → (`alt.compute` for collective) → `loop.step` → `plant.step`  
4. Tests: `tests/test_fase_c_position_loop_b1.py` + Catch2 case(s)  
5. Report + docs honesty: **sim GPS ≠ live GPS ≠ flying ≠ GO_TO on copper ≠ house map**  
6. `pyproject.toml` → **`0.5.40`** (+ re-pin `0.5.39` checkpoints)

**Checkpoint:** package **`0.5.40`** · suite green · host `ctest` green · C36/C37/C38/C11 smokes still green

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-position-loop`** — sim position sense + xy→tilt |
| 2 | One front | Do **not** fold AutonomyVerb executor (C40), Safety, ICM, craft↔FS, Assistant, silicon, altitude-law rewrite, mag/RC changes, specific-force IMU |
| 3 | What this Buy demonstrates | Horizontal motion stops being “only open-loop tilt / luck.” A simulated xy measurement drives roll/pitch so the toy plant moves toward an ENU point. **Human:** “ya hay un suelo de posición de juguete; el tip puede perseguir un metro al este, no solo quedarse en z.” |
| 4 | Sensor | Typed sample with at least `t_s` + **`x_m`** + **`y_m`** (ENU East/North). Prefer **direct position** from the sim (not NMEA, not WGS84, not optical-flow image theater) — document that this is a GPS/flow-shaped *port*. Name: **`PositionSample`** + **`SimulatedPositionHal`** |
| 5 | HAL contract | `read_position(true_x_m, true_y_m, t_s) -> PositionSample` (or equivalent) — **caller supplies true xy** (from `ToyQuad6DofPlant.true_position_m[0:2]`). HAL does **not** own a plant. Deterministic; noise off by default. Optional `z_m` on the sample is allowed but **not** required for the controller |
| 6 | Controller | **One** law only: xy error (+ optional velocity damping) → **small-angle roll/pitch** → `AttitudeSetpoint` quaternion (3-2-1 Euler, yaw held at **0** unless a documented alternative). Caps: finite `max_tilt_rad` (document; prefer ≤ `RC_MAX_TILT_RAD` / ~30° if that constant is reused). **Not** cascaded PID theater, not LQR, not velocity-loop-only without position. Signs: **document and prove** with a test that `x_des > x` (East) produces motion that **increases** `true_position_m[0]` under the closed loop |
| 7 | Integration with `step` | Position controller runs **outside** `FlightControlLoop.step` — produces the `AttitudeSetpoint` argument. Collective still from C38 `AltitudeController` (preferred in smoke) or a documented hover_bias constant — **do not** reinvent z inside this Buy. Prefer: `setpoint = pos.compute(...)` then `collective = alt.compute(...)` then `tick = loop.step(sample, setpoint, collective)` then `plant.step(tick.forces, dt)` |
| 8 | Setpoint | Typed **`PositionSetpoint(x_m, y_m)`** preferred (does not collide with `AttitudeSetpoint`). Plain `(x_des, y_des)` floats OK if documented. **Not** `AutonomyVerb.GO_TO` — that verb stays C4 surface / C40 executor |
| 9 | Languages | **Both** Python + C++ |
| 10 | Plants / alt / mag / RC | Dynamics of `ToyQuad*Plant` untouched except as test feed. C38 altitude modules / C37 mag / RC yaw untouched in behavior |
| 11 | Safety / craft / autonomy surface | Untouched — `propose_command(GO_TO)` still hits RejectAll; this Buy does **not** execute verbs |
| 12 | Version | **`0.5.39` → `0.5.40`**; tag on ACCEPT only |
| 13 | Forbidden claims | “GPS live” · “optical flow live” · “GO_TO executed” · “we fly” · “house map” · “position hold in air” |

**Product sentence:**

```text
Un sensor de posición horizontal de juguete y un lazo xy→tilt: la
planta 6-DoF puede acercarse a un punto ENU en RAM — sin GPS real,
sin mapa de casa y sin volar.
```

**Defaults locked by Cursor:**
- `PositionSample` + `SimulatedPositionHal` (caller-supplied true xy)  
- `PositionSetpoint(x_m, y_m)` + one PD-ish xy→roll/pitch controller outside `step`  
- Smoke chains C38 altitude + C39 position on `ToyQuad6DofPlant`; horizontal error shrinks  
- Yaw held at 0 in the attitude setpoint this Buy produces  
- Python + C++ · package **`0.5.40`**

---

## 1. Package layout (normative intent)

```text
src/jarvis/flight_software/flight_control/
  sim_position_hal.py / position_controller.py   # NEW — sample + HAL + controller (split OK)
  altitude_controller.py                         # UNCHANGED (reuse in smoke)
  loop.py / plant.py                             # UNCHANGED dynamics / role

native/flight_control/
  include/jarvis/fc/sim_position_hal.hpp …
  include/jarvis/fc/position_controller.hpp …
  src/…
  tests/test_position_loop.cpp                   # NEW

tests/test_fase_c_position_loop_b1.py            # NEW
```

Do **not** put this under `capabilities/` or `autonomy/` executor paths. Do **not** import Continuity. Naming: prefer `position_*` (not `gps_*` as the primary module name — avoids implying a live GNSS stack).

---

## 2. Tests (minimum)

| ID | Check |
|---|---|
| T1 | HAL at known true xy → `x_m`/`y_m` match (finite) |
| T2 | Invalid gains / non-finite setpoints / non-finite velocity inputs raise |
| T3 | Controller direction: documented East (or North) error → tilt command in the documented direction; tilt magnitude capped by `max_tilt_rad` |
| T4 | Closed loop with `ToyQuad6DofPlant`: start at `(0,0)`, `PositionSetpoint` with documented offset (e.g. `x_des>0`, `y_des=0`) → after N steps horizontal distance **strictly decreases** vs initial (or end distance < documented bound); z remains finite / smoke may assert altitude still near `z_des` if C38 is chained |
| T5 | `loop.step` still never calls plant; C36/C37/C38/C11 smokes still green |
| T6 | C++ Catch2: at least T1+T3+T4 equivalents |
| T7 | No craft/`library`/Board edits; Safety RejectAll intact; `AutonomyVerb.GO_TO` still `not_attempted` |
| T8 | `pyproject` **`0.5.40`**; suite + `ctest` green |
| T9 | Report: **sim GPS ≠ live GPS ≠ flying ≠ GO_TO on copper ≠ house map** |

---

## 3. Honesty / forbidden

```text
sim position ≠ live GPS/flow chip
xy→tilt in RAM ≠ position hold in air ≠ GO_TO executed
plant outside step ≠ MCU ISR ≠ motors
ENU point in RAM ≠ house map
```

---

## 4. Acceptance

**PASS when:** T1–T9 · HAL + controller Py+C++ · plant smoke shrinks horizontal error · `step` unchanged in role · version `0.5.40`.  
**FAIL if:** live GPS · AutonomyVerb executor · plant inside `step` · craft wiring · “we fly” · house map claim.

---

## 5. Handoff

```text
Engineer → ★ AUTHORIZED (this IC — Claude implements now)
Claude   → PositionSample + SimulatedPositionHal + xy→tilt (Py+C++) + tests + smoke + report + 0.5.40
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.40
Cola     → C40 autonomy executor (sim setpoints)
```

---

## 6. PRIORIDAD blurb (paste on landing)

```text
Fase C: ★ C39 position loop — sim position + xy→tilt.
Package 0.5.40. ≠ live GPS ≠ flying ≠ GO_TO on copper.
Cola after ACCEPT: C40 executor. Assistant PARKED. Silicon parked.
```

---

## 7. Engineer ★ checklist

- [x] ★ this IC (authorize Claude) — 2026-09-26 (IC passed to Claude = execute)  
- [ ] After landing: Cursor review · then ACCEPT + tag `v0.5.40`  
- [ ] Next = **C40**, not Assistant  
