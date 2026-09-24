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
a vendor BSP/SDK, or GPIO/UART/any real I/O beyond the single cited
status-LED pin C30 adds below — `syscalls_stub.c`'s `_write`/`_read`/
etc. are no-op/error stubs, not semihosting.

**C30 update (`B1-fase-c-mcu-flash-observable`, package `0.5.28`, not yet
tagged):** as of C18 through C29, this image was never flashed and its
idle loop was an empty `while (true)`. **Both of those changed this
Buy** — see "Flash it: USB DFU (C30)" below for the procedure, and
"`hello_led.c`: the first visible signal (C30)" under Layout for the
LED toggle itself. `flashed LED blink != flying != DShot != USART live
!= Betaflight HGLRCF405V2` — flashing this still does not make any real
vehicle fly, does not touch a motor pin, and does not claim to be the
board's own Betaflight target.

**Memory map (cited, C29, ★ ACCEPT CLOSED @ tag `v0.5.27`):** `FLASH`
1024K at `0x08000000` / `RAM` 128K at `0x20000000` (SRAM1+SRAM2
contiguous) — cited from **ST RM0090 Table 3** (STM32F405xx/07xx,
"Memory map") because the desk hardware's own FC manual (HGLRC F460 6S
V1 stack, FC SKU HGLRC F405 8S V1) names its MCU line as STM32F405.
CCM RAM (`0x10000000`, 64 KiB per RM0090) is deliberately **not**
included in this `MEMORY` block — folding it into a flat RAM region
would be its own undisclosed simplification. **Cited != flashed != boots
on this stack != Betaflight HGLRCF405V2** — this remains a compile/link-
time fact about which numbers the linker script uses, not a claim about
the HGLRC stack itself; no OpenOCD/J-Link path exists anywhere in this
repo, and no vendor SDK/BSP (STM32Cube, CMSIS device pack) was pulled in
to derive these numbers — see `mcu/linker_cortex_m4.ld`'s own header
comment for the full citation and disclosed residual (order-code suffix
unknown; re-cite if a teardown ever shows a different ST part). Before
C29, this map was the ARM-architected *generic* Cortex-M Code/SRAM
regions (`0x00000000` / `0x20000000`, 256 KiB / 64 KiB) — an explicitly
fictional, round illustrative size not sourced from any real part.

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

## Flash it: USB DFU (C30)

**Read this whole section before plugging anything in.**

**What this is:** flashing `fc_mcu_stub.bin` onto the desk hardware
(HGLRC F460 6S V1 stack / FC SKU HGLRC F405 8S V1 / MCU STM32F405) via
the chip's own built-in USB DFU bootloader — no OpenOCD, no J-Link, no
vendor programmer required. **What this is not:** ExpressLRS, DShot,
USART, Betaflight, or a claim any real vehicle flies. The only visible
effect after flashing is the onboard status LED toggling.

**⚠️ Props off. Battery disconnected during DFU.** This is a real,
physical flight controller. Remove propellers before touching this
procedure at all, and keep the LiPo disconnected while performing USB
DFU — power the board from USB only for both flashing and for looking at
the LED afterward (or, once flashed, from a battery with props still
removed, if you prefer).

**⚠️ This overwrites Betaflight.** Flashing `fc_mcu_stub.bin` replaces
whatever firmware currently runs on this FC — including this board's
factory/current Betaflight target, **HGLRCF405V2** — until it is
reflashed. This is **reversible only by reflashing**: to restore
Betaflight, use Betaflight Configurator's own firmware flasher, select
target **HGLRCF405V2**, and flash it back via the same USB DFU bootloader.
Jarvis is not claiming to replace or be that firmware permanently, and
this repo does not ship a copy of Betaflight to restore it for you — the
Configurator does that.

**Procedure:**

1. Remove propellers. Disconnect the LiPo. Connect the FC to your
   computer via USB while holding the board's **BOOT** button (consult
   the HGLRC F460/F405 manual for the exact button/pad location on this
   specific board — this repo does not repeat board-photo-level detail
   already in that manual), which puts the STM32F405 into its built-in
   DFU bootloader instead of running whatever firmware is currently
   flashed.
2. Confirm the device enumerates as a DFU device, e.g. `dfu-util -l`
   should list an STM32 BOOTLOADER entry.
3. Build the image (see "Build" above) — this also produces
   `build/flight_control_mcu/fc_mcu_stub.bin` via the CMake `POST_BUILD`
   step (C30), skipped with a `message(STATUS ...)` note (not a hard
   configure error) if `arm-none-eabi-objcopy` is not on `PATH`.
