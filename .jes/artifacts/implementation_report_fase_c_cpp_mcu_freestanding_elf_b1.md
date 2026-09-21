# Implementation Report — Fase C MCU freestanding `.elf` (`B1-fase-c-cpp-mcu-freestanding-elf`)

**IC:** [`implementation_contract_fase_c_cpp_mcu_freestanding_elf_b1.md`](implementation_contract_fase_c_cpp_mcu_freestanding_elf_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-21
**Status:** ★ ACCEPT CLOSED @ **`v0.5.16`**. See [review](implementation_review_fase_c_cpp_mcu_freestanding_elf_b1.md).

---

## 0. Read this first — from archive to linked image, honesty summary

C16 proved the steel-ladder sources *compile* freestanding for `arm-none-eabi` (a `.a` archive, symbols unresolved). This Buy proves they *link* into one coherent, inspectable ARM executable: **`fc_mcu_stub.elf`**, built from generic startup/linker/syscall-stub code that is entirely ours (no vendor BSP) plus a thin entry point that calls real `jarvis_fc` symbols. It is **not** flashed to any board, does not claim to boot on real hardware, and touches no GPIO/PWM/DShot/UART.

**A real toolchain requirement surfaced and was resolved cleanly:** linking (not just compiling) `.c` startup/syscall-stub sources required enabling the C language in `CMakeLists.txt`'s `project()` call — the first build attempt silently skipped `mcu/startup_cortex_m4.c`/`mcu/syscalls_stub.c` (CXX-only project) and the linker warned `cannot find entry symbol Reset_Handler; defaulting to 00000000`. Fixed by changing `project(jarvis_flight_control_native CXX)` to `project(jarvis_flight_control_native C CXX)`; re-verified the warning is gone and the entry point is correct (§3). This is disclosed here, not hidden — and the new pytest wrapper (§5) explicitly asserts the warning string never reappears.

**Memory map, disclosed as fictional (IC §0 decision 5):** `FLASH` at `0x00000000` / `RAM` at `0x20000000` — the ARM-architected generic Cortex-M Code/SRAM regions (not any vendor's remapped boot address, e.g. the `0x08000000` many real boards use for FLASH). 256 KiB / 64 KiB is a round illustrative size, not sourced from any real part's datasheet.

**C++ runtime, option (a) chosen (IC §0 decision 8):** the rung sources' `throw std::invalid_argument(...)` calls are untouched — this build links normally against the toolchain's own libstdc++/newlib and resolves the runtime via our own `mcu/syscalls_stub.c` (`_sbrk`, `_write`, `_exit`, …), never by disabling exceptions or rewriting any rung API.

---

## 1. Package layout vs IC §1

```text
native/flight_control/
  mcu/                           # NEW
    linker_cortex_m4.ld           # generic FLASH/RAM (fictional, disclosed)
    startup_cortex_m4.c            # 16-entry ARMv7-M vector table + Reset_Handler
    syscalls_stub.c                 # minimal newlib syscall stubs (ours, no semihosting)
    stub_main.cpp                    # calls real jarvis_fc symbols, then idles
  cmake/toolchains/arm-none-eabi.cmake   # C16 toolchain, REUSED unchanged (CPU/ABI flags identical)
  CMakeLists.txt                          # + C language enabled; + fc_mcu_stub.elf target (gated)
  README.md                                # + "Freestanding MCU .elf (C18)" section
  include/ src/                             # byte-unchanged (behavior freeze, confirmed §6)
```

Matches the IC's normative layout (§1) exactly — `mcu/` is the preferred path, all four files present, CMake target name `fc_mcu_stub.elf` documented here and in the README/CMakeLists comments.

---

## 2. Toolchain reuse + memory map + runtime strategy (IC §0 decisions 4, 5, 8)

**Toolchain file** (`cmake/toolchains/arm-none-eabi.cmake`) is the **same file C16 shipped**, with its header comment extended to describe the new `.elf` capability (no CPU/ABI flag changed — still `-mcpu=cortex-m4 -mthumb -mfloat-abi=soft`, per IC §0 decision 4's "do not invent a second CPU class").

**Linker script** (`mcu/linker_cortex_m4.ld`): `MEMORY { FLASH (rx) : ORIGIN = 0x00000000, LENGTH = 256K; RAM (rwx) : ORIGIN = 0x20000000, LENGTH = 64K }`, standard `.isr_vector`/`.text`/`.rodata`/`.ARM.extab`/`.ARM.exidx`/`.data`/`.bss` sections, `_estack` at top of RAM, `ENTRY(Reset_Handler)`, `.isr_vector` wrapped in `KEEP(...)` so `--gc-sections` cannot strip it.

**Startup** (`mcu/startup_cortex_m4.c`): a genuine 16-entry ARMv7-M system-exception vector table (word 0 = `_estack`, word 1 = `Reset_Handler`, remaining system exceptions point at a shared `Default_Handler` infinite-loop stub — no vendor external-IRQ layout modeled). `Reset_Handler` copies `.data` from its FLASH load address to RAM, zeroes `.bss`, then calls `main()`. No `__libc_init_array()` call — confirmed (by inspection of every rung `.cpp` file) that `jarvis_fc` has no global C++ objects with non-trivial (runtime) constructors, so static-init is unnecessary for this stub's own code path.

**Syscall stubs** (`mcu/syscalls_stub.c`): `_sbrk` (bump allocator between the linker's `end` symbol and `_estack`), plus `_write`/`_read`/`_close`/`_lseek`/`_fstat`/`_isatty`/`_exit`/`_kill`/`_getpid` as no-op/error stubs — satisfies newlib's link-time symbol requirements (pulled in transitively by the C++ exception runtime's allocator) without semihosting or any real I/O.

**Entry** (`mcu/stub_main.cpp`): constructs `ImuLowPassFilter` and calls `filter_sample` once, then builds a `MotorForceCommand` and calls `encode_motor_forces` once (both results stored in `volatile` globals so the calls cannot be optimized away), then idles in `while (true) {}` forever — matching IC §0 decision 7's minimum ("construct `ImuLowPassFilter`... or `encode_motor_forces`..." — this Buy does both).

---

## 3. Build + verification results (IC §4 T1–T3)

**A real problem hit and fixed, disclosed (§0):**

```text
[first attempt]
[ 90%] Building CXX object CMakeFiles/fc_mcu_stub.elf.dir/mcu/stub_main.cpp.obj
[100%] Linking CXX executable fc_mcu_stub.elf
.../arm-none-eabi/bin/ld: warning: cannot find entry symbol Reset_Handler; defaulting to 00000000
[100%] Built target fc_mcu_stub.elf
```

`mcu/startup_cortex_m4.c` and `mcu/syscalls_stub.c` were silently never compiled — `project(jarvis_flight_control_native CXX)` never enabled the C language. Fixed by changing to `project(jarvis_flight_control_native C CXX)` (+ `CMAKE_C_STANDARD 11`).

**After the fix — clean link, host reconfirmed unaffected first:**

```bash
$ cmake -S native/flight_control -B build/flight_control && cmake --build build/flight_control
$ cd build/flight_control && ctest
100% tests passed out of 28

$ export PATH="<xpack-arm-none-eabi-gcc-15.2.1-1.1>/bin:$PATH"
$ cmake -S native/flight_control -B build/flight_control_mcu \
    --toolchain "$(pwd)/native/flight_control/cmake/toolchains/arm-none-eabi.cmake"
-- The C compiler identification is GNU 15.2.1
-- The CXX compiler identification is GNU 15.2.1
-- Configuring done

$ cmake --build build/flight_control_mcu
[  8%] Building CXX object CMakeFiles/jarvis_fc.dir/src/filter.cpp.obj
...
[ 66%] Built target jarvis_fc
[ 75%] Building C object CMakeFiles/fc_mcu_stub.elf.dir/mcu/startup_cortex_m4.c.obj
[ 83%] Building C object CMakeFiles/fc_mcu_stub.elf.dir/mcu/syscalls_stub.c.obj
[ 91%] Building CXX object CMakeFiles/fc_mcu_stub.elf.dir/mcu/stub_main.cpp.obj
[100%] Linking CXX executable fc_mcu_stub.elf
[100%] Built target fc_mcu_stub.elf
   (no warnings — entry symbol found this time)
```

**T2 — artifact inspected, genuine ARM EXEC image:**

```bash
$ arm-none-eabi-readelf -h build/flight_control_mcu/fc_mcu_stub.elf
  Type:                              EXEC (Executable file)
  Machine:                           ARM
  Entry point address:               0x45
  Flags:                             0x5000200, Version5 EABI, soft-float ABI
  Number of program headers:         4

$ arm-none-eabi-objdump -f build/flight_control_mcu/fc_mcu_stub.elf
file format elf32-littlearm
start address 0x00000045
```

**T3 — real `jarvis_fc` symbols linked in (defined, not just referenced):**

```bash
$ arm-none-eabi-nm build/flight_control_mcu/fc_mcu_stub.elf | grep -iE "ImuLowPassFilter|encode_motor_forces|filter_sample"
00000168 T _ZN6jarvis2fc16ImuLowPassFilter13filter_sampleERKNS0_9ImuSampleE
00000160 T _ZN6jarvis2fc16ImuLowPassFilter5resetEv
000000fc T _ZN6jarvis2fc16ImuLowPassFilterC1Ed
000000fc T _ZN6jarvis2fc16ImuLowPassFilterC2Ed
00000334 T _ZN6jarvis2fc19encode_motor_forcesERKNS0_17MotorForceCommandEdd
```

`T` = defined in the text section (not `U` = undefined) — these are real, linked function bodies, demangling to `jarvis::fc::ImuLowPassFilter::filter_sample`, both constructors, and `jarvis::fc::encode_motor_forces`.

**Section layout / footprint** (`arm-none-eabi-size` / `objdump -h`): `.text` ≈ 79 KiB (fits comfortably in 256 KiB FLASH), `.data`/`.bss` well within 64 KiB RAM, `.data` correctly split VMA (RAM, `0x20000000`) / LMA (FLASH) by the linker script's `AT> FLASH` directive, `.isr_vector` present at 0x40 bytes (16 words × 4 bytes, matching the vector table), `.ARM.extab`/`.ARM.exidx` present (C++ exception unwind tables successfully resolved and placed in FLASH).

Toolchain used: xPack `arm-none-eabi-gcc` v15.2.1-1.1 (darwin-arm64) — same toolchain that produced C16's own verified `.a` build.

---

## 4. Tests (IC §4)

| ID | Check | Result |
|---|---|---|
| T1 | Linker script + startup + stub entry exist under `native/flight_control/` | ✅ `test_t1_linker_startup_and_stub_entry_exist` |
| T2 | When full toolchain present: MCU build produces `.elf`; `objdump`/`readelf` show ARM + entry point | ✅ §3; `test_t2_t3_mcu_elf_links_and_contains_real_jarvis_fc_symbols_or_skips` |
| T3 | ELF links symbols from `jarvis_fc` (nm/objdump evidence) | ✅ §3 — `nm` output; same test as T2 |
| T4 | When toolchain absent/incomplete: pytest skips with install hint | ✅ verified both ways — xPack toolchain: full link succeeds (9/9); bare Homebrew formula only: degrades to skip with reason quoting the real compiler error (8 passed, 1 skipped) |
| T5 | Host `ctest` still green; tip class ~15°→~0.25° | ✅ §3 — 28/28; `test_t5_host_smoke_still_recovers_if_built` |
| T6 | No OpenOCD/flash product scripts; no vendor BSP required; no GPIO drivers | ✅ `test_t6_no_gpio_flash_openocd_or_vendor_bsp_symbols_in_mcu_files` (real C/C++/linker-script comment stripping, not naive substring match — see honesty-test note below) |
| T7 | No `.cpp` under `src/jarvis/` from this Buy; craft isolation | ✅ `test_t7_no_cpp_under_src_jarvis_and_craft_isolation` |
| T8 | Report lists layout, memory-map honesty, runtime link strategy, inspect commands | ✅ §1, §2, §3 |
| T9 | Docs honest; no premature `v0.5.16` tag | ✅ §8 below |
| T10 | Python full suite green @ `0.5.16` | ✅ **3412 passed, 1 skipped** (was 3403 — exact +9 delta) |

New Python test module `tests/test_fase_c_cpp_mcu_freestanding_elf_b1.py` — **9 tests**, all passing:

```text
test_t1_linker_startup_and_stub_entry_exist PASSED
test_cmake_wires_elf_target_gated_on_cross_compiling PASSED
test_t2_t3_mcu_elf_links_and_contains_real_jarvis_fc_symbols_or_skips PASSED
test_t5_host_smoke_still_recovers_if_built PASSED
test_t6_no_gpio_flash_openocd_or_vendor_bsp_symbols_in_mcu_files PASSED
test_t7_no_cpp_under_src_jarvis_and_craft_isolation PASSED
test_default_safety_and_autonomy_submit_still_reject PASSED
test_capability_registry_default_still_empty PASSED
test_t9_pyproject_version_is_0_5_16 PASSED
```

**A false-positive honesty-test bug caught and fixed during this Buy (disclosed, matching the project's established convention):** the first draft of `test_t6_...`'s comment-stripper for `.c`/`.ld` files only handled `/*`/`*/` as whole-line markers, so it failed to strip block comments whose opening line also contained ordinary comment text — it false-failed on `startup_cortex_m4.c`'s own honesty comment ("No GPIO, no peripheral register access..."). Fixed with a proper character-by-character block-comment stripper (`_strip_c_style_comments`), verified against all four `mcu/` files afterward.

**Wrapper choice (IC §4 "document choice", same rationale + honesty as C16's own wrapper):** the wrapper actively drives configure+build itself (no pre-existing artifact to re-run — the point is proving the *link* succeeds); a compiler present but missing libstdc++ degrades to a skip with a specific install hint, verified both ways in this session (9/9 pass with xPack; 8 passed/1 skipped with the bare Homebrew formula alone, in a clean single-shell reproduction after correcting for the fact that `PATH` exports and CMake's cached `CMAKE_CXX_COMPILER` don't reset between separate shell invocations — a testing-methodology note, not a defect in the shipped code).

**T10 (full suite):** `pytest -q` — **3412 passed, 1 skipped** (baseline before this Buy was 3403 passed, 1 skipped; delta is exactly the 9 new tests, no other file's pass/fail count moved; the one skip is unrelated/pre-existing).

Twenty-three pre-existing test files hardcoded the prior checkpoint version string (`"0.5.15"`) as a version-pin assertion. Since this IC explicitly requires the `0.5.16` bump (§0 decision 14), all twenty-three were re-pinned to `"0.5.16"`:

- `tests/test_bom_sku_resolved_cameras_b1.py`
- `tests/test_catalog_camera_power_w_b1.py`
- `tests/test_fase_c_attitude_controller_rung_b1.py`
- `tests/test_fase_c_attitude_estimation_rung_b1.py`
- `tests/test_fase_c_autonomy_surface_b1.py`
- `tests/test_fase_c_capability_registry_scaffold_b1.py`
- `tests/test_fase_c_controlled_flight_sim_tip_b1.py`
- `tests/test_fase_c_cpp_esc_pwm_stub_b1.py`
- `tests/test_fase_c_cpp_flight_control_scaffold_b1.py`
- `tests/test_fase_c_cpp_mcu_cross_compile_b1.py`
- `tests/test_fase_c_cpp_unit_tests_b1.py`
- `tests/test_fase_c_esc_pwm_stub_rung_b1.py`
- `tests/test_fase_c_first_fc_rung_b1.py`
- `tests/test_fase_c_imu_filtering_rung_b1.py`
- `tests/test_fase_c_intent_safety_stub_b1.py`
- `tests/test_fase_c_mixer_rung_b1.py`
- `tests/test_fase_c_radio_dual_role_b1.py`
- `tests/test_fase_c_rate_torque_bridge_b1.py`
- `tests/test_fase_c_safety_real_policy_b1.py`
- `tests/test_geometry_prop_adapter_visor_x_b1.py`
- `tests/test_library_cameras_seed_b1.py`
- `tests/test_mission_power_w_b1.py`
- `tests/test_mission_vtx_identity_b1.py`

---

## 5. Honesty / forbidden confirmation (IC §5)

| Forbidden | Status | Evidence |
|---|---|---|
| "Runs on board X" / flash acceptance | ✅ absent | README/report explicitly: "never flashed... makes no claim that it would run correctly on any specific flight controller board" |
| Vendor Cube/RTOS required | ✅ absent | Only the cross-compiler + our own `mcu/` sources; T6 grep-confirmed no STM32Cube/CMSIS/ChibiOS/FreeRTOS/PX4/ArduPilot token in real code |
| Quiet rung refactors | ✅ absent | `include/`/`src/` byte-unchanged (confirmed — no diff on any rung file this Buy) |
| Breaking host default | ✅ absent | Host `ctest` re-verified 28/28 green after the CMakeLists.txt change (§3, T5) |

**"One front" discipline (process lock after C6):** this Buy stayed exactly within the freestanding MCU `.elf` scope. No flash scripts, GPIO/DShot, ELRS, craft↔FS wiring, Safety policy changes, or vendor BSP were touched or opened.

---

## 6. Integration rules (IC §3) — confirmed unchanged

- C16 `.a` path — kept; still builds first in the same MCU configure, the `.elf` is additive.
- Host Catch2 + smokes — remain green (§3, T5).
- Rung sources — math frozen; zero diff on `include/`/`src/`.
- Safety (C17) / craft / radio — untouched; grep-confirmed no reference to `fc_mcu_stub`/`flight_control_mcu` under `src/jarvis/core`/`adapters`.
- Flash / GPIO / BSP — out of scope, not touched.

---

## 7. Files changed

**New:**
- `native/flight_control/mcu/linker_cortex_m4.ld`
- `native/flight_control/mcu/startup_cortex_m4.c`
- `native/flight_control/mcu/syscalls_stub.c`
- `native/flight_control/mcu/stub_main.cpp`
- `tests/test_fase_c_cpp_mcu_freestanding_elf_b1.py`
- `.jes/artifacts/implementation_report_fase_c_cpp_mcu_freestanding_elf_b1.md` (this file)

**Modified:**
- `pyproject.toml` — version `0.5.15` → `0.5.16`
- `native/flight_control/CMakeLists.txt` — C language enabled alongside CXX; new `fc_mcu_stub.elf` target gated behind `JARVIS_FC_CROSS_COMPILING`
- `native/flight_control/cmake/toolchains/arm-none-eabi.cmake` — header/inline comments extended to describe the new `.elf` capability; **no CPU/ABI flag changed**
- `native/flight_control/README.md` — new "Freestanding MCU `.elf` (C18)" section, layout diagram updated
- `docs/ARCHITECTURE.md`, `docs/PLATFORM_CAPABILITY_VISION.md`, `docs/IMPLEMENTATION_TASKS.md`, `README.md` — C18 sections (see §8)
- 23 test files — re-pinned stale `0.5.15` version-checkpoint assertions to `0.5.16`

**Not touched (confirmed):** `orchestrator.py`, Board (`ui/spatial-board/`), `library/`, `native/flight_control/include/**` and `native/flight_control/src/**` (byte-unchanged — behavior freeze), `native/flight_control/{tests,smoke}/**` (byte-unchanged), `src/jarvis/capabilities/**` (C17's Safety gate untouched), `.jes/state/engineering_state.json`.

---

## 8. Docs honesty confirmation (IC §6, §4 T9)

- README header banner: "v0.5.15 tagged tip · working tree ahead toward v0.5.16 (C18 ... awaiting Cursor review + Engineer ACCEPT)" — no premature tag claim.
- `docs/IMPLEMENTATION_TASKS.md` PRIORIDAD banner and C18 row: "landed — awaiting Cursor review + ★ ACCEPT ... tag not on git yet"; **Parked** blurb updated to move "MCU `.elf`" from parked to this Buy, per IC §6.
- `docs/ARCHITECTURE.md` C18 paragraph: "aterrizado, pendiente de review de Cursor + ACCEPT del Engineer — sin tag `v0.5.16` todavía".
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 C18 block: "landed — awaiting Cursor review + Engineer ACCEPT — no tag `v0.5.16` yet".
- Confirmed via `git tag -l | sort -V`: latest Fase C tag is `v0.5.15` (C17); no `v0.5.16` tag exists.
- Explicit **exists vs. impossible** statement, present in README/ARCHITECTURE/PLATFORM_CAPABILITY_VISION: **exists** = an inspectable freestanding ARM `.elf` linking real `jarvis_fc` code, verified via `readelf`/`objdump`/`nm`; **impossible** = a flashed flight controller, motors spinning, GPIO, "boots on hardware."

---

## 9. Residual — what comes next

Per this IC's own §8 handoff: still one front at a time, Engineer-prioritized — actual board flash/bring-up (a separately-scoped future Buy, with its own real hardware-verification claims if ever attempted), a real link (ELRS), or craft↔FS wiring. Not decided here.

---

## 10. Acceptance self-check against IC §7

- T1–T10: ✅ (see §4 table)
- ELF built with implementer evidence: ✅ (§3 — `readelf`/`objdump`/`nm` transcripts)
- Host green: ✅ (§3 — 28/28 `ctest`)
- No flash/BSP/GPIO: ✅ (§5)
- `0.5.16`: ✅
- Not FAIL conditions: host not broken (§3, T5) · no vendor SDK required (§2, §5) · flash not claimed (§0, §5) · no "runs on FC" claim anywhere (§8) · no silent rung math changes (§6, byte-diff confirmed)
