# `native/flight_control/` — Fase C C++ scaffold (C13)

**What this is:** a **host-only** C++17 port of the Python
`flight_software/flight_control/` wooden ladder (filter → attitude
estimator → PD controller → rate→torque bridge → mixer → toy plant),
built with CMake. It runs the same closed-loop tip criterion as Python's
C11/C12 smoke: a toy quadrotor plant is seeded tilted, and the loop must
recover.

**What this is not:** MCU firmware, a board bring-up, anything that
touches GPIO/PWM/DShot/serial/sockets, PX4/ArduPilot, or a claim that any
real vehicle flies. See `.jes/artifacts/implementation_report_fase_c_cpp_flight_control_scaffold_b1.md`
for the full honesty statement.

## Build (host, desktop)

Requires CMake ≥ 3.16 and a C++17 compiler (tested with Apple Clang 21 /
`clang++`; any recent `g++` should also work).

```bash
cmake -S native/flight_control -B build/flight_control
cmake --build build/flight_control
```

## Run the tip smoke

```bash
./build/flight_control/fc_closed_loop_smoke
```

Prints the initial and final true tilt error (degrees) and exits `0` on
recovery, nonzero on failure.

## Run the ESC/PWM stub smoke (C14)

```bash
./build/flight_control/fc_esc_pwm_smoke
```

Prints one `ok`/`FAIL` line per assertion (force→µs endpoints and linear
midpoint, 4-pulse/`pwm_us` shape, invalid-bounds rejection, disarmed
record-but-refuse, armed apply) and exits `0` only if every assertion
held. Steel-ladder parity for the Python C10 stub — no GPIO, no PWM
hardware write, no claim any motor spins.

Both smoke binaries are also runnable via CTest.

## Run the unit-test suite (C15)

A real test framework — **Catch2 v3, pinned to release tag `v3.7.1`**
(commit `fa43b77429ba76c462b1898d6cd2f2d7a9416b14`) — is fetched via CMake
`FetchContent` the first time you configure this tree. That first
configure needs network once, to clone the pinned tag; after that, the
sources live under `build/flight_control/_deps/catch2-src` and every
later configure/build/`ctest` cycle needs **no network** (the same build
directory can be reused offline).

```bash
./build/flight_control/fc_unit_tests          # run directly, verbose with -s
# or, together with both smokes, individually discovered:
cd build/flight_control && ctest --output-on-failure
```

`fc_unit_tests` has **≥1 `TEST_CASE` per steel rung** (filter, attitude,
controller, rate_torque, mixer, esc) — 26 cases / \~494 assertions as of
C15. This is a **behavior-freeze** Buy: it adds coverage, it does not
change `filter.cpp`…`esc.cpp`/`plant.cpp`/`quat_math.hpp` (confirmed
`git diff`-clean on all of them in the C15 report). It is **not** MCU
verification, not "production-hardened," not a certification of any kind
— a host desktop unit-test run, nothing more.

## Cross-compile for MCU (C16) — additive, host stays default

**What this is:** an ARM bare-metal (`arm-none-eabi`, generic Cortex-M4,
`-mcpu=cortex-m4 -mthumb -mfloat-abi=soft`) cross-compile of **only the
`jarvis_fc` static library** — a compile-time proof that the same
behavior-frozen steel-ladder sources build freestanding for this
instruction set. **What this is not:** flashing any board, a vendor SDK/BSP (no
STM32Cube/CMSIS device pack/ChibiOS/FreeRTOS/PX4/ArduPilot), GPIO/PWM/
DShot, or a claim that any firmware "runs on a flight controller." The
host build above remains the default path and is unaffected — this is
purely additive. (C18, below, adds a linked freestanding `.elf` on the
same toolchain — still no flash, no BSP.)

**Install a toolchain first.** A plain `arm-none-eabi-gcc` package is
sometimes just a bare compiler with **no bundled `newlib`/`libstdc++`** —
compiling will fail with `fatal error: optional: No such file or
directory` if so (this was hit and disclosed while building this Buy: the
Homebrew `arm-none-eabi-gcc` formula alone lacks a C++ standard library).
Use a **full** toolchain distribution instead, e.g.:

