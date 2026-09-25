# Implementation Report — Fase C SPI scripted slave (`B1-fase-c-spi-scripted-slave`)

**IC:** [`implementation_contract_fase_c_spi_scripted_slave_b1.md`](implementation_contract_fase_c_spi_scripted_slave_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-25
**Status:** ★ ACCEPT CLOSED @ **`v0.5.31`** (Engineer 2026-09-25). Cursor review of record: PASS WITH NOTES (N1–N3 folded; N4–N6 residual).

---

## 0. Read this first — honesty summary

This Buy adds a **second** `SpiBytePort` implementation, `ScriptedSpi`, to the
existing `native/flight_control/include/jarvis/fc/spi.hpp`/`src/spi.cpp` (C32).
`LoopbackSpi` (C32, unchanged this Buy) only ever echoes what you send it —
RX = TX. A real device answers with **its own** bytes, independent of TX.
`ScriptedSpi` fills RX from a pre-loaded byte script instead of from TX —
this is how a test can pretend "a device answered" without any real chip.
TX is never inspected or required to match anything.

**Scripted SPI != gyro live != chip SPI != flying.**

**Exists:** a canned-RX test double on the same `SpiBytePort` interface.
**Impossible:** reading the ICM42688P; a chip SPI bus; DShot on a pin; IMU
samples into `step`. Nothing in this Buy is any of those — no CMSIS, no
CS/NSS GPIO, no register, no gyro sample, no shipped WHO_AM_I API.

---

## 1. Package layout vs IC §1

```text
native/flight_control/include/jarvis/fc/spi.hpp   # EXTENDED — ScriptedSpi added
native/flight_control/src/spi.cpp                   # EXTENDED — ScriptedSpi added
native/flight_control/tests/test_spi.cpp             # EXTENDED — 6 new Catch2 cases
tests/test_fase_c_spi_scripted_slave_b1.py            # NEW — 9 tests
```

No new file under `native/` — `ScriptedSpi` was added to the existing
`spi.hpp`/`spi.cpp` per the IC's own required output #1, so `CMakeLists.txt`
needed **no change** (both files were already registered in `jarvis_fc` /
`fc_unit_tests` since C32). Confirmed by `test_scripted_spi_declared_alongside_loopback_spi_not_a_new_file`
and by `git diff --stat -- native/flight_control/CMakeLists.txt` being empty.

---

## 2. Types / API implemented vs IC §0 decision 4

| Item | IC ref | Match |
|---|---|---|
| `ScriptedSpi(std::vector<uint8_t> canned_rx = {})` | §0.4 | ✅ constructor takes the script directly |
| `set_next_rx(std::vector<uint8_t> canned_rx)` | §0.4 | ✅ reprograms the script between calls |
| `transfer`: `rx[0..accepted) = canned_rx_[0..accepted)`, never reads `tx` | §0.4 | ✅ exact — `tx` parameter marked `/*tx*/`, unused |
| Short count if script shorter than `n` | §0.4/§0.6 | ✅ `accepted = min(n, canned_rx_.size())` |
| `LoopbackSpi` behavior-unchanged | §0.5 | ✅ `git diff` on its own methods: none — only new class appended after it |

### 2.1 Design decision disclosed (IC left this open)

The IC's own §0.4 offered two equally valid shapes: a constructor-only
`ScriptedSpi(span of uint8_t canned_rx)`, or a `set_next_rx(...)`-based
reprogram API. I implemented **both** — a constructor for the initial
script, plus `set_next_rx(...)` to change it later — since the IC's T2-T3
worked examples only require the constructor path and T-series doesn't
distinguish. The remaining ambiguity (does `transfer` *consume* the script
across multiple calls, or return the same fixed bytes until reprogrammed?)
was resolved as **fixed response until `set_next_rx`** — each `transfer()`
call fills RX from the **start** of the currently-loaded script. This is
the simpler of the two reasonable readings and is disclosed in both the
header comment (`spi.hpp`) and Catch2 case
`"ScriptedSpi: set_next_rx replaces the script for subsequent transfers"`,
which calls `transfer` **twice** on the same unchanged script (both return
`0x11`) **then** `set_next_rx` and a third `transfer` (`0x22`) — fixed
replay, not a consuming stream. Cursor review N3: the first landing of
this case only did one call before reprogram; the second identical call
was added in the notes-fold so the report and the test agree.

### 2.2 Non-goals (IC §0 decisions 2/7) — confirmed absent

ICM42688P driver, WHO_AM_I as a shipped API, IMU samples into `step`, chip
SPI, CS GPIO, DShot wire, C30 DFU — confirmed by grep (§7) and by
`test_who_am_i_and_icm42688p_appear_only_in_comments` /
`test_no_gyro_driver_or_imu_wiring_added_this_buy`.

---

## 3. Verified — a real build, real symbols

```text
$ cmake --build build/flight_control -j
[ 11%] Built target jarvis_fc
[ 14%] Built target fc_esc_pwm_smoke
[ 14%] Built target fc_closed_loop_smoke
[100%] Built target fc_unit_tests
$ ctest --output-on-failure
100% tests passed out of 66
```

```text
$ export PATH="/private/tmp/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin:$PATH"
$ cmake --build build/flight_control_mcu -j
[ 73%] Built target jarvis_fc
[100%] Built target fc_mcu_stub.elf
```

`spi.cpp` compiles cleanly for both the host and the ARM cross target. The
rebuild's "Built target" (no explicit compile line) was verified genuine,
not stale — `spi.cpp.obj` mtime postdates `spi.cpp` source mtime — the same
staleness check used in every prior MCU-adjacent Buy since C24.

---

## 4. Integration rules vs IC §3 / §0

| Existing | This Buy |
|---|---|
| C32 `LoopbackSpi` | **Byte-unchanged** — no edits to `LoopbackSpi`'s own constructor/`transfer`; `ScriptedSpi` appended as a separate class |
| C31 DShot encode | **Byte-unchanged** — `dshot.hpp`/`dshot.cpp`/`dshot.py` all `git diff --stat` empty |
| C30 `hello_led`/`stub_main` | **Byte-unchanged** — `hello_led.h`/`hello_led.c`/`stub_main.cpp` all `git diff --stat` empty |
| C28 `uart.hpp`/`uart.cpp` | **Byte-unchanged** — `git diff --stat` empty |
| C3 `SimulatedImuHal` / C4 `loop.{hpp,cpp,py}` | **Unchanged** — `sim_imu_hal.py`, `loop.hpp`, `loop.cpp`, `loop.py` all `git diff --stat` empty |
| Native CRSF/ELRS lock | Holds — tree-wide grep zero matches |
| WHO_AM_I/ICM42688P comment-only lock (new, §0 decision 7) | Holds — 4 mentions in `spi.hpp`, all inside `//` comment lines authored for this Buy |

---

## 5. Tests run

### 5.1 Python — new module

`tests/test_fase_c_spi_scripted_slave_b1.py` — **9 tests**, covering IC §4's
T5, T6, T8 (T1-T4/T7 are the C++ Catch2 cases below; T9 is the full-suite/ctest
run in §3/§5.3; T10 is this report):

| Test | Covers |
|---|---|
| `test_t5_stub_main_dshot_uart_git_unchanged` | T5 |
| `test_t6_native_tree_still_zero_crsf_elrs_and_no_spi_registers_in_new_code` | T6 |
| `test_who_am_i_and_icm42688p_appear_only_in_comments` | IC §0 decision 7 |
| `test_scripted_spi_declared_alongside_loopback_spi_not_a_new_file` | IC §1 output #1 (extend, not add a file) |
| `test_t8_pyproject_version_is_0_5_31` | T8 |
| `test_t9_full_suite_process_gate_placeholder` | T9 marker (real gate is the full-suite run below) |
| `test_no_gyro_driver_or_imu_wiring_added_this_buy` | IC §0 decision 2 (no IMU/gyro wiring) |
| `test_default_safety_gate_still_reject_all` | Safety default unchanged |
| `test_no_craft_or_core_imports_reference_scripted_spi_and_registry_still_empty` | craft/registry isolation |

```text
tests/test_fase_c_spi_scripted_slave_b1.py: 9 passed
```

### 5.2 Full Python suite

```text
3667 passed, 2 skipped in 7.72s
```

Baseline before this Buy: `3658 passed, 2 skipped` (this baseline already
included unrelated, externally-authored craft/geometry test files landed in
parallel by a separate track — not part of this Buy). Delta: **+9**,
exactly matching the new test count — zero regressions attributable to
this Buy.

### 5.3 C++ — new Catch2 cases + full host `ctest`

`native/flight_control/tests/test_spi.cpp` — 6 new `TEST_CASE`s, tag `[spi][c33]`:

1. `ScriptedSpi is convertible to SpiBytePort*` (IC T1)
2. `ScriptedSpi: transfer fills RX from the script, not from TX echo` (IC T2 — worked example: TX `{1,2}` + script `{9,8}` → RX `{9,8}`, `REQUIRE(rx != tx)`)
3. `ScriptedSpi: script shorter than n gives a short count, tail of RX untouched` (IC T3)
4. `ScriptedSpi: set_next_rx replaces the script for subsequent transfers` (disclosed design decision, §2.1)
5. `ScriptedSpi: an empty script returns 0 regardless of n` (edge case)
6. `LoopbackSpi: still RX=TX after ScriptedSpi exists (regression)` (IC T4)

```text
100% tests passed out of 66
```

Baseline before this Buy: 60 host tests. Delta: **+6**, exactly the new
`TEST_CASE` count. `fc_closed_loop_smoke` and `fc_esc_pwm_smoke` both still
pass.

---

## 6. Module-boundary / forbidden-symbol grep (run at close of this Buy)

```text
$ git diff --stat -- native/flight_control/mcu/stub_main.cpp native/flight_control/mcu/hello_led.c \
    native/flight_control/mcu/hello_led.h native/flight_control/include/jarvis/fc/dshot.hpp \
    native/flight_control/src/dshot.cpp src/jarvis/flight_software/flight_control/dshot.py \
    native/flight_control/include/jarvis/fc/uart.hpp native/flight_control/src/uart.cpp
(empty)

$ grep -rin "crsf\|elrs" native/
# no match (exit 1) — the C21-C32 native-tree lock holds

$ grep -in "who_am_i\|icm42688p" native/flight_control/include/jarvis/fc/spi.hpp
# 4 hits, all inside // comment lines (lines 12, 14, 17, 73)
```

`git status --short` at close of this Buy shows exactly the expected file
set: `spi.hpp`, `spi.cpp`, `test_spi.cpp` (modified), `test_fase_c_spi_scripted_slave_b1.py`
(new), plus `pyproject.toml` + version-checkpoint test re-pins + docs. No
`dshot.{hpp,cpp,py}`, `hello_led.{h,c}`, `stub_main.cpp`, `uart.{hpp,cpp}`,
`sim_imu_hal.py`, `loop.{hpp,cpp,py}`, or `CMakeLists.txt` touched.

---

## 7. Files changed

**New:**
- `tests/test_fase_c_spi_scripted_slave_b1.py`
- `.jes/artifacts/implementation_report_fase_c_spi_scripted_slave_b1.md` (this file)

**Modified:**
- `native/flight_control/include/jarvis/fc/spi.hpp` (`ScriptedSpi` class added after `LoopbackSpi`)
- `native/flight_control/src/spi.cpp` (`ScriptedSpi` constructor/`transfer`/`set_next_rx` added)
- `native/flight_control/tests/test_spi.cpp` (6 new Catch2 cases, header comment updated to "C32/C33")
- `pyproject.toml` (`0.5.30` → `0.5.31`)
- 38 pre-existing test files re-pinned from `0.5.30` to `0.5.31` (literal `'version = "X.Y.Z"' in text` pattern and the `match.group(1) == "X.Y.Z"` regex pattern)
- `README.md`, `docs/ARCHITECTURE.md` (new §1c paragraph after C32), `docs/PLATFORM_CAPABILITY_VISION.md` §13, `docs/IMPLEMENTATION_TASKS.md` (see §9)

No `CMakeLists.txt` change was needed — see §1. No pre-existing test needed
a disclosed retargeting this Buy — `ScriptedSpi` introduced no token any
prior Buy's own lock had already claimed as globally forbidden.

---

## 8. Docs updated (honesty confirmed — not claiming CLOSED/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.31 includes (landed, awaiting Cursor review + Engineer ★ ACCEPT — no `v0.5.31` tag yet)" section; the v0.5.30 section's own "Next" line updated to point at C33 LANDED.
- `docs/ARCHITECTURE.md` §1c — new C33 paragraph after the C32 block, banner updated to "C33 LANDED @ package `0.5.31` (awaiting Cursor review + Engineer ★ ACCEPT, no `v0.5.31` tag yet)."
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C33 block, same "landed — awaiting ... no tag yet" phrasing, honesty line verbatim ("Scripted SPI ≠ gyro live ≠ chip SPI ≠ flying").
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner's "Parked: C33" line and the C33 table row both changed from "READY (awaiting Engineer ★)" to "LANDED (awaiting Cursor review + Engineer ★ ACCEPT, no tag yet)"; suite count updated `3658` → `3667`. The external "PRIORIDAD AHORA" (Taller dims / standoff cylinder layout, a separate parallel track) was left untouched, as it is not this Buy's concern.

No file in this Buy claims `v0.5.31` is tagged or ACCEPT CLOSED, and none
claims a gyro sample, a chip SPI bus, or a shipped WHO_AM_I API exists.
Confirmed via `git tag -l | sort -V | tail -3` at close of this Buy:
`v0.5.28`, `v0.5.29`, `v0.5.30` — `v0.5.31` does not exist yet.

---

## 9. Residual / next steps

- DShot *wire*, on-chip USART, C30's own desk DFU smoke, a gyro (ICM42688P)
  register driver, and craft↔FS all remain independently parked axes per
  the existing process lock and the 2026-09-24 "bench before silicon"
  engineer note — none opened by this Buy.
- `SimulatedImuHal` (C3) stays the only IMU-sample source in this repo —
  this Buy did not wire `ScriptedSpi`/`LoopbackSpi` into any sensing path.
- A future gyro driver would use `ScriptedSpi` to fake WHO_AM_I-shaped
  responses in tests (e.g. loading `0x47` as a placeholder byte) — that
  driver itself would be a separate, explicitly-scoped Buy, not an
  extension of this one.
- The disclosed design decision in §2.1 (fixed-response-until-reprogrammed
  semantics) should be confirmed or revised by Cursor/Engineer review —
  it is within the IC's own stated flexibility but was my own judgment
  call where the IC left the exact consuming-vs-fixed shape open.

---

## 10. Acceptance self-check vs IC §7

- T1-T4, T7 (C++ Catch2): ✅ all pass, 6/6 new cases green.
- T5, T6, T8 (Python + source-level): ✅ all pass, 9/9 new tests green.
- T9 (full suite + `ctest` green): ✅ `3667 passed, 2 skipped` (Python); `66/66` (`ctest`).
- T10 (this report's honesty content): ✅ this section.
- `LoopbackSpi` unchanged: ✅ `git diff` shows only an appended class, no edits to existing methods.
- No gyro driver: ✅ no register map, no WHO_AM_I shipped API, no IMU-into-`step` wiring.
- C32/C31/C30/C28 frozen: ✅ `git diff --stat` empty on all freeze-list files.
- No CRSF/ELRS in native: ✅ tree-wide grep, zero matches.
- WHO_AM_I/ICM42688P comment-only: ✅ 4 hits, all inside comments.
- Version `0.5.31`: ✅ `pyproject.toml` + all 38 checkpoint tests re-pinned.

**PASS** against every criterion in IC §7. **FAIL conditions** (ICM42688P
register map, WHO_AM_I as a shipped API, `step` reading SPI, chip SPI
registers) — none present, verified above.
