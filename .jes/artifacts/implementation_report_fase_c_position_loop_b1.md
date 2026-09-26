# Implementation Report — Fase C position loop (`B1-fase-c-position-loop`)

**IC:** [`implementation_contract_fase_c_position_loop_b1.md`](implementation_contract_fase_c_position_loop_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-26
**Status:** ★ **ACCEPT CLOSED** @ tag **`v0.5.40`** (Engineer 2026-09-26) · Cursor review PASS WITH NOTES.

---

## 0. Read this first — honesty summary

This Buy adds a simulated horizontal position sensor and an xy→tilt
controller so `ToyQuad6DofPlant` (C36) can chase a documented ENU point
— horizontal motion stops being only open-loop tilt or luck.

```text
sim position != live GPS/flow chip
xy->tilt in RAM != position hold in air != GO_TO executed
plant outside step != MCU ISR != motors
ENU point in RAM != a house map
```

**Exists:** a direct-ENU simulated HAL; an xy→tilt controller with
proven signs that demonstrably shrinks horizontal distance to a
setpoint on the 6-DoF plant. **Impossible:** a real GPS/flow chip;
position hold on real hardware; `GO_TO` executing on copper; a house
map. Nothing in this Buy is any of those.

---

## 1. Package layout vs IC §1

```text
src/jarvis/flight_software/flight_control/sim_position_hal.py    # NEW — PositionSample + SimulatedPositionHal
src/jarvis/flight_software/flight_control/position_controller.py   # NEW — PositionSetpoint + PositionController
src/jarvis/flight_software/flight_control/__init__.py               # EXTENDED — new exports
src/jarvis/vehicle_profiles/smoke.py                                  # EXTENDED — run_position_loop_smoke
src/jarvis/vehicle_profiles/__init__.py                                # EXTENDED — new export
src/jarvis/flight_software/flight_control/loop.py                    # UNCHANGED
src/jarvis/flight_software/flight_control/plant.py                    # UNCHANGED
src/jarvis/flight_software/flight_control/altitude_controller.py     # UNCHANGED (reused in smoke)
src/jarvis/flight_software/flight_control/sim_altitude_hal.py        # UNCHANGED (reused in smoke)

native/flight_control/include/jarvis/fc/sim_position_hal.hpp   # NEW
native/flight_control/src/sim_position_hal.cpp                   # NEW
native/flight_control/include/jarvis/fc/position_controller.hpp  # NEW
native/flight_control/src/position_controller.cpp                  # NEW
native/flight_control/tests/test_position_loop.cpp                # NEW — 8 Catch2 cases

tests/test_fase_c_position_loop_b1.py   # NEW — 9 tests
```

Not placed under `capabilities/` or any `autonomy/` executor path;
neither new module imports Continuity. Named `position_*`, not
`gps_*`, per IC §1's naming preference.

---

## 2. Types / API implemented vs IC §0 / §2

| Item | IC ref | Match |
|---|---|---|
| `PositionSample(t_s, x_m, y_m, z_m=None)` | §0.4 | ✅ named `PositionSample` (the IC's preferred name), direct ENU, not NMEA/WGS84/flow theater |
| `SimulatedPositionHal.read_position(true_x_m, true_y_m, t_s)` | §0.5 | ✅ caller-supplied true xy; HAL never owns/consults a plant; deterministic, no noise; optional `z_m` not required by controller |
| `PositionController.compute(setpoint, position, vx_mps, vy_mps, t_s) -> AttitudeSetpoint` | §0.6 | ✅ one law: xy error + velocity damping → small-angle roll/pitch → quaternion, yaw held at 0; capped by `max_tilt_rad` |
| `FlightControlLoop.step`/`ControlLoop::step` unchanged, no plant call | §0.7 | ✅ position controller runs outside `step`, produces its `setpoint` argument; collective still from C38's `AltitudeController`, unchanged |
| `PositionSetpoint(x_m, y_m)` typed | §0.8 | ✅ typed, no collision risk (unlike C38's disclosed plain-float choice) — see §2.1 |
| Both Python + C++ | §0.9 | ✅ |

### 2.1 Disclosed design choices

**Setpoint type (follows "typed preferred" without reservation, unlike
C38):** `PositionSetpoint(x_m, y_m)` is used directly, typed. C38 chose
a plain `z_des_m` float instead of a wrapper type specifically because
`AltitudeSetpoint` would sit one letter away from the existing
`AttitudeSetpoint` (C8) — a standing typo hazard. `PositionSetpoint` has
no such near-homograph in this codebase, so the IC's own "typed
preferred" default is followed here without deviation.

**No naming-collision risk (contrast with C38):** "position"/"altitude"/
"attitude" are all visually distinct — `position_controller.py`,
`sim_position_hal.py`, `PositionController`, `PositionSample`,
`SimulatedPositionHal` are named directly, no `gps_*` prefix (per IC
§1, to avoid implying a live GNSS stack).

**Signs, derived and empirically verified before any formal test:**
rotating the body `+Z` thrust vector by a positive-pitch quaternion
`(cos(θ/2), 0, sin(θ/2), 0)` (rotation about `Y`) yields world
`(sin(θ)·T, 0, cos(θ)·T)` — positive pitch → **positive world X**
(East). Rotating by a positive-roll quaternion `(cos(φ/2), sin(φ/2), 0,
0)` (rotation about `X`) yields world `(0, -sin(φ)·T, cos(φ)·T)` —
positive roll → **negative world Y** (South). Consequently:
`pitch_raw = kp*(x_des-x) - kd*vx` (no sign flip) and `roll_raw =
-(kp*(y_des-y) - kd*vy)` (sign-flipped). Verified with two scratch
closed-loop runs (deleted after verification, not committed) before
writing any formal test: an East-only setpoint `(5.0, 0.0)` converges
with zero `y` drift; a North-only setpoint `(0.0, 3.0)` converges with
zero `x` drift.

**Gains:** `kp=0.15, kd=0.3` (Python and C++ defaults, matching), chosen
empirically via the same scratch verification — monotonic convergence
from initial distance `5.0` to `0.005` at step 800, small subsequent
oscillation to `0.116` at step 900 (well within the IC's own "strictly
decreases vs initial" requirement). `max_tilt_rad` defaults to
`RC_MAX_TILT_RAD`/`kRcMaxTiltRad` (pi/6, 30 degrees, C25's own
constant), reused rather than duplicated as a numeric literal in
Python; duplicated as the same numeric literal in the C++ header
default (to avoid an unwanted `rc_setpoint.hpp` include — see §2.2).

**`vx_mps`/`vy_mps` source (same pattern as C38's own `vz_mps`):**
caller-supplied arguments, not internally integrated or
finite-differenced — the shipped smoke passes
`ToyQuad6DofPlant.true_velocity_mps[0:2]` directly.

**Yaw held at 0:** the `AttitudeSetpoint` this controller produces
always has yaw `0` — no heading-following behavior is invented, and
RC yaw (C37) is untouched.

### 2.2 Per-module-private-helper convention followed

`_roll_pitch_yaw_to_quat`/`roll_pitch_yaw_to_quat` (Euler-composition
helper) is a private copy in both `position_controller.py` and
`position_controller.cpp` (C++: anonymous namespace), matching this
project's established convention (`rc_setpoint.py`/`.cpp` each keep
their own copy too) rather than sharing via `quat_math.hpp` — that
header is reserved for GENERIC quaternion primitives only, not
Euler-composition-order-specific functions. `position_controller.hpp`
duplicates the `RC_MAX_TILT_RAD` numeric literal directly in its
default-argument expression rather than including `rc_setpoint.hpp`
(which would pull in unrelated RC-channel-mapping symbols this module
has no need of).

### 2.3 Non-goals (IC §0 decision 2) — confirmed absent

`AutonomyVerb.GO_TO` executor (C40), Safety deepen, ICM client,
craft↔FS, Assistant, silicon, altitude-law rewrite, mag/RC changes,
specific-force IMU — confirmed by grep (§6) and by `test_t7_...`
(craft/registry isolation + `GO_TO` still `not_attempted`).

---

## 3. Verified — real builds, real test runs

Before formalizing any test, `run_position_loop_smoke()` was run
standalone confirming the closed loop converges as documented:

```text
$ python3 -c "..."
start (0.0, 0.0, 0.0) end (5.210778111372186, 0.0, 1.3825834863674868)
dist start 5.0 dist end 0.2107781113721856
```

```text
$ cmake --build build/flight_control -j4
[ 89%] Building CXX object CMakeFiles/fc_unit_tests.dir/tests/test_position_loop.cpp.o
[100%] Built target fc_unit_tests
$ ctest --output-on-failure
100% tests passed out of 101
```

```text
$ python -m pytest tests/test_fase_c_position_loop_b1.py -v
9 passed
$ python -m pytest -q
3723 passed, 9 skipped
```

Baseline before this Buy: `3714 passed, 9 skipped` (Python), `93/93`
(host `ctest`). Delta: **+9 passed** (Python), **+8** (`ctest`) — exactly
the new test counts, zero regressions.

---

## 4. Integration rules vs IC §3

| Existing | This Buy |
|---|---|
| `ToyQuadAttitudePlant`/`ToyQuad6DofPlant` dynamics | Untouched — `git diff --stat` empty |
| `FlightControlLoop.step`/`ControlLoop::step` | No plant call, unchanged role |
| `attitude.py`/`.hpp`/`.cpp` (C37's mag fusion) | Untouched — `git diff --stat` empty |
| `rc_setpoint.py`/`.hpp`/`.cpp` (C37's RC yaw) | Untouched — `git diff --stat` empty |
| `altitude_controller.py`/`.hpp`/`.cpp`, `sim_altitude_hal.py`/`.hpp`/`.cpp` (C38) | Untouched — `git diff --stat` empty; reused as-is in the smoke |
| `mag.py`/`sim_mag_hal.py`/`.hpp`/`.cpp` (C37) | Untouched — `git diff --stat` empty |
| esc/mixer/filter/rate_torque/rc_hold/crsf_failsafe/spi/spi_probe/dshot/uart | Untouched — `git diff --stat` empty |
| Safety/craft/registry | Untouched |

No pre-existing test required a disclosed retarget in this Buy (unlike
C37/C38, which each had one) — this Buy is a pure addition with no
behavior change to any frozen module.

---

## 5. Tests run

### 5.1 Python — new module

`tests/test_fase_c_position_loop_b1.py` — **9 tests**, covering IC §2's
T1-T5, T7, T8 (T6 is the C++ Catch2 cases below; T8's "suite+ctest
green" half is the process run in §3; T9 is this report):

| Test | Covers |
|---|---|
| `test_t1_simulated_position_hal_known_true_xy_matches_finite` | T1 |
| `test_t1_optional_z_m_round_trips_when_provided` | T1 |
| `test_t2_invalid_gains_and_non_finite_inputs_raise` | T2 |
| `test_t3_controller_direction_east_and_north_and_clipping` | T3 |
| `test_t4_closed_loop_with_toy_quad_6dof_plant_horizontal_distance_shrinks` | T4 |
| `test_t5_loop_step_never_calls_plant_and_c11_c36_c37_c38_smokes_still_green` | T5 |
| `test_t7_no_craft_continuity_library_board_edits_and_safety_default_reject_all` | T7 |
| `test_t8_pyproject_version_is_0_5_40` | T8 (version half) |
| `test_t8_full_suite_process_gate_placeholder` | T8 marker |

### 5.2 C++ — new Catch2 cases

`native/flight_control/tests/test_position_loop.cpp` — 8 new
`TEST_CASE`s, tag `[position][c39]`: T1 (`SimulatedPositionHal` known
xy), optional `z_m` round-trip, T2 (HAL non-finite rejection), T2
(controller invalid gains/non-finite velocity), T3 (East → positive
pitch), T3 (North → negative roll), T3 (yaw held at 0 + tilt cap), and
T4 (closed loop with `ToyQuad6DofPlant`, horizontal distance strictly
decreases).

```text
100% tests passed out of 101
```

Baseline before this Buy: 93 host tests. Delta: **+8**, exactly the new
`TEST_CASE` count.

---

## 6. Module-boundary / forbidden-symbol grep

```text
$ git diff --stat -- native/flight_control/include/jarvis/fc/loop.hpp native/flight_control/src/loop.cpp \
    src/jarvis/flight_software/flight_control/loop.py \
    native/flight_control/include/jarvis/fc/plant.hpp native/flight_control/src/plant.cpp \
    src/jarvis/flight_software/flight_control/plant.py \
    native/flight_control/include/jarvis/fc/controller.hpp native/flight_control/src/controller.cpp \
    src/jarvis/flight_software/flight_control/controller.py \
    native/flight_control/include/jarvis/fc/attitude.hpp native/flight_control/src/attitude.cpp \
    src/jarvis/flight_software/flight_control/attitude.py \
    native/flight_control/include/jarvis/fc/rc_setpoint.hpp native/flight_control/src/rc_setpoint.cpp \
    src/jarvis/flight_software/flight_control/rc_setpoint.py \
    native/flight_control/include/jarvis/fc/mag.hpp native/flight_control/src/mag.cpp \
    src/jarvis/flight_software/flight_control/mag.py src/jarvis/flight_software/flight_control/sim_mag_hal.py \
    native/flight_control/include/jarvis/fc/altitude_controller.hpp native/flight_control/src/altitude_controller.cpp \
    native/flight_control/include/jarvis/fc/sim_altitude_hal.hpp native/flight_control/src/sim_altitude_hal.cpp \
    src/jarvis/flight_software/flight_control/altitude_controller.py \
    src/jarvis/flight_software/flight_control/sim_altitude_hal.py \
    [... esc/mixer/filter/rate_torque/rc_hold/crsf_failsafe/spi/spi_probe/dshot/uart ...]
native/flight_control/CMakeLists.txt | 3 +++
1 file changed, 3 insertions(+)
(only the CMakeLists.txt wiring for the two new source files + new
test file — every named module byte-unchanged)

$ git status --short -- ui/spatial-board library src/jarvis/core src/jarvis/adapters \
    src/jarvis/workspace src/jarvis/actions src/jarvis/schemas src/jarvis/knowledge
# only pre-existing, external, unrelated diffs (parallel craft-geometry
# track, present before this Buy, not touched by it)
```

---

## 7. Files changed

**New:**
- `src/jarvis/flight_software/flight_control/sim_position_hal.py`
- `src/jarvis/flight_software/flight_control/position_controller.py`
- `native/flight_control/include/jarvis/fc/sim_position_hal.hpp`
- `native/flight_control/src/sim_position_hal.cpp`
- `native/flight_control/include/jarvis/fc/position_controller.hpp`
- `native/flight_control/src/position_controller.cpp`
- `native/flight_control/tests/test_position_loop.cpp`
- `tests/test_fase_c_position_loop_b1.py`
- `.jes/artifacts/implementation_report_fase_c_position_loop_b1.md` (this file)

**Modified:**
- `src/jarvis/flight_software/flight_control/__init__.py` (new exports)
- `src/jarvis/vehicle_profiles/smoke.py` (`run_position_loop_smoke` appended)
- `src/jarvis/vehicle_profiles/__init__.py` (new export)
- `native/flight_control/CMakeLists.txt` (two new sources added to `jarvis_fc`; one new test file added to `fc_unit_tests`)
- `pyproject.toml` (`0.5.39` → `0.5.40`)
- 44 pre-existing test files re-pinned from `0.5.39` to `0.5.40`
- `README.md`, `docs/ARCHITECTURE.md` (new §1c paragraph after C38), `docs/PLATFORM_CAPABILITY_VISION.md` §13, `docs/IMPLEMENTATION_TASKS.md`, `native/flight_control/README.md` (see §8)

---

## 8. Docs updated (honesty confirmed — not claiming ACCEPT/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.40 includes (LANDED — awaiting Cursor review + Engineer ★ ACCEPT, no tag yet)" section; "Next" pointers retargeted.
- `docs/ARCHITECTURE.md` §1c — new C39 paragraph after the C38 block, banner updated.
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C39 block, honesty line verbatim.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner and the C39 table row both changed to "LANDED (awaiting Cursor review + Engineer ★ ACCEPT, no tag yet)".
- `native/flight_control/README.md` — new paragraph after the C38 paragraph naming `sim_position_hal.*`/`position_controller.*` and the disclosed sign derivation.

No file in this Buy claims `v0.5.40` is tagged, ACCEPT CLOSED, "GPS
live," "optical flow live," "GO_TO executed," "we fly," "position hold
in air," or "house map." Confirmed via `git tag -l | sort -V | tail -6`
at close of this Buy: `v0.5.33`, `v0.5.34`, `v0.5.35`, `v0.5.37`,
`v0.5.38`, `v0.5.39` — `v0.5.40` does not exist yet.

---

## 9. Residual / next steps

- C40 (autonomy executor, sim setpoints) is next per the IC's own handoff, after Cursor review + Engineer ★ ACCEPT + tag `v0.5.40`. Assistant/placement work stays PARKED until C43.
- The pre-existing MCU-toolchain environment issue (disclosed in C36's own report) remains unfixed, unrelated to this Buy.
- A caller driving a `ToyQuad6DofPlant` configured with non-default gains would need its own tuned `kp`/`kd`/`max_tilt_rad` for `PositionController` — this controller does not import `plant.py`/`plant.hpp` or reach into any plant instance, keeping it as plant-agnostic as `SimulatedAltitudeHal`/`SimulatedMagHal` already are. Disclosed, not silent.
- A caller wanting to combine position hold with a non-zero commanded yaw would need a separate, explicitly-scoped Buy — this controller always emits yaw `0`.

---

## 10. Acceptance self-check vs IC §4 (Acceptance)

- T1-T9: ✅ T1-T5/T7/T8 in Python (9/9 passing), T1-T4 equivalents in C++ Catch2 (8/8 passing, exceeding "at least T1+T3+T4"), T8's suite/ctest half in §3, T9 in this report.
- HAL + controller Py+C++: ✅ both implemented, sign-consistent by construction (both derived from the same hand-derivation, both tested independently).
- Plant smoke shrinks horizontal error: ✅ `run_position_loop_smoke`/Catch2 T4, distance shrinks from `5.0` to `<0.25` over 1000 steps (10s sim time), no cross-axis coupling.
- `step` unchanged in role: ✅ re-verified via source inspection; `loop.py`/`.hpp`/`.cpp` `git diff --stat` empty.
- Version `0.5.40`: ✅ `pyproject.toml` + all 44 checkpoint tests re-pinned.

**PASS** against every criterion in IC §4. **FAIL conditions** (live
GPS, `AutonomyVerb` executor, plant inside `step`, craft wiring, "we
fly," house map claim) — none present, verified above.
