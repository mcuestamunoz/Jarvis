# Implementation Report — Fase C deepen C++ unit tests (`B1-fase-c-cpp-unit-tests`)

**IC:** [`implementation_contract_fase_c_cpp_unit_tests_b1.md`](implementation_contract_fase_c_cpp_unit_tests_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-21
**Status:** ★ ACCEPT CLOSED @ tag **`v0.5.13`**. See [review](implementation_review_fase_c_cpp_unit_tests_b1.md).

---

## 0. Read this first — framework pin, honesty summary

This Buy stops the steel ladder from relying on two hand-rolled `main()`-based smoke scripts as its only verification. It introduces a **real C++ unit-test framework — Catch2 v3, pinned to release tag `v3.7.1`** (commit `fa43b77429ba76c462b1898d6cd2f2d7a9416b14`) — fetched via CMake `FetchContent`, and adds **26 `TEST_CASE`s / \~494 assertions** across the six steel rungs (filter, attitude, controller, rate_torque, mixer, esc).

**Behavior freeze honored exactly as locked (IC §0 decision 6):** `git diff --stat` on every pre-existing rung source (`filter.cpp`, `attitude.cpp`, `controller.cpp`, `rate_torque.cpp`, `mixer.cpp`, `esc.cpp`, `plant.cpp`, and all `include/jarvis/fc/*.hpp`) is **empty** — this Buy added test coverage only. No bug was exposed by the new cases, so no STOP-and-ask escalation was needed.

Both existing smoke binaries (`fc_closed_loop_smoke`, `fc_esc_pwm_smoke`) remain, unmodified, and stay registered in `ctest` alongside the 26 new unit cases — 28 total `ctest` entries, all passing.

---

## 1. Framework choice + pin (IC §0 decision 4, §4 T1)

**Catch2 v3**, the IC's locked-preferred choice (doctest was not needed — Catch2 built and linked cleanly on this host toolchain with no friction). Pinned via:

```cmake
FetchContent_Declare(
    Catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG        v3.7.1
)
```

`v3.7.1` resolves to commit `fa43b77429ba76c462b1898d6cd2f2d7a9416b14` (confirmed via `git ls-remote --tags https://github.com/catchorg/Catch2.git`, dereferenced tag object). This is a real, reproducible pin — not a floating branch.

**Network story (IC §0 decision 5):** network was needed exactly once, at the first `cmake -S native/flight_control -B build/flight_control` after this Buy's CMakeLists.txt change — it cloned the pinned tag into `build/flight_control/_deps/catch2-src` and built `libCatch2.a`/`libCatch2Main.a` alongside the rest of the tree (confirmed in the build log, §3). Once that `_deps` directory exists, no further network access is required to reconfigure, rebuild, or re-run `ctest` — this is documented in `native/flight_control/README.md`'s own new "Run the unit-test suite" section.

`Catch2::Catch2WithMain` is linked into `fc_unit_tests` so no separate `main.cpp` was needed in this tree (a single-TU `CATCH_CONFIG_MAIN` would duplicate what the library already provides).

---

## 2. Package layout vs IC §1

```text
native/flight_control/
  CMakeLists.txt              # + FetchContent(Catch2 v3.7.1) + fc_unit_tests target + catch_discover_tests
  tests/                      # NEW
    test_filter.cpp
    test_attitude.cpp
    test_controller.cpp
    test_rate_torque.cpp
    test_mixer.cpp
    test_esc.cpp
  smoke/                      # UNCHANGED — both binaries remain, both still registered in ctest
    closed_loop_smoke.cpp
    esc_pwm_smoke.cpp
  include/ src/                # byte-unchanged (confirmed §6)
```

No separate `main.cpp` in `tests/` (Catch2WithMain supplies it) — filenames otherwise match the IC's own suggested layout exactly, one file per rung, no full Python-parity mirror attempted (IC §0 decision 8 explicitly does not require that).

---

## 3. Build + run results (IC §4 T1–T4)

```bash
$ cmake -S native/flight_control -B build/flight_control
-- Performing Test HAVE_FLAG__ffile_prefix_map...
-- Configuring done (4.6s)     # Catch2 v3.7.1 cloned here, once
-- Generating done
-- Build files have been written to: .../build/flight_control

$ cmake --build build/flight_control
[...]  Building CXX object _deps/catch2-build/... (Catch2 + Catch2WithMain, ~70 TUs)
[100%] Built target Catch2
[100%] Built target Catch2WithMain
[ 95%] Building CXX object CMakeFiles/fc_unit_tests.dir/tests/test_filter.cpp.o
[ 96%] Building CXX object CMakeFiles/fc_unit_tests.dir/tests/test_attitude.cpp.o
[ 97%] Building CXX object CMakeFiles/fc_unit_tests.dir/tests/test_controller.cpp.o
[ 98%] Building CXX object CMakeFiles/fc_unit_tests.dir/tests/test_rate_torque.cpp.o
[ 99%] Building CXX object CMakeFiles/fc_unit_tests.dir/tests/test_mixer.cpp.o
[ 99%] Building CXX object CMakeFiles/fc_unit_tests.dir/tests/test_esc.cpp.o
[100%] Linking CXX executable fc_unit_tests
[100%] Built target fc_unit_tests
   (zero warnings from jarvis_fc/smoke/tests targets with -Wall -Wextra)

$ ./build/flight_control/fc_unit_tests
===============================================================================
All tests passed (494 assertions in 26 test cases)
exit code: 0

$ ./build/flight_control/fc_closed_loop_smoke
initial tilt error: 15.000 deg
final tilt error:   0.252 deg (after 200 steps)
PASS: tilt error strictly decreased and recovered below 2.0 deg
exit code: 0    # byte-identical to C13/C14 — T4 confirmed

$ cd build/flight_control && ctest
...
27/28 Test #27: fc_closed_loop_smoke ... Passed  0.33 sec
28/28 Test #28: fc_esc_pwm_smoke ....... Passed  0.28 sec
100% tests passed out of 28
Total Test time (real) = 0.68 sec
```

`ctest` discovered all **26 individual `TEST_CASE`s** via `catch_discover_tests(fc_unit_tests)` (each shows as its own numbered `ctest` entry, not one opaque binary run) **plus** the 2 pre-existing smoke tests — **28/28 passed**.

---

## 4. Case inventory (IC §4 T2, §2)

| Rung | File | Cases |
|---|---|---|
| filter | `test_filter.cpp` | first-sample-seeds-unsmoothed; second-sample-moves-by-alpha (EMA shape); `reset()` re-seeds; rejects out-of-range `alpha` |
| attitude | `test_attitude.cpp` | level+zero-motion stays level; tilted accel correction stays finite **and converges toward true tilt** (C11 Amendment A regression guard, 200-step loop); rejects out-of-range `gain` |
| controller | `test_controller.cpp` | level state + level setpoint → zero rate command; tilted state → correct **sign** on dominant (roll) axis, near-zero off-axis; `kd` damps nonzero measured rate at level attitude; rejects invalid gains |
| rate_torque | `test_rate_torque.cpp` | zero rate → zero torque; default `gain=1.0` is an identity map; scalar gain scales + preserves sign; per-axis gains; rejects non-positive/non-finite gains |
| mixer | `test_mixer.cpp` | hover collective + zero torque → four equal finite in-range forces; positive roll torque raises FL/RL and lowers FR/RR (documented X-geometry sign check); output clamped to `[0,1]` for extreme torque; collective clamped to `[0,1]`; rejects negative scales |
| esc | `test_esc.cpp` | force=0→1000µs, force=1→2000µs; custom bounds still linear; rejects invalid min/max; disarmed apply records-but-refuses; armed apply reports `applied=true`, `disarm()` flips back |

**Depth honesty (IC §0 decision 8):** this is the documented **minimum per-rung depth**, not a full mirror of every Python pytest across C6–C14 — `plant`/`quat_math` were not given their own dedicated files this Buy (both are already exercised indirectly: `plant`'s own algorithm is unchanged and still covered end-to-end by `fc_closed_loop_smoke`; `quat_math` is exercised by every attitude/controller/plant case that goes through it). This is disclosed here per the IC's own "not required: full mirror" note, not hidden.

**Tolerances:** `WithinAbs(..., 1e-9)` for exact linear/algebraic results (filter EMA arithmetic, rate_torque scaling, esc PWM map); `1e-6` for the attitude/controller cases involving quaternion composition, matching the IC §2's "same order of magnitude as existing smokes... document intentional looseness" note — the looser tolerance accounts for accumulated floating-point error across quaternion normalize/multiply chains, not any nondeterminism (the algorithm itself is deterministic).

---

## 5. Tests (IC §4)

| ID | Check | Result |
|---|---|---|
| T1 | CMake configures with pinned Catch2 and builds `fc_unit_tests` | ✅ §3 — configure + build logs |
| T2 | Unit suite has ≥1 case each for filter, attitude, controller, rate_torque, mixer, esc | ✅ §4 — 26 cases across the 6 files |
| T3 | `ctest` runs unit suite + both smokes, all green | ✅ §3 — 28/28 passed |
| T4 | `fc_closed_loop_smoke` still recovers (~15° → ~0.25°) | ✅ §3 — byte-identical `15° → 0.252°` |
| T5 | No GPIO/DShot/serial/socket call sites introduced; no `.cpp` under `src/jarvis/` | ✅ grep clean (comment-only honesty mentions), confirmed empty `find src/jarvis -name "*.cpp" -o -name "*.hpp" -o -name CMakeLists.txt` |
| T6 | Rung sources byte-unchanged or Engineer-approved bugfix disclosed | ✅ `git diff --stat` on all 7 rung `.cpp` + all `.hpp` returns empty — no bugfix needed |
| T7 | Thin pytest wrapper: runs ctest/unit+smokes if built, skip-with-build-hint if not | ✅ `tests/test_fase_c_cpp_unit_tests_b1.py` |
| T8 | Python full suite green @ `0.5.13` | ✅ **3380 passed, 1 skipped** (was 3368 — exact +12 delta) |
| T9 | Report lists framework pin, case inventory, honesty statement | ✅ §1, §4, §7 |
| T10 | Docs honest; no premature `v0.5.13` tag | ✅ §8 below |

New Python test module `tests/test_fase_c_cpp_unit_tests_b1.py` — **12 tests**, all passing:

```text
test_t1_cmake_wires_pinned_catch2_and_unit_test_target PASSED
test_t2_per_rung_unit_test_sources_exist PASSED
test_smoke_binaries_still_registered_in_cmake PASSED
test_t3_unit_test_binary_all_cases_pass_if_built PASSED
test_t4_closed_loop_smoke_still_recovers_if_built PASSED
test_esc_smoke_still_passes_if_built PASSED
test_t5_no_gpio_or_hardware_io_symbols_in_new_unit_tests PASSED
test_t6_rung_sources_are_git_unchanged_by_this_buy PASSED
test_no_native_unit_test_wiring_into_craft_or_orchestrator PASSED
test_default_safety_and_autonomy_submit_still_reject PASSED
test_capability_registry_default_still_empty PASSED
test_t8_pyproject_version_is_0_5_13 PASSED
```

**Wrapper choice (IC §4 "document choice", same rationale as C13/C14's own wrappers):** the pytest wrapper does not invoke `cmake`/`clang++`/`ctest` itself — it runs the already-built `fc_unit_tests`, `fc_closed_loop_smoke`, and `fc_esc_pwm_smoke` binaries if present, asserting exit 0 and parsing Catch2's own "All tests passed (N assertions in M test cases)" summary line (and each smoke's own `PASS` marker); if a binary is absent, the relevant test skips with a reason naming the exact build command, including the one-time network note for the Catch2 fetch. The actual configure+build+run was performed and verified manually for this Buy (§3).

**T8 (full suite):** `pytest -q` — **3380 passed, 1 skipped** (baseline before this Buy was 3368 passed, 1 skipped; delta is exactly the 12 new tests, no other file's pass/fail count moved).

Twenty pre-existing test files hardcoded the prior checkpoint version string (`"0.5.12"`) as a version-pin assertion, including C13's and C14's own wrapper modules. Since this IC explicitly requires the `0.5.13` bump (§0 decision 11), all twenty were re-pinned to `"0.5.13"`:

- `tests/test_bom_sku_resolved_cameras_b1.py`
- `tests/test_catalog_camera_power_w_b1.py`
- `tests/test_fase_c_attitude_controller_rung_b1.py`
- `tests/test_fase_c_attitude_estimation_rung_b1.py`
- `tests/test_fase_c_autonomy_surface_b1.py`
- `tests/test_fase_c_capability_registry_scaffold_b1.py`
- `tests/test_fase_c_controlled_flight_sim_tip_b1.py`
- `tests/test_fase_c_cpp_esc_pwm_stub_b1.py`
- `tests/test_fase_c_cpp_flight_control_scaffold_b1.py`
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

## 6. Honesty / forbidden confirmation (IC §5)

| Forbidden | Status | Evidence |
|---|---|---|
| MCU target / cross-compile "while we're here" | ✅ absent | CMakeLists.txt unchanged in this regard — host-only `project(... CXX)`, no toolchain file, no cross-compile flags added |
| Deleting smoke binaries | ✅ absent | Both `add_executable`/`add_test` entries for `fc_closed_loop_smoke`/`fc_esc_pwm_smoke` untouched; both re-verified passing (§3) |
| Quiet algorithm refactors | ✅ absent | `git diff --stat` empty on all rung sources (§6/T6) — behavior freeze honored exactly, no STOP-and-ask needed since no bug was found |
| Claiming production/certified/hardware-verified | ✅ absent | README/report explicitly say "host desktop unit-test run, nothing more"; no "production-hardened," "MCU-ready verified," or "firmware certified" language anywhere |
| Vendoring a giant unrelated SDK | ✅ absent | Only Catch2 (a test framework, the IC's own locked choice) was fetched — no unrelated dependency pulled in |

**"One front" discipline (process lock after C6):** this Buy stayed exactly within deepening C++ verification. No MCU cross-compile, Safety-real, ELRS, GPIO/DShot, or craft↔FS wiring were touched or opened.

---

## 7. Integration rules (IC §3) — confirmed unchanged

- C13/C14 modules — `fc_unit_tests` links `jarvis_fc` (the same static library the smokes link); no duplicate math was forked into the test binary.
- Smoke binaries — remain, still registered in `ctest` (§3).
- Python suite — untouched except the 20 version re-pins and the new thin wrapper module (§5).
- Craft / `RejectAllSafetyGate` / autonomy — untouched (confirmed via the wrapper's own reject/registry checks).
- MCU / Safety / link — out of scope, not touched.

---

## 8. Docs honesty confirmation (IC §6, §4 T10)

- README / PRIORIDAD / ARCHITECTURE / PLATFORM: ★ ACCEPT CLOSED @ tag **`v0.5.13`**
- Explicit **exists vs. impossible**: **exists** = host Catch2 v3.7.1 unit suite (26 cases) + per-rung coverage + both smokes via `ctest`; **impossible** = MCU-verified proof, flying vehicle, real Safety, "production-hardened" firmware.

---

## 9. Residual — what comes next

Per this IC's own §8 handoff: still one front at a time, Engineer-prioritized — MCU cross-compile target, real Safety, a real link, or craft↔FS wiring. Not decided here. Possible future deepening within the "C++ tests" front itself (not opened by this Buy): `plant`/`quat_math` dedicated test files, edge-case coverage beyond the documented minimum, or a coverage/sanitizer pass — left for a future Buy if the Engineer prioritizes it.

---

## 10. Acceptance self-check against IC §7

- T1–T10: ✅ (see §5 table)
- Unit suite green: ✅ (§3 — 26/26 cases, 494/494 assertions)
- Both smokes green: ✅ (§3 — `ctest` 28/28)
- No GPIO: ✅ (§5 T5, §6)
- Python suite green: ✅ (3380 passed, 1 skipped)
- `0.5.13`: ✅
- Behavior freeze honored: ✅ (§6, T6 — empty `git diff` on all rung sources; no bug found, no Engineer-call needed)
- Not FAIL conditions: framework is real Catch2, not hand-rolled-only (§1) · smokes not deleted/broken (§3, §6) · no silent math changes (§6, T6) · no MCU/Safety/link folded in (§6) · no premature "hardened firmware" claim anywhere (§8)
