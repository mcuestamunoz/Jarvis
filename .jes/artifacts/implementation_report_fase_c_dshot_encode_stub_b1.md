# Implementation Report — Fase C DShot encode stub (`B1-fase-c-dshot-encode-stub`)

**IC:** [`implementation_contract_fase_c_dshot_encode_stub_b1.md`](implementation_contract_fase_c_dshot_encode_stub_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-24
**Status:** Landed — awaiting Cursor review + Engineer ★ ACCEPT. Package **`0.5.29`** — **no `v0.5.29` git tag yet** (`git tag -l` still tops out at `v0.5.28`, confirmed at close of this Buy).

---

## 0. Read this first — honesty summary

This Buy names the **DShot 16-bit frame** the desk ESC (HGLRC 60A 6S,
Bluejay, DShot150/300/600) will someday want — the same move C10 made
for PWM-µs, applied to DShot: `encode_dshot_frame(throttle, telemetry)
-> uint16` computes the packet **in RAM, on the Mac**. There is still no
timer, no GPIO, no motor, and `EscOutput`/`SimulatedEscSink` (C26) keep
their PWM-µs default unchanged.

**DShot encode != pin != motors != flying.**

**Exists:** a 16-bit DShot packet computed in software, in Python and
C++, matching the exact vectors DShot's own published frame algorithm
produces. **Impossible:** an ESC seeing a waveform; the C30 LED observed
on the desk (still a separate Engineer smoke). Nothing in this Buy is
any of those.

---

## 1. Package layout vs IC §1

```text
src/jarvis/flight_software/flight_control/dshot.py   # NEW
native/flight_control/include/jarvis/fc/dshot.hpp     # NEW
native/flight_control/src/dshot.cpp                     # NEW — added to jarvis_fc
native/flight_control/tests/test_dshot.cpp              # NEW Catch2 cases (4)
tests/test_fase_c_dshot_encode_stub_b1.py                # NEW — 16 tests
```

No CRSF token was named in any C++ file (confirmed §8). `dshot.py` was not added to `flight_software/flight_control/__init__.py`'s exports — matching C25's own `rc_setpoint.py` precedent, which was never added there either; both stay reachable via their own module path, not a package-level re-export.

---

## 2. Types / API implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| `encode_dshot_frame(throttle: int, telemetry: bool = False) -> int` (Python) / `uint16_t encode_dshot_frame(int throttle, bool telemetry = false)` (C++) | §2 | ✅ exact signature both languages |
| Throw/return documented error if `throttle` outside `[0, 2047]` | §2 | ✅ `ValueError` (Python) / `std::invalid_argument` (C++), both typed, both tested |

### 2.1 Non-goals (IC §2.1) — confirmed absent

GPIO, TIM, DMA, bit-bang, ESC registers, Bluejay passthrough, C30 DFU, switching `SimulatedEscSink` off PWM — confirmed by grep (§8) and by `test_t4_pwm_encode_and_esc_output_still_pwm_unchanged` / `test_t7_no_gpio_tim_bsrr_pigpio_in_new_dshot_files`.

---

## 3. The algorithm, verified against the IC's own locked vectors (empirically, before any formal test)

```text
0 0x0 True
48 0x606 True
2047 0xffee True
telem 48: 0x617
telem changes bit4 of value pre-checksum: True
rejected 2048 throttle must be in [0, 2047], got 2048
rejected -1 throttle must be in [0, 2047], got -1
rejected 3000 throttle must be in [0, 2047], got 3000
rejected float: throttle must be an int, got 5.0
rejected bool: throttle must be an int, got True
force frames: ['0x606', '0x830b', '0xffee', '0x4488']
```

All three of the IC's own known vectors (`0 -> 0x0000`, `48 -> 0x0606`, `2047 -> 0xFFEE`) match exactly, in both languages (Python script above; C++ Catch2 case `"encode_dshot_frame: known vectors 0x0000 / 0x0606 / 0xFFEE"`). The telemetry-bit case (`48, telemetry=True -> 0x0617`) matches the IC's own worked example.

**Force-helper span check:** `force=0.0 -> throttle 48 -> 0x0606`; `force=1.0 -> throttle 2047 -> 0xFFEE`; `force=0.5 -> throttle 1048 -> 0x830B` (`48 + round(0.5 * 1999) = 48 + 1000 = 1048`) — verified the mapping never produces a throttle inside the `0..47` command range for any force in `[0, 1]`.

---

## 4. Integration rules vs IC §3

| Existing | This Buy |
|---|---|
| C10/C14/C26 PWM encode + `EscOutput` | **Unchanged** default path — `esc.py`/`esc.hpp`/`esc.cpp`/`mixer.py`/`mixer.hpp`/`mixer.cpp` all `git diff --stat` empty; `test_t4_pwm_encode_and_esc_output_still_pwm_unchanged` re-verifies `encode_motor_forces` still `1000..2000` µs and `SimulatedEscSink.apply_forces` still PWM |
| C30 `hello_led`/`stub_main` | **Byte-unchanged** — `hello_led.h`/`hello_led.c`/`stub_main.cpp` all `git diff --stat` empty |
| Native CRSF lock | Holds — tree-wide grep zero matches |
| Host `ctest` | Green + 4 new DShot cases |

---

## 5. Tests run

### 5.1 Python — new module

`tests/test_fase_c_dshot_encode_stub_b1.py` — **16 tests**, covering IC §4's T1-T7 and T9 (T8 is the C++ Catch2 case, T10 is the full-suite/ctest run, T11 is this report):

| Test | Covers |
|---|---|
| `test_t1_known_vectors` | T1 |
| `test_t2_telemetry_bit_changes_value_before_checksum` | T2 |
| `test_t3_rejects_out_of_range_throttle` | T3 |
| `test_t3b_rejects_non_int_throttle` | T3 (extended: float/str/None/bool) |
| `test_t4_pwm_encode_and_esc_output_still_pwm_unchanged` | T4 |
| `test_t5_stub_main_and_hello_led_git_unchanged` | T5 |
| `test_t6_native_tree_still_zero_crsf_elrs_tokens` | T6 |
| `test_t7_no_gpio_tim_bsrr_pigpio_in_new_dshot_files` | T7 |
| `test_t9_pyproject_version_is_0_5_29` | T9 |
| `test_t10_full_suite_process_gate_placeholder` | T10 marker (real gate is the full-suite run below) |
| `test_encode_motor_forces_dshot_endpoints_and_no_command_range_collision` | force-helper contract (IC §0 decision 7) |
| `test_encode_motor_forces_dshot_never_calls_pwm_encode_or_esc_output` | parallel-path isolation |
| `test_dshot_not_under_capabilities_or_core` | IC §1 placement lock |
| `test_no_command_table_invented` | IC §0 decision 6 |
| `test_default_safety_gate_still_reject_all` | Safety default unchanged |
| `test_no_craft_or_core_imports_of_dshot_and_registry_still_empty` | craft/registry isolation |

```text
tests/test_fase_c_dshot_encode_stub_b1.py: 16 passed
```

**A stale, pre-C31 test needed a disclosed, narrow update, not a weakening (same pattern as C26's esc.cpp and C30's stub_main.cpp fixes):** C13's own `tests/test_fase_c_cpp_flight_control_scaffold_b1.py::test_t4_no_gpio_or_hardware_io_symbols_in_native_tree` used `"dshot"` as a blanket-forbidden substring across every `.cpp`/`.hpp` in `native/flight_control/`, written when no legitimate DShot code existed anywhere in the tree. This Buy's own `dshot.hpp`/`dshot.cpp`/`test_dshot.cpp` legitimately contain the word. Rather than deleting the check, I added a narrow, disclosed, named-file exclusion (only for those three C31-authorized files) for the single token `"dshot"` — every other forbidden token (`gpio`, `pigpio`, `termios`, etc.) stays checked in those same three files, and `"dshot"` stays forbidden in every other file in the tree (including any future one), which is exactly the guard that would catch DShot logic leaking into, say, `mixer.cpp` or `hello_led.c`.

### 5.2 Full Python suite

```text
3635 passed, 2 skipped in 7.14s
```

Baseline before this Buy: `3619 passed, 2 skipped`. Delta: **+16**, exactly matching the new test count — zero regressions, including the retargeted C13 test.

### 5.3 C++ — new Catch2 cases + full host `ctest`

`native/flight_control/tests/test_dshot.cpp` — 4 new `TEST_CASE`s:

1. `encode_dshot_frame: known vectors 0x0000 / 0x0606 / 0xFFEE` (IC T1)
2. `encode_dshot_frame: telemetry bit changes value before checksum` (IC T2)
3. `encode_dshot_frame: rejects throttle outside [0, 2047]`
4. `encode_motor_forces_dshot: force endpoints map to throttle 48 and 2047`

```text
$ cmake --build build/flight_control -j4     # clean build, zero warnings
$ ctest
100% tests passed out of 55

Total Test time (real) = 0.67 sec
```

Baseline before this Buy: 51 host tests. Delta: **+4**, exactly the new `TEST_CASE` count. `fc_closed_loop_smoke` and `fc_esc_pwm_smoke` both still pass.

### 5.4 MCU cross-compile re-verification (not required by IC §4, done for completeness)

```text
$ export PATH="/private/tmp/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin:$PATH"
$ cmake --build build/flight_control_mcu -j4
[  5%] Building CXX object CMakeFiles/jarvis_fc.dir/src/dshot.cpp.obj
[ 11%] Linking CXX static library libjarvis_fc.a
[100%] Built target fc_mcu_stub.elf
```

`dshot.cpp` compiles cleanly for the ARM cross target alongside every other rung, and `fc_mcu_stub.elf` still links (`--gc-sections` discards the unreferenced DShot symbols from the final image, since `stub_main.cpp` never calls them — confirmed byte-unchanged, §4).

---

## 6. Honesty / forbidden — confirmed

| Forbidden (IC §5, §0 decision 13) | Verified absent |
|---|---|
| "DShot live" | Not claimed — no waveform, no pin, anywhere in this Buy |
| "motors spin" | Not claimed — pure integer encoding |
| "GPIO" | Not touched — grep-clean in both new files |
| "this is Bluejay on the ESC" | Not claimed — Bluejay named only as the desk ESC's own firmware, in citation comments |
| "C30 LED was seen on desk" | Not claimed — this report explicitly repeats C30's own "not flashed on desk" disclosure, unchanged |

Honesty line, shipped verbatim in this report and in the docs updated below:

```text
DShot encode != pin != motors != flying
```

---

## 7. Module-boundary / forbidden-symbol grep (run at close of this Buy)

```text
$ git diff --stat -- native/flight_control/mcu/stub_main.cpp native/flight_control/mcu/hello_led.c \
    native/flight_control/mcu/hello_led.h native/flight_control/mcu/startup_cortex_m4.c \
    native/flight_control/mcu/syscalls_stub.c native/flight_control/cmake/toolchains/arm-none-eabi.cmake \
    native/flight_control/include/jarvis/fc/esc.hpp native/flight_control/src/esc.cpp \
    src/jarvis/flight_software/flight_control/esc.py src/jarvis/flight_software/flight_control/mixer.py \
    native/flight_control/include/jarvis/fc/mixer.hpp native/flight_control/src/mixer.cpp
(empty)

$ grep -rin "crsf|elrs" native/
# no match (exit 1) — the C21-C30 native-tree lock holds
```

`git status --short` at close of this Buy shows exactly the expected file set: `dshot.hpp`, `dshot.cpp`, `test_dshot.cpp`, `dshot.py`, `test_fase_c_dshot_encode_stub_b1.py` (new), `CMakeLists.txt` (modified to register the two new C++ files), plus `pyproject.toml` + version-checkpoint test re-pins + the one disclosed C13-test retargeting + docs. No `hello_led.{h,c}`, `stub_main.cpp`, `esc.{py,hpp,cpp}`, or `mixer.{py,hpp,cpp}` touched.

---

## 8. Files changed

**New:**
- `src/jarvis/flight_software/flight_control/dshot.py`
- `native/flight_control/include/jarvis/fc/dshot.hpp`
- `native/flight_control/src/dshot.cpp`
- `native/flight_control/tests/test_dshot.cpp`
- `tests/test_fase_c_dshot_encode_stub_b1.py`
- `.jes/artifacts/implementation_report_fase_c_dshot_encode_stub_b1.md` (this file)

**Modified:**
- `native/flight_control/CMakeLists.txt` (`src/dshot.cpp` added to `jarvis_fc`; `tests/test_dshot.cpp` added to `fc_unit_tests`)
- `tests/test_fase_c_cpp_flight_control_scaffold_b1.py` (disclosed, narrow retargeting of the stale C13 "dshot" blanket-forbidden token — §5.1)
- `pyproject.toml` (`0.5.28` → `0.5.29`)
- ~30 pre-existing test files re-pinned from `0.5.28` to `0.5.29` (literal `'version = "X.Y.Z"' in text` pattern)
- `README.md`, `docs/ARCHITECTURE.md` (new §1c paragraph after C30), `docs/PLATFORM_CAPABILITY_VISION.md`, `docs/IMPLEMENTATION_TASKS.md` (see §9)

---

## 9. Docs updated (honesty confirmed — not claiming CLOSED/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.29 includes (working tree — not yet tagged)" section, explicitly says "no `v0.5.29` tag yet."
- `docs/ARCHITECTURE.md` §1c — new C31 paragraph after the C30 block, top banner updated to "Working tree ahead: package `0.5.29` ... awaiting Cursor review + Engineer ★ ACCEPT — no `v0.5.29` tag yet."
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C31 block, same "landed — awaiting ... no tag yet" phrasing, honesty line verbatim.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner and the C31 table row both changed to "Landed — awaiting Cursor review + ★ ACCEPT (no `v0.5.29` tag yet)."

No file in this Buy claims `v0.5.29` is tagged or ACCEPT CLOSED, and none claims the C30 LED has been observed on the desk (that disclosure is repeated verbatim from C30's own report). Confirmed via `git tag -l | sort -V | tail -3` at close of this Buy: `v0.5.26`, `v0.5.27`, `v0.5.28` — `v0.5.29` does not exist yet.

---

## 10. Residual / next steps

- DShot *wire* (GPIO/TIM/DMA bit-bang), on-chip USART, C30's own desk DFU smoke, and craft↔FS all remain independently parked axes per the existing process lock and the 2026-09-24 "bench before silicon" engineer note — none opened by this Buy.
- No command table (beep, 3D mode, save-settings) was implemented for the `0..47` DShot command range — this Buy only documents that range exists and encodes whatever 11-bit value it is given, per the IC's own explicit non-goal.
- `EscOutput`'s own abstract `apply_forces` was not touched or overloaded for DShot — a future pin driver would encode DShot inside its own override, reusing `encode_dshot_frame`, not by editing `esc.hpp`/`esc.cpp`.

---

## 11. Acceptance self-check vs IC §7

- T1-T9 (vectors, telemetry bit, range rejection, PWM unchanged, C30 freeze, native grep, no GPIO/TIM, version): ✅ all pass, 16/16 new Python tests + 4/4 new Catch2 cases green.
- T10 (full suite + `ctest` green): ✅ `3635 passed, 2 skipped` (Python); `55/55` (`ctest`).
- T11 (this report's honesty content): ✅ this section.
- PWM sink unchanged: ✅ `git diff --stat` empty on `esc.py`/`esc.hpp`/`esc.cpp`/`mixer.py`/`mixer.hpp`/`mixer.cpp`.
- C30 LED files frozen: ✅ `git diff --stat` empty on `hello_led.{h,c}`/`stub_main.cpp`.
- Version `0.5.29`: ✅ `pyproject.toml` + all checkpoint tests re-pinned.

**PASS** against every criterion in IC §7. **FAIL conditions** (GPIO/timer, `apply_forces` switched to DShot, command table invented as product, live-motor claim) — none present, verified above.
