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
instruction set. **What this is not:** flashing any board, a linked
bootable `.elf`, a vendor SDK/BSP (no STM32Cube/CMSIS device pack/
ChibiOS/FreeRTOS/PX4/ArduPilot), GPIO/PWM/DShot, or a claim that any
firmware "runs on a flight controller." The host build above remains the
default path and is unaffected — this is purely additive.

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

## Layout

```text
native/flight_control/
  CMakeLists.txt
  cmake/toolchains/arm-none-eabi.cmake   # NEW (C16) — MCU cross-compile toolchain
  include/jarvis/fc/    # public headers — types, filter, attitude,
                         # controller, rate_torque, mixer, plant, esc,
                         # quat_math (shared helper, see its own header
                         # comment for the documented deviation from
                         # Python's per-module-private-helper style)
  src/                   # implementations
  smoke/closed_loop_smoke.cpp   # the C13 tip harness
  smoke/esc_pwm_smoke.cpp       # the C14 ESC/PWM stub harness
  tests/                         # NEW (C15) — Catch2 per-rung unit cases
    test_filter.cpp
    test_attitude.cpp
    test_controller.cpp
    test_rate_torque.cpp
    test_mixer.cpp
    test_esc.cpp
```

`esc.hpp`/`esc.cpp` (C14) closes the steel-ladder's own sixth rung —
force→PWM-µs encoding plus an in-memory `SimulatedEscSink`, mirroring
Python C10. Kept as a separate smoke target from the closed-loop tip
(IC C14 §0 "Defaults locked") — the tip still steps on `MotorForceCommand`
directly and never needs PWM encoding to close the loop.
