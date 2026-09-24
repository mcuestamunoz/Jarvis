# Implementation Contract — Fase C MCU flash + one observable (`B1-fase-c-mcu-flash-observable`)

**Project:** Jarvis  
**Date:** 2026-09-24  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer desk smoke (LED blink ≠ flying · DFU ≠ DShot · overwrite Betaflight is reversible only via reflash · CMake `.ld` dep ≠ “the board works”)

**Status:** ★ ACCEPT CLOSED @ **`v0.5.28`** (software). LED **not observed** on desk. DFU smoke parked until bench — [bench note](engineer_note_fase_c_bench_before_silicon_2026_09_24.md).  
**Parents:**
- Engineer 2026-09-24: desk stack **HGLRC F460 6S V1** / FC **HGLRC F405 8S V1** / MCU **STM32F405** / BF target **HGLRCF405V2**  
- [C29 B1 ★ ACCEPT](implementation_contract_fase_c_silicon_cited_flash_map_b1.md) — cited FLASH/RAM map @ **`v0.5.27`**; **N1 residual:** `-T linker_cortex_m4.ld` is **not** a CMake link dependency; T9 delete-then-rebuild is a **test workaround**, not a CMake fix  
- [C18 ★ ACCEPT](implementation_contract_fase_c_cpp_mcu_freestanding_elf_b1.md) — `fc_mcu_stub.elf` idle `main` @ **`v0.5.16`** (one-shot `jarvis_fc`, then empty `while (true)`)  
- [C16 ★ ACCEPT](implementation_contract_fase_c_cpp_mcu_cross_compile_b1.md) — `-mcpu=cortex-m4 -mthumb -mfloat-abi=soft` @ **`v0.5.14`**  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — first **hello-world on this silicon**: produce a DFU-able image whose idle loop **toggles the onboard status LED**, and close C29 B1 N1 so a `.ld` edit **relinks**. This is the Buy that makes “flash the board” distinguishable from a dead/bricked FC.  
**Package:** bump Jarvis `pyproject.toml` to **`0.5.28`**; git tag **`v0.5.28`** only after Engineer ACCEPT.  
**Not** DShot / motor pins · not chip USART / IRQ / DMA · not CMSIS / STM32Cube pack · not PLL clock tree · not live ELRS · not Safety execute · not craft↔FS · not “this is Betaflight” · not a claim of timed milliseconds.

**Outputs (required):**
1. CMake: `fc_mcu_stub.elf` **`LINK_DEPENDS`** on `mcu/linker_cortex_m4.ld` (close C29 N1)  
2. Post-build **`.bin`** (and optionally `.hex`) from the ELF, load address still **`0x08000000`**  
3. Bare-metal **PC13** toggle after the existing one-shot `jarvis_fc` exercise — cited pin + cited STM32F405 MMIO, **no** CMSIS headers  
4. Tests: `tests/test_fase_c_mcu_flash_observable_b1.py` — CMake dep + pin/MMIO citations + `.bin` when toolchain present; **no plugged board required for green**  
5. `native/flight_control/README.md` — USB DFU procedure + overwrite/restore Betaflight + props-off  
6. `.jes/artifacts/implementation_report_fase_c_mcu_flash_observable_b1.md`  
7. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **flashed LED blink ≠ flying ≠ DShot ≠ Betaflight ≠ USART live**  
8. `pyproject.toml` → **`0.5.28`** (+ re-pin `0.5.27` checkpoints)

