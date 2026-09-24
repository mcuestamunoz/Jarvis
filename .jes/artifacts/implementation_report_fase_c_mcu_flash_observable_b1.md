# Implementation Report — Fase C MCU flash + one observable (`B1-fase-c-mcu-flash-observable`)

**IC:** [`implementation_contract_fase_c_mcu_flash_observable_b1.md`](implementation_contract_fase_c_mcu_flash_observable_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-24
**Status:** Landed — awaiting Cursor review + Engineer ★ ACCEPT. Package **`0.5.28`** — **no `v0.5.28` git tag yet** (`git tag -l` still tops out at `v0.5.27`, confirmed at close of this Buy). Per the IC's own §8 handoff: this Buy's **software** gates are complete and green; the LED was **not** observed on the desk board in this session (no hardware was flashed as part of implementing this software) — see §11.

---

## 0. Read this first — honesty summary

C29 B1 left two residuals uncorrected in code: **(a)** `stub_main`'s
idle loop was an empty `while (true)` — a successfully-reached
`Reset_Handler` was indistinguishable from a dead board; **(b)** CMake
had no dependency on `linker_cortex_m4.ld`, so editing that file never
triggered a relink (C29's own T9 test worked around this by deleting the
`.elf` first — a test-side workaround, never the real fix). This Buy
closes **both**, and adds the flash path to make the fix observable:
USB DFU + a `.bin` artifact + a PC13 status-LED toggle cited from this
desk's own Betaflight target.

**Flashed LED blink != flying != DShot != USART live != Betaflight HGLRCF405V2.**

**Exists:** an image the Engineer can DFU onto the desk F405 whose idle
loop toggles the cited status LED; CMake now relinks if the linker
script changes. **Impossible:** the craft flying; ESCs seeing DShot;
ELRS on UART2; this repo becoming Betaflight. Nothing in this Buy is any
of those — no CMSIS, no HAL, no motor pin, no USART, no IRQ/DMA.

---

## 1. Package layout vs IC §1

```text
native/flight_control/
  CMakeLists.txt                 # LINK_DEPENDS + POST_BUILD .bin
  mcu/hello_led.h                 # NEW — declarations
  mcu/hello_led.c                 # NEW — PC13 MMIO + busy-wait
  mcu/stub_main.cpp                # one-shot jarvis_fc, then hello_led_spin()
  README.md                        # DFU procedure + restore BF + honesty

tests/
  test_fase_c_mcu_flash_observable_b1.py   # NEW — 21 tests
```

No STM32Cube/CMSIS was added under `src/jarvis/`. No CRSF token was named in any touched file (confirmed §8). No `MOTOR`/`C06`-`C09` pin was driven (confirmed §6, T5).

---

## 2. Types / API implemented vs IC §2

| Item | IC ref | Match |
|---|---|---|
| `void hello_led_init(void);` — RCC GPIOCEN + PC13 output; dummy-read after clock enable | §2 | ✅ exact |
| `void hello_led_spin(void) __attribute__((noreturn));` — toggle PC13 via BSRR, busy-wait, forever | §2 | ✅ exact |
| `main` keeps the C18 one-shot, then calls `hello_led_spin()` | §2 | ✅ via `hello_led_init()` then `hello_led_spin()` |
| Busy-wait: `volatile` counter, documented "roughly visible, not calibrated" | §2 | ✅ `volatile uint32_t counter` local; header/source comments both say "uncalibrated"/"visible flicker" |

### 2.1 Non-goals (IC §2.1) — confirmed absent

DShot, motor pins, USART, IRQ, DMA, PLL, CMSIS pack, OpenOCD as a required dependency, Safety execute, craft↔FS, C21 Python on the MCU, Darwin `IOSSIOSPEED` — confirmed by grep (§8) and by the new test suite's `test_t5_no_pa8_as_led_and_no_motor_pin_writes` / `test_t8_no_cmsis_or_hal_includes_in_new_mcu_files` / `test_no_nvic_or_irq_or_dma_in_new_files`.

---

## 3. The PC13 citation (IC §0 decision 4, locked verbatim)

Betaflight's own unified target for this desk hardware —
`HGLR-HGLRCF405V2.config` — names the status LED with `resource LED 1
C13`. This is quoted, in exact form, in `hello_led.c`'s own header
comment and in this report. **PA8 was deliberately not used**: on that
same V2 target, PA8 is `resource MOTOR 6 A08` — a motor-timer pin, not
the status LED (an older, non-V2 `HGLRCF405` target used PA8 for the
LED; this board's own current target does not). **PB1 was deliberately
not used either**: `LED_STRIP` drives addressable wire LEDs, not the
onboard status LED. Confirmed absent from real code by
`test_t5_no_pa8_as_led_and_no_motor_pin_writes` (checks for `GPIOA`/the
GPIOA base address `0x40020000`, and for the bare word "motor", in
`hello_led.c`'s own real code, not its citation comments).

---

## 4. The MMIO register map (IC §0 decision 6, locked verbatim)

| Register | Address | Use |
|---|---|---|
| `RCC` base | `0x40023800` | cited, documented |
| `RCC_AHB1ENR` | `0x40023830` | bit 2 = GPIOCEN, set to enable the GPIOC peripheral clock |
| `GPIOC` base | `0x40020800` | cited, documented |
| `GPIOC_MODER` | `0x40020800` | pin 13, bits [27:26] = `01` (general-purpose output) |
| `GPIOC_BSRR` | `0x40020818` | `BS13` = bit 13 (set high), `BR13` = bit 29 (set low) |

All four addresses appear as bare `volatile uint32_t *` pointer casts in `hello_led.c` — no CMSIS device header, no ST HAL, no vendor SDK. A dummy read-back of `RCC_AHB1ENR` immediately follows the clock-enable write, per RM0090's own documented clock-enable delay. Confirmed present by `test_t4_led_source_has_cited_mmio_addresses`.

---

## 5. Verified — a real relink, and a real `.bin`, not stale artifacts

**LINK_DEPENDS (closing C29 N1), verified empirically before writing any test:**

```text
$ elf_mtime_before=<mtime of pre-existing .elf>
$ touch native/flight_control/mcu/linker_cortex_m4.ld
$ cmake --build build/flight_control_mcu -j4 --target fc_mcu_stub.elf
[ 70%] Built target jarvis_fc
[ 76%] Linking CXX executable fc_mcu_stub.elf
C30: objcopy fc_mcu_stub.elf -> fc_mcu_stub.bin (DFU image, load addr 0x08000000)
[100%] Built target fc_mcu_stub.elf
$ elf_mtime_after=<mtime of .elf>
RELINKED (LINK_DEPENDS works)   # mtime_after > mtime_before, elf NOT deleted first
```

This is the exact scenario C29's own T9 could only fake by deleting the `.elf` first — this Buy's `set_property(TARGET fc_mcu_stub.elf APPEND PROPERTY LINK_DEPENDS ...)` makes CMake genuinely aware that a linker-script edit invalidates the link step, without any test-side workaround. The new test suite's own `test_t2_touching_linker_script_relinks_without_deleting_elf_if_toolchain_present` reproduces this exact sequence and asserts on the mtime delta.

**Real symbols, real load address:**

```text
$ arm-none-eabi-readelf -h build/flight_control_mcu/fc_mcu_stub.elf
  Entry point address:               0x8000045
$ arm-none-eabi-readelf -l build/flight_control_mcu/fc_mcu_stub.elf
  LOAD  0x001000 0x08000000 0x08000000 0x14144 0x14144 R E 0x1000
$ arm-none-eabi-nm build/flight_control_mcu/fc_mcu_stub.elf | grep hello_led
  080000fc T hello_led_init
  0800012c T hello_led_spin
```

Both `hello_led_init`/`hello_led_spin` are real, defined (`T`) symbols — not merely referenced. Load address is still `0x08000000`, unchanged from C29's own citation.

**`.bin` produced:**

```text
$ ls -la build/flight_control_mcu/fc_mcu_stub.bin
-rwxr-xr-x  84424 bytes
```

---

## 6. Tests run

### 6.1 Python — new module

`tests/test_fase_c_mcu_flash_observable_b1.py` — **21 tests**, covering IC §4's T1-T14 (T15 is the full-suite/ctest run, T16 is this report):

| Test | Covers |
|---|---|
| `test_t1_cmake_sets_link_depends_on_linker_script` | T1 |
| `test_t2_touching_linker_script_relinks_without_deleting_elf_if_toolchain_present` | T2 |
| `test_t3_led_source_cites_pc13_and_hglrcf405v2` | T3 |
| `test_t4_led_source_has_cited_mmio_addresses` | T4 |
| `test_t5_no_pa8_as_led_and_no_motor_pin_writes` | T5 |
| `test_t6_stub_main_still_calls_jarvis_fc_once_and_idle_is_not_empty_while_true` | T6 |
| `test_t7_honesty_no_longer_claims_never_flashed_and_has_the_new_line` | T7 |
| `test_t8_no_cmsis_or_hal_includes_in_new_mcu_files` | T8 |
| `test_t9_native_tree_still_zero_crsf_elrs_tokens` | T9 |
| `test_t10_bin_produced_and_load_address_unchanged_if_toolchain_present` | T10 |
| `test_t11_uart_hpp_and_crsf_serial_py_git_unchanged` | T11 |
| `test_t12_readme_documents_dfu_util_and_restore_and_props_off` | T12 |
| `test_t13_module_import_does_not_require_a_plugged_dfu_device` | T13 |
| `test_t14_pyproject_version_is_0_5_28` | T14 |
| `test_t15_full_suite_process_gate_placeholder` | T15 marker (real gate is the full-suite run below) |
| `test_hello_led_files_not_under_src_jarvis` | IC §1 placement lock |
| `test_startup_and_syscalls_git_unchanged` | scope isolation |
| `test_toolchain_flags_unchanged` | C16 flags frozen |
| `test_no_nvic_or_irq_or_dma_in_new_files` | IC §0 decision 18 |
| `test_default_safety_gate_still_reject_all` | Safety default unchanged |
| `test_no_craft_or_core_imports_reference_hello_led_and_registry_still_empty` | craft/registry isolation |

```text
tests/test_fase_c_mcu_flash_observable_b1.py: 21 passed
```

**No board plugged in for any of these** — T2/T10 drive the actual toolchain build+relink and inspect the resulting artifacts on disk; none of them enumerate USB devices or attempt a DFU transfer (`test_t13` documents this contract explicitly).

**A stale, C29-era test needed a disclosed update, not a weakening (same pattern as C26's own esc.cpp fix):** C29 B1's own `tests/test_fase_c_silicon_cited_flash_map_b1.py::test_t5_stub_main_git_unchanged` asserted `stub_main.cpp` stays byte-unchanged forever — a check meaningful for C29 B1's own scope (which never needed to touch that file), now legitimately contradicted by this Buy's own ★-approved IC (§0 decision 8: *"stub_main.cpp MAY change this Buy — unlike C28/C29 freeze"*). Rather than deleting the check, I retargeted it (renamed `test_t5_stub_main_unchanged_by_c29b1_itself`) to assert the narrower, still-true fact that no CMSIS/HAL/vendor-header content exists in the file — a real code check (comment-stripped, to avoid a second honesty-prose-vs-real-usage false positive caught while fixing this), not a byte-freeze that this Buy's own IC explicitly authorizes breaking.

### 6.2 Full Python suite

```text
3619 passed, 2 skipped in 8.17s
```

Baseline before this Buy: `3598 passed, 2 skipped`. Delta: **+21**, exactly matching the new test count — zero regressions, including the retargeted C29 B1 test.

### 6.3 Host `ctest` (unaffected, re-confirmed)

```text
100% tests passed out of 51
```

Identical to the C29 baseline — `hello_led.c` is MCU-cross-compile-only and is never compiled or linked into the host build.

### 6.4 MCU cross-compile (fresh configure + build + relink test)

Covered in full in §5 above — a genuine build, a genuine forced relink, and genuine artifact inspection were performed, not a stale re-run.

---

## 7. Honesty / forbidden — confirmed

| Forbidden (IC §5, §0 decision 20) | Verified absent |
|---|---|
| "Flying" | Not claimed anywhere |
| "DShot live" | Not touched — no motor pin, no DShot encoding anywhere in this Buy |
| "USART / ELRS live" | Not touched — no USART register, no radio-link protocol named |
| "this is Betaflight HGLRCF405V2" | Explicitly disclaimed in every honesty comment/doc this Buy touched |
| "1 ms SysTick" | Not claimed — the busy-wait is explicitly documented as uncalibrated |
| "CMake workaround T9 is the fix" | Explicitly disclaimed — §5/§6 both state `LINK_DEPENDS` is this Buy's own real fix; C29's T9 stays a historical test, not re-presented as the solution |

Honesty line, shipped verbatim in this report and in the docs updated below:

```text
flashed LED blink != flying != DShot != USART live != Betaflight HGLRCF405V2
```

---

## 8. Module-boundary / forbidden-symbol grep (run at close of this Buy)

```text
$ git diff --stat -- native/flight_control/mcu/startup_cortex_m4.c native/flight_control/mcu/syscalls_stub.c \
    native/flight_control/cmake/toolchains/arm-none-eabi.cmake native/flight_control/include/jarvis/fc/uart.hpp \
    native/flight_control/src/uart.cpp src/jarvis/capabilities/crsf_serial.py
(empty)

$ grep -rin "crsf|elrs" native/
# no match (exit 1) — the C21-C29 native-tree lock holds
```

`git status --short` at close of this Buy shows exactly the expected file set: `hello_led.h`, `hello_led.c` (new), `CMakeLists.txt` (modified — `LINK_DEPENDS` + `POST_BUILD`), `stub_main.cpp` (modified — LED spin), `native/flight_control/README.md` (modified — DFU section + honesty), `test_fase_c_mcu_flash_observable_b1.py` (new), plus `pyproject.toml` + version-checkpoint test re-pins + docs + one disclosed C29-era test update. No `startup_cortex_m4.c`, `syscalls_stub.c`, toolchain file, `uart.{hpp,cpp}`, or `crsf_serial.py` touched.

---

## 9. Files changed

**New:**
- `native/flight_control/mcu/hello_led.h`
- `native/flight_control/mcu/hello_led.c`
- `tests/test_fase_c_mcu_flash_observable_b1.py`
- `.jes/artifacts/implementation_report_fase_c_mcu_flash_observable_b1.md` (this file)

**Modified:**
- `native/flight_control/CMakeLists.txt` (`mcu/hello_led.c` added to `fc_mcu_stub.elf`; `LINK_DEPENDS` property; `POST_BUILD` `.bin` step)
- `native/flight_control/mcu/stub_main.cpp` (idle loop replaced by `hello_led_init()`/`hello_led_spin()`; honesty comment rewritten — "never flashed" removed, replaced with the DFU-aware honesty line)
- `native/flight_control/README.md` (new "Flash it: USB DFU (C30)" section + `hello_led.c` Layout paragraph + C18 section's "what this is not" updated)
- `pyproject.toml` (`0.5.27` → `0.5.28`)
- `tests/test_fase_c_silicon_cited_flash_map_b1.py` (disclosed, retargeted update to the stale `stub_main.cpp` byte-freeze test — §6.1)
- ~30 pre-existing test files re-pinned from `0.5.27` to `0.5.28` (literal `'version = "X.Y.Z"' in text` pattern)
- `README.md`, `docs/ARCHITECTURE.md` (new §1c paragraph after C29 B1), `docs/PLATFORM_CAPABILITY_VISION.md`, `docs/IMPLEMENTATION_TASKS.md` (see §10)

---

## 10. Docs updated (honesty confirmed — not claiming CLOSED/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.28 includes (working tree — not yet tagged)" section, explicitly says "no `v0.5.28` tag yet."
- `docs/ARCHITECTURE.md` §1c — new C30 paragraph after the C29 B1 block, top banner updated to "Working tree ahead: package `0.5.28` ... awaiting Cursor review + Engineer ★ ACCEPT — no `v0.5.28` tag yet."
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C30 block, same "landed — awaiting ... no tag yet" phrasing, honesty line verbatim.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner and the C30 table row both changed to "Landed — awaiting Cursor review + ★ ACCEPT (no `v0.5.28` tag yet)."
- `native/flight_control/README.md` — full "Flash it: USB DFU (C30)" procedure (props-off/battery-off, `dfu-util` command, restore via Betaflight Configurator target HGLRCF405V2), plus the `hello_led.c` Layout paragraph and the C18 section's "what this is not" list corrected (no longer claims "flashed to any board").

No file in this Buy claims `v0.5.28` is tagged or ACCEPT CLOSED. Confirmed via `git tag -l | sort -V | tail -3` at close of this Buy: `v0.5.25`, `v0.5.26`, `v0.5.27` — `v0.5.28` does not exist yet.

---

## 11. Desk smoke — explicitly not performed this session

Per the IC's own §8 handoff: *"Engineer ACCEPT of the software Buy does not require the LED to have been seen if DFU was not attempted; the report must then say not flashed on desk."*

**Not flashed on desk.** This session implemented and verified the software side only — the cross-compile, the relink behavior, the `.bin` artifact, and the register-level source citations. No `dfu-util` command was run against real hardware, no board was plugged in, and the LED has not been visually confirmed to blink. That remains an Engineer-performed desk smoke (props off, LiPo disconnected during DFU, USB-powered observation afterward), to be done separately and reported back before anyone claims "hello-world on silicon" as an observed fact rather than a built-and-inspected one.

---

## 12. Residual / next steps

- GPIO/DShot wiring, on-chip USART, and craft↔FS all remain independently parked axes per the existing process lock — none opened by this Buy.
- The desk LED smoke (§11) is the natural next confirmation step, independent of any further software Buy.
- `startup_cortex_m4.c` still declares only the 16 system exceptions (no NVIC/EXTI) — this Buy's IC explicitly locked "GPIO toggle is polled in `main`" and forbade adding interrupt infrastructure; that stays a later, separate decision if ever prioritized.

---

## 13. Acceptance self-check vs IC §7

- T1-T14 (Python + CMake/source-level): ✅ all pass, 21/21 new tests green.
- T15 (full suite + `ctest` green): ✅ `3619 passed, 2 skipped` (Python); `51/51` (`ctest`).
- T16 (this report's honesty content): ✅ this section.
- PC13 cited from HGLRCF405V2: ✅ §3.
- `LINK_DEPENDS` is real (not a T9-only fix): ✅ §5, verified via mtime delta without deleting the `.elf`.
- `.bin` produced: ✅ §5.
- No CMSIS pack, no motor pins: ✅ grep + dedicated tests.
- Version `0.5.28`: ✅ `pyproject.toml` + all checkpoint tests re-pinned.

**PASS** against every criterion in IC §7. **FAIL conditions** (PA8 guessed, flash-of-empty-idle with no observable, CMake still missing `LINK_DEPENDS`, Cube/CMSIS required, DShot/USART/IRQ, pytest requiring a plugged board, live-Betaflight/flying claim) — none present, verified above.
