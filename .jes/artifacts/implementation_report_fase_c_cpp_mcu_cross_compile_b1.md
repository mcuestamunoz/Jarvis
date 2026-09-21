# Implementation Report — Fase C MCU cross-compile scaffold (`B1-fase-c-cpp-mcu-cross-compile`)

**IC:** [`implementation_contract_fase_c_cpp_mcu_cross_compile_b1.md`](implementation_contract_fase_c_cpp_mcu_cross_compile_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-21
**Status:** ★ ACCEPT CLOSED @ tag **`v0.5.14`**. See [review](implementation_review_fase_c_cpp_mcu_cross_compile_b1.md).

---

## 0. Read this first — a real toolchain-completeness finding, honesty summary

This Buy adds a CMake cross-compile toolchain file targeting `arm-none-eabi` (generic Cortex-M4, `-mcpu=cortex-m4 -mthumb -mfloat-abi=soft`) that builds **only** `libjarvis_fc.a` — a compile-time proof the steel-ladder sources build freestanding for this instruction set. It does **not** flash any board, does **not** link a bootable `.elf`, requires **no** vendor SDK/BSP, and touches **no** GPIO/PWM/DShot. The host build remains the unmodified default path.

**A genuine obstacle was hit and is disclosed here, not papered over:** the first toolchain candidate installed (`brew install arm-none-eabi-gcc`, a bare Homebrew formula) answers `arm-none-eabi-g++ --version` but has **no bundled `newlib`/`libstdc++`** — compiling any rung source fails with `fatal error: optional: No such file or directory`. This is a toolchain-*packaging* problem, not a bug in `jarvis_fc` or this Buy's CMake. It was resolved by downloading the official **xPack `arm-none-eabi-gcc` v15.2.1-1.1 (darwin-arm64)** release — a full toolchain bundling libstdc++ for the `thumb/v7e-m/nofp` multilib — and a **real, successful cross-build was performed and verified** with it (§3). The `brew install --cask gcc-arm-embedded` alternative (the official Arm GNU Toolchain) could not be completed in this session because its installer requires interactive `sudo` (not available non-interactively) — this is disclosed as a blocked path, not claimed as done.

Because of this real-world "compiler present but incomplete" case, the pytest wrapper (§5) does **not** treat "found `arm-none-eabi-g++` on PATH" as a guarantee of success — it attempts the actual build and degrades to a **skip with a specific, actionable install hint** if compilation fails, rather than a hard suite failure. This was itself verified both ways in this session (§5).

---

## 1. Toolchain choice + pin (IC §0 decisions 4, 10; §4 T1)

**File:** `native/flight_control/cmake/toolchains/arm-none-eabi.cmake` (matches the IC's own preferred path).

**Locked target (IC §0 decision 4):** `CMAKE_SYSTEM_NAME Generic`, `CMAKE_SYSTEM_PROCESSOR arm`, CPU flags `-mcpu=cortex-m4 -mthumb -mfloat-abi=soft` — a generic Cortex-M4 class, explicitly disclosed in the file's own header comment as **not a claim about any specific board's silicon**. No `-mfpu` flag is set (soft float ABI), so the same flags stay valid across Cortex-M4 parts with or without a hardware FPU.

**Deliberately not set:** `-ffreestanding -fno-exceptions -fno-rtti`. Reasoned in the toolchain file's own comment: this Buy's only output is a static library — `ar` archives object files without resolving symbols, so the `throw std::invalid_argument(...)` calls already present in the behavior-frozen rung sources (unchanged by this Buy) do not need their C++ exception runtime satisfied at this stage. A future Buy that links a full `.elf` would need to make that call explicitly — out of this Buy's scope.

**Toolchain actually used for the verified build (§3):** xPack `arm-none-eabi-gcc` **v15.2.1-1.1**, `darwin-arm64` release, downloaded from `https://github.com/xpack-dev-tools/arm-none-eabi-gcc-xpack/releases/download/v15.2.1-1.1/xpack-arm-none-eabi-gcc-15.2.1-1.1-darwin-arm64.tar.gz` — GCC 15.2.1, bundles `libstdc++` headers for `arm-none-eabi/include/c++/15.2.1` and the `thumb/v7e-m/nofp` multilib. This is documented in the README's own install-hint section as one of the recommended full-toolchain options, alongside `brew install --cask gcc-arm-embedded` (official Arm GNU Toolchain) and Debian's `apt-get install gcc-arm-none-eabi`.

**CMake path-resolution note (a real gotcha, disclosed in README):** `--toolchain <path>` and `-DCMAKE_TOOLCHAIN_FILE=<path>` resolve a **relative** path against the `-S` source directory (or fail outright from certain relative forms tried from the repo root) — an absolute path always works. This is documented explicitly in the README to save a future user the same trial-and-error.

---

## 2. Package layout vs IC §1

```text
native/flight_control/
  cmake/toolchains/arm-none-eabi.cmake   # NEW
  CMakeLists.txt                          # gated: host-only targets (Catch2, unit tests, both smokes)
                                           # skipped entirely when JARVIS_FC_CROSS_COMPILING is set
  README.md                               # NEW section: MCU cross-compile commands + toolchain install hint
  include/ src/                            # byte-unchanged (behavior freeze, confirmed §6)
  tests/ smoke/                             # host-only; untouched, not built on the MCU path
```

---

## 3. Build + verification results (IC §0 decision 3, §4 T2)

**Host path reconfirmed unaffected first:**

```bash
$ cmake -S native/flight_control -B build/flight_control
-- Configuring done
$ cmake --build build/flight_control
[100%] Built target fc_unit_tests   (+ jarvis_fc, fc_closed_loop_smoke, fc_esc_pwm_smoke)
$ cd build/flight_control && ctest
100% tests passed out of 28
```

**MCU cross-build (xPack toolchain on PATH):**

```bash
$ export PATH="<xpack-arm-none-eabi-gcc-15.2.1-1.1>/bin:$PATH"
$ cmake -S native/flight_control -B build/flight_control_mcu \
    --toolchain "$(pwd)/native/flight_control/cmake/toolchains/arm-none-eabi.cmake"
-- The CXX compiler identification is GNU 15.2.1
-- Configuring done
-- Generating done

$ cmake --build build/flight_control_mcu --target jarvis_fc
[ 12%] Building CXX object CMakeFiles/jarvis_fc.dir/src/filter.cpp.obj
[ 25%] Building CXX object CMakeFiles/jarvis_fc.dir/src/attitude.cpp.obj
[ 37%] Building CXX object CMakeFiles/jarvis_fc.dir/src/controller.cpp.obj
[ 50%] Building CXX object CMakeFiles/jarvis_fc.dir/src/rate_torque.cpp.obj
[ 62%] Building CXX object CMakeFiles/jarvis_fc.dir/src/mixer.cpp.obj
[ 75%] Building CXX object CMakeFiles/jarvis_fc.dir/src/plant.cpp.obj
[ 87%] Building CXX object CMakeFiles/jarvis_fc.dir/src/esc.cpp.obj
[100%] Linking CXX static library libjarvis_fc.a
[100%] Built target jarvis_fc
```

**Artifact verified as genuine ARM (not a native macOS archive):**

```bash
$ arm-none-eabi-objdump -a build/flight_control_mcu/libjarvis_fc.a
filter.cpp.obj:     file format elf32-littlearm
...
$ arm-none-eabi-ar t build/flight_control_mcu/libjarvis_fc.a
filter.cpp.obj
attitude.cpp.obj
controller.cpp.obj
rate_torque.cpp.obj
mixer.cpp.obj
plant.cpp.obj
esc.cpp.obj

$ arm-none-eabi-objdump -f build/flight_control_mcu/CMakeFiles/jarvis_fc.dir/src/filter.cpp.obj
file format elf32-littlearm
architecture: armv7e-m, flags 0x00000011:
HAS_RELOC, HAS_SYMS
```

`armv7e-m` is the ARM architecture family Cortex-M4 implements — confirming the `-mcpu=cortex-m4 -mthumb` flags reached the compiler and produced real target-specific code, not a silently-native fallback. All **7 rung source files** (all six steel rungs plus `plant.cpp`) are present in the archive.

**Failed candidate, disclosed (IC §0 decision 10's own spirit — show the real story):**

```bash
$ arm-none-eabi-g++ -mcpu=cortex-m4 -mthumb -mfloat-abi=soft -c src/filter.cpp ...
fatal error: optional: No such file or directory
```

using the plain `brew install arm-none-eabi-gcc` formula (confirmed via its own `-v` header-search-path dump: only GCC's internal include dirs, no `arm-none-eabi/include/c++/...` path at all — this formula ships no newlib/libstdc++).

---

## 4. Tests (IC §4)

| ID | Check | Result |
|---|---|---|
| T1 | Toolchain file sets `CMAKE_SYSTEM_NAME`/compilers for `arm-none-eabi` + locked CPU flags | ✅ `test_t1_toolchain_file_sets_arm_none_eabi_system_and_locked_cpu_flags` |
| T2 | When toolchain present: MCU configure+build produces static archive; artifact is ARM | ✅ §3 — real build + `objdump` proof; `test_t2_t3_mcu_cross_build_produces_arm_archive_or_skips_with_hint` (9/9 passed with xPack toolchain on PATH) |
| T3 | When toolchain absent (or incomplete): pytest skips with install hint | ✅ verified both ways — with xPack toolchain: full build succeeds (9 passed); with only the bare Homebrew formula: `test_t2_t3_...` degrades to a skip with a specific hint quoting the real compiler error (8 passed, 1 skipped) — see §5 |
| T4 | Host build + `ctest` (unit + both smokes) still green; tip class ~15°→~0.25° | ✅ §3 — 28/28; `fc_closed_loop_smoke` re-verified `PASS` |
| T5 | No GPIO/DShot/flash/OpenOCD product scripts; no vendor BSP required | ✅ grep clean on toolchain file + CMakeLists.txt (comment-only honesty mentions) |
| T6 | No `.cpp` under `src/jarvis/`; craft isolation | ✅ `find src/jarvis -name "*.cpp" -o -name "*.hpp" -o -name CMakeLists.txt` empty; no references to `arm-none-eabi`/`flight_control_mcu` under `src/jarvis/core`/`adapters` |
| T7 | Report lists toolchain pin/flags, artifact path, honesty statement, skip story | ✅ §1, §3, §5 |
| T8 | Python full suite green @ `0.5.14` | ✅ **3389 passed, 1 skipped** (was 3380 — exact +9 delta; the pre-existing unrelated skip carries forward) |
| T9 | Docs honest; no premature `v0.5.14` tag | ✅ §8 below |

New Python test module `tests/test_fase_c_cpp_mcu_cross_compile_b1.py` — **9 tests**, all passing:

```text
test_t1_toolchain_file_sets_arm_none_eabi_system_and_locked_cpu_flags PASSED
test_cmake_gates_host_only_targets_behind_cross_compiling_flag PASSED
test_t2_t3_mcu_cross_build_produces_arm_archive_or_skips_with_hint PASSED
test_t4_host_build_and_ctest_still_green_if_built PASSED
test_t5_no_gpio_flash_openocd_or_vendor_bsp_symbols_in_toolchain_file PASSED
test_t6_no_cpp_under_src_jarvis_and_craft_isolation PASSED
test_default_safety_and_autonomy_submit_still_reject PASSED
test_capability_registry_default_still_empty PASSED
test_t8_pyproject_version_is_0_5_14 PASSED
```

**Wrapper choice, documented (IC §4's own "document choice" requirement, extended for this Buy's real complication):** unlike C13-C15's wrappers (which only *re-run* an already-built artifact), this wrapper actively **drives** the MCU configure+build itself — there is no pre-existing executable to just invoke, the output is a library. It checks `shutil.which("arm-none-eabi-g++")`; if absent, skips with an install hint (T3, "toolchain absent" case). If present, it runs the real `cmake --toolchain ...` + `cmake --build ... --target jarvis_fc` and, **only if either step fails**, treats that as the "toolchain incomplete" case and skips with a message quoting the real compiler/linker error and recommending a full toolchain distribution — this was the actual situation hit on the implementer's own machine with the bare Homebrew formula, and is the more honest and robust design than a hard failure that would break the suite for anyone whose `arm-none-eabi-g++` happens to be incomplete. When the build genuinely succeeds, it asserts `libjarvis_fc.a` exists and (when `arm-none-eabi-objdump` is also present) that its output actually says `elf32-littlearm`.

**T8 (full suite):** `pytest -q` — **3389 passed, 1 skipped** (baseline before this Buy was 3380 passed, 1 skipped; delta is exactly the 9 new tests, no other file's pass/fail count moved; the one skip is unrelated/pre-existing).

Twenty-one pre-existing test files hardcoded the prior checkpoint version string (`"0.5.13"`) as a version-pin assertion, including C13's, C14's, and C15's own wrapper modules. Since this IC explicitly requires the `0.5.14` bump (§0 decision 12), all twenty-one were re-pinned to `"0.5.14"`:

- `tests/test_bom_sku_resolved_cameras_b1.py`
- `tests/test_catalog_camera_power_w_b1.py`
- `tests/test_fase_c_attitude_controller_rung_b1.py`
- `tests/test_fase_c_attitude_estimation_rung_b1.py`
- `tests/test_fase_c_autonomy_surface_b1.py`
- `tests/test_fase_c_capability_registry_scaffold_b1.py`
- `tests/test_fase_c_controlled_flight_sim_tip_b1.py`
- `tests/test_fase_c_cpp_esc_pwm_stub_b1.py`
- `tests/test_fase_c_cpp_flight_control_scaffold_b1.py`
- `tests/test_fase_c_cpp_unit_tests_b1.py`
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
| "Firmware verified on hardware" | ✅ absent | README/report explicitly: "a compile-time proof, not a hardware proof: no MCU has run this code" |
| Flash CI as acceptance | ✅ absent | No OpenOCD/J-Link script anywhere; the toolchain file's own header says "no flashing" |
| Vendor Cube/RTOS required | ✅ absent | Only the cross-compiler + our own sources; grep-confirmed no STM32Cube/CMSIS/ChibiOS/FreeRTOS/PX4/ArduPilot token in code (T5) |
| GPIO/PWM/DShot drivers | ✅ absent | Grep-confirmed (T5); the MCU library is the same behavior-frozen sources — none of them ever had GPIO code |
| Breaking host default path | ✅ absent | Host `ctest` re-verified 28/28 green after this Buy's CMakeLists.txt gating change (§3, T4) |

**"One front" discipline (process lock after C6):** this Buy stayed exactly within the MCU cross-compile scaffold scope. No Safety-real, ELRS, craft↔FS wiring, or GPIO product path were touched or opened. The `--cask gcc-arm-embedded` sudo-installer path was attempted and abandoned (not forced past, not worked around with elevated privileges) when it required interactive credentials this session doesn't have — the xPack alternative was used instead, itself one of the two toolchains this Buy's own README recommends.

---

## 6. Integration rules (IC §3) — confirmed unchanged

- Host Catch2 + smokes — remain, still green on the host build (§3, T4).
- Rung sources — math frozen; **no** `#ifdef` was introduced into any rung source; all gating lives in `CMakeLists.txt` via the `JARVIS_FC_CROSS_COMPILING` flag, matching the IC's own "prefer CMake gating" note.
- Python suite — untouched except the 21 version re-pins and the new thin MCU wrapper module.
- Craft / `RejectAllSafetyGate` / autonomy — untouched (confirmed via the wrapper's own reject/registry checks).
- Safety / link / GPIO drivers — out of scope, not touched.

---

## 7. Files changed

**New:**
- `native/flight_control/cmake/toolchains/arm-none-eabi.cmake`
- `tests/test_fase_c_cpp_mcu_cross_compile_b1.py`
- `.jes/artifacts/implementation_report_fase_c_cpp_mcu_cross_compile_b1.md` (this file)

**Modified:**
- `pyproject.toml` — version `0.5.13` → `0.5.14`
- `native/flight_control/CMakeLists.txt` — host-only targets (Catch2 FetchContent, `fc_unit_tests`, `fc_closed_loop_smoke`, `fc_esc_pwm_smoke`, `enable_testing`/`add_test`) wrapped in `if(NOT JARVIS_FC_CROSS_COMPILING) ... endif()`; `jarvis_fc` itself stays outside the gate (built on both paths)
- `native/flight_control/README.md` — new "Cross-compile for MCU (C16)" section: install hints, exact commands, the relative-path gotcha, artifact verification command, layout diagram updated
- `docs/ARCHITECTURE.md`, `docs/PLATFORM_CAPABILITY_VISION.md`, `docs/IMPLEMENTATION_TASKS.md`, `README.md` — C16 sections (see §8)
- 21 test files — re-pinned stale `0.5.13` version-checkpoint assertions to `0.5.14`

**Not touched (confirmed):** `orchestrator.py`, Board (`ui/spatial-board/`), `library/`, `src/jarvis/capabilities/*`, `src/jarvis/flight_software/autonomy/*`, all `native/flight_control/{include,src}/**` (byte-unchanged — behavior freeze), `native/flight_control/{tests,smoke}/**` (byte-unchanged), `.jes/state/engineering_state.json`.

**Local, non-repo state from this session (disclosed, not a repo change):** the xPack toolchain was downloaded and extracted into this session's scratchpad directory (outside the repo, gitignored `build/` dirs); the Homebrew `arm-none-eabi-gcc`/`arm-none-eabi-binutils` formulae were installed on the host machine via `brew install` (not removed — the wrapper is designed to degrade gracefully around this bare, incomplete formula, per §0/§5, so no cleanup was required for correctness).

---

## 8. Docs honesty confirmation (IC §6, §4 T9)

- README header banner: "v0.5.13 tagged tip · working tree ahead toward v0.5.14 (C16 ... awaiting Cursor review + Engineer ACCEPT)" — no premature tag claim.
- `docs/IMPLEMENTATION_TASKS.md` PRIORIDAD banner and C16 row: "landed — awaiting Cursor review + ★ ACCEPT ... tag not on git yet".
- `docs/ARCHITECTURE.md` C16 paragraph: "aterrizado, pendiente de review de Cursor + ACCEPT del Engineer — sin tag `v0.5.14` todavía".
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 C16 block: "landed — awaiting Cursor review + Engineer ACCEPT — no tag `v0.5.14` yet".
- Confirmed via `git tag -l | sort -V`: latest Fase C tag is `v0.5.13` (C15); no `v0.5.14` tag exists.
- Explicit **exists vs. impossible** statement, present in README/ARCHITECTURE/PLATFORM_CAPABILITY_VISION: **exists** = a documented cross-compile recipe producing a real ARM `.a` when a complete toolchain is installed (verified in this report with `objdump` proof); **impossible** = a board running this code, motors spinning, real Safety, "firmware verified on hardware."

---

## 9. Residual — what comes next

Per this IC's own §8 handoff: still one front at a time, Engineer-prioritized — real Safety, a real link, or craft↔FS wiring; a later, separately-scoped Buy for actual board bring-up/flash (with its own linker script, startup code, and explicit hardware-verification claims) if ever prioritized. Not decided here.

**Disclosed housekeeping note for the Engineer/Cursor:** the plain Homebrew `arm-none-eabi-gcc` formula is now on this dev machine's PATH but cannot compile this tree's C++ sources (no libstdc++) — anyone reproducing this Buy's MCU build on the same or a similar machine should install a full toolchain (xPack release or `--cask gcc-arm-embedded`) rather than assume the bare formula suffices; the pytest wrapper handles this gracefully (skip, not failure) either way.

---

## 10. Acceptance self-check against IC §7

- T1–T9: ✅ (see §4 table)
- Host green: ✅ (§3 — 28/28 `ctest`)
- MCU `.a` when toolchain present, with implementer evidence: ✅ (§3 — real build + `objdump` `elf32-littlearm` proof)
- No BSP/flash/GPIO: ✅ (§5)
- `0.5.14`: ✅
- Not FAIL conditions: host not broken (§3, T4) · no vendor SDK required (§1, §5) · flash not claimed as done (§0, §5) · no GPIO drivers shipped (§5) · no "runs on FC" claim anywhere (§8)
