# Implementation Contract — Fase C altitude loop (`B1-fase-c-altitude-loop`)

**Project:** Jarvis  
**Date:** 2026-09-26  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — ★ AUTHORIZED: **implement now**  
**Reviewer:** Cursor against this IC · Engineer spot-check (sim baro ≠ live baro · z-loop ≠ flying ≠ HOLD in air · plant outside `step`)

**Status:** ★ **AUTHORIZED** (Engineer 2026-09-26 — IC passed to Claude = execute directly)  
**Parents:**
- [C37 ★ ACCEPT](implementation_contract_fase_c_mag_yaw_rung_b1.md) — sim mag + RC yaw @ **`v0.5.38`**  
- [C36 ★ ACCEPT](implementation_contract_fase_c_sim_6dof_plant_b1.md) — `ToyQuad6DofPlant` pose ENU @ **`v0.5.37`**  
- [C24 ★ ACCEPT](implementation_contract_fase_c_control_loop_tick_b1.md) — `step(sample, setpoint, collective)` @ **`v0.5.22`**  
- [Month note](engineer_note_software_month_until_bench_2026_09_26.md) — C38 after C37  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — add a **simulated altitude sensor** (baro or ToF — one toy path) and a **z → collective** controller so the 6-DoF plant can hold / climb to a height in sim.  
**Package:** bump **`0.5.38` → `0.5.39`**; git tag **`v0.5.39`** only after Engineer ACCEPT.

**Not** live baro/ToF chip · not position xy loop (C39) · not executor HOLD/LAND (C40) · not Safety deepen · not craft↔FS · not Assistant · not specific-force IMU change · not folding plant into `step` · not claiming altitude hold in air.

**Outputs (required):**
1. Python: altitude sample type + `SimulatedBaroHal` (or `SimulatedAltitudeHal` / ToF twin — **pick one primary name**, document) + altitude controller producing **collective** ∈ `[0,1]`  
2. C++ twin under `native/flight_control/`  
3. Thin smoke: `ToyQuad6DofPlant` + altitude loop → `|z − z_des|` decreases from a documented offset (or climbs toward a higher setpoint) over N steps, chaining `loop.step` → `plant.step` with collective from the altitude controller  
4. Tests: `tests/test_fase_c_altitude_loop_b1.py` + Catch2 case(s)  
5. Report + docs honesty: **sim baro ≠ live baro ≠ flying ≠ HOLD in air**  
6. `pyproject.toml` → **`0.5.39`** (+ re-pin `0.5.38` checkpoints)

**Checkpoint:** package **`0.5.39`** · suite green · host `ctest` green · C36 plant + C37 mag + C11 recovery still green

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-altitude-loop`** — sim altitude sense + z→collective |
| 2 | One front | Do **not** fold xy position loop, GO_TO executor, Safety, ICM, craft↔FS, Assistant, silicon, mag changes, specific-force IMU |
| 3 | What this Buy demonstrates | Collective stops being “only the RC stick / a constant.” A simulated height measurement drives thrust so the toy plant moves in **z**. **Human:** “ya hay un suelo de altura de juguete; el gas puede perseguir un metro, no solo un número fijo.” |
| 4 | Sensor | Typed sample with at least `t_s` + **`altitude_m`** (ENU Up = +z). Prefer **direct altitude** from the sim (not a fake ISA pressure table) — document that this is a ToF/baro-shaped *port*, not a meteorology model. Name: **`AltitudeSample`** + **`SimulatedAltitudeHal`** (preferred) **or** `BaroSample`/`SimulatedBaroHal` if you keep “baro” in the name but still emit `altitude_m` |
| 5 | HAL contract | `read_altitude(true_z_m, t_s) -> AltitudeSample` (or equivalent) — **caller supplies true z** (from `ToyQuad6DofPlant.true_position_m[2]`). HAL does **not** own a plant. Deterministic; noise off by default |
| 6 | Controller | **One** law only: e.g. `collective = clip(hover_bias + kp*(z_des − z) − kd*vz, 0, 1)` with finite `kp>0`, `kd>=0`, documented `hover_bias` (may reuse `hover_collective()` ≈ 0.5 as default bias — document). Optional `vz` from plant `true_velocity_mps[2]` or finite difference — pick one, document. **Not** cascaded PID theater, not LQR |
| 7 | Integration with `step` | Altitude controller runs **outside** `FlightControlLoop.step` — produces the `collective` argument. Attitude setpoint still from RC/level as today. Prefer: smoke does `collective = alt.compute(...)` then `tick = loop.step(sample, setpoint, collective)` then `plant.step(tick.forces, dt)` |
| 8 | Setpoint | `AltitudeSetpoint(z_m)` or plain `z_des` float — typed preferred |
| 9 | Languages | **Both** Python + C++ |
| 10 | Plants / mag / RC | Dynamics of `ToyQuad*Plant` untouched except as test feed. Mag / RC yaw from C37 untouched |
| 11 | Safety / craft | Untouched |
| 12 | Version | **`0.5.38` → `0.5.39`**; tag on ACCEPT only |
| 13 | Forbidden claims | “baro live” · “altitude hold in flight” · “we fly” · “LAND executed” · ToF chip |

**Product sentence:**

```text
Un sensor de altura de juguete y un lazo z→collective: la planta 6-DoF
puede subir o quedarse cerca de un metro en RAM — sin baro real y sin
volar.
```

**Defaults locked by Cursor:**
- `AltitudeSample` + `SimulatedAltitudeHal` (caller-supplied true z → `altitude_m`)  
- One PD-ish z→collective controller outside `step`  
- Smoke with `ToyQuad6DofPlant` shows z error shrinks or climbs to setpoint  
- Python + C++ · package **`0.5.39`**

---

## 1. Package layout (normative intent)

```text
src/jarvis/flight_software/flight_control/
  altitude.py / sim_altitude_hal.py   # NEW — sample + HAL + controller (split OK)
  loop.py                             # UNCHANGED (no plant, no required alt inside step)
  plant.py                            # UNCHANGED dynamics