**Checkpoint:** package **`0.5.28`** · Python suite ≥ **3598** + new tests · host `ctest` still green · MCU `.elf` still ARM Cortex-M4 when toolchain present · C28 `uart.hpp` / C22–C23 Python serial **byte-unchanged**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-mcu-flash-observable`** — flash path + **one** human-visible signal + CMake linker-script dependency |
| 2 | One front | Do **not** fold DShot, motor GPIO (C06–C09), USART ISR, CMSIS/STM32Cube pack, PLL/HSE clock tree, FPU ABI change, Safety execute, live ELRS, or craft↔FS |
| 3 | Why this Buy (the gap) | C29 B1 left **two** residuals **uncorrected in code**: (a) **silent idle** — `stub_main` one-shot then empty `while (true)`; a successful Reset_Handler looks like a dead board; (b) **CMake N1** — `-T` is not an implicit dep; T9 delete-elf-then-rebuild is a **workaround**. This Buy **closes both**. Do not ship flash-of-idle-stub. |
| 4 | Observable (locked) | Onboard **status LED** = **PC13**. Citation (must appear in source comment **and** report): Betaflight unified target `HGLR-HGLRCF405V2.config` line `resource LED 1 C13` — https://raw.githubusercontent.com/betaflight/unified-targets/master/configs/default/HGLR-HGLRCF405V2.config . **Forbidden:** copy **PA8** from the older **HGLRCF405** target (on V2, `resource MOTOR 6 A08` — PA8 is a motor timer, not the status LED). **Forbidden:** `LED_STRIP` **PB1** (wire LEDs, not the onboard status LED) |
| 5 | If the V2 line were missing | Fail closed. Do **not** guess PA8. UART-byte fallback is **out of this Buy** (would collide with RX on UART2 / need cited USART pins + baud). LED citation is already in hand — use it |
| 6 | MMIO (STM32F405, RM0090) | Bare `volatile` stores. **No** `stm32f4xx.h`, **no** HAL. Locked addresses: **RCC** `0x40023800`, **RCC_AHB1ENR** `0x40023830` bit **2** = GPIOCEN; **GPIOC** `0x40020800`; **GPIOC_MODER** `0x40020800` pin 13 bits 27:26 = `01` (output); **GPIOC_BSRR** `0x40020818` BS13 bit 13 / BR13 bit 29. After enabling GPIOC clock, **dummy-read** AHB1ENR (STM32 clock-enable delay). Cite RM0090 register map / RCC_AHB1ENR / GPIOx_MODER / GPIOx_BSRR in the comment |
| 7 | Clock | Use **reset default HSI 16 MHz**. **Forbidden:** PLL / HSE / `SystemInit` from a Cube pack this Buy. Busy-wait loop is **not** a millisecond clock — disclose “visible flicker, not 1.000 Hz” |
| 8 | `stub_main.cpp` | **May change this Buy** (unlike C28/C29 freeze). Keep the existing one-shot `ImuLowPassFilter` + `encode_motor_forces`. Replace the empty idle `while (true)` with a call that **never returns** and toggles PC13. Rewrite the “This file is never flashed” comment — it becomes a lie the moment we document DFU |
| 9 | File split | Prefer `mcu/hello_led.c` (+ tiny header or `extern "C"`) so MMIO stays out of `jarvis_fc`. Do **not** put GPIO registers in `src/jarvis/` or in the host library |
| 10 | CMake N1 close | `set_target_properties(fc_mcu_stub.elf … LINK_DEPENDS <abs path to linker_cortex_m4.ld>)` **or** `set_property(… APPEND PROPERTY LINK_DEPENDS …)`. Equivalent. Tests must prove the property exists **even when the ARM toolchain is absent** (source/CMake grep). When the MCU build dir exists: `os.utime` on the `.ld` then `cmake --build … --target fc_mcu_stub.elf` must **relink** (elf mtime increases) **without** deleting the elf first |
| 11 | Image for DFU | POST_BUILD `objcopy -O binary` → `fc_mcu_stub.bin` next to the elf. LOAD/VirtAddr remains **`0x08000000`** (C29 map). Optional `.hex` is fine; `.bin` is required |
| 12 | Flash path (primary) | **USB DFU** via the STM32 built-in bootloader (BOOT button + `dfu-util -a 0 -s 0x08000000:leave -D fc_mcu_stub.bin`). Document in native README. **Not** a pytest gate — skip/absent-device. OpenOCD / ST-Link / `st-flash` are **optional extras**, not required deps. Note: V2 maps `OSD_CS` to **A13** (SWDIO) in Betaflight — USB DFU is the honest primary path on this board |
| 13 | Desk smoke (Engineer, not CI) | Props **off**. LiPo **disconnected** during USB DFU. After flash, power the FC from USB (or battery with props still off) and look at the **onboard status LED**. Blink = Reset_Handler reached + GPIOC writes. No blink → report it; do not “fix” by driving motor pins. Polarity may be active-low — toggling both edges is enough |
| 14 | Overwrite / restore | This image **replaces Betaflight** until the Engineer reflashes target **HGLRCF405V2** from Betaflight Configurator (DFU). README must say that in one paragraph. Jarvis is **not** claiming to be that firmware |
| 15 | Native-tree lock | **Zero** `crsf`/`elrs` under `native/` (even comments) |
| 16 | C16 flags | Keep `-mcpu=cortex-m4 -mthumb -mfloat-abi=soft`. No FPU hard-float this Buy |
| 17 | C28 / host serial | `uart.hpp` / `LoopbackUart` **byte-unchanged**. `crsf_serial.py` **byte-unchanged**. No USART registers |
| 18 | Vector table | `startup_cortex_m4.c` may stay 16 system exceptions. GPIO toggle is **polled** in `main`. **Forbidden:** NVIC / EXTI this Buy |
| 19 | Version | **`0.5.27` → `0.5.28`**; tag **`v0.5.28`** on ACCEPT only |
| 20 | Forbidden claims | “Flying” · “DShot live” · “USART / ELRS live” · “this is Betaflight HGLRCF405V2” · “1 ms SysTick” · “CMake workaround T9 is the fix” (T9 stays a C29 historical test; **this** Buy’s LINK_DEPENDS is the fix) |

**Product sentence:**

```text
Flashear el stub del STM32F405 con un LED que se ve (PC13, target
HGLRCF405V2) y hacer que CMake relinkee si cambia el .ld — hello-world
de silicio, no vuelo.
```

**Defaults locked by Cursor (Engineer asked to draft the recommended next Buy 2026-09-24):**
- Observable = **PC13** from **HGLRCF405V2** (`resource LED 1 C13`), not PA8  
- Close C29 N1 with **`LINK_DEPENDS`**  
- USB **DFU** documented; suite green **without** a plugged board  
- `stub_main` may change only for the LED spin after the existing one-shot  

---

## 1. Package layout (normative intent)

```text
native/flight_control/
  CMakeLists.txt                 # LINK_DEPENDS + POST_BUILD .bin
  mcu/hello_led.c                # PC13 MMIO + busy-wait (preferred)
  mcu/hello_led.h                # optional; or extern "C" in stub_main
  mcu/stub_main.cpp              # one-shot jarvis_fc, then hello_led_spin()
  README.md                      # DFU + restore BF + honesty

