# Implementation Report — Fase C SPI scripted gyro-shaped probe (`B1-fase-c-spi-scripted-gyro-probe`)

**IC:** [`implementation_contract_fase_c_spi_scripted_gyro_probe_b1.md`](implementation_contract_fase_c_spi_scripted_gyro_probe_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-25
**Status:** ★ ACCEPT CLOSED @ **`v0.5.32`** (Engineer 2026-09-25). Cursor review of record: PASS WITH NOTES (N3–N4 folded; N1–N2 residual).

---

## 0. Read this first — honesty summary

This Buy adds the first **client** of `SpiBytePort`: `probe_rx`. C33's
`ScriptedSpi` gave the port a way to lie with bytes (canned RX); this Buy
is the other half — a caller that asks the port for `n` bytes and copies
back whatever RX the *current* implementation returns. `probe_rx` sends a
dummy TX of all-zero bytes — a full-duplex-shaped exchange, never a
register address — and never inspects or decodes the RX bytes it gets
back. On the desk today the implementation behind the port is
`LoopbackSpi` (echo) or `ScriptedSpi` (canned); the day a real SPI1 port
exists, only that implementation changes, not this client.

**Scripted gyro probe != gyro live != chip SPI != WHO_AM_I != flying.**

**Exists:** a function that asks `SpiBytePort` for bytes; tests can
preload those bytes via `ScriptedSpi`. **Impossible:** reading the
ICM42688P; a chip SPI bus; IMU samples from this probe. Nothing in this
Buy is any of those — no CMSIS, no CS/NSS GPIO, no register, no
`WHO_AM_I` API, no register address `0x75` anywhere in library code.

---

## 1. Package layout vs IC §1

```text
native/flight_control/include/jarvis/fc/spi_probe.hpp   # NEW
native/flight_control/src/spi_probe.cpp                   # NEW — added to jarvis_fc
native/flight_control/tests/test_spi_probe.cpp             # NEW — 5 Catch2 cases, added to fc_unit_tests
tests/test_fase_c_spi_scripted_gyro_probe_b1.py              # NEW — 12 tests
```

`spi.hpp`/`spi.cpp` (C32/C33's own files) got **zero edits** — confirmed
by `test_spi_hpp_and_spi_cpp_also_git_unchanged` and `git diff --stat`
(§6). `probe_rx` lives entirely in the new `spi_probe.*` files per IC §0
decision 5 ("`spi.hpp` stays the port. `spi_probe.hpp` is the first
caller. Do not add methods on `LoopbackSpi`/`ScriptedSpi`").

---

## 2. Types / API implemented vs IC §0 decision 4 / §2

| Item | IC ref | Match |
|---|---|---|
| `std::size_t probe_rx(SpiBytePort& port, std::uint8_t* rx, std::size_t n)` | §0.4/§2 | ✅ exact signature |
| Dummy TX = all-zero bytes, sized `n` | §0.4 | ✅ stack up to 256 bytes (notes-fold); heap only if `n>256`; `n==0` does not allocate |
| Calls `port.transfer(dummy_tx.data(), rx, n)`, returns that count | §0.4 | ✅ exact — no own logic, pure pass-through |
| `n == 0` returns `0` | §0.4 | ✅ inherited from `transfer`'s own `n==0` contract, verified explicitly (T5) |
| Null `rx` with `n>0` | §2 | Not special-cased, same as C32/C33 `transfer` — tests only pass valid buffers, per IC's own note |

### 2.1 Fixture-byte strictness (IC §0 decision 6 / T8) — stricter than C33's own comment-OK rule

IC §0 decision 6 permits a comment citing the fixture byte ("Comment OK:
placeholder, not a WHO_AM_I claim"), but T8 independently requires that
`spi_probe.*` contain **zero** occurrences of the literal `0x47` — even
in a comment. I resolved this in favor of the stricter, testable T8: the
header comment in `spi_probe.hpp` describes "a placeholder fixture byte"
without naming `0x47` anywhere in the file. The fixture value itself
lives only in `test_spi_probe.cpp` and
`tests/test_fase_c_spi_scripted_gyro_probe_b1.py`. Verified by
`test_t8_no_0x47_literal_anywhere_in_library_files` and by direct `grep`
(§6).

### 2.2 Non-goals (IC §2.1) — confirmed absent

Chip SPI, CS pin, ICM42688P registers, WHO_AM_I API, IMU into `step`,
denser `step` suite, DShot wire, USART, C30 DFU, Taller CSS, standoff
points — confirmed by grep (§6) and by
`test_no_gyro_driver_imu_wiring_or_step_reference_added_this_buy`.

---

## 3. Verified — a real build, real symbols

```text
$ cmake --build build/flight_control -j
[  1%] Building CXX object CMakeFiles/jarvis_fc.dir/src/spi_probe.cpp.o
...
[100%] Built target fc_unit_tests
$ ctest --output-on-failure
100% tests passed out of 71
```

```text
$ export PATH="/private/tmp/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin:$PATH"
$ cmake --build build/flight_control_mcu -j
[ 10%] Building CXX object CMakeFiles/jarvis_fc.dir/src/spi_probe.cpp.obj
[ 15%] Linking CXX static library libjarvis_fc.a
[100%] Built target fc_mcu_stub.elf
```

`spi_probe.cpp` compiles cleanly for both the host and the ARM cross
target, `-Wall -Wextra` clean. `fc_mcu_stub.elf` still links —
`--gc-sections` discards the unreferenced `probe_rx` symbol from the
final image since `stub_main.cpp` never calls it (confirmed byte-
unchanged, §6).

---

## 4. Integration rules vs IC §3

| Existing | This Buy |
|---|---|
| C32 `LoopbackSpi` | Unchanged (echo) — `probe_rx` on it returns all-zeros (the dummy TX), proving the client is port-shaped |
| C33 `ScriptedSpi` | Unchanged (canned RX, fixed replay) — `probe_rx` on it returns the canned fixture byte |
| C24 `step` / `loop.*` | **Byte-unchanged** — `probe_rx` does not feed the control tick; `git diff --stat` empty on `loop.hpp`/`loop.cpp`/`loop.py` |
| C3 `SimulatedImuHal` | **Unchanged** — `git diff --stat` empty |
| C31 DShot / C28 UART / C30 LED | **Byte-unchanged** — `git diff --stat` empty on all six files |
| Native CRSF/ELRS lock | Holds — tree-wide grep zero matches |

---

## 5. Tests run

### 5.1 Python — new module

`tests/test_fase_c_spi_scripted_gyro_probe_b1.py` — **12 tests**,
covering IC §4's T6, T7, T8, T10 (T1-T5/T9 are the C++ Catch2 cases
below; T11 is the full-suite/ctest run in §3/§5.3; T12 is this report):

| Test | Covers |
|---|---|
| `test_t6_stub_main_dshot_uart_loop_git_unchanged` | T6 |
| `test_spi_hpp_and_spi_cpp_also_git_unchanged` | IC §0 decision 9 (prefer zero edit on the port itself) |
| `test_t7_native_tree_zero_crsf_elrs_and_no_forbidden_tokens_in_new_code` | T7 |
| `test_t8_no_0x47_literal_anywhere_in_library_files` | T8 |
| `test_probe_rx_declared_in_new_files_not_folded_into_scripted_spi` | IC §0 decision 5 / output 1 |
| `test_cmake_wires_spi_probe_into_jarvis_fc_and_unit_tests` | CMake registration sanity |
| `test_t10_pyproject_version_is_0_5_32` | T10 |
| `test_t11_full_suite_process_gate_placeholder` | T11 marker (real gate is the full-suite run below) |
| `test_no_gyro_driver_imu_wiring_or_step_reference_added_this_buy` | IC §2.1 non-goals |
| `test_default_safety_gate_still_reject_all` | Safety default unchanged |
| `test_no_craft_or_core_imports_reference_probe_rx_and_registry_still_empty` | craft/registry isolation |
| `test_no_python_spi_port_added` | IC's own locked default (C++ native only) |

```text
tests/test_fase_c_spi_scripted_gyro_probe_b1.py: 12 passed
```

### 5.2 Full Python suite

```text
3679 passed, 2 skipped in 8.38s
```

Baseline before this Buy: `3667 passed, 2 skipped`. Delta: **+12**,
exactly matching the new test count — zero regressions.

### 5.3 C++ — new Catch2 cases + full host `ctest`

`native/flight_control/tests/test_spi_probe.cpp` — 5 new `TEST_CASE`s,
tag `[spi_probe][c34]`:

1. `probe_rx takes a SpiBytePort& (compiles against the abstract port)` (IC T1)
2. `probe_rx on ScriptedSpi returns the canned fixture byte` (IC T2)
3. `probe_rx on LoopbackSpi returns zeros (dummy TX is all-zero, not a hidden script)` (IC T3)
4. `probe_rx: script shorter than n gives a short count, tail of RX untouched` (IC T4)
5. `probe_rx: n=0 returns 0` (IC T5)

```text
100% tests passed out of 71
```

Baseline before this Buy: 66 host tests. Delta: **+5**, exactly the new
`TEST_CASE` count. `fc_closed_loop_smoke` and `fc_esc_pwm_smoke` both
still pass.

---

## 6. Module-boundary / forbidden-symbol grep (run at close of this Buy)

```text
$ git diff --stat -- native/flight_control/mcu/stub_main.cpp native/flight_control/mcu/hello_led.c \
    native/flight_control/mcu/hello_led.h native/flight_control/include/jarvis/fc/dshot.hpp \
    native/flight_control/src/dshot.cpp src/jarvis/flight_software/flight_control/dshot.py \
    native/flight_control/include/jarvis/fc/uart.hpp native/flight_control/src/uart.cpp \
    native/flight_control/include/jarvis/fc/loop.hpp native/flight_control/src/loop.cpp \
    src/jarvis/flight_software/flight_control/loop.py \
    native/flight_control/include/jarvis/fc/spi.hpp native/flight_control/src/spi.cpp \
    native/flight_control/tests/test_spi.cpp
(empty)

$ grep -rin "crsf\|elrs" native/
# no match (exit 1) — the C21-C33 native-tree lock holds

$ grep -in "0x75\|who_am_i\|icm42688p\|spi1\|cmsis" native/flight_control/include/jarvis/fc/spi_probe.hpp \
    native/flight_control/src/spi_probe.cpp native/flight_control/tests/test_spi_probe.cpp
# no match — none of these tokens appear anywhere in the new files, real code or comments

$ grep -n "0x47" native/flight_control/include/jarvis/fc/spi_probe.hpp native/flight_control/src/spi_probe.cpp
# no match — fixture byte lives only in test_spi_probe.cpp and the Python test module
```

`git status --short` at close of this Buy shows exactly the expected file
set: `spi_probe.hpp`, `spi_probe.cpp`, `test_spi_probe.cpp`,
`test_fase_c_spi_scripted_gyro_probe_b1.py` (new), `CMakeLists.txt`
(modified to register the two new files), plus `pyproject.toml` +
version-checkpoint test re-pins + docs. No `dshot.{hpp,cpp,py}`,
`hello_led.{h,c}`, `stub_main.cpp`, `uart.{hpp,cpp}`, `loop.{hpp,cpp,py}`,
`spi.hpp`, or `spi.cpp` touched.

---

## 7. Files changed

**New:**
- `native/flight_control/include/jarvis/fc/spi_probe.hpp`
- `native/flight_control/src/spi_probe.cpp`
- `native/flight_control/tests/test_spi_probe.cpp`
- `tests/test_fase_c_spi_scripted_gyro_probe_b1.py`
- `.jes/artifacts/implementation_report_fase_c_spi_scripted_gyro_probe_b1.md` (this file)

**Modified:**
- `native/flight_control/CMakeLists.txt` (`src/spi_probe.cpp` added to `jarvis_fc`; `tests/test_spi_probe.cpp` added to `fc_unit_tests`)
- `pyproject.toml` (`0.5.31` → `0.5.32`)
- 39 pre-existing test files re-pinned from `0.5.31` to `0.5.32` (literal `'version = "X.Y.Z"' in text` pattern and the `match.group(1) == "X.Y.Z"` regex pattern)
- `README.md`, `docs/ARCHITECTURE.md` (new §1c paragraph after C33), `docs/PLATFORM_CAPABILITY_VISION.md` §13, `docs/IMPLEMENTATION_TASKS.md` (see §9)

No pre-existing test needed a disclosed retargeting this Buy — `probe_rx`
introduced no token any prior Buy's own lock had already claimed as
globally forbidden.

---

## 8. Docs updated (honesty confirmed — not claiming CLOSED/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.32 includes (landed, awaiting Cursor review + Engineer ★ ACCEPT — no `v0.5.32` tag yet)" section; the v0.5.31 section's own "Next" line and the bottom "Next" mention both updated to point at C34 LANDED.
- `docs/ARCHITECTURE.md` §1c — new C34 paragraph after the C33 block, banner updated to "C34 LANDED @ package `0.5.32` (awaiting Cursor review + Engineer ★ ACCEPT, no `v0.5.32` tag yet)."
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C34 block, same "landed — awaiting ... no tag yet" phrasing, honesty line verbatim ("Scripted gyro probe ≠ gyro live ≠ chip SPI ≠ WHO_AM_I ≠ flying").
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner's "PRIORIDAD AHORA" line and the C34 table row both changed from "★ in flight" to "LANDED (awaiting Cursor review + Engineer ★ ACCEPT, no tag yet)"; suite/ctest counts updated `3667`/`66/66` → `3679`/`71/71`.

No file in this Buy claims `v0.5.32` is tagged or ACCEPT CLOSED, and none
claims a gyro sample, a chip SPI bus, or a shipped WHO_AM_I API exists.
Confirmed via `git tag -l | sort -V | tail -3` at close of this Buy:
`v0.5.29`, `v0.5.30`, `v0.5.31` — `v0.5.32` does not exist yet.

---

## 9. Residual / next steps

- DShot *wire*, on-chip USART, C30's own desk DFU smoke, a gyro
  (ICM42688P) register driver, denser `step` tests (cola 2), Taller CSS
  (cola 3), and standoff points (cola 4) all remain independently parked
  axes per the existing process lock and the "situation after C33"
  engineer note — none opened by this Buy.
- `SimulatedImuHal` (C3) stays the only IMU-sample source in this repo —
  this Buy did not wire `probe_rx` into any sensing path.
- A future gyro driver would call `probe_rx` (or use it as a reference
  shape) against a real SPI1 port implementation of `SpiBytePort` — that
  driver itself, including any WHO_AM_I register read, would be a
  separate, explicitly-scoped Buy, not an extension of this one.
- The T8 vs IC §0.6 tension (whether the fixture byte may appear in a
  `spi_probe.*` comment) was resolved in favor of the stricter, testable
  reading — see §2.1. Flagged for Cursor/Engineer to confirm this was the
  intended precedence.

---

## 10. Acceptance self-check vs IC §7

- T1-T5, T9 (C++ Catch2): ✅ all pass, 5/5 new cases green.
- T6-T8, T10 (Python + source-level): ✅ all pass, 12/12 new tests green.
- T11 (full suite + `ctest` green): ✅ `3679 passed, 2 skipped` (Python); `71/71` (`ctest`).
- T12 (this report's honesty content): ✅ this section.
- Probe is a port client: ✅ `probe_rx` takes `SpiBytePort&`, lives in new `spi_probe.*` files, never folded into `LoopbackSpi`/`ScriptedSpi`.
- No register map: ✅ no `0x75`, no `WHO_AM_I`, no `ICM42688P` anywhere in `spi_probe.*` (code or comments).
- `step` untouched: ✅ `git diff --stat` empty on `loop.hpp`/`loop.cpp`/`loop.py`.
- C33/C32/C31/C30/C28 frozen: ✅ `git diff --stat` empty on all freeze-list files, including `spi.hpp`/`spi.cpp` themselves.
- No CRSF/ELRS in native: ✅ tree-wide grep, zero matches.
- No Python SPI port: ✅ `SpiBytePort`/`probe_rx` absent from `src/jarvis/flight_software/`.
- Version `0.5.32`: ✅ `pyproject.toml` + all 39 checkpoint tests re-pinned.

**PASS** against every criterion in IC §7. **FAIL conditions** (ICM42688P
driver, WHO_AM_I as a shipped API, `0x75` in code, `step` reading SPI,
chip registers, a Python SPI port) — none present, verified above.
