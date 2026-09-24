# Implementation Contract — Fase C silicon + cited FLASH map (`B1-fase-c-silicon-cited-flash-map`)

**Project:** Jarvis  
**Date:** 2026-09-24  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer spot-check (cited map ≠ flashed · ≠ Betaflight on the desk · ≠ GPIO · HGLRC manual ≠ ST memory map · `stub_main` still idle)

**Status:** ★ ACCEPT CLOSED @ **`v0.5.27`**  
**Parents:**
- Engineer 2026-09-24: desk hardware **HGLRC F460 6S V1 Stack** (manual PDF) — FC **HGLRC F405 8S V1**, MCU printed **STM32F405**; ESC **HGLRC 60A 6S V1 8 BL-S**  
- [C29 B0 ★ ACCEPT](investigation_contract_fase_c_silicon_cited_flash_map_b0.md) — park-until-named; un-park: desk MCU named  
- [C28 ★ ACCEPT](implementation_contract_fase_c_mcu_uart_hal_stub_b1.md) — `UartBytePort` @ **`v0.5.26`**  
- [C18 ★ ACCEPT](implementation_contract_fase_c_cpp_mcu_freestanding_elf_b1.md) — fictional `0x00000000` / 256K FLASH @ **`v0.5.16`**  
- [C16 ★ ACCEPT](implementation_contract_fase_c_cpp_mcu_cross_compile_b1.md) — generic Cortex-M4 class @ **`v0.5.14`**  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no flash, GPIO, CMSIS pack, DShot wire, Safety execute, or craft↔FS  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Implementation Contract** — replace C18’s **disclosed fiction** in `linker_cortex_m4.ld` with FLASH/RAM `ORIGIN`/`LENGTH` taken from **ST RM0090 Table 3** for **STM32F405xx**, because the desk FC’s own manual names that MCU. Still no OpenOCD, no Betaflight, no claim the `.elf` boots on the stack.  
**Package:** bump Jarvis `pyproject.toml` to **`0.5.27`**; git tag **`v0.5.27`** only after Engineer ACCEPT.  
**Not** flashing the HGLRC stack · not STM32Cube/CMSIS · not DShot on M1–M4 · not UART ISR · not “Jarvis firmware for HGLRCF405V2” · not changing C16 `-mfloat-abi=soft` this Buy.

**Outputs (required):**
1. Rewrite `native/flight_control/mcu/linker_cortex_m4.ld` `MEMORY` + honesty comment (cite HGLRC identity + ST RM0090 Table 3)  
2. Update `native/flight_control/README.md` C18 memory-map paragraph (fiction → cited; still ≠ flashed)  
3. Tests: `tests/test_fase_c_silicon_cited_flash_map_b1.py` — linker numbers + citations present; `stub_main` still has no peripheral; native CRSF lock holds  
4. `.jes/artifacts/implementation_report_fase_c_silicon_cited_flash_map_b1.md`  
5. Docs honesty: PRIORIDAD · PLATFORM §13 · ARCHITECTURE / README — **cited FLASH map ≠ flashed ≠ boots on FC ≠ Betaflight**  
6. `pyproject.toml` → **`0.5.27`** (+ re-pin `0.5.26` checkpoints)

**Checkpoint:** package **`0.5.27`** · Python suite ≥ **3584** + new tests · host `ctest` still green · MCU `.elf` still links when toolchain present · `stub_main.cpp` **byte-unchanged**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-fase-c-silicon-cited-flash-map`** — cited linker map for the desk STM32F405 |
| 2 | One front | Do **not** fold OpenOCD/J-Link, GPIO, DShot, CMSIS/STM32Cube, UART ISR, FPU ABI change, Safety execute, or craft↔FS |
| 3 | What this Buy demonstrates | El `.elf` se **enlaza** contra las direcciones que ST publica para este MCU. **Human:** “el plano ya es el de *este* chip; todavía no hemos metido el programa en la placa.” |
| 4 | Board identity (HGLRC, not ST) | Desk stack = **HGLRC F460 6S V1**. FC SKU in the same manual: **HGLRC F405 8S V1**. MCU line: **STM32F405**. Betaflight target name printed: **HGLRCF405V2**. ESC is a **different** board (60A 6S, DShot150/300/600, Bluejay) — out of this Buy |
| 5 | Memory map (ST, not HGLRC) | HGLRC PDF does **not** print FLASH ORIGIN/LENGTH. Cite **RM0090** Table 3 (STM32F405xx/07xx): Flash **`0x0800 0000`–`0x080F FFFF`** (1 MiB); SRAM1 **`0x2000 0000`–`0x2001 BFFF`** (112 KiB); SRAM2 **`0x2001 C000`–`0x2001 FFFF`** (16 KiB). DS STM32F405RG: “up to 1 Mbyte of flash”, “up to 192+4 Kbytes of SRAM” (192 = 128 SRAM + 64 CCM) |
| 6 | Linker numbers (locked) | `FLASH (rx): ORIGIN = 0x08000000, LENGTH = 1024K` · `RAM (rwx): ORIGIN = 0x20000000, LENGTH = 128K` (SRAM1+SRAM2 contiguous). **Do not** add CCM (`0x10000000` / 64 KiB) to this `RAM` region this Buy |
| 7 | Residual (disclosed) | HGLRC does not print the package suffix (RG vs VG). STM32F405 family flash is 1 MiB in RM0090 Table 3. If a later teardown shows a different ST part, recut — do not guess F411/F722 |
| 8 | C16 flags | Keep `-mcpu=cortex-m4 -mthumb -mfloat-abi=soft`. FPU hard-float is a **later** Buy |
| 9 | `stub_main.cpp` | **Byte-unchanged** idle. **Forbidden:** flash, USART, GPIO, DShot in `Reset_Handler`/`main` |
| 10 | Native-tree lock | **Zero** `crsf`/`elrs` under `native/` (even comments) |
| 11 | No vendor BSP | **Forbidden:** STM32Cube, CMSIS device pack, libopencm3 as required deps |
| 12 | Version | **`0.5.26` → `0.5.27`**; tag **`v0.5.27`** on ACCEPT only |
| 13 | Forbidden claims | “Flashed onto the HGLRC” · “boots / flies” · “this is Betaflight HGLRCF405V2” · “DShot live” · “USART live” |

**Product sentence:**

```text
Citar el mapa FLASH/RAM del STM32F405 de la F405 que llegó hoy
(RM0090 Table 3) en el linker — inspectable en el Mac, sin flashear
la stack HGLRC.
```

**Defaults locked by Cursor (Engineer named the desk stack 2026-09-24):**
- Identity from HGLRC F460/F405 manual  
- Numbers from ST RM0090 Table 3  
- 1024K FLASH @ `0x08000000` · 128K SRAM @ `0x20000000`  
- No flash · no CMSIS · `stub_main` idle · C16 flags unchanged  

---

## 1. Package layout (normative intent)

```text
native/flight_control/mcu/linker_cortex_m4.ld   # MEMORY + comment rewrite
native/flight_control/README.md                 # C18 map paragraph
tests/test_fase_c_silicon_cited_flash_map_b1.py
```

Do **not** add STM32 headers under `src/jarvis/`. Do **not** name CRSF in the linker file.

---

## 2. Honesty comment (normative intent)

The linker header must state, in substance:

```text
Desk identity: HGLRC F460 6S V1 stack / HGLRC F405 8S V1 FC / MCU STM32F405
  (HGLRC F460 6S V1 manual — MCU line; not a memory-map source).

