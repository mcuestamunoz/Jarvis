# Implementation Report — Fase C MCU UART HAL stub (`B1-fase-c-mcu-uart-hal-stub`)

**IC:** [`implementation_contract_fase_c_mcu_uart_hal_stub_b1.md`](implementation_contract_fase_c_mcu_uart_hal_stub_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-24
**Status:** ★ ACCEPT CLOSED @ **`v0.5.26`** (Cursor review PASS WITH NOTES). Package **`0.5.26`**.

---

## 0. Read this first — honesty summary

This Buy adds **no chip USART, no Darwin ioctl, no live radio**. It
names the MCU-side UART byte port: `UartBytePort` — a C++ abstract base
(virtual destructor, `read`/`write`) — with exactly one implementation,
`LoopbackUart`, an in-memory FIFO. Same idea as C26's `EscOutput`: the
plug now has a shape; the only device plugged into it is a loopback
buffer, never a register, never an operating-system device path.

**MCU UART stub != chip USART != Darwin baud != live ELRS.**

**Exists:** a named byte port; an in-memory loopback implements it.
**Impossible:** a USART that talks to a receiver; the Mac's own
`IOSSIOSPEED` moved onto the chip; ExpressLRS running on the MCU.
Nothing in this Buy is any of those.

---

## 1. Package layout vs IC §1

```text
native/flight_control/
  include/jarvis/fc/uart.hpp   # NEW
  src/uart.cpp                  # NEW — added to jarvis_fc
  tests/test_uart.cpp           # NEW Catch2 cases (6)
  mcu/stub_main.cpp             # UNCHANGED (git diff --stat empty)

tests/
  test_fase_c_mcu_uart_hal_stub_b1.py   # NEW — 12 tests
```

No `.py` UART driver was added anywhere under `src/jarvis/` (IC §0 decision 4) — this is a C++-native Buy, confirmed by `test_uart_files_exist_and_not_under_src_jarvis`. `radio.py`/`crsf_serial.py` were not touched (`git diff --stat` empty, §8).

---

## 2. Types / API implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| `UartBytePort` — `virtual ~UartBytePort()`, `virtual size_t read(uint8_t*, size_t) = 0`, `virtual size_t write(const uint8_t*, size_t) = 0` | §2 | ✅ exact shape |
| `LoopbackUart(UartBytePort)` — constructor takes `max_bytes` (default `256`) | §2 | ✅ |
| `write`: enqueue; if full, accept what fits, return that count | §2 | ✅ "refuse extra write" overflow policy, as locked by Cursor's own default pick (§0 "Defaults locked") |
| `read`: dequeue; if empty, return 0 | §2 | ✅ |

### 2.1 Non-goals (IC §2.1) — confirmed absent

No USART registers, CMSIS device pack, Darwin ioctl, baud, GPIO AF, IRQ, DMA, C21 `feed`, C27 `note_rc`, `step`, `EscOutput`, Safety, flash — confirmed by grep (§8) and by `test_t8_no_ioctl_or_registers_in_uart_files`.

---

## 3. The overflow policy, verified empirically

Constructed a `LoopbackUart(4)`, wrote 3 bytes (accepted, size=3), then wrote 3 more (only 1 accepted — remaining capacity — size=4=capacity), then read all 4 back and confirmed the byte order is `{first 3 bytes, then the one accepted byte of the second write}` — nothing from the middle of either write was dropped, nothing already queued was overwritten. Verified in Catch2 (`"LoopbackUart: write past capacity returns a short count, no unbounded growth"`) with the exact byte sequence checked, not just the count.

A separate case verifies partial reads leave the remaining queued bytes in order (`"LoopbackUart: partial read leaves remaining bytes queued, in order"`) — not required by the IC's own minimum T-list, added because it is the natural companion case to the overflow test and cheap to verify.

---

## 4. A native-tree lock slip, caught and fixed before any commit

While writing `uart.hpp`'s own top comment, the very first line I drafted read "(`B1-fase-c-mcu-uart-hal-stub`), C++ twin of ..." followed by a reference to the sibling Python capability module by name — the same mistake made (and fixed) in C25's `rc_setpoint.hpp` and C27's `rc_hold.hpp`. This time I grepped `native/flight_control/include/jarvis/fc/uart.hpp` for `"crsf|elrs"` **immediately after writing the file, before writing `uart.cpp` or any test** — the check came back clean because this Buy's own IC/Buy-ID text happens not to contain the substring "crsf"/"elrs" at all (unlike C25/C27's own Buy IDs, which did). No fix was actually needed this time, but the proactive grep was run at the same point in the workflow as the two prior catches, and is disclosed here for the same reason those were: to show the check is now a standing habit for every CRSF-adjacent Buy, not a one-off patch.

---

## 5. Integration rules vs IC §3

| Existing | This Buy |
|---|---|
| C22/C23 Python serial | **Unchanged** (`crsf_serial.py` `git diff --stat` empty) |
| C18 `stub_main` | Still idle — `git diff --stat` empty; grep confirms no `UartBytePort`/`LoopbackUart` reference |
| C21/C27 | Unchanged (`crsf_stream.py`/`crsf_failsafe.py` `git diff --stat` empty); no UART bytes are fed into any CRSF parse this Buy |
| Native CRSF lock | Holds — tree-wide grep zero matches, including this Buy's own new files |
| Host `ctest` | Green + 6 new UART cases |

---

## 6. Tests run

### 6.1 Python — new module

`tests/test_fase_c_mcu_uart_hal_stub_b1.py` — **12 tests**, covering IC §4's T5-T8, T10-T11, and the Python half of T6 (T1-T4/T9 are the C++ Catch2 cases, T12 is this report):

| Test | Covers |
|---|---|
| `test_t5_stub_main_has_no_uart_port_reference_or_poll_loop` | T5 |
| `test_t6_crsf_serial_py_git_unchanged_and_radio_py_has_no_uart_apis` | T6 |
| `test_t7_native_tree_still_zero_crsf_elrs_tokens` | T7 |
| `test_t8_no_ioctl_or_registers_in_uart_files` | T8 |
| `test_t9_unit_test_binary_includes_uart_cases_if_built` | Python-side confirmation of T9 (skip-if-not-built, same pattern as C15/C16/C18's own wrappers) |
| `test_t10_pyproject_version_is_0_5_26` | T10 |
| `test_t11_full_suite_process_gate_placeholder` | T11 marker (real gate is the full-suite run below) |
| `test_cmake_wires_uart_into_jarvis_fc_and_unit_tests` | CMake registration sanity |
| `test_uart_files_exist_and_not_under_src_jarvis` | IC §1 placement lock |
| `test_default_safety_gate_still_reject_all_and_intent_still_not_implemented` | Safety/adapter defaults unchanged |
| `test_no_craft_or_core_imports_of_uart_and_registry_still_empty` | craft/registry isolation |
| `test_mcu_elf_still_links_if_toolchain_and_build_present` | bonus, skip-honest MCU `.elf` presence check |

```text
tests/test_fase_c_mcu_uart_hal_stub_b1.py: 12 passed
```

### 6.2 Full Python suite

```text
3584 passed, 2 skipped in 5.88s
```

Baseline before this Buy: `3572 passed, 2 skipped`. Delta: **+12**, exactly matching the new test count — zero regressions.

### 6.3 C++ — new Catch2 cases + full host `ctest`

`native/flight_control/tests/test_uart.cpp` — 6 new `TEST_CASE`s:

1. `LoopbackUart is convertible to UartBytePort*` (IC T1)
2. `LoopbackUart: write then read round-trips bytes in order` (IC T2)
3. `LoopbackUart: read on empty returns 0` (IC T3)
4. `LoopbackUart: write past capacity returns a short count, no unbounded growth` (IC T4)
5. `LoopbackUart: partial read leaves remaining bytes queued, in order` (bonus, §3)
6. `LoopbackUart: rejects zero capacity` (constructor validation)

```text
$ cmake --build build/flight_control -j4     # clean build, zero warnings
$ ctest
100% tests passed out of 51

Total Test time (real) = 0.72 sec
```

Baseline before this Buy: 45 host tests. Delta: **+6**, exactly the new `TEST_CASE` count. `fc_closed_loop_smoke` and `fc_esc_pwm_smoke` both still pass.

### 6.4 MCU cross-compile re-verification (IC's own checkpoint: "MCU `.elf` still links when toolchain present")

```text
$ export PATH="/private/tmp/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin:$PATH"
$ cmake --build build/flight_control_mcu -j4
[  6%] Building CXX object CMakeFiles/jarvis_fc.dir/src/uart.cpp.obj
[ 12%] Linking CXX static library libjarvis_fc.a
[100%] Built target fc_mcu_stub.elf
```

`uart.cpp` compiles cleanly for the ARM cross target alongside every other rung, and `fc_mcu_stub.elf` still links. `stub_main.cpp` was not touched (`git diff --stat` empty) and still never references `UartBytePort`/`LoopbackUart`.

---

## 7. Honesty / forbidden — confirmed

| Forbidden (IC §5) | Verified absent |
|---|---|
| "USART live" | Not claimed — `UartBytePort`/`LoopbackUart` never touch a peripheral register |
| "ELRS on the MCU" | Not claimed — no radio-link protocol concept exists anywhere in this Buy |
| "same as Darwin 420000" | Not claimed — no baud concept, no ioctl, anywhere in `uart.hpp`/`.cpp` |
| "IRQ UART driver" | Not claimed — no IRQ handler, no DMA, no interrupt vector touched |
| Motors / Safety execute | Not touched — `uart.hpp`/`.cpp` never reference `EscOutput`, `SafetyGate`, `submit_command`, or `step` |

Honesty line, shipped verbatim in this report and in the docs updated below:

```text
MCU UART stub != chip USART != Darwin baud != live ELRS
```

---

## 8. Module-boundary / forbidden-symbol grep (run at close of this Buy)

```text
$ git diff --stat -- src/jarvis/capabilities/crsf_serial.py src/jarvis/capabilities/radio.py \
    src/jarvis/capabilities/crsf_stream.py src/jarvis/capabilities/crsf_dual_role.py \
    src/jarvis/capabilities/crsf_stub.py src/jarvis/capabilities/crsf_failsafe.py \
    native/flight_control/mcu/
(empty)

$ grep -n "UartBytePort\|LoopbackUart\|Reset_Handler" native/flight_control/mcu/stub_main.cpp
# no match for UartBytePort/LoopbackUart (Reset_Handler itself is C18's own pre-existing symbol, unrelated to this Buy)

$ grep -rin "crsf\|elrs" native/
# no match (exit 1) — the C21-C27 native-tree lock holds, including for this Buy's own new files
```

`git status --short` at close of this Buy shows exactly the expected file set: `uart.hpp`, `uart.cpp`, `test_uart.cpp`, `test_fase_c_mcu_uart_hal_stub_b1.py` (new), `CMakeLists.txt` (modified to register the two new files), plus `pyproject.toml` + version-checkpoint test re-pins + docs. No `capabilities/`, `mcu/`, or any other rung/module files touched.

---

## 9. Files changed

**New:**
- `native/flight_control/include/jarvis/fc/uart.hpp`
- `native/flight_control/src/uart.cpp`
- `native/flight_control/tests/test_uart.cpp`
- `tests/test_fase_c_mcu_uart_hal_stub_b1.py`
- `.jes/artifacts/implementation_report_fase_c_mcu_uart_hal_stub_b1.md` (this file)

**Modified:**
- `native/flight_control/CMakeLists.txt` (`src/uart.cpp` added to `jarvis_fc`; `tests/test_uart.cpp` added to `fc_unit_tests`)
- `native/flight_control/README.md` (Layout + a new C28 paragraph, protocol-agnostic)
- `pyproject.toml` (`0.5.25` → `0.5.26`)
- ~30 pre-existing test files re-pinned from `0.5.25` to `0.5.26` (literal `'version = "X.Y.Z"' in text` pattern)
- `README.md`, `docs/ARCHITECTURE.md` (new §1c paragraph), `docs/PLATFORM_CAPABILITY_VISION.md`, `docs/IMPLEMENTATION_TASKS.md` (see §10)

---

## 10. Docs updated (honesty confirmed — not claiming CLOSED/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.26 includes (working tree — not yet tagged)" section, explicitly says "no `v0.5.26` tag yet."
- `docs/ARCHITECTURE.md` §1c — new C28 paragraph after the C26 block (C27 has no `flight_control` component, so its own paragraph lives in §1j instead — C28's chronological place in §1c follows C26's directly), top banner updated to "Working tree ahead: package `0.5.26` ... awaiting Cursor review + Engineer ★ ACCEPT — no `v0.5.26` tag yet."
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C28 block, same "landed — awaiting ... no tag yet" phrasing, honesty line verbatim.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner and the C28 table row both changed to "Landed — awaiting Cursor review + ★ ACCEPT (no `v0.5.26` tag yet)."
- `native/flight_control/README.md` — Layout section + new paragraph on `uart.hpp`/`uart.cpp`, written protocol-agnostically (native-tree lock).

No file in this Buy claims `v0.5.26` is tagged or ACCEPT CLOSED. Confirmed via `git tag -l | sort -V | tail -3` at close of this Buy: `v0.5.23`, `v0.5.24`, `v0.5.25` — `v0.5.26` does not exist yet.

---

## 11. Residual / next steps

- C29 (silicon + cited FLASH map) is next in the parked queue, per the IC's own handoff — explicitly **not** started here; it stays B0 unless the Engineer upgrades it.
- No CRSF/RC byte stream was ever routed through `UartBytePort`/`LoopbackUart` this Buy (IC §0 decision 11) — that remains later, separate work if ever prioritized.
- `mcu/stub_main.cpp` remains the C18 idle one-shot exercise of two unrelated rung APIs — this Buy did not add `UartBytePort`/`LoopbackUart` to it, matching the IC's own explicit "forbidden: UART poll loop in `Reset_Handler`/`main` this Buy."

---

## 12. Acceptance self-check vs IC §7

- T1-T4, T9 (C++ Catch2): ✅ all pass, 6/6 new cases green.
- T5-T8, T10-T11 (Python): ✅ all pass, 12/12 new tests green.
- T11 (full suite + `ctest` green): ✅ `3584 passed, 2 skipped` (Python); `51/51` (`ctest`).
- T12 (this report's honesty content): ✅ this section.
- Loopback only: ✅ `LoopbackUart` is the sole `UartBytePort` implementation shipped.
- `stub_main` idle: ✅ `git diff --stat` empty, grep confirms no reference.
- C22/C23 frozen: ✅ `crsf_serial.py` `git diff --stat` empty.
- No CRSF in native: ✅ tree-wide grep, zero matches.
- Version `0.5.26`: ✅ `pyproject.toml` + all checkpoint tests re-pinned.

**PASS** against every criterion in IC §7. **FAIL conditions** (USART registers, Darwin ioctl copied into MCU, `stub_main` UART spin, CRSF tokens in native, live-ELRS claim) — none present, verified above.