tests/
  test_fase_c_mcu_flash_observable_b1.py
```

Do **not** add STM32Cube/CMSIS under `src/jarvis/`. Do **not** name CRSF in these files. Do **not** drive `MOTOR 1..4` (`C06`–`C09`).

---

## 2. Types / APIs (normative intent)

```text
void hello_led_init(void);   /* RCC GPIOCEN + PC13 output; dummy-read after clock */
void hello_led_spin(void);   /* noreturn: toggle PC13 via BSRR, busy-wait, forever */
```

`main` keeps the C18 one-shot, then calls `hello_led_spin()`.

Busy-wait: `volatile` counter. Document that HSI 16 MHz after reset makes the period **roughly visible**, not calibrated.

### 2.1 Non-goals

DShot, motor pins, USART, IRQ, DMA, PLL, CMSIS pack, OpenOCD as required, Safety execute, craft↔FS, C21 Python on the MCU, Darwin `IOSSIOSPEED`.

---

## 3. Integration rules

| Existing | C30 rule |
|---|---|
| C29 linker MEMORY | **Unchanged** numbers (`0x08000000` / 1024K · `0x20000000` / 128K) |
| C16 toolchain flags | Unchanged |
| C28 `UartBytePort` | Unchanged; still no USART |
| C18 one-shot `jarvis_fc` in `main` | **Kept**; idle loop becomes LED spin |
| C22/C23 Python serial | **Unchanged** |
| Native CRSF lock | Holds |
| Host `ctest` | Still green (host does not run `hello_led.c`) |
| C29 T9 | May remain; **not** a substitute for LINK_DEPENDS |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | `CMakeLists.txt` sets `LINK_DEPENDS` on `linker_cortex_m4.ld` for `fc_mcu_stub.elf` (source grep — **no toolchain required**) |
| T2 | When MCU build dir + toolchain exist: touching the `.ld` **relinks** (elf mtime increases) **without** deleting the elf |
| T3 | LED source cites `C13` / `PC13` **and** `HGLRCF405V2` / `LED 1 C13` |
| T4 | LED source has RCC `0x40023800` or `0x40023830`, GPIOC `0x40020800`, BSRR `0x40020818` (or equivalent named stores to those addresses) |
| T5 | LED / stub sources do **not** treat **PA8** as the status LED; no `MOTOR` pin writes (`C06`/`C07`/`C08`/`C09`) |
| T6 | `stub_main.cpp` still calls `ImuLowPassFilter` + `encode_motor_forces` once; idle is no longer an empty `while (true)` |
| T7 | Honesty comment no longer claims the image is “never flashed”; new line: flashed LED ≠ flying ≠ DShot ≠ Betaflight |
| T8 | No CMSIS/`stm32f4xx.h`/`HAL_GPIO` / STM32Cube includes in this Buy’s new/touched MCU files |
| T9 | Native grep still zero `crsf`/`elrs` |
| T10 | When toolchain present: `fc_mcu_stub.bin` exists after MCU build; `readelf -l` LOAD still `0x08000000` |
| T11 | `uart.hpp` / `crsf_serial.py` git-unchanged |
| T12 | README documents `dfu-util` to `0x08000000` **and** restore via Betaflight **HGLRCF405V2**; props-off / battery-off for DFU |
| T13 | Pytest does **not** fail when no DFU device is plugged (no live-flash gate in CI) |
| T14 | `pyproject` **`0.5.28`**; re-pin `0.5.27` |
| T15 | Full Python suite + host `ctest` green |
| T16 | Report: flashed LED blink ≠ flying ≠ DShot ≠ USART live ≠ Betaflight; C29 N1 closed by LINK_DEPENDS (not by T9) |

---

## 5. Honesty / forbidden

```text
flashed LED blink ≠ flying ≠ DShot ≠ USART live ≠ Betaflight HGLRCF405V2
```

**Exists:** an image the Engineer can DFU onto the desk F405 whose idle loop toggles the cited status LED; CMake will relink if the linker script changes.  
**Impossible:** the craft flying; ESCs seeing DShot; ELRS on UART2; this repo becoming Betaflight.

---

## 6. Docs

PRIORIDAD · PLATFORM §13 · ARCHITECTURE · README “What v0.5.28 includes” · `native/flight_control/README.md` DFU + restore

---

## 7. Acceptance

**PASS when:** T1–T16 · PC13 cited from HGLRCF405V2 · LINK_DEPENDS is real · `.bin` produced · no CMSIS pack · no motor pins · version `0.5.28`.  
**FAIL if:** PA8 guessed from HGLRCF405 · flash-of-empty-idle with no observable · CMake still missing LINK_DEPENDS (T9-only “fix”) · Cube/CMSIS required · DShot/USART/IRQ · pytest requires a plugged board · live-Betaflight / flying claim.

---

## 8. Handoff

```text
Engineer → ★ this IC (C30)
Claude   → LINK_DEPENDS + PC13 hello + .bin + DFU docs + tests + report + 0.5.28
Cursor   → independent review
Engineer → desk DFU smoke (optional for ACCEPT of software gates; required
           before claiming “the board blinked”) + ACCEPT + tag v0.5.28
Cursor   → next remains parked: GPIO/DShot wire · USART on-chip · craft↔FS
```

Engineer ACCEPT of the **software** Buy does not require the LED to have been seen if DFU was not attempted; the report must then say **not flashed on desk**. Claiming “hello-world on silicon” without that smoke is a docs fail.

---

## 9. PRIORIDAD blurb

```text
Fase C: C29 B1 CLOSED @ v0.5.27. C30 B1-fase-c-mcu-flash-observable READY —
PC13 status LED (HGLRCF405V2) + DFU image + CMake LINK_DEPENDS on the
.ld (closes C29 N1). Not DShot, not flying, not Betaflight.
```

---

## 10. Engineer ★ checklist

1. Buy = **flash + one visible LED + CMake `.ld` dep** (not DShot, not USART) OK?  
2. Pin **PC13** from **HGLRCF405V2** (`resource LED 1 C13`), **not** PA8, OK?  
3. Overwrite Betaflight; restore = reflash **HGLRCF405V2**; props off OK?  
4. Suite green without a plugged board; desk DFU is Engineer smoke OK?  
5. Version **`0.5.28`** OK?  
