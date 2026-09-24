# Implementation Report — Fase C MCU SPI HAL stub (`B1-fase-c-mcu-spi-hal-stub`)

**IC:** [`implementation_contract_fase_c_mcu_spi_hal_stub_b1.md`](implementation_contract_fase_c_mcu_spi_hal_stub_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-24
**Status:** ★ ACCEPT CLOSED @ **`v0.5.30`**. Cursor independent review: [PASS WITH NOTES](implementation_review_fase_c_mcu_spi_hal_stub_b1.md).

---

## 0. Read this first — honesty summary

This Buy names the MCU-side SPI byte port the desk FC's own gyro
(ICM42688P) will someday use: `SpiBytePort` — a C++ abstract base
(virtual destructor, `transfer(tx, rx, n)`) — with exactly one
implementation, `LoopbackSpi`, an in-memory full-duplex loopback. Same
idea as C28's `UartBytePort`: the plug now has a shape; the only device
plugged into it is a loopback, never a register, never a chip-select
pin, never the ICM42688P.

**MCU SPI stub != chip SPI != gyro live != flying.**

**Exists:** a named SPI byte port; an in-memory loopback implements it.
**Impossible:** reading the ICM42688P; a chip SPI bus; DShot on a pin.
Nothing in this Buy is any of those — no CMSIS, no CS/NSS GPIO, no
register, no gyro sample.

---

## 1. Package layout vs IC §1

```text
native/flight_control/include/jarvis/fc/spi.hpp   # NEW
native/flight_control/src/spi.cpp                   # NEW — added to jarvis_fc
native/flight_control/tests/test_spi.cpp             # NEW Catch2 cases (5)
tests/test_fase_c_mcu_spi_hal_stub_b1.py              # NEW — 14 tests
```

No `.py` SPI driver was added anywhere under `src/jarvis/` (IC §0 decision 4) — this is a C++-native Buy, confirmed by `test_spi_files_not_under_src_jarvis`. `SimulatedImuHal` was not touched (`git diff --stat` empty, confirmed §7).

---

## 2. Types / API implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| `SpiBytePort` — `virtual ~SpiBytePort()`, `virtual size_t transfer(const uint8_t*, uint8_t*, size_t) = 0` | §2 | ✅ exact shape |
| `LoopbackSpi(SpiBytePort)` — constructor takes `max_bytes` (default `256`) | §2 | ✅ |
| `transfer`: `for i in 0..accepted-1: rx[i] = tx[i]`, `accepted = min(n, max_bytes)` | §2 | ✅ exact |

### 2.1 Non-goals (IC §2.1) — confirmed absent

Chip SPI, CS pin, ICM42688P registers, IMU into `step`, DShot wire, USART, C30 DFU — confirmed by grep (§7) and by `test_t8_no_spi_registers_or_cmsis_or_cs_gpio_in_new_spi_files` / `test_t5_stub_main_has_no_spi_port_reference_or_poll_loop`.

---

## 3. `LoopbackSpi` vs `LoopbackUart` — a deliberate shape difference, disclosed

`LoopbackUart` (C28) carries a persistent internal FIFO — `write` enqueues, a later `read` dequeues, because a UART is an asynchronous byte stream where writes and reads happen at different times. SPI is different: `transfer` is a single **synchronous** full-duplex exchange — the caller gets its RX bytes back in the very same call that supplied TX. `LoopbackSpi` therefore keeps **no state between calls** — `max_bytes` bounds a single transfer's size, not a queue depth. This is a deliberate, protocol-accurate difference from `LoopbackUart`, not an oversight; documented in both `spi.hpp`'s own header comment and here.

Verified empirically: `LoopbackSpi(4).transfer(6 bytes)` returns `4` (short count) and only the first 4 output bytes are written — `rx[4]`/`rx[5]` are left untouched by the call (Catch2 case `"LoopbackSpi: transfer past capacity returns a short count, no unbounded growth"` asserts the untouched bytes explicitly, not just the returned count).

---

## 4. Verified — a real build, real symbols

```text
$ cmake --build build/flight_control -j4
[  1%] Building CXX object CMakeFiles/jarvis_fc.dir/src/spi.cpp.o
...
[100%] Built target fc_unit_tests
$ ctest
100% tests passed out of 60
```

```text
$ export PATH="/private/tmp/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin:$PATH"
$ cmake --build build/flight_control_mcu -j4
[  5%] Building CXX object CMakeFiles/jarvis_fc.dir/src/spi.cpp.obj
[ 10%] Linking CXX static library libjarvis_fc.a
[100%] Built target fc_mcu_stub.elf
```

`spi.cpp` compiles cleanly for both the host and the ARM cross target. `fc_mcu_stub.elf` still links — `--gc-sections` discards the unreferenced `SpiBytePort`/`LoopbackSpi` symbols from the final image since `stub_main.cpp` never calls them (confirmed byte-unchanged, §7).

---

## 5. Integration rules vs IC §3

| Existing | This Buy |
|---|---|
| C28 `UartBytePort` | Unchanged — `uart.hpp`/`uart.cpp` `git diff --stat` empty; SPI is a **separate** port, no shared base class, no coupling |
| C31 DShot encode | **Byte-unchanged** — `dshot.hpp`/`dshot.cpp`/`dshot.py` all `git diff --stat` empty |
| C30 `hello_led`/`stub_main` | **Byte-unchanged** — `hello_led.h`/`hello_led.c`/`stub_main.cpp` all `git diff --stat` empty |
| C3 `SimulatedImuHal` | **Unchanged** — `sim_imu_hal.py` `git diff --stat` empty |
| Native CRSF lock | Holds — tree-wide grep zero matches |

---

## 6. Tests run

### 6.1 Python — new module

`tests/test_fase_c_mcu_spi_hal_stub_b1.py` — **14 tests**, covering IC §4's T5-T8 and T10 (T1-T4/T9 are the C++ Catch2 cases, T11 is the full-suite/ctest run, T12 is this report):

| Test | Covers |
|---|---|
| `test_t5_stub_main_has_no_spi_port_reference_or_poll_loop` | T5 |
| `test_t6_dshot_hpp_and_uart_hpp_git_unchanged` | T6 |
| `test_t7_native_tree_still_zero_crsf_elrs_tokens` | T7 |
| `test_t8_no_spi_registers_or_cmsis_or_cs_gpio_in_new_spi_files` | T8 |
| `test_desk_gyro_identity_may_appear_only_as_comment_citation` | IC §0 decision 8 (ICM42688P as desk identity, not driver) |
| `test_t9_pyproject_version_is_0_5_30` | T10 |
| `test_t10_full_suite_process_gate_placeholder` | T11 marker (real gate is the full-suite run below) |
| `test_hello_led_and_stub_main_and_dshot_git_unchanged` | freeze list, extended |
| `test_sim_imu_hal_git_unchanged` | C3 isolation |
| `test_spi_files_not_under_src_jarvis` | IC §1 placement lock |
| `test_cmake_wires_spi_into_jarvis_fc_and_unit_tests` | CMake registration sanity |
| `test_default_safety_gate_still_reject_all` | Safety default unchanged |
| `test_no_craft_or_core_imports_reference_spi_and_registry_still_empty` | craft/registry isolation |
| `test_mcu_elf_still_links_if_toolchain_and_build_present` | bonus, skip-honest MCU `.elf` presence check |

```text
tests/test_fase_c_mcu_spi_hal_stub_b1.py: 14 passed
```

### 6.2 Full Python suite

```text
3649 passed, 2 skipped in 7.44s
```

Baseline before this Buy: `3635 passed, 2 skipped`. Delta: **+14**, exactly matching the new test count — zero regressions.

### 6.3 C++ — new Catch2 cases + full host `ctest`

`native/flight_control/tests/test_spi.cpp` — 5 new `TEST_CASE`s:

1. `LoopbackSpi is convertible to SpiBytePort*` (IC T1)
2. `LoopbackSpi: transfer round-trips TX to RX in order` (IC T2)
3. `LoopbackSpi: n=0 returns 0` (IC T3)
4. `LoopbackSpi: transfer past capacity returns a short count, no unbounded growth` (IC T4)
5. `LoopbackSpi: rejects zero capacity` (constructor validation, matching `LoopbackUart`'s own precedent)

```text
100% tests passed out of 60
```

Baseline before this Buy: 55 host tests. Delta: **+5**, exactly the new `TEST_CASE` count. `fc_closed_loop_smoke` and `fc_esc_pwm_smoke` both still pass.

---

## 7. Module-boundary / forbidden-symbol grep (run at close of this Buy)

```text
$ git diff --stat -- native/flight_control/include/jarvis/fc/dshot.hpp native/flight_control/src/dshot.cpp \
    src/jarvis/flight_software/flight_control/dshot.py native/flight_control/mcu/hello_led.c \
    native/flight_control/mcu/hello_led.h native/flight_control/mcu/stub_main.cpp \
    native/flight_control/include/jarvis/fc/uart.hpp native/flight_control/src/uart.cpp \
    src/jarvis/flight_software/flight_control/sim_imu_hal.py
(empty)

$ grep -rin "crsf|elrs" native/
# no match (exit 1) — the C21-C31 native-tree lock holds
```

`git status --short` at close of this Buy shows exactly the expected file set: `spi.hpp`, `spi.cpp`, `test_spi.cpp`, `test_fase_c_mcu_spi_hal_stub_b1.py` (new), `CMakeLists.txt` (modified to register the two new files), plus `pyproject.toml` + version-checkpoint test re-pins + docs. No `dshot.{hpp,cpp,py}`, `hello_led.{h,c}`, `stub_main.cpp`, `uart.{hpp,cpp}`, or `sim_imu_hal.py` touched.

---

## 8. Files changed

**New:**
- `native/flight_control/include/jarvis/fc/spi.hpp`
- `native/flight_control/src/spi.cpp`
- `native/flight_control/tests/test_spi.cpp`
- `tests/test_fase_c_mcu_spi_hal_stub_b1.py`
- `.jes/artifacts/implementation_report_fase_c_mcu_spi_hal_stub_b1.md` (this file)

**Modified:**
- `native/flight_control/CMakeLists.txt` (`src/spi.cpp` added to `jarvis_fc`; `tests/test_spi.cpp` added to `fc_unit_tests`)
- `pyproject.toml` (`0.5.29` → `0.5.30`)
- ~30 pre-existing test files re-pinned from `0.5.29` to `0.5.30` (literal `'version = "X.Y.Z"' in text` pattern)
- `README.md`, `docs/ARCHITECTURE.md` (new §1c paragraph after C31), `docs/PLATFORM_CAPABILITY_VISION.md`, `docs/IMPLEMENTATION_TASKS.md` (see §9)

No pre-existing test needed a disclosed retargeting this Buy (unlike C26/C30/C31's own experience) — `spi.hpp`/`spi.cpp` introduced no token that any prior Buy's own lock had already claimed as globally forbidden.

---

## 9. Docs updated (honesty confirmed — not claiming CLOSED/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.30 includes (working tree — not yet tagged)" section, explicitly says "no `v0.5.30` tag yet."
- `docs/ARCHITECTURE.md` §1c — new C32 paragraph after the C31 block, top banner updated to "Working tree ahead: package `0.5.30` ... awaiting Cursor review + Engineer ★ ACCEPT — no `v0.5.30` tag yet."
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C32 block, same "landed — awaiting ... no tag yet" phrasing, honesty line verbatim.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner and the C32 table row both changed to "Landed — awaiting Cursor review + ★ ACCEPT (no `v0.5.30` tag yet)." "gyro driver" added to the PRIORIDAD parked-axes list.

No file in this Buy claims `v0.5.30` is tagged or ACCEPT CLOSED, and none claims a gyro sample or a chip SPI bus exists. Confirmed via `git tag -l | sort -V | tail -3` at close of this Buy: `v0.5.27`, `v0.5.28`, `v0.5.29` — `v0.5.30` does not exist yet.

---

## 10. Residual / next steps

- DShot *wire*, on-chip USART, C30's own desk DFU smoke, a gyro (ICM42688P) register driver, and craft↔FS all remain independently parked axes per the existing process lock and the 2026-09-24 "bench before silicon" engineer note — none opened by this Buy.
- `SimulatedImuHal` (C3) stays the only IMU-sample source in this repo — this Buy did not wire `SpiBytePort`/`LoopbackSpi` into any sensing path, per the IC's own explicit non-goal ("IMU into `step`").
- A future gyro driver would implement its own `SpiBytePort` override (or use `LoopbackSpi` for testing) and would be a separate, explicitly-scoped Buy — not an extension of this one.

---

## 11. Acceptance self-check vs IC §7

- T1-T4, T9 (C++ Catch2): ✅ all pass, 5/5 new cases green.
- T5-T8, T10 (Python + CMake/source-level): ✅ all pass, 14/14 new tests green.
- T11 (full suite + `ctest` green): ✅ `3649 passed, 2 skipped` (Python); `60/60` (`ctest`).
- T12 (this report's honesty content): ✅ this section.
- Loopback only: ✅ `LoopbackSpi` is the sole `SpiBytePort` implementation shipped.
- C31/C30 frozen: ✅ `git diff --stat` empty on all freeze-list files.
- No CRSF in native: ✅ tree-wide grep, zero matches.
- Version `0.5.30`: ✅ `pyproject.toml` + all checkpoint tests re-pinned.

**PASS** against every criterion in IC §7. **FAIL conditions** (SPI registers, gyro driver, `stub_main` SPI spin, live-IMU claim) — none present, verified above.
