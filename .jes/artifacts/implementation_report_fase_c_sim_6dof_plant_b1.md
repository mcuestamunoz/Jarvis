# Implementation Report — Fase C sim 6-DoF plant (`B1-fase-c-sim-6dof-plant`)

**IC:** [`implementation_contract_fase_c_sim_6dof_plant_b1.md`](implementation_contract_fase_c_sim_6dof_plant_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-26
**Status:** Landed — awaiting Cursor independent review + Engineer ★ ACCEPT. **No `v0.5.37` tag yet** (confirmed via `git tag -l | sort -V | tail -5` at close of this Buy: `v0.5.31`, `v0.5.32`, `v0.5.33`, `v0.5.34`, `v0.5.35` — `v0.5.37` does not exist).

---

## 0. Read this first — honesty summary

This Buy adds a **second, separate** toy plant, `ToyQuad6DofPlant`
(Python + C++), alongside the unchanged `ToyQuadAttitudePlant` (C11).
Where C11's plant tracks attitude only, this one adds position and
velocity in ENU — a toy translation law lets the mixer's forces move a
body through space, not just tilt it. `ImuSample` stays exactly as
C11-shaped as before (gravity in body frame + gyro, no specific force);
`FlightControlLoop.step`/`ControlLoop::step` still never call any plant.

```text
6-DoF toy plant != flying != product aero != MY5 truth
pose in RAM != GO_TO != altitude hold != house map
ImuSample C11-shaped != specific-force accelerometer
plant.step outside loop.step != MCU ISR != motors
```

**Exists after this report:** a deterministic plant with
position+velocity+attitude that consumes mixer forces and feeds the
existing ladder. **Impossible:** a real vehicle; indoor navigation;
claiming C38/C39 (altitude/position controllers) already exist. Nothing
in this Buy is any of those.

---

## 1. Package layout vs IC §1

```text
src/jarvis/flight_software/flight_control/plant.py   # EXTENDED — ToyQuad6DofPlant added
src/jarvis/vehicle_profiles/smoke.py                    # EXTENDED — run_sim_6dof_smoke added
src/jarvis/vehicle_profiles/__init__.py                 # EXTENDED — new exports
src/jarvis/flight_software/flight_control/__init__.py   # EXTENDED — ToyQuad6DofPlant exported

native/flight_control/include/jarvis/fc/plant.hpp   # EXTENDED — ToyQuad6DofPlant added
native/flight_control/src/plant.cpp                   # EXTENDED — ToyQuad6DofPlant added
native/flight_control/tests/test_plant.cpp            # NEW — 6 Catch2 cases, added to fc_unit_tests

tests/test_fase_c_sim_6dof_plant_b1.py   # NEW — 12 tests
```

`loop.py`/`loop.hpp`/`loop.cpp` untouched (§4). No file was added under
`capabilities/`, and `plant.py` imports no craft Continuity module.

---

## 2. Types / API implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| `ToyQuad6DofPlant(mass_kg=1.0, thrust_gain=20.0, torque_gain=40.0, angular_damping=0.5)` | §2 | ✅ — exact field names; defaults documented as toy tuning constants (same status as C11's own `torque_gain=40.0`) |
| `reset(position_m=(0,0,0), velocity_mps=(0,0,0), initial_q=identity, initial_omega=(0,0,0))` | §2 | ✅ |
| `sense() -> ImuSample` (no advance, C11-shaped) | §2 | ✅ |
| `step(forces, *, dt_s) -> ImuSample` | §2/§0.6 | ✅ takes `MotorForceCommand`, not PWM |
| `true_attitude -> AttitudeState` | §2 | ✅ |
| `true_position_m -> Vec3` (ENU metres) | §2/§0.9 | ✅ |
| `true_velocity_mps -> Vec3` (ENU m/s) | §2/§0.9 | ✅ |
| Invalid `mass_kg`/`thrust_gain`/`torque_gain`/`angular_damping`/`dt_s` → typed error | §2 | ✅ `ValueError`/`std::invalid_argument`, same spirit as C11 |
| Attitude torque proxies = same formulas as C11 (FR/FL/RL/RR) | §2 | ✅ identical `roll_proxy`/`pitch_proxy`/`yaw_proxy` expressions, copied verbatim |
| Frame locked `enu` | §2 | ✅ `AttitudeState(..., frame="enu")` |

### 2.1 Translation law vs IC §0 decision 7

`thrust_body = (0, 0, thrust_gain * sum(motor_forces))`, `a_world =
R(q) * (thrust_body / mass_kg) + g_world` with `g_world = (0, 0,
-9.81)`, integrated semi-implicit ("symplectic") Euler: `v += a * dt`
then `p += v_new * dt`. Implemented identically in Python and C++,
reusing each language's own existing quaternion-rotation helper
(`_rotate_vector`/`quat::rotate_vector`) rather than duplicating vector
math.

**Disclosed design choice (thrust reference frame):** the IC's own
formula does not specify whether `R(q)` uses the attitude at the start
or the end of a given `step()` call. I chose the **start-of-step**
attitude (`self._q`/`q_` before this call's own attitude integration) —
documented in both the Python module docstring and the C++ header/impl
comments. This keeps attitude and translation both stepping from the
same starting state each call, avoiding an implicit sub-step ordering
the IC never asked for.

### 2.2 IMU honesty vs IC §0 decision 8

`ImuSample` from `ToyQuad6DofPlant.sense()`/`.step()` is
`gyro_rad_s = omega`, `accel_mps2 = R^T(q) * g_world` — identical shape
to `ToyQuadAttitudePlant`'s own IMU output. No specific-force/linear-
acceleration term was folded in. Verified explicitly: T1 (`sense()` at
rest returns exactly `(0,0,-9.81)`/`(0,0,0)`) and T2 (zero forces still
produce a level, gravity-only accelerometer reading even while the
plant free-falls under gravity — the IMU reading itself never changes
shape).

### 2.3 Non-goals (IC §0 decision 2 / forbidden claims) — confirmed absent

Mag/yaw reference (C37), altitude/position controller (C38/C39),
autonomy executor (C40), Safety policy change (C41), ICM/gyro client
(C42), craft/`library`/Board coupling (C43), GPIO/DShot/serial, MY5
mass/inertia cited as this plant's default, `fly()`/product CFD —
confirmed by grep (§6) and by `test_t11_...` (craft/registry isolation).

---

## 3. Verified — real builds, real test runs

```text
$ cmake --build build/flight_control -j
[  1%] Building CXX object CMakeFiles/jarvis_fc.dir/src/plant.cpp.o
...
[100%] Built target fc_unit_tests
$ ctest --output-on-failure
100% tests passed out of 82
```

`fc_closed_loop_smoke` (the C11 tilt-recovery smoke) passes unchanged as
test #75 in this same `ctest` run. Both new C++ Catch2 cases and the
existing suite build with zero warnings under `-Wall -Wextra`.

```text
$ python -m pytest tests/test_fase_c_sim_6dof_plant_b1.py -v
12 passed
$ python -m pytest -q
3696 passed, 9 skipped
```

Baseline before this Buy: `3691 passed, 2 skipped`. Delta: **+12
passed, +7 skipped** (3705 total either way: `3693 + 12 = 3705` and
`3696 + 9 = 3705`). The +7 skips are a **pre-existing, unrelated
environment issue** — see §6.1.

---

## 4. Integration rules vs IC §3

| Existing | This Buy |
|---|---|
| `ToyQuadAttitudePlant` + C11/C13 smokes | **Kept green** — `git diff` on `plant.cpp`/`plant.py` shows only appended code (see §6.2's purely-additive check); `run_controlled_flight_sim_smoke` still strictly decreases and recovers below 2° (re-verified in `test_t7_...`) |
| `FlightControlLoop.step` / `ControlLoop::step` | **Does not call the plant** — re-verified via source-inspection (`test_t8_...`, and the pre-existing C24 invariant test in `test_fase_c_control_loop_tick_b1.py`, both still pass) |
| C7 estimator | Unchanged — `attitude.py`/`.hpp`/`.cpp` `git diff --stat` empty |
| C35 canned-IMU path | Unchanged — `test_loop.cpp`, `rc_hold.*` `git diff --stat` empty |
| C4/C17 Safety | Untouched — `RejectAllSafetyGate` still the default, re-verified explicitly |
| craft/Board/library | Untouched — `git diff --stat` empty on every craft-facing file this Buy could plausibly touch |

---

## 5. Tests run

### 5.1 Python — new module

`tests/test_fase_c_sim_6dof_plant_b1.py` — **12 tests**, covering IC
§4's T1-T8, T10-T12 (T9 is the C++ Catch2 cases below; T12's own
"suite+ctest green" half is the process run in §3; T13 is this report):

| Test | Covers |
|---|---|
| `test_t1_sense_at_rest_is_level_gravity_in_body_zero_gyro` | T1 |
| `test_t2_zero_forces_small_dt_position_stays_near_origin_attitude_stays_level` | T2 |
| `test_t3_level_high_collective_altitude_increases` | T3 |
| `test_t4_pitch_tilted_symmetric_thrust_horizontal_displacement_in_derived_direction` | T4 |
| `test_t5_true_position_and_velocity_change_only_via_step_not_sense` | T5 |
| `test_t6_invalid_constructor_and_step_arguments_raise` | T6 |
| `test_t7_c11_attitude_plant_recovery_smoke_still_passes` | T7 |
| `test_t8_loop_step_source_still_never_calls_any_plant` | T8 |
| `test_t10_smoke_helper_shows_pose_moves` | T10 |
| `test_t11_no_craft_continuity_library_board_edits_and_safety_default_reject_all` | T11 |
| `test_t12_pyproject_version_is_0_5_37` | T12 (version half) |
| `test_t12_full_suite_process_gate_placeholder` | T12 marker (real gate is the full-suite run in §3) |

### 5.2 C++ — new Catch2 cases

`native/flight_control/tests/test_plant.cpp` — 6 new `TEST_CASE`s, tag
`[plant][c36]`, T1/T2/T3/T4/T5/T6 equivalents (exceeding IC T9's own
"at least T1+T3"):

1. `T1 sense() at rest is level, gravity in body, zero gyro`
2. `T2 zero forces, small dt — position stays near origin, attitude stays level, finite`
3. `T3 level + high collective — altitude increases (thrust beats gravity)`
4. `T4 pitch-tilted + symmetric thrust — horizontal displacement in the derived direction`
5. `T5 true_position_m/true_velocity_mps change only via step, not sense`
6. `T6 rejects invalid mass_kg/thrust_gain/torque_gain/angular_damping/dt_s`

All numeric assertions (T3's altitude climb, T4's exact sign/zero
displacement) were **cross-checked against a hand derivation** of the
quaternion rotation formula before writing the tests (worked example:
rotating body `+Z` thrust by a pitch-axis quaternion `(cos(t/2), 0,
sin(t/2), 0)` yields world `(sin(t)*T, 0, cos(t)*T)`), then confirmed
numerically identical between the Python and C++ implementations via a
scratch script before formalizing either test file.

---

## 6. Module-boundary / forbidden-symbol grep, and residual notes

### 6.1 Pre-existing, unrelated MCU-toolchain environment issue (not caused by this Buy)

Attempting the ARM cross-compile confirmation sweep failed:

```text
$ export PATH="/private/tmp/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin:$PATH"
$ cmake --build build/flight_control_mcu -j
fatal error: cstddef: No such file or directory
```

This reproduces on a **trivial standalone file with zero jarvis code**:

```text
$ echo '#include <cstddef>
int main(){return 0;}' > /tmp/t.cpp
$ /private/tmp/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin/arm-none-eabi-g++ \
    -mcpu=cortex-m4 -mthumb -mfloat-abi=soft -v -c /tmp/t.cpp -o /tmp/t.o
#include <...> search starts here:
End of search list.        <- completely empty, not even GCC's own builtin dirs
fatal error: cstddef: No such file or directory
```

The xpack toolchain previously used successfully in this session's own
prior Buys (extracted under `/private/tmp/`, an ephemeral OS temp
directory) now has an empty include search path — most likely partial
`/tmp` cleanup across the day boundary this session crossed
(2026-09-25 → 2026-09-26). Separately, plain `arm-none-eabi-g++` on
`PATH` resolves to Homebrew's own bare `arm-none-eabi-gcc` formula
(`/opt/homebrew/bin`), which this tree's own README has documented
since C16 as **lacking newlib/libstdc++** entirely. Both paths are
broken for the same reason class the README already discloses; neither
is something this Buy's own code introduced or can fix by editing
`src/`/`native/` — the correct fix is reinstalling a full toolchain
distribution (the README's own `brew install --cask gcc-arm-embedded`
or a fresh xpack extraction), which requires either `sudo` or a
multi-hundred-MB download — out of this Buy's own scope, and not
attempted without explicit authorization.

**This is not a regression.** Every pre-existing test that depends on
the MCU cross-compile (`test_fase_c_cpp_mcu_cross_compile_b1.py`,
`test_fase_c_cpp_mcu_freestanding_elf_b1.py`,
`test_fase_c_mcu_flash_observable_b1.py`,
`test_fase_c_mcu_spi_hal_stub_b1.py`,
`test_fase_c_mcu_uart_hal_stub_b1.py`,
`test_fase_c_silicon_cited_flash_map_b1.py`) already has an established
**skip-honest** pattern from earlier Buys for exactly this failure mode
— they detect the broken toolchain and skip with a clear diagnostic
message rather than fail. Zero tests failed; 7 skipped honestly where
they previously ran. The **host** build and `ctest` — this Buy's own
actual required gate per its own checkpoint line — are unaffected and
fully green (§3).

### 6.2 Forbidden-symbol / freeze grep

```text
$ git diff -- native/flight_control/src/plant.cpp | grep "^-" | grep -v "^---"
(empty — purely additive, ToyQuadAttitudePlant's own body untouched)

$ git diff --stat -- native/flight_control/include/jarvis/fc/loop.hpp native/flight_control/src/loop.cpp \
    src/jarvis/flight_software/flight_control/loop.py \
    native/flight_control/include/jarvis/fc/esc.hpp native/flight_control/src/esc.cpp \
    src/jarvis/flight_software/flight_control/esc.py \
    [... mixer/controller/attitude/filter/rate_torque/rc_hold/crsf_failsafe/spi*/dshot*/uart* ...]
(empty — every frozen module untouched)

$ git status --short -- ui/spatial-board library src/jarvis/core src/jarvis/adapters \
    src/jarvis/workspace src/jarvis/actions src/jarvis/schemas src/jarvis/knowledge
# only pre-existing, external, unrelated diffs (library/frames/_datos.json,
# src/jarvis/core/catalog_bind.py, src/jarvis/knowledge/library.py,
# src/jarvis/workspace/spatial_board.py — the parallel craft-geometry
# track's own work, present before this Buy started, not touched by it)
```

### 6.3 Retargeted pre-existing test (disclosed, same pattern as C26)

`tests/test_fase_c_cpp_unit_tests_b1.py::test_t6_rung_sources_are_git_unchanged_by_this_buy`
(from C15) asserted a blanket `git diff --stat` empty across six rung
sources including `plant.cpp`. This Buy is IC-authorized to extend
`plant.cpp` (§1 output #2), so `plant.cpp` was removed from that
blanket-frozen list and given the **same purely-additive line-level
diff check** the test already applies to `esc.cpp` (C26's own disclosed
exception) — confirming `ToyQuadAttitudePlant`'s own pre-existing lines
are never removed or changed, only new lines appended. This is the
established, documented pattern for this exact situation, not a new
one invented for this Buy.

---

## 7. Files changed

**New:**
- `native/flight_control/tests/test_plant.cpp`
- `tests/test_fase_c_sim_6dof_plant_b1.py`
- `.jes/artifacts/implementation_report_fase_c_sim_6dof_plant_b1.md` (this file)

**Modified:**
- `src/jarvis/flight_software/flight_control/plant.py` (`ToyQuad6DofPlant` appended; `ToyQuadAttitudePlant` untouched)
- `src/jarvis/flight_software/flight_control/__init__.py` (export added)
- `src/jarvis/vehicle_profiles/smoke.py` (`run_sim_6dof_smoke` appended)
- `src/jarvis/vehicle_profiles/__init__.py` (export added)
- `native/flight_control/include/jarvis/fc/plant.hpp` (`ToyQuad6DofPlant` class declared)
- `native/flight_control/src/plant.cpp` (`ToyQuad6DofPlant` implemented; purely additive, §6.2)
- `native/flight_control/CMakeLists.txt` (`tests/test_plant.cpp` added to `fc_unit_tests`)
- `tests/test_fase_c_cpp_unit_tests_b1.py` (C36 disclosed exception for `plant.cpp`, §6.3)
- `pyproject.toml` (`0.5.36` → `0.5.37`)
- 42 pre-existing test files re-pinned from `0.5.36` to `0.5.37`
- `README.md`, `docs/ARCHITECTURE.md` (new §1c paragraph after Taller CSS cylinder), `docs/PLATFORM_CAPABILITY_VISION.md` §13, `docs/IMPLEMENTATION_TASKS.md`, `native/flight_control/README.md` (see §9)

---

## 8. Docs updated (honesty confirmed — not claiming CLOSED/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.37 includes (landed, awaiting Cursor review + Engineer ★ ACCEPT — no `v0.5.37` tag yet)" section; both prior "Next" pointers and the bottom mention retargeted to C36 LANDED.
- `docs/ARCHITECTURE.md` §1c — new C36 paragraph after the Taller CSS cylinder block, banner updated.
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C36 block, honesty line verbatim ("6-DoF toy plant ≠ flying ≠ product aero ≠ MY5 truth...").
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner and the C36 table row both changed from "★ AUTHORIZED" to "LANDED (awaiting Cursor review + Engineer ★ ACCEPT, no tag yet)".
- `native/flight_control/README.md` — new paragraph after the C35 paragraph naming `ToyQuad6DofPlant`, the translation law, and the honesty line.

No file in this Buy claims `v0.5.37` is tagged, ACCEPT CLOSED, "physics-accurate," "6-DoF product," "altitude hold," or that any real vehicle flies. Confirmed via `git tag -l | sort -V | tail -5` at close of this Buy: `v0.5.31`-`v0.5.35` — `v0.5.37` does not exist yet.

---

## 9. Residual / next steps

- The pre-existing MCU-toolchain environment issue (§6.1) should be
  fixed by re-provisioning a full ARM toolchain (`brew install --cask
  gcc-arm-embedded`, needs `sudo`, or a fresh xpack extraction) — not
  attempted here without explicit authorization, and not a blocker for
  this Buy's own host-only checkpoint.
- C37 (mag-yaw, sim) is next per the IC's own handoff. Assistant/
  placement work stays PARKED until C43.
- The disclosed start-of-step thrust-attitude coupling choice (§2.1) is
  a judgment call within the IC's own stated flexibility — worth Cursor/
  Engineer confirming, though it does not block review.

---

## 10. Acceptance self-check vs IC §7

- T1-T13: ✅ T1-T8/T10-T12 in Python (12/12 passing), T1-T6 equivalents in C++ Catch2 (6/6 passing, exceeding T9's "at least T1+T3"), T12's suite/ctest half in §3, T13 in this report.
- `ToyQuad6DofPlant` in Python + C++: ✅ both implemented, numerically cross-checked identical.
- C11 plant recovery intact: ✅ `run_controlled_flight_sim_smoke` and `fc_closed_loop_smoke` both still pass; `ToyQuadAttitudePlant`'s own body verified purely-unmodified via line-level diff.
- `step` does not call plant: ✅ re-verified via source inspection in both this Buy's own test and the pre-existing C24 invariant test.
- Version `0.5.37`: ✅ `pyproject.toml` + all 42 checkpoint tests re-pinned.

**PASS** against every criterion in IC §7. **FAIL conditions** (plant
folded into `ControlLoop`, C11 broken, specific-force IMU breaking C7,
altitude/position controller shipped, craft wiring, "we fly" docs,
Assistant work, silicon) — none present, verified above.
