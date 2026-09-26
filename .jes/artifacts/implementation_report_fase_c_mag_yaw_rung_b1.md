# Implementation Report — Fase C mag-yaw rung (`B1-fase-c-mag-yaw-rung`)

**IC:** [`implementation_contract_fase_c_mag_yaw_rung_b1.md`](implementation_contract_fase_c_mag_yaw_rung_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-26
**Status:** Landed — awaiting Cursor independent review + Engineer ★ ACCEPT. **No `v0.5.38` tag yet** (confirmed via `git tag -l | sort -V | tail -5` at close of this Buy: `v0.5.32`, `v0.5.33`, `v0.5.34`, `v0.5.35`, `v0.5.37` — `v0.5.38` does not exist).

---

## 0. Read this first — honesty summary

This Buy adds a simulated magnetometer and fuses it into `ComplementaryAttitudeEstimator`
so estimated yaw finally has an absolute reference, then unlocks the RC
yaw stick now that heading is honest.

```text
sim mag != live mag chip != ICM SPI mag
yaw reference in RAM != compass flight
RC yaw unlock != motors != flying
```

**Exists:** a deterministic simulated magnetometer; an optional yaw
correction that pulls estimated heading toward a documented world-north
reference; a yaw stick that honestly sets a heading in the setpoint.
**Impossible:** a real compass chip; heading-hold on hardware; GPS
heading. Nothing in this Buy is any of those.

---

## 1. Package layout vs IC §1

```text
src/jarvis/flight_software/flight_control/mag.py          # NEW — MagSample
src/jarvis/flight_software/flight_control/sim_mag_hal.py   # NEW — SimulatedMagHal
src/jarvis/flight_software/flight_control/attitude.py      # EXTENDED — optional mag yaw correction
src/jarvis/flight_software/flight_control/rc_setpoint.py   # EXTENDED — RC_CH_YAW unlocked
src/jarvis/flight_software/flight_control/__init__.py      # EXTENDED — new exports
src/jarvis/flight_software/flight_control/loop.py          # UNCHANGED

native/flight_control/include/jarvis/fc/mag.hpp   # NEW
native/flight_control/src/mag.cpp                   # NEW
native/flight_control/include/jarvis/fc/attitude.hpp   # EXTENDED
native/flight_control/src/attitude.cpp                   # EXTENDED
native/flight_control/include/jarvis/fc/rc_setpoint.hpp   # EXTENDED
native/flight_control/src/rc_setpoint.cpp                   # EXTENDED
native/flight_control/tests/test_mag.cpp             # NEW — 6 Catch2 cases
native/flight_control/tests/test_rc_setpoint.cpp       # RETARGETED — C37 disclosed exception

tests/test_fase_c_mag_yaw_rung_b1.py   # NEW — 10 tests
```

`MagSample` was kept in a new `mag.py` file rather than added to
`types.py`, since that module's own docstring locks its scope to "the
only data type in the first `flight_control` rung" (C3) — a new sensing
type is a separate rung concern, not an extension of C3's own boundary.
No file was added under `capabilities/`; `attitude.py`/`rc_setpoint.py`
import no craft Continuity module.

---

## 2. Types / API implemented vs IC §0 / §2

| Item | IC ref | Match |
|---|---|---|
| `MagSample(t_s, mag_body_uT)` | §0.4 | ✅ toy µT numbers, documented, no datasheet claim |
| `SimulatedMagHal(world_field_enu=(0,1,0))` | §0.5 | ✅ deterministic, no noise by default, world field horizontal-only (documented simplification) |
| `read_mag(true_q_body_to_world, t_s)` | §0.5 | ✅ caller-supplied true attitude — HAL never owns/consults a plant |
| `ComplementaryAttitudeEstimator.update(sample, mag=None)` | §0.6 | ✅ one estimator, not a second AHRS; `mag=None` byte-identical to pre-C37 |
| `RC_CH_YAW` = index 3 | §0.7 | ✅ |
| Yaw scale: separate `RC_MAX_YAW_RAD` (pi, 180°) | §0.7 | ✅ documented choice over reusing the 30° tilt limit |
| `FlightControlLoop.step`/`ControlLoop::step` unchanged, no plant call | §0.8 | ✅ mag fusion happens outside `step`, caller-driven (the "prefer caller fuses outside step" option) |
| Both Python + C++ | §0.9 | ✅ |

### 2.1 Mag yaw correction — derivation disclosed

The tilt-corrected estimate (`q_new`, after the existing accel branch)
rotates the measured body mag vector into world frame, projects onto
the horizontal plane (drops Up — only the horizontal component carries
a heading reference), and computes `error = cross(measured_horizontal,
world_north_reference)`. Because a **world-frame** correction must be
composed on the **left** of `q_new` (not the right, unlike the accel
branch's body-frame correction) — `q_corrected = R * q_new` — this is
the reverse composition order from the existing accel-tilt correction,
explicitly documented inline (both languages) to avoid silent confusion
between the two.

**Verified before writing formal tests** (scratch check, both Python
and C++, numerically identical): a 30° initial yaw offset converges to
under 0.3° over 30 updates at `gain=0.2, mag_gain=0.15`; the formal
tests use a looser, more conservative `< 5°` bound.

### 2.2 RC yaw quaternion — derivation disclosed

The existing `(cp*cr, cp*sr, sp*cr, -sp*sr)` roll/pitch formula is the
`yaw=0` special case of the general body 3-2-1 (`q = q_yaw * q_pitch *
q_roll`) composition — derived by hand, confirmed algebraically to
reduce to the exact pre-C37 formula at `yaw=0` (`cy=1, sy=0` zeroes
every `sy`-weighted term), then verified numerically identical in both
languages before formalizing tests.

### 2.3 Non-goals (IC §0 decision 2) — confirmed absent

Altitude/position loops (C38/C39), autonomy executor (C40), Safety
deepen (C41), ICM/gyro client (C42), craft↔FS (C43), Assistant, GPIO,
live mag chip, ICM/SPI mag, a second AHRS brand — confirmed by grep
(§6) and by `test_t9_...` (craft/registry isolation).

---

## 3. Verified — real builds, real test runs

```text
$ cmake --build build/flight_control -j
[  1%] Building CXX object CMakeFiles/jarvis_fc.dir/src/mag.cpp.o
...
[100%] Built target fc_unit_tests
$ ctest --output-on-failure
100% tests passed out of 88
```

`fc_closed_loop_smoke` (C11 tilt-recovery smoke) passes unchanged.

```text
$ python -m pytest tests/test_fase_c_mag_yaw_rung_b1.py -v
10 passed
$ python -m pytest -q
3706 passed, 9 skipped
```

Baseline before this Buy: `3696 passed, 9 skipped`. Delta: **+10
passed, +0 skipped** — exactly the new test count, zero regressions,
including zero change to the pre-existing +7 skip count from the
unrelated MCU-toolchain environment issue disclosed in C36's own report
(still present, still not this Buy's concern — not re-attempted here).

---

## 4. Integration rules vs IC §3 — including two disclosed pre-existing test retargets

| Existing | This Buy |
|---|---|
| `ComplementaryAttitudeEstimator` without mag | **Byte-identical behavior** — all 16 pre-existing C7 tests pass unchanged; re-verified explicitly in this Buy's own T3 |
| `ToyQuadAttitudePlant`/`ToyQuad6DofPlant` dynamics | Untouched — `git diff --stat` empty on `plant.py`/`plant.hpp`/`plant.cpp` |
| `FlightControlLoop.step`/`ControlLoop::step` | No plant call, unchanged role — re-verified via source inspection |
| C35 canned-IMU path | Unchanged — `test_loop.cpp`, `rc_hold.*` untouched |
| Safety/craft/registry | Untouched |

**Disclosed exception 1 (Python):**
`tests/test_fase_c_rc_setpoint_b1.py::test_t4_yaw_channel_does_not_change_setpoint_or_collective`
locked C25's own "yaw unused" decision. Retargeted to
`test_t4_yaw_channel_now_sets_setpoint_yaw_c37_disclosed_exception`,
locking the new intentional behavior (yaw mid→0°, max→180°, min→-180°,
collective unaffected) instead.

**Disclosed exception 2 (C++):**
`native/flight_control/tests/test_rc_setpoint.cpp`'s own "yaw channel
changes do not change setpoint/collective" case only checked `.w`/`.x`
(both coincidentally `0` at yaw min/max with roll=pitch=mid, so it
never actually caught the real change, which shows up in `.z`) — a
pre-existing **false negative**, not a real invariant. Retargeted to
check all four quaternion components via `atan2`-derived yaw angle,
locking the same new behavior as the Python twin.

**Disclosed exception 3 (`attitude.cpp` freeze check):**
`tests/test_fase_c_cpp_unit_tests_b1.py::test_t6_rung_sources_are_git_unchanged_by_this_buy`
listed `attitude.cpp` as blanket-frozen. Unlike `esc.cpp`(C26)/`plant.cpp`(C36),
this Buy's own IC explicitly required extending
`ComplementaryAttitudeEstimator`'s constructor and `update()` with new
optional trailing parameters — which cannot be purely additive (the
existing signature lines must be edited in place). Removed from the
blanket list; a dedicated check now verifies the diff removes **exactly**
the two expected signature lines (confirmed via `git diff`, §6.3) and
nothing else — every method body line is untouched.

---

## 5. Tests run

### 5.1 Python — new module

`tests/test_fase_c_mag_yaw_rung_b1.py` — **10 tests**, covering IC §2's
T1-T7, T9, T10 (T8 is the C++ Catch2 cases below; T10's "suite+ctest
green" half is the process run in §3; T11 is this report):

| Test | Covers |
|---|---|
| `test_t1_simulated_mag_hal_identity_q_matches_documented_world_field` | T1 |
| `test_t2_known_yaw_rotation_rotates_body_mag_consistently_finite` | T2 |
| `test_t3_estimator_without_mag_c7_regressions_still_pass` | T3 |
| `test_t4_estimator_with_mag_yaw_error_decreases_over_n_updates` | T4 |
| `test_t5_rc_yaw_map_unlocked_roll_pitch_throttle_unchanged` | T5 |
| `test_t6_invalid_mag_gain_and_world_field_raise` | T6 |
| `test_t7_loop_step_never_calls_plant_and_c35_c36_smokes_still_green` | T7 |
| `test_t9_no_craft_continuity_library_board_edits_and_safety_default_reject_all` | T9 |
| `test_t10_pyproject_version_is_0_5_38` | T10 (version half) |
| `test_t10_full_suite_process_gate_placeholder` | T10 marker |

### 5.2 C++ — new/retargeted Catch2 cases

`native/flight_control/tests/test_mag.cpp` — 6 new `TEST_CASE`s, tag
`[mag][c37]`: T1/T2 (`SimulatedMagHal`), a world-field-validation case,
T3 (behavior-freeze regression), T4 (yaw convergence), and an
invalid-`mag_gain` case.

`native/flight_control/tests/test_rc_setpoint.cpp` — 1 retargeted case
(§4, disclosed exception 2), tag `[rc_setpoint][c37]`.

```text
100% tests passed out of 88
```

Baseline before this Buy: 82 host tests. Delta: **+6** (the new
`test_mag.cpp` cases; the retargeted `test_rc_setpoint.cpp` case
replaces one existing case 1:1, no net count change from it).

---

## 6. Module-boundary / forbidden-symbol grep, and disclosed-diff verification

```text
$ git diff --stat -- native/flight_control/include/jarvis/fc/loop.hpp native/flight_control/src/loop.cpp \
    src/jarvis/flight_software/flight_control/loop.py \
    [... plant/esc/mixer/filter/rate_torque/rc_hold/crsf_failsafe/spi*/dshot*/uart* ...]
(empty — every frozen module untouched)

$ git status --short -- ui/spatial-board library src/jarvis/core src/jarvis/adapters \
    src/jarvis/workspace src/jarvis/actions src/jarvis/schemas src/jarvis/knowledge
# only pre-existing, external, unrelated diffs (parallel craft-geometry
# track, present before this Buy, not touched by it)
```

### 6.1 `attitude.cpp` diff — exactly the two disclosed signature lines

```text
$ git diff -- native/flight_control/src/attitude.cpp | grep '^-' | grep -v '^---'
-ComplementaryAttitudeEstimator::ComplementaryAttitudeEstimator(double gain, Quat initial_q)
-    : gain_(gain), initial_q_(quat::normalize(initial_q)) {
-AttitudeState ComplementaryAttitudeEstimator::update(const ImuSample& sample) {
```

Exactly the constructor declaration/initializer-list line and the
`update` declaration line — both edited only to append a new trailing
optional parameter, nothing else. Every existing method body line
survives untouched (confirmed by reading the full diff, §6 above, and
pinned as an exact-match assertion in
`test_fase_c_cpp_unit_tests_b1.py`'s own retargeted T6).

---

## 7. Files changed

**New:**
- `src/jarvis/flight_software/flight_control/mag.py`
- `src/jarvis/flight_software/flight_control/sim_mag_hal.py`
- `native/flight_control/include/jarvis/fc/mag.hpp`
- `native/flight_control/src/mag.cpp`
- `native/flight_control/tests/test_mag.cpp`
- `tests/test_fase_c_mag_yaw_rung_b1.py`
- `.jes/artifacts/implementation_report_fase_c_mag_yaw_rung_b1.md` (this file)

**Modified:**
- `src/jarvis/flight_software/flight_control/attitude.py` (optional mag yaw correction appended; hard-cut bullet list updated to note supersession)
- `src/jarvis/flight_software/flight_control/rc_setpoint.py` (`RC_CH_YAW`/`RC_MAX_YAW_RAD` added; `_roll_pitch_to_quat` → `_roll_pitch_yaw_to_quat`)
- `src/jarvis/flight_software/flight_control/__init__.py` (new exports)
- `native/flight_control/include/jarvis/fc/attitude.hpp` / `src/attitude.cpp` (mirrors Python)
- `native/flight_control/include/jarvis/fc/rc_setpoint.hpp` / `src/rc_setpoint.cpp` (mirrors Python)
- `native/flight_control/CMakeLists.txt` (`src/mag.cpp` added to `jarvis_fc`; `tests/test_mag.cpp` added to `fc_unit_tests`)
- `tests/test_fase_c_rc_setpoint_b1.py` (T4 retargeted, disclosed exception 1)
- `native/flight_control/tests/test_rc_setpoint.cpp` (yaw case retargeted, disclosed exception 2)
- `tests/test_fase_c_cpp_unit_tests_b1.py` (`attitude.cpp` freeze check retargeted, disclosed exception 3)
- `pyproject.toml` (`0.5.37` → `0.5.38`)
- 43 pre-existing test files re-pinned from `0.5.37` to `0.5.38`
- `README.md`, `docs/ARCHITECTURE.md` (new §1c paragraph after C36), `docs/PLATFORM_CAPABILITY_VISION.md` §13, `docs/IMPLEMENTATION_TASKS.md`, `native/flight_control/README.md` (see §9)

---

## 8. Docs updated (honesty confirmed — not claiming CLOSED/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.38 includes (landed, awaiting Cursor review + Engineer ★ ACCEPT — no `v0.5.38` tag yet)" section; "Next" pointers retargeted.
- `docs/ARCHITECTURE.md` §1c — new C37 paragraph after the C36 block, banner updated.
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C37 block, honesty line verbatim.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner and the C37 table row both changed from "★ AUTHORIZED" to "LANDED (awaiting Cursor review + Engineer ★ ACCEPT, no tag yet)".
- `native/flight_control/README.md` — the stale "yaw channel... never used (no magnetometer in this tree)" claim corrected; new C37 paragraph appended naming `mag.hpp`/`mag.cpp` and the `attitude.hpp`/`rc_setpoint.hpp` extensions.

No file in this Buy claims `v0.5.38` is tagged, ACCEPT CLOSED, "compass live," "GPS heading," "heading hold on hardware," or that mag is on SPI1. Confirmed via `git tag -l | sort -V | tail -5` at close of this Buy: `v0.5.32`-`v0.5.35`, `v0.5.37` — `v0.5.38` does not exist yet.

---

## 9. Residual / next steps

- C38 (altitude loop, sim) is next per the IC's own handoff. Assistant/placement work stays PARKED until C43.
- The pre-existing MCU-toolchain environment issue (disclosed in C36's own report §6.1) remains unfixed, unrelated to this Buy, and does not block its own host-only checkpoint.
- The disclosed left/right composition-order distinction between the accel (body-frame, right) and mag (world-frame, left) corrections is a judgment call worth Cursor/Engineer confirming, though it does not block review — it follows directly from standard quaternion composition rules, not an arbitrary choice.

---

## 10. Acceptance self-check vs IC §4/§4 (Acceptance)

- T1-T11: ✅ T1-T7/T9/T10 in Python (10/10 passing), T1-T5 equivalents in C++ Catch2 (6/6 passing, exceeding "at least T1+T4+T5"), T10's suite/ctest half in §3, T11 in this report.
- Mag optional path: ✅ `update(sample, mag=None)` in both languages, `mag=None` byte-identical (16/16 pre-existing C7 tests unchanged).
- RC yaw unlocked: ✅ mid→0°, max→180°, min→-180°, collective/roll/pitch/throttle unaffected.
- C7-without-mag frozen: ✅ re-verified explicitly.
- Version `0.5.38`: ✅ `pyproject.toml` + all 43 checkpoint tests re-pinned.

**PASS** against every criterion in IC §4. **FAIL conditions** (live
mag, second AHRS brand, altitude/position controller, plant inside
`step`, craft wiring, "we fly") — none present, verified above.
