# Investigation Contract — Fase C silicon + cited FLASH map (`B0-fase-c-silicon-cited-flash-map`)

**Project:** Jarvis  
**Date:** 2026-09-24  
**Author:** JES / Cursor (Engineer Interface) — **investigation only**  
**Investigator:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this contract · Engineer pick (named part vs park)

**Status:** ★ ACCEPT CLOSED (investigation) — park was correct on the report’s evidence; Engineer later named desk STM32F405. Next: [B1 IC](implementation_contract_fase_c_silicon_cited_flash_map_b1.md). Tip remains **`v0.5.26`**.  
**Parents:**
- [C28 ★ ACCEPT](implementation_contract_fase_c_mcu_uart_hal_stub_b1.md) — `UartBytePort` @ **`v0.5.26`**  
- [C18 ★ ACCEPT](implementation_contract_fase_c_cpp_mcu_freestanding_elf_b1.md) — `fc_mcu_stub.elf` + **fictional** FLASH/RAM @ **`v0.5.16`**  
- [C16 ★ ACCEPT](implementation_contract_fase_c_cpp_mcu_cross_compile_b1.md) — generic Cortex-M4 class, **not a named board** @ **`v0.5.14`**  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**; no flash, GPIO, CMSIS device pack, Safety execute, or craft↔FS  
- Craft SoT Continuity / CLI / Board / `library/` **unchanged**

**Type:** **Investigation Contract** — C18’s linker script is an honest fiction (`FLASH` at `0x00000000` / 256 KiB, `RAM` at `0x20000000` / 64 KiB). A **cited** map requires a **named MCU + datasheet section**. No board is on the desk. This Buy does **not** flash, does **not** pick silicon in silence, and does **not** rewrite the linker until the Engineer names a part (or explicitly parks).  
**Package:** **do not bump** `pyproject.toml` (investigation). Git tag only if a later B1 IC ACCEPTs.  
**Not** an Implementation Contract · not OpenOCD/J-Link · not STM32Cube/CMSIS pack · not “this `.elf` boots on our FC” · not GPIO · not USART registers · not live ELRS.

**Outputs (required):**
1. `.jes/artifacts/investigation_report_fase_c_silicon_cited_flash_map_b0.md`  
2. Cite C18’s actual `mcu/linker_cortex_m4.ld` numbers vs ARM Code/SRAM regions vs a typical vendor remap (e.g. many STM32 flash at `0x08000000`) — **as contrast, not as a part pick**  
3. State what a later B1 would need: **part number + datasheet (or RM) section + ORIGIN/LENGTH**  
4. Recommend **one** of: park until the Engineer names the MCU they will buy · provisional cited class (still labeled not-this-desk) · keep C18 fiction forever until silicon arrives  
5. Docs honesty only if the report is ACCEPTed as investigation — **cited map ≠ flashed ≠ boots on FC**

**Checkpoint:** package remains **`0.5.26`** · no `src/` / `native/` linker rewrite this Buy · suite unchanged unless the report is docs-only

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B0-fase-c-silicon-cited-flash-map`** — investigation, not a flash |
| 2 | One front | Do **not** fold OpenOCD, GPIO, CMSIS device pack, USART silicon, C21-on-MCU, Safety execute, or craft↔FS |
| 3 | What this Buy demonstrates | El `.elf` de C18 **enlaza** contra un mapa inventado. Un mapa **citado** exige ficha de un chip con nombre. **Human:** “todavía no hay placa en la mesa; no vamos a fingir la dirección de su FLASH.” |
| 4 | No silent part pick | Investigator **must not** change `linker_cortex_m4.ld` ORIGIN/LENGTH. Recommendation only |
| 5 | Citation bar | A later B1 map is honest only if ORIGIN/LENGTH come from a **named** datasheet/RM section (page or table id), not from “typical STM32” folklore |
| 6 | C18 fiction stays until B1 | `0x00000000` / 256K / `0x20000000` / 64K remain the linked map unless a **separate** B1 IC is ★ after this report |
| 7 | Native-tree lock | **Zero** `crsf`/`elrs` under `native/` if any comment is touched later; this B0 should not touch `native/` at all |
| 8 | `stub_main` | Untouched |
| 9 | Forbidden claims | “Flashed” · “boots on the FC” · “this is our STM32” · “vector table verified on silicon” |

**Product sentence:**

```text
Investigar qué ficha (chip + sección) haría honesto el mapa FLASH/RAM
del .elf — sin flashear, sin elegir silicio a ciegas, sin mentir
0x00000000 como si fuera esa placa.
```

**Defaults locked by Cursor (Engineer: C29 after C28 ACCEPT, left B0):**
- Investigation report only  
- No linker rewrite  
- Engineer names the part **before** any B1  

---

## 1. Why this exists

Shipped today (C18, still true at `v0.5.26`):

```text
mcu/linker_cortex_m4.ld
  FLASH  ORIGIN = 0x00000000  LENGTH = 256K   # fictional class size
  RAM    ORIGIN = 0x20000000  LENGTH = 64K    # ARM SRAM region, still unsized-from-datasheet
