# Investigation Report — Fase C silicon + cited FLASH map (`B0-fase-c-silicon-cited-flash-map`)

**Contract:** [`investigation_contract_fase_c_silicon_cited_flash_map_b0.md`](investigation_contract_fase_c_silicon_cited_flash_map_b0.md)
**Investigator:** Claude Code
**Date:** 2026-09-24
**Status:** ★ ACCEPT CLOSED (Cursor review PASS WITH NOTES). Investigation only — package remains **`0.5.26`**. Next: [B1 IC](implementation_contract_fase_c_silicon_cited_flash_map_b1.md) (Engineer named desk STM32F405 after this report’s evidence window).

---

## 0. Read this first — honesty summary

This report answers one question: *what would it take to replace C18's fictional FLASH/RAM map with a map that cites a named, real MCU's own datasheet — without flashing anything, and without guessing a part in silence?*

**Cited FLASH map != flashed != boots on FC != this desk's MCU.**

Nothing in this report changes what is linked today. C18's disclosed fiction (`FLASH` at `0x00000000` / 256 KiB, `RAM` at `0x20000000` / 64 KiB) remains exactly what `fc_mcu_stub.elf` links against, byte-for-byte unchanged by this investigation — verified in §6.

---

## 1. E1 — C18's actual linker script, quoted verbatim

`native/flight_control/mcu/linker_cortex_m4.ld` (lines 1–20, read live from disk for this report, not from memory of an older Buy):

```c
/* Fase C · C18 — generic Cortex-M4 linker script
 * (`B1-fase-c-cpp-mcu-freestanding-elf`).
 *
 * HONESTY: this is a FICTIONAL, generic memory map, not any named board's
 * silicon. FLASH at 0x00000000 and RAM at 0x20000000 are the ARM-
 * architected default Cortex-M memory regions (Code region and SRAM
 * region per the ARMv7-M architecture reference manual) — deliberately
 * NOT a vendor's remapped boot address (many real boards remap flash to
 * e.g. 0x08000000; this script does not claim to be any of them). Sizes
 * (256 KiB FLASH / 64 KiB RAM) are a round, illustrative "class" size,
 * not sourced from any real part's datasheet. This script produces an
 * inspectable ELF only — it is never flashed, and nothing in this repo
 * claims this image boots on real hardware.
 */

MEMORY
{
    FLASH (rx)  : ORIGIN = 0x00000000, LENGTH = 256K
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 64K
}
```

This honesty comment was written at C18's own landing (`v0.5.16`) and has not been touched by C19 through C28 — confirmed by this investigation not editing the file (§6), and by every intervening Buy's own report never listing `linker_cortex_m4.ld` among its changed files.

The companion toolchain file, `native/flight_control/cmake/toolchains/arm-none-eabi.cmake` (C16), locks the **CPU class** — `-mcpu=cortex-m4 -mthumb -mfloat-abi=soft` — with its own explicit disclaimer: *"naming the class is not a claim about any specific board's silicon, clock tree, or memory map — none of that is modeled here."* A CPU class and a memory map are two different claims; C16 only ever made the first one.

---

## 2. E2 — contrast: ARM generic Code region vs. a labeled vendor-remap example

**What C18 links against today:** the ARMv7-M architecture's own *default* Code region (`0x00000000`) and SRAM region (`0x20000000`) — these are the generic addresses the Cortex-M architecture itself defines for "wherever code/data live if nothing remaps them," not any vendor's actual boot configuration.