```bash
brew install --cask gcc-arm-embedded     # macOS — official Arm GNU Toolchain (needs sudo)
# or download an xPack arm-none-eabi-gcc release for your platform:
# https://github.com/xpack-dev-tools/arm-none-eabi-gcc-xpack/releases
# Debian/Ubuntu:
apt-get install gcc-arm-none-eabi
```

**Configure + build:**

```bash
cmake -S native/flight_control -B build/flight_control_mcu \
  --toolchain native/flight_control/cmake/toolchains/arm-none-eabi.cmake
cmake --build build/flight_control_mcu --target jarvis_fc
```

(Pass the toolchain path either relative to `-S`'s source directory, as
above, or as an absolute path — a path relative to your current shell
directory is **not** what CMake resolves it against, and will fail with
"Could not find toolchain file.")

**Verify the artifact is genuinely ARM:**

```bash
arm-none-eabi-objdump -a build/flight_control_mcu/libjarvis_fc.a
# expect: file format elf32-littlearm, architecture: armv7e-m
```

The MCU configure automatically **gates off** Catch2/the unit-test binary
and both smoke executables (IC C16 §0 decision 7 — no Catch2 on a
library-only MCU target); only `jarvis_fc` itself is built. No network is
needed for the MCU configure/build (unlike the host build's one-time
Catch2 fetch).

## Freestanding MCU `.elf` (C18) — same toolchain, linked this time

**What this is:** a linked, inspectable, freestanding ARM ELF —
`fc_mcu_stub.elf` — built from OUR OWN generic Cortex-M4 linker script
(`mcu/linker_cortex_m4.ld`) + minimal startup (`mcu/startup_cortex_m4.c`:
vector table + `Reset_Handler`) + newlib syscall stubs
(`mcu/syscalls_stub.c`) + a thin entry point (`mcu/stub_main.cpp`) that
calls real `jarvis_fc` code (`ImuLowPassFilter::filter_sample`,
`encode_motor_forces`) once before idling forever. **What this is not:**
flashed to any board, a claim that this image boots on real hardware, a
vendor BSP/SDK, or GPIO/UART/any real I/O — `syscalls_stub.c`'s
`_write`/`_read`/etc. are no-op/error stubs, not semihosting.

**Memory map (fictional, disclosed):** `FLASH` at `0x00000000` / `RAM` at
`0x20000000` — the ARM-architected *generic* Cortex-M Code/SRAM regions
(not a vendor's remapped boot address like the `0x08000000` many real
boards use), 256 KiB / 64 KiB, a round illustrative size not sourced from
any real part's datasheet.

**C++ runtime choice (IC §0 decision 8, option (a)):** the rung sources'
existing `throw std::invalid_argument(...)` calls are left exactly as
they are — this build links normally against the toolchain's own
libstdc++/newlib and resolves the runtime via `mcu/syscalls_stub.c`'s own
stubs (`_sbrk`, `_write`, `_exit`, …), not by disabling exceptions or
touching any rung API.

**Build (reuses the exact same toolchain file as C16):**

```bash
cmake -S native/flight_control -B build/flight_control_mcu \
  --toolchain native/flight_control/cmake/toolchains/arm-none-eabi.cmake
cmake --build build/flight_control_mcu --target fc_mcu_stub.elf
```

**Inspect it:**

```bash
arm-none-eabi-readelf -h build/flight_control_mcu/fc_mcu_stub.elf
# expect: Machine: ARM, Type: EXEC, an Entry point address, soft-float ABI flag

arm-none-eabi-objdump -f build/flight_control_mcu/fc_mcu_stub.elf
# expect: file format elf32-littlearm

arm-none-eabi-nm build/flight_control_mcu/fc_mcu_stub.elf | grep ImuLowPassFilter
# expect: real jarvis::fc::ImuLowPassFilter symbols, defined (T), not just referenced
```

`jarvis_fc` (the `.a`, C16) still builds alongside the `.elf` in the same
MCU configure — this target is additive, not a replacement.

## Layout