native/flight_control/
  include/jarvis/fc/altitude.hpp …    # twins
  src/…
  tests/test_altitude.cpp             # NEW or extend

tests/test_fase_c_altitude_loop_b1.py # NEW
```

Do **not** put this under `capabilities/`. Do **not** import Continuity.

---

## 2. Tests (minimum)

| ID | Check |
|---|---|
| T1 | HAL at known true z → `altitude_m` matches (finite) |
| T2 | Invalid gains / non-finite z_des / dt raise |
| T3 | Controller: z below setpoint → collective **>** hover_bias (or documented direction); z above → collective **<** hover_bias (clipped to `[0,1]`) |
| T4 | Closed loop with `ToyQuad6DofPlant`: start at z=0, z_des>0 documented → after N steps `true_position_m[2]` **increases** and `|z−z_des|` **strictly decreases** vs initial error (or end error < documented bound) |
| T5 | `loop.step` still never calls plant; C36/C37/C11 smokes still green |
| T6 | C++ Catch2: at least T1+T3+T4 equivalents |
| T7 | No craft/`library`/Board edits; Safety RejectAll intact |
| T8 | `pyproject` **`0.5.39`**; suite + `ctest` green |
| T9 | Report: **sim altitude ≠ live baro ≠ flying ≠ HOLD in air** |

---

## 3. Honesty / forbidden

```text
sim altitude ≠ live baro/ToF chip
z→collective in RAM ≠ altitude hold in air
plant outside step ≠ MCU ISR ≠ motors
```

---

## 4. Acceptance

**PASS when:** T1–T9 · HAL + controller Py+C++ · plant smoke moves z · `step` unchanged in role · version `0.5.39`.  
**FAIL if:** live baro · xy position loop · executor · plant inside `step` · craft wiring · “we fly.”

---

## 5. Handoff

```text
Engineer → ★ AUTHORIZED (this IC — Claude implements now)
Claude   → AltitudeSample + SimulatedAltitudeHal + z→collective (Py+C++) + tests + smoke + report + 0.5.39
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.39
Cola     → C39 position loop (sim)
```

---

## 6. PRIORIDAD blurb (paste on landing)

```text
Fase C: ★ C38 altitude loop — sim altitude + z→collective.
Package 0.5.39. ≠ live baro ≠ flying.
Cola after ACCEPT: C39 position. Assistant PARKED. Silicon parked.
```

---

## 7. Engineer ★ checklist

- [x] ★ this IC (authorize Claude) — 2026-09-26 (IC passed to Claude = execute)  
- [ ] After landing: Cursor review · then ACCEPT + tag `v0.5.39`  
- [ ] Next = **C39**, not Assistant  
