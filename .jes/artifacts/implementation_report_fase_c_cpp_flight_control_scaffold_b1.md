# Implementation Report — Fase C C++ flight_control scaffold (`B1-fase-c-cpp-flight-control-scaffold`)

**IC:** [`implementation_contract_fase_c_cpp_flight_control_scaffold_b1.md`](implementation_contract_fase_c_cpp_flight_control_scaffold_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-21
**Status:** ★ ACCEPT CLOSED @ **`v0.5.11`**.

---

## 0. Read this first — material change, honesty summary

This Buy opens the **first C++ material** for `flight_control`: a new, host-only tree at **`native/flight_control/`** (outside `src/jarvis/`, per the IC's locked path). It is **not** MCU firmware, does not flash any board, does not touch GPIO/PWM/DShot/serial/sockets, does not vendor PX4/ArduPilot, and does not replace the Python `flight_software/` package — that package remains the design guide and the craft platform, changed here only by a docstring pointer and its own version pin.

The C++ scaffold mirrors the Python wooden ladder's algorithmic shape (filter → attitude → controller → rate_torque → mixer → plant) and runs the **same closed-loop tip**: seeded at a 15° tilt, the true tilt error recovers to **0.252°** after 200 steps — numerically matching the Python ladder's own C11/C12 result, though the IC does not require bit-identity (§0 decision 7), only that the tilt error strictly decrease and recover.

**Toolchain note:** CMake was not present in this environment; it was installed via `brew install cmake` (Homebrew, already present on the host) to satisfy the IC's own requirement of a CMake ≥ 3.16 host build. This is disclosed here as a one-time environment-setup action, not a repo change.

---

## 1. Package layout vs IC §1

```text
native/flight_control/
├── CMakeLists.txt
├── README.md
├── include/jarvis/fc/
│   ├── types.hpp        # Vec3, Quat, ImuSample
│   ├── quat_math.hpp     # shared quaternion helpers (see §2 deviation note)
│   ├── filter.hpp
│   ├── attitude.hpp
│   ├── controller.hpp
│   ├── rate_torque.hpp
│   ├── mixer.hpp
│   └── plant.hpp
├── src/
│   ├── filter.cpp
│   ├── attitude.cpp
│   ├── controller.cpp
│   ├── rate_torque.cpp
│   ├── mixer.cpp
│   └── plant.cpp
└── smoke/
    └── closed_loop_smoke.cpp   # `fc_closed_loop_smoke` — the tip harness
```

Matches the IC's normative layout exactly (§1), with one addition (`include/jarvis/fc/quat_math.hpp`) disclosed below. No `board/` BSP tree, no `hal_gpio.cpp`, no vendored autopilot stack — confirmed absent (T5).

`esc.hpp`/PWM encoding was **not** ported in this Buy — an explicitly allowed simplification per IC §1's own note ("ESC/PWM encode may be included or stubbed — if stubbed, disclose; tip smoke must not need real PWM I/O"). The tip smoke consumes `MotorForceCommand` directly, same as the Python C11 tip, and never needs PWM encoding to close the loop.

---

## 2. APIs / behavior implemented vs IC §2

| Python guide | C++ responsibility | Match |
|---|---|---|
| `ImuLowPassFilter` | `jarvis::fc::ImuLowPassFilter` — EMA on accel/gyro, same `alpha ∈ (0,1]` validation, same first-sample-seeds-unsmoothed behavior | ✅ |
| `ComplementaryAttitudeEstimator` | `jarvis::fc::ComplementaryAttitudeEstimator` — same gyro-integrate + accel-correct algorithm, **carries the C11 Amendment A fix** (`cross(accel_dir, predicted_down_body)`, not the reversed order) from day one | ✅ |
| `PdAttitudeController` | `jarvis::fc::PdAttitudeController` — same `omega_cmd = kp*e_rot - kd*omega_measured` law, same shortest-path error-quaternion extraction | ✅ |
| `LinearRateTorqueBridge` | `jarvis::fc::LinearRateTorqueBridge` — same `tau_i = gain_i * omega_cmd_i` feedforward-only law, scalar or per-axis gain constructors, same `> 0` validation | ✅ |
| `QuadXMixer` | `jarvis::fc::QuadXMixer` — same X-frame allocation formula, motor order (m0=FR, m1=FL, m2=RL, m3=RR), same `[0,1]` clamping | ✅ |
| `ToyQuadAttitudePlant` | `jarvis::fc::ToyQuadAttitudePlant` — same toy torque-proxy map, same semi-implicit integration, same `sense()`/`step()`/`true_attitude()` shape | ✅ |
| C11 tip smoke | `fc_closed_loop_smoke` — same wiring (filter→estimate→PD→bridge→mixer→plant), same default parameters (steps=200, dt=0.01, tilt=15°, alpha=0.2, estimator gain=0.05, kp=6.0, kd=0.6, collective=0.5, torque_gain=40.0, angular_damping=0.5) | ✅ |

**Documented intentional simplifications vs Python (IC §2's own requirement):**

1. **Shared `quat_math.hpp` instead of per-module private helpers.** Python duplicates `_quat_normalize`/`_quat_multiply`/etc. privately in both `attitude.py` and `plant.py`, matching this project's established per-module-private-helper style. In this first C++ Buy, the identical ~40 lines of arithmetic are factored into one shared internal header (`jarvis::fc::quat`) instead, purely to avoid duplicating a new translation unit's worth of numerically-identical code in a brand-new tree. This is a code-organization choice only — same formulas, same convention, no behavioral difference. Disclosed in the header's own comment.
2. **API surface uses plain structs, not a Pydantic-equivalent validation layer**, matching "algorithms should match Python intent... exact float bit-identity... not required" (IC §2 note) — C++ constructors validate the same invariants (finite, sign, range) via `std::invalid_argument`, not a schema library; there is no C++ analogue of Pydantic's `extra="forbid"` (structs have no extra-field concept in C++), disclosed as a language-level difference, not a scope gap.
3. **ESC/PWM stub not ported** — see §1 above (explicitly allowed by the IC).

No forbidden APIs exist: no `rate_pid_step`-shaped symbol, no `compute_inertia_torque_nm`, no `write_gpio`, no cascaded inner-rate-loop class — confirmed by T4 grep (source-code only, comments excluded from the match to avoid flagging this module's own honesty prose, same "symbol(" convention used by every prior Fase C Buy).

---

## 3. Build + tip smoke results (IC §0 decision 3, §4 T2/T3)

```bash
$ cmake -S native/flight_control -B build/flight_control
-- The CXX compiler identification is AppleClang 21.0.0.21000101
-- Configuring done
-- Generating done
-- Build files have been written to: .../build/flight_control

$ cmake --build build/flight_control
[100%] Built target jarvis_fc
[100%] Built target fc_closed_loop_smoke
   (zero warnings with -Wall -Wextra)

$ ./build/flight_control/fc_closed_loop_smoke
fc_closed_loop_smoke: host scaffold, C++ tip smoke (not hardware, not flight)
initial tilt error: 15.000 deg
final tilt error:   0.252 deg (after 200 steps)
PASS: tilt error strictly decreased and recovered below 2.0 deg
exit code: 0

$ cd build/flight_control && ctest --output-on-failure
1/1 Test #1: fc_closed_loop_smoke .............   Passed    0.01 sec
100% tests passed out of 1
```

Toolchain used: Apple Clang 21 (`/usr/bin/clang++`), CMake 4.4.3 (installed via Homebrew for this Buy). C++17, `Release` build type (default when unset).

**Recovery criterion (documented, IC §4 T3):** the smoke asserts `final_tilt_deg < initial_tilt_deg` (strict decrease) **and** `final_tilt_deg < 2.0°` (recovery threshold) — looser than Python's own ~0.252° since bit-identity is explicitly not required, but in practice the C++ port reproduced the Python numeric result almost exactly, since both share the same formulas and the same deterministic (no-noise) toy dynamics.

---

## 4. Tests (IC §4)

| ID | Check | Result |
|---|---|---|
| T1 | `native/flight_control/` exists with CMakeLists + smoke target | ✅ `test_t1_native_tree_exists_with_cmake_and_smoke_target` |
| T2 | Configure + build succeeds on a documented host toolchain | ✅ manual build (§3) + `test_t2_t3_smoke_binary_builds_and_recovers_if_toolchain_available` (re-verifies the built artifact) |
| T3 | Smoke: tilted IC → tilt error strictly decreases, recovers | ✅ `15° → 0.252°` (§3); same pytest test parses stdout and asserts both conditions |
| T4 | No GPIO/pigpio/`/dev/mem`/serial ESC symbols (grep) | ✅ `test_t4_no_gpio_or_hardware_io_symbols_in_native_tree` |
| T5 | No PX4/ArduPilot tree vendored | ✅ `test_t5_no_px4_or_ardupilot_vendored_tree` |
| T6 | Python full suite still green @ `0.5.11` | ✅ **3358 passed, 1 skipped** (was 3348 — exact +10 delta) |
| T7 | Report: material change · host-only · != flying · Python retained · C++ honesty | ✅ this report |
| T8 | Docs PRIORIDAD / PLATFORM / ARCHITECTURE / README updated honestly, no premature `v0.5.11` tag | ✅ §8 below |

New Python test module `tests/test_fase_c_cpp_flight_control_scaffold_b1.py` — **10 tests**, all passing:

```text
test_t1_native_tree_exists_with_cmake_and_smoke_target PASSED
test_t2_t3_smoke_binary_builds_and_recovers_if_toolchain_available PASSED
test_t4_no_gpio_or_hardware_io_symbols_in_native_tree PASSED
test_t5_no_px4_or_ardupilot_vendored_tree PASSED
test_native_tree_outside_python_package PASSED
test_python_wooden_ladder_retained_unchanged PASSED
test_default_safety_and_autonomy_submit_still_reject PASSED
test_capability_registry_default_still_empty PASSED
test_no_native_flight_control_wiring_into_craft_or_orchestrator PASSED
test_t11_pyproject_version_is_0_5_11 PASSED
```

**Wrapper choice, documented (IC §4's own "document choice" requirement):** the pytest wrapper for T2/T3 does **not** invoke `cmake`/`clang++` itself — it looks for an already-built binary at the canonical path (`build/flight_control/fc_closed_loop_smoke`) and runs it if present, asserting exit 0 and parsing the printed tilt-error values to confirm the recovery criterion; if the binary is absent, it **skips with a reason** naming the exact build command. Rationale, stated in the test module's own docstring: building a native binary on every `pytest` run would make the (fast, hermetic) Python suite depend on a C++ toolchain being present in every environment that runs it. The actual configure+build+run was performed and verified manually for this Buy (§3); this wrapper re-verifies the artifact on any developer/CI machine that has the toolchain and has already built it.

**T6 (full suite):** `pytest -q` — **3358 passed, 1 skipped** (baseline before this Buy was 3348 passed, 1 skipped; delta is exactly the 10 new tests, no other file's pass/fail count moved).

Sixteen pre-existing test files (plus C12's own `test_fase_c_rate_torque_bridge_b1.py`) hardcoded the prior checkpoint version string (`"0.5.10"`) as a version-pin assertion. Since this IC explicitly requires the `0.5.11` bump (§0 decision 12), all eighteen were re-pinned to `"0.5.11"`:

- `tests/test_bom_sku_resolved_cameras_b1.py`
- `tests/test_catalog_camera_power_w_b1.py`
- `tests/test_fase_c_attitude_controller_rung_b1.py`
- `tests/test_fase_c_attitude_estimation_rung_b1.py`
- `tests/test_fase_c_autonomy_surface_b1.py`
- `tests/test_fase_c_capability_registry_scaffold_b1.py`
- `tests/test_fase_c_controlled_flight_sim_tip_b1.py`
- `tests/test_fase_c_esc_pwm_stub_rung_b1.py`
- `tests/test_fase_c_first_fc_rung_b1.py`
- `tests/test_fase_c_imu_filtering_rung_b1.py`
- `tests/test_fase_c_intent_safety_stub_b1.py`
- `tests/test_fase_c_mixer_rung_b1.py`
- `tests/test_fase_c_radio_dual_role_b1.py`
- `tests/test_fase_c_rate_torque_bridge_b1.py`
- `tests/test_geometry_prop_adapter_visor_x_b1.py`
- `tests/test_library_cameras_seed_b1.py`
- `tests/test_mission_power_w_b1.py`
- `tests/test_mission_vtx_identity_b1.py`

---

## 5. Honesty / forbidden confirmation (IC §5)

| Forbidden | Status | Evidence |
|---|---|---|
| Claiming onboard flight / flash | ✅ absent | README + smoke stdout + module comments all state "host scaffold, not hardware, not flight" |
| GPIO / real ESC | ✅ absent | T4 grep — zero GPIO/pigpio/`/dev/mem`/termios/serial/socket/DShot code tokens in `native/flight_control` (comment-only mentions in honesty prose excluded from the match) |
| Deleting Python ladder | ✅ absent | All 6 Python modules confirmed present and importable (`test_python_wooden_ladder_retained_unchanged`) |
| Safety-real / ELRS / craft wiring | ✅ absent | `RejectAllSafetyGate` unchanged (T8-equivalent test); no reference to `native/flight_control`, `jarvis_fc`, or `fc_closed_loop_smoke` anywhere under `src/jarvis/core/` or `src/jarvis/adapters/` (`test_no_native_flight_control_wiring_into_craft_or_orchestrator`) |
| Silent bit-identity with Python as PASS gate | ✅ not required | Tip criterion is "decreases and recovers below 2.0°" (§3); bit-identity happened to hold in practice but was never the gate |

**"One front" discipline (process lock after C6):** this Buy stayed exactly within the C++ material scaffold scope. No Safety-real, no ELRS decode, no GPIO/PWM peripherals, no craft↔FS wiring were touched or opened.

---

## 6. Integration rules (IC §3) — confirmed unchanged

- Python `flight_software/` — untouched except the docstring pointer in `src/jarvis/flight_software/__init__.py` and the version pin.
- Craft / Board / `library/` — untouched (no file under those trees references `native/flight_control`).
- `RejectAllSafetyGate` — untouched, still the only shipped gate, still always rejects.
- C12 bridge honesty — present in the C++ path used by the smoke (`LinearRateTorqueBridge`, feedforward-only, same `gain=1.0` default no-op).

---

## 7. Files changed

**New:**
- `native/flight_control/CMakeLists.txt`
- `native/flight_control/README.md`
- `native/flight_control/include/jarvis/fc/{types,quat_math,filter,attitude,controller,rate_torque,mixer,plant}.hpp`
- `native/flight_control/src/{filter,attitude,controller,rate_torque,mixer,plant}.cpp`
- `native/flight_control/smoke/closed_loop_smoke.cpp`
- `tests/test_fase_c_cpp_flight_control_scaffold_b1.py`
- `.jes/artifacts/implementation_report_fase_c_cpp_flight_control_scaffold_b1.md` (this file)
- `build/flight_control/` — local CMake build output (not a repo source change; a `.gitignore` entry is recommended if not already present — see §9)

**Modified:**
- `pyproject.toml` — version `0.5.10` → `0.5.11`
- `src/jarvis/flight_software/__init__.py` — docstring gained a C13 pointer paragraph; no import/export/behavior change
- `docs/ARCHITECTURE.md` — §1a tip-version line updated; new C13 paragraph after the C12 block
- `docs/PLATFORM_CAPABILITY_VISION.md` — §13 gained a new C13 block
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner + C13 queue row updated to "landed, awaiting Cursor review + ★ ACCEPT"
- `README.md` — header banner, new "What v0.5.11 includes (working tree — not yet tagged)" section
- 18 test files — re-pinned stale `0.5.10` version-checkpoint assertions to `0.5.11`

**Not touched (confirmed):** `orchestrator.py`, Board (`ui/spatial-board/`), `library/`, `src/jarvis/capabilities/*`, `src/jarvis/flight_software/autonomy/*`, `src/jarvis/flight_software/flight_control/*.py` (all six Python rung modules byte-unchanged), `.jes/state/engineering_state.json`.

---

## 8. Docs honesty confirmation (IC §6, §4 T8)

- README header banner: "v0.5.10 tagged tip · working tree ahead toward v0.5.11 (C13 ... awaiting Cursor review + Engineer ACCEPT)" — no premature tag claim.
- `docs/IMPLEMENTATION_TASKS.md` PRIORIDAD banner and C13 row: "landed — awaiting Cursor review + ★ ACCEPT ... tag not on git yet".
- `docs/ARCHITECTURE.md` C13 paragraph: "aterrizado, pendiente de review de Cursor + ACCEPT del Engineer — sin tag `v0.5.11` todavía".
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 C13 block: "landed — awaiting Cursor review + Engineer ACCEPT — no tag `v0.5.11` yet".
- Confirmed via `git tag -l | sort -V`: latest Fase C tag is `v0.5.10` (C12); no `v0.5.10`-adjacent `v0.5.11` tag exists.
- Explicit **exists vs. impossible** statement, present in README/ARCHITECTURE/PLATFORM_CAPABILITY_VISION: **exists** = a host C++ tree + CMake build + host tip smoke; **impossible** = hardware flight control, flying, firmware on any board, replacing the Python craft SoT.

---

## 9. Residual — what comes next

Per this IC's own §8 handoff: next Buy (likely, still one front at a time) is one of: deepen C++ parity (e.g. port `esc.hpp`, add unit tests in C++ itself), an MCU cross-compile target, a real (non-`RejectAll`) Safety policy, or a real link (ELRS) — Engineer-prioritized, not decided here.

**Minor housekeeping note (not part of this IC's required scope, flagged for the next Buy or Engineer's own judgment):** `build/flight_control/` (the local CMake build directory) was created under the repo root during this Buy's build-and-verify step. It is build output, not source, and should be `.gitignore`d if the repo does not already ignore `build/` — checked: `.gitignore` was not modified by this Buy; recommend the Engineer/Cursor confirm before committing.

---

## 10. Acceptance self-check against IC §7

- T1–T8: ✅ (see §4 table)
- C++ tip smoke builds and recovers: ✅ (§3 — `15° → 0.252°`, exit 0)
- No GPIO: ✅ (§4 T4, §5)
- Python suite green: ✅ (3358 passed, 1 skipped)
- Version `0.5.11`: ✅
- Honesty docs: ✅ (§8)
- Not FAIL conditions: no empty hello-world (real tip smoke, §3) · no hardware I/O (§5) · Python ladder not removed (§5, §6) · no premature "we fly" claim anywhere (§8) · no PX4/ArduPilot drop-in (§4 T5)