Cited map: ST RM0090 Table 3 (STM32F405xx/07xx):
  FLASH  0x08000000–0x080FFFFF  (1 MiB)
  SRAM1  0x20000000–0x2001BFFF  (112 KiB)
  SRAM2  0x2001C000–0x2001FFFF  (16 KiB)
This script uses FLASH 1024K @ 0x08000000 and RAM 128K @ 0x20000000
(SRAM1+SRAM2). CCM at 0x10000000 is not in this MEMORY block.

Cited map != flashed != boots on this stack != Betaflight HGLRCF405V2.
```

---

## 3. Integration rules

| Existing | C29 B1 rule |
|---|---|
| C18 `stub_main` / startup / syscalls | **Unchanged** except linker MEMORY + comments |
| C16 toolchain flags | Unchanged |
| C28 `UartBytePort` | Unchanged; no USART registers |
| Native CRSF lock | Holds |
| Host `ctest` | Still green |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | `linker_cortex_m4.ld` FLASH `ORIGIN = 0x08000000` and `LENGTH = 1024K` |
| T2 | RAM `ORIGIN = 0x20000000` and `LENGTH = 128K` |
| T3 | Honesty comment cites `RM0090` and `HGLRC` / `STM32F405` |
| T4 | No `0x00000000` FLASH ORIGIN left as the load region |
| T5 | `stub_main.cpp` git-unchanged |
| T6 | Native grep still zero `crsf`/`elrs` |
| T7 | No CMSIS / STM32Cube / OpenOCD in this Buy’s touched files |
| T8 | `pyproject` **`0.5.27`**; re-pin `0.5.26` |
| T9 | Host `ctest` green; MCU `.elf` still links if toolchain present |
| T10 | Report: cited FLASH map ≠ flashed ≠ boots on FC ≠ Betaflight |

---

## 5. Honesty / forbidden

```text
cited FLASH map ≠ flashed ≠ boots on FC ≠ Betaflight HGLRCF405V2
```

**Exists:** a linker script whose addresses match ST’s published map for the MCU named on the desk FC.  
**Impossible:** the HGLRC stack running this image; DShot on M1–M4; ELRS on UART2.

---

## 6. Docs

PRIORIDAD · PLATFORM §13 · ARCHITECTURE · README “What v0.5.27 includes”

---

## 7. Acceptance

**PASS when:** T1–T10 · numbers match §0.6 · `stub_main` idle · no flash path · no CMSIS · version `0.5.27`.  
**FAIL if:** OpenOCD/flash · Cube/CMSIS pack · `stub_main` peripherals · folklore numbers with no RM0090 cite · live-Betaflight claim.

---

## 8. Handoff

```text
Engineer → ★ this IC (C29 B1)
Claude   → linker MEMORY rewrite + tests + report + 0.5.27
Cursor   → independent review
Engineer → ACCEPT + tag v0.5.27
Cursor   → next remains parked: board flash · GPIO/DShot wire · craft↔FS
```

---

## 9. PRIORIDAD blurb

```text
Fase C: C28 CLOSED @ v0.5.26. C29 B1-fase-c-silicon-cited-flash-map READY —
STM32F405 on the desk HGLRC F405 FC; linker cites RM0090 Table 3;
not flashed, not Betaflight.
```

---

## 10. Engineer ★ checklist

1. Buy = **cited linker map** (not flash, not Betaflight) OK?  
2. FLASH `0x08000000` / 1024K · RAM `0x20000000` / 128K OK?  
3. `stub_main` idle · C16 flags unchanged OK?  
4. Version **`0.5.27`** OK?  