```

That is enough to **link and objdump** an ARM image on the Mac. It is **not** enough to claim the image’s load address matches any flight-controller MCU.

Wrong answers:

```text
· Copy 0x08000000 from “STM32 folklore” with no part number
· Flash via OpenOCD “to see if it boots”
· Pull in STM32Cube / a CMSIS device pack to “get the real map”
· Treat C16’s generic Cortex-M4 flags as a board identity
```

Right question:

> On the **live linker script + live C16/C18 honesty comments**, what **named** MCU (if any) is the Engineer willing to cite, and what is the **minimum B1** that would replace C18’s fiction with ORIGIN/LENGTH taken from that datasheet — still without flashing?

---

## 2. Locked stances

1. **Fiction stays labeled fiction** until a B1 IC rewrites the script.  
2. **A class (Cortex-M4) is not a part.** C16 `-mcpu=cortex-m4` does not imply FLASH base `0x08000000`.  
3. **Cite or do not change.** No “round numbers that look like an F405.”  
4. **Flash remains parked** (OpenOCD/J-Link product path = later C, not this B0).  
5. **No vendor BSP** as a required outcome of this investigation.  
6. **Fail closed:** if the Engineer has not named a part they will buy, recommend **park**, not a guessed map.

---

## 3. Evidence the report must show

| ID | Check |
|---|---|
| E1 | Quote C18 `linker_cortex_m4.ld` MEMORY block + its honesty comment |
| E2 | Contrast ARM Code region `0x00000000` vs a **labeled example** vendor remap (cite a public RM/datasheet, clearly “example, not our board”) |
| E3 | List what a B1 PR would touch (`linker_cortex_m4.ld` comments + MEMORY; maybe README) — and what it must **not** touch (`stub_main`, UART ISR, CMSIS) |
| E4 | Recommend **one** next move: park · Engineer-named B1 · provisional cited class (only if Engineer already wants a named candidate) |
| E5 | Honesty line in the report: **cited FLASH map ≠ flashed ≠ boots on FC ≠ this desk’s MCU** |

---

## 4. Honesty / forbidden

```text
cited FLASH map ≠ flashed ≠ boots on FC ≠ this desk’s MCU
```

**Exists today:** a freestanding `.elf` linked against a **disclosed fiction**.  
**Impossible this Buy:** a vector table that a real chip fetched from its own FLASH.

---

## 5. Docs

Do **not** retitle C18 as “cited silicon” in PRIORIDAD / PLATFORM / README. If the investigation report is later ACCEPTed, a one-line “C29 B0 closed — still fictional map until named B1” is enough.

---

## 6. Acceptance (investigation)

**PASS when:** E1–E5 · no linker rewrite · no flash path · no silent part pick · recommendation is one of the three locked options.  
**FAIL if:** `linker_cortex_m4.ld` ORIGIN/LENGTH changed · CMSIS pack added · “boots on STM32” claimed · CRSF tokens added under `native/`.

---

## 7. Handoff

```text
Engineer → ★ this B0 (or upgrade: name a part and ask for a B1 IC instead)
Claude   → investigation_report only (no native/ rewrite)
Cursor   → independent investigation review
Engineer → park · or ★ a later B1 with the named part
```

---

## 8. PRIORIDAD blurb

```text
Fase C: C28 CLOSED @ v0.5.26. C29 B0-fase-c-silicon-cited-flash-map READY —
investigate a datasheet FLASH/RAM map; not flash, not C18 0x00000000 as if
it were a board.
```

---

## 9. Engineer ★ checklist

1. Buy = **investigation** (not flash, not guessed STM32) OK?  
2. No linker rewrite until a named part OK?  
3. Citation bar = datasheet/RM section, not folklore OK?  
4. Package stays **`0.5.26`** OK?  
