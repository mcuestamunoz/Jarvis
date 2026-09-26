# Implementation Report — Fase C altitude loop (`B1-fase-c-altitude-loop`)

**IC:** [`implementation_contract_fase_c_altitude_loop_b1.md`](implementation_contract_fase_c_altitude_loop_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-26
**Status:** ★ **ACCEPT CLOSED** @ tag **`v0.5.39`** (Engineer 2026-09-26) · Cursor review PASS WITH NOTES.

---

## 0. Read this first — honesty summary

This Buy adds a simulated altitude sensor and a z→collective controller
so `ToyQuad6DofPlant` (C36) can climb toward, or hold near, a documented
height — collective stops being only the RC stick or a fixed constant.

```text
sim altitude != live baro/ToF chip
z -> collective in RAM != altitude hold in air
plant outside step != MCU ISR != motors
```

**Exists:** a direct-altitude simulated HAL; a z→collective controller
that demonstrably climbs the 6-DoF plant and shrinks `|z-z_des|`.
**Impossible:** a real baro/ToF chip; altitude hold on real hardware;
`HOLD` executing in air. Nothing in this Buy is any of those.

---

## 1. Package layout vs IC §1

```text
src/jarvis/flight_software/flight_control/sim_altitude_hal.py    # NEW — AltitudeSample + SimulatedAltitudeHal
src/jarvis/flight_software/flight_control/altitude_controller.py   # NEW — AltitudeController
src/jarvis/flight_software/flight_control/__init__.py               # EXTENDED — new exports
src/jarvis/vehicle_profiles/smoke.py                                  # EXTENDED — run_altitude_loop_smoke
src/jarvis/vehicle_profiles/__init__.py                                # EXTENDED — new export
src/jarvis/flight_software/flight_control/loop.py                    # UNCHANGED
src/jarvis/flight_software/flight_control/plant.py                    # UNCHANGED

native/flight_control/include/jarvis/fc/sim_altitude_hal.hpp   # NEW
native/flight_control/src/sim_altitude_hal.cpp                   # NEW
native/flight_control/include/jarvis/fc/altitude_controller.hpp  # NEW
native/flight_control/src/altitude_controller.cpp                  # NEW
native/flight_control/tests/test_altitude_loop.cpp                # NEW — 5 Catch2 cases

tests/test_fase_c_altitude_loop_b1.py   # NEW — 8 tests
```

Deliberately **not** named `altitude.py`/`altitude.hpp` — this tree
already ships `attitude.py`/`attitude.hpp` (the C7 estimator), and
"altitude"/"attitude" differ by one letter. No file was added under
`capabilities/`; neither new module imports craft Continuity.

---

## 2. Types / API implemented vs IC §0 / §2

| Item | IC ref | Match |
|---|---|---|
| `AltitudeSample(t_s, altitude_m)` | §0.4 | ✅ named `AltitudeSample` (the IC's preferred name), direct altitude, not a baro pressure model |
| `SimulatedAltitudeHal.read_altitude(true_z_m, t_s)` | §0.5 | ✅ caller-supplied true z; HAL never owns/consults a plant; deterministic, no noise |
| `AltitudeController.compute(z_des_m, altitude, vz_mps) -> collective` | §0.6 | ✅ one law: `clip(hover_bias + kp*(z_des-z) - kd*vz, 0, 1)` |
| `FlightControlLoop.step`/`ControlLoop::step` unchanged, no plant call | §0.7 | ✅ altitude controller runs outside `step`, produces its `collective` argument |
| Setpoint: plain `z_des_m` float, not a typed wrapper | §0.8 | ✅ disclosed choice, §2.1 |
| Both Python + C++ | §0.9 | ✅ |

### 2.1 Disclosed design choices

**Setpoint type (deviates from "typed preferred"):** a plain `float
z_des_m` is used instead of a wrapper type like `AltitudeSetpoint` —
this codebase already has `AttitudeSetpoint` (C8); a class named
`AltitudeSetpoint` sitting next to it would be a standing one-letter-typo
readability hazard. `AltitudeController` and `AltitudeSample` already
satisfy the IC's own "typed preferred" intent.

**`vz_mps` source:** caller-supplied argument, not internally integrated
or finite-differenced — the shipped smoke passes
`ToyQuad6DofPlant.true_velocity_mps[2]` directly, since that truth
already exists on the plant.

**No `dt` parameter:** `compute(...)` is a pure, stateless function —
no internal time integration, so there is nothing for a `dt` to update.
IC T2 anticipated a `dt` argument to validate; this design has none, so
T2 validates every argument this design actually has instead
(`kp`/`kd`/`hover_bias`/`z_des_m`/`vz_mps`).

**`hover_bias` default (the significant deviation, verified empirically
before locking):** the IC's own §0 decision 6 suggests reusing
`hover_collective()` (`0.5`) as the default bias. Before writing formal
tests, I ran the actual closed loop with that default and found it
never converges — `ToyQuad6DofPlant`'s own default `thrust_gain=20.0`
means `collective=0.5` produces roughly 4x the thrust needed to counter
gravity, so the loop finds a new equilibrium several metres above
`z_des_m` instead of settling there (observed: `z_des_m=2.0` settles at
`z≈2.6` and climbing, never converging, at the IC's suggested default).
Switching the default to `mass_kg * 9.81 / (4 * thrust_gain)` (evaluated
at `ToyQuad6DofPlant`'s own default constants, `≈0.1226`) fixed this
completely — verified converging monotonically, no overshoot, to within
`0.07m` over 500 steps. This is disclosed in both language modules'
docstrings.

### 2.2 Non-goals (IC §0 decision 2) — confirmed absent

xy position loop (C39), executor HOLD/LAND (C40), Safety deepen, ICM
client, craft↔FS, Assistant, specific-force IMU changes, mag/RC changes
— confirmed by grep (§6) and by `test_t7_...` (craft/registry
isolation).

---

## 3. Verified — real builds, real test runs

Before formalizing any test, I compiled and ran a standalone C++
scratch program against the same closed loop the Python scratch used,
confirming both languages produce numerically identical output
(`final z=1.9330 vz=0.0460 err=0.0670`, `500` steps, `z_des_m=2.0`) —
the scratch file was deleted after verification, not committed.

```text
$ cmake --build build/flight_control -j
[  1%] Building CXX object CMakeFiles/jarvis_fc.dir/src/altitude_controller.cpp.o
...
[100%] Built target fc_unit_tests
$ ctest --output-on-failure
100% tests passed out of 93
```

```text
$ python -m pytest tests/test_fase_c_altitude_loop_b1.py -v
8 passed
$ python -m pytest -q
3714 passed, 9 skipped
```

Baseline before this Buy: `3706 passed, 9 skipped`. Delta: **+8 passed,
+0 skipped** — exactly the new test count, zero regressions.

---

## 4. Integration rules vs IC §3, and one incidentally-discovered pre-existing test bug

| Existing | This Buy |
|---|---|
| `ToyQuadAttitudePlant`/`ToyQuad6DofPlant` dynamics | Untouched — `git diff --stat` empty |
| `FlightControlLoop.step`/`ControlLoop::step` | No plant call, unchanged role |
| `attitude.py`/`.hpp`/`.cpp` (C37's own mag fusion) | Untouched — `git diff --stat` empty |
| `rc_setpoint.py`/`.hpp`/`.cpp` (C37's own RC yaw) | Untouched — `git diff --stat` empty |
| Safety/craft/registry | Untouched |

**Incidentally discovered and fixed (not caused by this Buy's own
code):** `tests/test_fase_c_cpp_unit_tests_b1.py`'s own C37 disclosed
exception for `attitude.cpp` (added in the C37 report) asserted a
specific `git diff` shape. Since C37 has since been ACCEPTed and tagged
(`v0.5.38`), that diff is now permanently empty from any future clean
checkout's perspective, and the test was failing on this Buy's own
first full-suite run — **not because this Buy touched `attitude.cpp`**
(it did not; `git diff --stat` on it is empty for this Buy), but because
the check itself could never pass again once its subject commit landed.
Fixed by rewriting the check against current source **content**
(presence of `mag_gain`/`std::optional<MagSample>`, absence of the exact
pre-C37 signatures) instead of a transient `git diff`, which holds true
regardless of commit status. This is the same class of fragility this
session has fixed before (false-positive/false-negative pre-existing
checks), just discovered here rather than introduced here.

---

## 5. Tests run

### 5.1 Python — new module

`tests/test_fase_c_altitude_loop_b1.py` — **8 tests**, covering IC §2's
T1-T5, T7, T8 (T6 is the C++ Catch2 cases below; T8's "suite+ctest
green" half is the process run in §3; T9 is this report):

| Test | Covers |
|---|---|
| `test_t1_simulated_altitude_hal_known_true_z_matches_finite` | T1 |
| `test_t2_invalid_gains_and_non_finite_inputs_raise` | T2 |
| `test_t3_controller_direction_and_clipping` | T3 |
| `test_t4_closed_loop_with_toy_quad_6dof_plant_climbs_and_error_shrinks` | T4 |
| `test_t5_loop_step_never_calls_plant_and_c11_c36_c37_smokes_still_green` | T5 |
| `test_t7_no_craft_continuity_library_board_edits_and_safety_default_reject_all` | T7 |
| `test_t8_pyproject_version_is_0_5_39` | T8 (version half) |
| `test_t8_full_suite_process_gate_placeholder` | T8 marker |

### 5.2 C++ — new Catch2 cases

`native/flight_control/tests/test_altitude_loop.cpp` — 5 new
`TEST_CASE`s, tag `[altitude][c38]`: T1 (`SimulatedAltitudeHal`), an
invalid-argument case, T2 equivalent (constructor/compute validation),
T3 (direction + clipping), and T4 (closed loop with `ToyQuad6DofPlant`).

```text
100% tests passed out of 93
```

Baseline before this Buy: 88 host tests. Delta: **+5**, exactly the new
`TEST_CASE` count.

---

## 6. Module-boundary / forbidden-symbol grep

```text
$ git diff --stat -- native/flight_control/include/jarvis/fc/loop.hpp native/flight_control/src/loop.cpp \
    src/jarvis/flight_software/flight_control/loop.py \
    native/flight_control/include/jarvis/fc/plant.hpp native/flight_control/src/plant.cpp \
    src/jarvis/flight_software/flight_control/plant.py \
    native/flight_control/include/jarvis/fc/attitude.hpp native/flight_control/src/attitude.cpp \
    src/jarvis/flight_software/flight_control/attitude.py \
    native/flight_control/include/jarvis/fc/rc_setpoint.hpp native/flight_control/src/rc_setpoint.cpp \
    src/jarvis/flight_software/flight_control/rc_setpoint.py \
    native/flight_control/include/jarvis/fc/mag.hpp native/flight_control/src/mag.cpp \
    src/jarvis/flight_software/flight_control/mag.py src/jarvis/flight_software/flight_control/sim_mag_hal.py \
    [... controller/esc/mixer ...]
(empty — every frozen module untouched)

$ git status --short -- ui/spatial-board library src/jarvis/core src/jarvis/adapters \
    src/jarvis/workspace src/jarvis/actions src/jarvis/schemas src/jarvis/knowledge
# only pre-existing, external, unrelated diffs (parallel craft-geometry
# track, present before this Buy, not touched by it)
```

---

## 7. Files changed

**New:**
- `src/jarvis/flight_software/flight_control/sim_altitude_hal.py`
- `src/jarvis/flight_software/flight_control/altitude_controller.py`
- `native/flight_control/include/jarvis/fc/sim_altitude_hal.hpp`
- `native/flight_control/src/sim_altitude_hal.cpp`
- `native/flight_control/include/jarvis/fc/altitude_controller.hpp`
- `native/flight_control/src/altitude_controller.cpp`
- `native/flight_control/tests/test_altitude_loop.cpp`
- `tests/test_fase_c_altitude_loop_b1.py`
- `.jes/artifacts/implementation_report_fase_c_altitude_loop_b1.md` (this file)

**Modified:**
- `src/jarvis/flight_software/flight_control/__init__.py` (new exports)
- `src/jarvis/vehicle_profiles/smoke.py` (`run_altitude_loop_smoke` appended)
- `src/jarvis/vehicle_profiles/__init__.py` (new export)
- `native/flight_control/CMakeLists.txt` (two new sources added to `jarvis_fc`; one new test file added to `fc_unit_tests`)
- `tests/test_fase_c_cpp_unit_tests_b1.py` (C37 disclosed exception check fixed to be commit-status-agnostic, §4)
- `pyproject.toml` (`0.5.38` → `0.5.39`)
- 44 pre-existing test files re-pinned from `0.5.38` to `0.5.39`
- `README.md`, `docs/ARCHITECTURE.md` (new §1c paragraph after C37), `docs/PLATFORM_CAPABILITY_VISION.md` §13, `docs/IMPLEMENTATION_TASKS.md`, `native/flight_control/README.md` (see §9)

---

## 8. Docs updated (honesty confirmed — not claiming CLOSED/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.39 includes (landed, awaiting Cursor review + Engineer ★ ACCEPT — no `v0.5.39` tag yet)" section; "Next" pointers retargeted.
- `docs/ARCHITECTURE.md` §1c — new C38 paragraph after the C37 block, banner updated.
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C38 block, honesty line verbatim.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner and the C38 table row both changed from "★ AUTHORIZED" to "LANDED (awaiting Cursor review + Engineer ★ ACCEPT, no tag yet)".
- `native/flight_control/README.md` — new paragraph after the C37 paragraph naming `sim_altitude_hal.*`/`altitude_controller.*` and the disclosed `hover_bias` deviation.

No file in this Buy claims `v0.5.39` is tagged, ACCEPT CLOSED, "baro
live," "altitude hold in flight," "we fly," "LAND executed," or that a
ToF chip exists. Confirmed via `git tag -l | sort -V | tail -5` at close
of this Buy: `v0.5.33`-`v0.5.35`, `v0.5.37`, `v0.5.38` — `v0.5.39` does
not exist yet.

---

## 9. Residual / next steps

- C39 (position loop, sim) is next per the IC's own handoff. Assistant/placement work stays PARKED until C43.
- The pre-existing MCU-toolchain environment issue (disclosed in C36's own report §6.1) remains unfixed, unrelated to this Buy.
- A caller driving a `ToyQuad6DofPlant` configured with non-default `mass_kg`/`thrust_gain` must compute and pass its own `hover_bias` — this controller does not import `plant.py`/`plant.hpp` or reach into any plant instance to compute it automatically, keeping it as plant-agnostic as `SimulatedMagHal`/`SimulatedAltitudeHal` already are. This is disclosed in both language modules, not silent.
- The `test_fase_c_cpp_unit_tests_b1.py` fix (§4) is a general lesson for this session's own established pattern: any future "disclosed exception" check that asserts a `git diff` shape will need the same content-based rewrite once its own subject IC is ACCEPTed and tagged.

---

## 10. Acceptance self-check vs IC §4 (Acceptance)

- T1-T9: ✅ T1-T5/T7/T8 in Python (8/8 passing), T1-T4 equivalents in C++ Catch2 (5/5 passing, exceeding "at least T1+T3+T4"), T8's suite/ctest half in §3, T9 in this report.
- HAL + controller Py+C++: ✅ both implemented, numerically cross-checked identical via scratch verification before formal tests.
- Plant smoke moves z: ✅ `run_altitude_loop_smoke`/Catch2 T4, error shrinks from `2.0` to `0.067` over 500 steps, no overshoot.
- `step` unchanged in role: ✅ re-verified via source inspection; `loop.py`/`.hpp`/`.cpp` `git diff --stat` empty.
- Version `0.5.39`: ✅ `pyproject.toml` + all 44 checkpoint tests re-pinned.

**PASS** against every criterion in IC §4. **FAIL conditions** (live
baro, xy position loop, executor, plant inside `step`, craft wiring,
"we fly") — none present, verified above.