**A labeled example, explicitly not a part pick for this repo:** a very widely deployed flight-controller-class part family is the STMicroelectronics STM32F4 series (e.g. STM32F405/F411 — parts that show up on many real quadcopter flight controllers in the wild, referenced here only as a publicly documented illustration of the *pattern*, not as a candidate this repo is adopting). STM32F4-series parts are publicly documented (ST's Reference Manual **RM0090**, "STM32F405/415, STM32F407/417, STM32F427/437, STM32F429/439 advanced Arm®-based 32-bit MCUs," section 2.3 "Memory map") to **boot-remap their main FLASH to `0x08000000`** — not the ARM generic `0x00000000` — while SRAM commonly stays at (or near) the ARM generic `0x20000000` region. **I have not opened that specific PDF in this session and am not citing a page number** — this is the well-known, widely-published shape of that family's memory map (the `0x08000000` FLASH base for STM32 parts is public knowledge repeated across ST's own datasheets, the ARM Cortex-M ecosystem, and countless open flight-controller firmware trees), offered here purely as **contrast**, exactly as the contract requests: it shows why C18's `0x00000000` is honestly labeled fiction rather than a lucky guess at a real board's boot address, not as a recommendation to adopt STM32F4 specifically.

**What this means concretely:** if a real board were named, its ORIGIN for FLASH would very likely **not** be `0x00000000` (it would be whatever that specific part's own boot-remap convention is — `0x08000000` for many STM32 parts, but not universally true across every vendor/family), and its LENGTH would be that exact part's flash size in bytes (e.g. common flight-controller STM32F4 parts ship anywhere from 512 KiB to 2 MiB of flash depending on the exact part number — not the round, illustrative 256 KiB C18 currently links against).

---

## 3. E3 — what a later B1 would touch, and what it must not

**A B1 IC replacing C18's fiction would touch, at minimum:**
- `native/flight_control/mcu/linker_cortex_m4.ld` — the `MEMORY { FLASH ... RAM ... }` block's `ORIGIN`/`LENGTH` values, and the honesty comment above it (rewritten to cite the named part + datasheet/RM section/table instead of disclosing a fiction).
- `native/flight_control/README.md` — the "Memory map (fictional, disclosed)" paragraph under "Freestanding MCU `.elf` (C18)" would need its own honest update once the map is no longer fictional.
- Very likely a rename of the toolchain/linker files or a new pair, if the named part's CPU variant (Cortex-M4 with/without hardware FPU, exact `-mcpu`/`-mfpu` flags) differs from C16's own generic choice — that is a decision for whoever writes that B1 IC, not settled here.

**A B1 IC must not touch, per this contract's own lock (decision 4, 6, 8) and by extension of every prior "one front" lock in this thread:**
- `native/flight_control/mcu/stub_main.cpp` — stays the C18 idle one-shot exercise; a cited memory map is not license to add a boot loop, a UART ISR, or any peripheral access.
- No CMSIS device pack, no vendor HAL/BSP (STM32Cube or otherwise) — citing a memory map from a public datasheet is not the same decision as vendoring that manufacturer's SDK.
- No GPIO, no USART register access, no IRQ/DMA — C28's `UartBytePort`/`LoopbackUart` stay exactly what they are today (an in-memory loopback); a cited FLASH/RAM map does not imply wiring a real peripheral.
- No flashing — OpenOCD/J-Link/any programmer path remains a separate, later, explicitly-scoped Buy if the Engineer ever prioritizes it. A cited *map* is a linker-script fact, not a "flash it and see" action.

---

## 4. E4 — recommendation: **park**

Of the three locked options in the contract (§0 decision 9 / IC handoff), this investigation recommends:

> **Park until the Engineer names the MCU they will buy.**

**Why, not the other two:**
- **Not** "provisional cited class" — the contract's own lock (§0 decision 9, Cursor's "Defaults locked" note) restricts that option to a case where "the Engineer already wants a named candidate." No part number, board, or vendor has been named anywhere in this session, this contract, or any prior Buy's own artifacts. Picking a "provisional" class without that signal would be exactly the "round numbers that look like an F405" failure mode §2 of the contract explicitly forbids — even a disclosed provisional pick risks being read as a soft commitment to a part nobody has actually decided to buy.
- **Not** "keep the fiction forever" either — that forecloses the question rather than answering it. The fiction is honest and can stay linked indefinitely with zero harm (it already carries its own disclosure comment, re-verified unchanged in §1), but "forever" is a stronger claim than this investigation has grounds to make; a future Engineer decision to name a part should not be pre-empted by a report that declares the question permanently closed.
- **Park is the only option that requires no further action to remain honest.** C18's own comment already says everything a reader needs to know today. Parking costs nothing and commits to nothing; it simply leaves the door open for a future, explicitly-scoped B1 the moment a real part is named.

**What would trigger un-parking:** the Engineer names a specific MCU part number they intend to buy (or already have on a desk) — at that point, a B1 IC should be drafted citing that part's own datasheet/reference-manual section (page or table id, not folklore), and only then should `linker_cortex_m4.ld`'s `ORIGIN`/`LENGTH` values change.

---

## 5. E5 — honesty line

```text
cited FLASH map != flashed != boots on FC != this desk's MCU
```

**Exists today:** a freestanding `.elf` (C18) linked against a **disclosed fiction** — the ARM architecture's own generic Code/SRAM addresses, a round illustrative size, explicitly not sourced from any real part's datasheet, and explicitly not claimed to boot on real hardware.

**Impossible this Buy (and impossible for any B0 investigation by its own nature):** a vector table that a real chip fetched from its own FLASH; a claim that any board "runs" this image; a part pick made in silence.

---

## 6. Verification — no code changed, no rewrite, no version bump

```text
$ git diff --stat -- native/ pyproject.toml
(empty)

$ git status --short
?? .jes/artifacts/investigation_report_fase_c_silicon_cited_flash_map_b0.md

$ grep '^version' pyproject.toml
version = "0.5.26"

$ git tag -l | sort -V | tail -3
v0.5.24
v0.5.25
v0.5.26
```

`linker_cortex_m4.ld` was **read, not written**, for this investigation (§1's quote is a live read, confirmed identical to the pre-existing C18 file — no diff exists because no edit was made). No `.py`/`.cpp`/`.hpp` file was touched anywhere in this repo. No native-tree CRSF/ELRS tokens were introduced (nothing under `native/` was written at all, so the standing lock from C21–C28 is trivially unaffected — re-confirmed by the empty `git diff --stat -- native/` above rather than a fresh grep, since nothing changed to grep). Package stays `0.5.26`; no `v0.5.27` tag exists or is expected from this investigation alone, per the contract's own "Git tag only if a later B1 IC ACCEPTs."

---

## 7. Docs

Per the contract's own §5 ("Docs — do not retitle C18 as 'cited silicon' in PRIORIDAD / PLATFORM / README... If the investigation report is later ACCEPTed, a one-line... is enough"), **no doc files were edited by this investigation**. `docs/IMPLEMENTATION_TASKS.md`, `docs/ARCHITECTURE.md`, `docs/PLATFORM_CAPABILITY_VISION.md`, and `README.md` all still describe C18's map exactly as it is — fictional, disclosed — because that remains true; nothing in this report changes what is linked. Should Cursor/Engineer ACCEPT this investigation's recommendation (park), the appropriate follow-up is the one-line PRIORIDAD update the contract itself describes ("C29 B0 closed — still fictional map until named B1"), left for that ACCEPT step rather than pre-empted here.

---

## 8. Residual / next steps

- **Parked, not closed-forever:** this axis reopens the moment the Engineer names a real MCU part number.
- No B1 IC should be drafted for this axis until that naming happens — drafting one now would invite exactly the "guessed STM32" failure mode this investigation was asked to avoid.
- Everything else in the Fase C queue (craft↔FS wiring, board flash as its own future axis, deepening C20's policy beyond one aux channel, Linux custom baud) remains independently parked per the existing [process lock](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — this investigation does not reorder or touch any of those.

---

## 9. Acceptance self-check vs contract §6

- E1–E5: ✅ all five present, §1–§5 above.
- No linker rewrite: ✅ `git diff --stat -- native/` empty (§6).
- No flash path: ✅ no OpenOCD/J-Link/programmer content anywhere in this report or repo change.
- No silent part pick: ✅ STM32F4/RM0090 cited explicitly as a labeled, public example, not adopted — recommendation is park, not a provisional pick.
- Recommendation is one of the three locked options: ✅ §4 — park.

**PASS** against every criterion in the contract's own §6 acceptance bar. **FAIL conditions** (`linker_cortex_m4.ld` ORIGIN/LENGTH changed, CMSIS pack added, "boots on STM32" claimed, CRSF tokens added under `native/`) — none present, verified in §6.