4. Flash it, load address `0x08000000` (C29's own cited FLASH origin):

   ```bash
   dfu-util -a 0 -s 0x08000000:leave -D build/flight_control_mcu/fc_mcu_stub.bin
   ```

5. The board resets and runs the flashed image. Power it from USB (props
   still off) and look at the onboard status LED — it should toggle
   on/off with a visible, human-eye-scale flicker (an uncalibrated
   busy-wait at reset-default HSI 16 MHz — **not** a timed/calibrated
   frequency; see `mcu/hello_led.c`'s own header comment). Polarity may
   be active-low on some boards — either way, seeing the LED change
   state at all confirms `Reset_Handler` was reached and the GPIOC
   writes executed.
6. **No blink?** Report it — do not "fix" it by touching motor pins or
   adding peripherals outside this Buy's own scope. A dead LED with a
   successful build/flash is diagnostic information, not license to
   expand scope.
7. **Restore Betaflight** via Betaflight Configurator's firmware
   flasher, target **HGLRCF405V2**, same USB DFU bootloader entry
   procedure as step 1.

OpenOCD/ST-Link/`st-flash` are optional alternative flashing paths if
you happen to have that hardware — USB DFU (above) is the **primary**,
no-extra-hardware path for this specific board, and the only one this
README documents in detail. None of this is a `pytest` gate: the test
suite for C30 passes with **no board plugged in at all** — flashing is
an Engineer-performed desk smoke, not a CI requirement.

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
                         # rc_hold (C27 — age-only stale/failsafe
                         # watch, protocol-agnostic, see below),
                         # uart (C28 — UartBytePort + LoopbackUart,
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
    test_rc_hold.cpp             # C27 — RcHoldWatch cases
    test_uart.cpp                # C28 — LoopbackUart cases
  mcu/                            # C18 — freestanding linked .elf, DFU-able since C30
    linker_cortex_m4.ld
    startup_cortex_m4.c
    syscalls_stub.c
    hello_led.h                  # C30 — PC13 status-LED MMIO, declarations
    hello_led.c                  # C30 — PC13 status-LED MMIO, implementation
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

`rc_hold.hpp`/`rc_hold.cpp` (C27, ★ ACCEPT CLOSED @ tag `v0.5.25`) is
an **age-only stale/failsafe watch** — `RcHoldWatch::note_rc(now_s)`
records that a valid RC-channels sample was available; `evaluate(now_s)`
compares that against `timeout_s` (default `kRcHoldTimeoutS = 0.5`) and
returns `stale`/`reason`/`age_s`. Every method takes `now_s` as an
argument — no wall-clock call anywhere in this file. `now_s` earlier
than the last noted time throws `std::invalid_argument`.
`failsafe_loop_inputs(t_s)` returns `level_setpoint(t_s)` plus
`collective = 0.0` (an `RcLoopInputs`, C25's own type, reused unchanged)
and never calls `ControlLoop::step`, `EscOutput`, or any Safety gate.
This file names **no radio-link protocol anywhere, even in comments** —
the same lock `rc_setpoint.hpp` already held for this tree.

`uart.hpp`/`uart.cpp` (C28, ★ ACCEPT CLOSED @ tag `v0.5.26`) names the
**MCU-side UART byte port**: `UartBytePort` (abstract, virtual
destructor, `read(dst, n)`/`write(src, n)`) and `LoopbackUart`, the
**only** implementation — an in-memory FIFO (default capacity `256`). A
write past remaining capacity returns a short count (refuses the extra
bytes) instead of growing unbounded. **No USART registers, no CMSIS, no
`IOSSIOSPEED`/`termios`, no IRQ/DMA** anywhere in either file.
`mcu/stub_main.cpp` still never references `UartBytePort`/`LoopbackUart`
— no UART poll loop, `Reset_Handler` stays idle. This file, like
`rc_hold.hpp`, names **no radio-link protocol anywhere, even in
comments** — the Python host-serial module (C22/C23) is untouched by
this C++-only Buy.

### `hello_led.c`: the first visible signal (C30)

`mcu/hello_led.h`/`hello_led.c` (C30, package `0.5.28`, not yet tagged)
is the first bare-metal MMIO on this tree — two functions,
`hello_led_init()` and `hello_led_spin()` (noreturn), that toggle **PC13**
via `volatile` register stores. No CMSIS device header, no ST HAL — the
register addresses (RCC base `0x40023800`, `RCC_AHB1ENR` `0x40023830` bit
2 = GPIOCEN, `GPIOC_MODER` `0x40020800`, `GPIOC_BSRR` `0x40020818`) are
transcribed by hand from **RM0090** and cited in the file's own header
comment. **PC13 is cited, not guessed:** Betaflight's own unified target
for this exact FC (`HGLR-HGLRCF405V2.config`, line `resource LED 1 C13`)
names it as the status LED — deliberately **not** PA8 (that pin is
`resource MOTOR 6 A08` on this same V2 target — a motor-timer pin, not
an LED) and **not** PB1 (`LED_STRIP` — wire LEDs, not the onboard LED).
The busy-wait delay between toggles is explicitly **uncalibrated** —
"visible flicker at reset-default HSI 16 MHz," never a claimed
millisecond period; no PLL/HSE/`SystemInit` was added. `mcu/stub_main.cpp`
now calls `hello_led_init()` then `hello_led_spin()` after its existing
C18 one-shot `jarvis_fc` exercise, replacing the old empty
`while (true)`. **`fc_mcu_stub.elf` now has `LINK_DEPENDS` on
`linker_cortex_m4.ld`** (closing C29's own N1 residual — CMake previously
did not know a `.ld` edit should trigger a relink; verified by touching
the script and rebuilding without deleting the prior `.elf` first) and a
`POST_BUILD` step produces `fc_mcu_stub.bin` via `arm-none-eabi-objcopy`
for USB DFU (see "Flash it: USB DFU (C30)" above). **Flashed LED blink
!= flying != DShot != USART live != Betaflight HGLRCF405V2.**