```text
native/flight_control/
  CMakeLists.txt
  cmake/toolchains/arm-none-eabi.cmake   # C16 — MCU cross-compile toolchain, reused unchanged by C18
  include/jarvis/fc/    # public headers — types, filter, attitude,
                         # controller, rate_torque, mixer, plant, esc,
                         # loop (C24 — named tick, see below),
                         # rc_setpoint (C25 — RC units -> tick args,
                         # see below),
                         # quat_math (shared helper, see its own header
                         # comment for the documented deviation from
                         # Python's per-module-private-helper style)
  src/                   # implementations
  smoke/closed_loop_smoke.cpp   # the C13 tip harness — now calls ControlLoop::step (C24)
  smoke/esc_pwm_smoke.cpp       # the C14 ESC/PWM stub harness
  tests/                         # C15 — Catch2 per-rung unit cases
    test_filter.cpp
    test_attitude.cpp
    test_controller.cpp
    test_rate_torque.cpp
    test_mixer.cpp
    test_esc.cpp
    test_loop.cpp                # C24 — ControlLoop::step cases
    test_rc_setpoint.cpp         # C25 — map_rc_to_loop_inputs cases
  mcu/                            # NEW (C18) — freestanding linked .elf, host-inspectable only
    linker_cortex_m4.ld
    startup_cortex_m4.c
    syscalls_stub.c
    stub_main.cpp
```

`esc.hpp`/`esc.cpp` (C14) closes the steel-ladder's own sixth rung —
force→PWM-µs encoding plus an in-memory `SimulatedEscSink`, mirroring
Python C10. Kept as a separate smoke target from the closed-loop tip
(IC C14 §0 "Defaults locked") — the tip still steps on `MotorForceCommand`
directly and never needs PWM encoding to close the loop.

`esc.hpp`/`esc.cpp` extended again for C26 (★ ACCEPT CLOSED @ tag `v0.5.24`): `EscOutput` is a new abstract base (virtual destructor,
`apply_forces`/`arm`/`disarm`/`armed` as pure virtuals) naming the port
C10/C14 already implemented as a concrete sink. `SimulatedEscSink`
public-inherits it; `apply_forces` is a thin `encode_motor_forces` +
`apply` wrapper — the diff in `esc.cpp` is purely additive (four lines
added, zero removed/changed). `mixer.hpp`/`mixer.cpp` and every other
rung file are untouched. `loop.hpp`/`loop.cpp` still never call
`apply`/`apply_forces` — `EscOutput HAL != pin != motors != DShot`.

`loop.hpp`/`loop.cpp` (C24, ★ ACCEPT CLOSED @ tag `v0.5.22`) names the
one-cycle control tick this tree already ran inlined:
`jarvis::fc::ControlLoop::step(sample, setpoint, collective) ->
ControlTickResult` — `filter_sample -> estimator.update ->
controller.compute -> bridge.convert -> mixer.mix`, same order, same
existing rung classes, no new math. `step` never calls the plant, reads a
real HAL, or writes a pin — `fc_closed_loop_smoke` still owns the
`plant.step(...)` call in its own loop, unchanged in role. `mcu/stub_main.cpp`
still has no `ControlLoop`/`step(` — this stays a host-callable tick, not
an MCU ISR.

`rc_setpoint.hpp`/`rc_setpoint.cpp` (C25, ★ ACCEPT CLOSED @ tag `v0.5.23`) converts already-decoded RC channel units into the two arguments
`ControlLoop::step` already accepts: `map_rc_to_loop_inputs(channels,
t_s) -> RcLoopInputs`. `channels` is a plain `std::vector<int>` — this
tree carries no decoded-channels type of its own, and the constants
(`kRcChMin`/`kRcChMid`/`kRcChMax` = `172`/`992`/`1811`) are named
without any radio-protocol prefix on purpose: the C21-C23 lock of
**zero radio-link-protocol mentions anywhere under `native/`**, even in
comments, stays intact for this Buy too. Only roll/pitch/throttle
(indices 0/1/2) are read; a yaw channel may be present but is never used
(no magnetometer in this tree). `loop.hpp`/`loop.cpp` are untouched by
this file.
