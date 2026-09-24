# Implementation Report — Fase C silicon + cited FLASH map (`B1-fase-c-silicon-cited-flash-map`)

**IC:** [`implementation_contract_fase_c_silicon_cited_flash_map_b1.md`](implementation_contract_fase_c_silicon_cited_flash_map_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-24
**Status:** ★ ACCEPT CLOSED @ **`v0.5.27`** (Cursor review PASS WITH NOTES). Package **`0.5.27`**.

---

## 0. Read this first — honesty summary

C29 B0 (investigation) recommended **park until the Engineer names the
MCU they will buy**. On 2026-09-24 the Engineer did: desk stack
**HGLRC F460 6S V1**, flight controller SKU **HGLRC F405 8S V1**, MCU
line **STM32F405** — printed on that FC's own manual. This Buy replaces
C18's disclosed fiction (`FLASH` at `0x00000000` / 256 KiB, `RAM` at
`0x20000000` / 64 KiB) with a **cited** map, taken from ST's own
published Reference Manual, not from folklore.

**Cited FLASH map != flashed != boots on FC != Betaflight HGLRCF405V2.**

**Exists:** a linker script whose addresses match ST's published map for
the MCU named on the desk FC. **Impossible:** the HGLRC stack running
this image; DShot on M1-M4; ELRS on UART2. Nothing in this Buy is any of
those — no OpenOCD, no J-Link, no vendor SDK, no peripheral touched.

---

## 1. Package layout vs IC §1

```text
native/flight_control/mcu/linker_cortex_m4.ld   # MEMORY + honesty comment rewritten
native/flight_control/README.md                  # C18 map paragraph updated
tests/test_fase_c_silicon_cited_flash_map_b1.py  # NEW — 14 tests
```

No STM32 headers were added under `src/jarvis/`. No CRSF/ELRS token was named in the linker file (confirmed §7).

---

## 2. The cited numbers vs IC §0 decisions 5-6

| Region | Cited (RM0090 Table 3) | Linked (this Buy) |
|---|---|---|
| FLASH | `0x08000000`-`0x080FFFFF` (1 MiB) | `ORIGIN = 0x08000000`, `LENGTH = 1024K` |
| SRAM1 | `0x20000000`-`0x2001BFFF` (112 KiB) | folded into `RAM` |
| SRAM2 | `0x2001C000`-`0x2001FFFF` (16 KiB) | folded into `RAM` |
| `RAM` (SRAM1+SRAM2) | 112 + 16 = 128 KiB | `ORIGIN = 0x20000000`, `LENGTH = 128K` |
| CCM | `0x10000000`, 64 KiB | **excluded**, per IC §0 decision 6 lock |

Exactly matches the IC's own locked numbers (§0 decision 6): `FLASH (rx): ORIGIN = 0x08000000, LENGTH = 1024K` and `RAM (rwx): ORIGIN = 0x20000000, LENGTH = 128K`.

---

## 3. The honesty comment — full rewrite, quoted

```c
/* Fase C · C18 — generic Cortex-M4 linker script
 * (`B1-fase-c-cpp-mcu-freestanding-elf`), memory map re-cited for C29
 * (`B1-fase-c-silicon-cited-flash-map`).
 *
 * Desk identity: HGLRC F460 6S V1 stack / HGLRC F405 8S V1 FC / MCU line
 * STM32F405 (from the HGLRC F460 6S V1 stack manual — that manual names
 * the MCU line; it is not a memory-map source and prints no
 * ORIGIN/LENGTH numbers itself).
 *
 * Cited map: ST RM0090 Table 3 (STM32F405xx/07xx, STM32F415xx/17xx),
 * "Memory map":
 *   FLASH  0x08000000-0x080FFFFF  (1 MiB)
 *   SRAM1  0x20000000-0x2001BFFF  (112 KiB)
 *   SRAM2  0x2001C000-0x2001FFFF  (16 KiB)
 * This script uses FLASH 1024K @ 0x08000000 and RAM 128K @ 0x20000000
 * (SRAM1+SRAM2 taken as one contiguous region). CCM RAM (0x10000000,
 * 64 KiB per RM0090) is deliberately NOT included in this MEMORY block
 * this Buy — CCM is not bus-accessible by DMA/some peripherals on this
 * family and folding it into a flat RAM region would be its own,
 * separate, undisclosed simplification; a later Buy can add a distinct
 * CCM region if ever needed.
 *
 * Residual disclosed (C29 IC §0 decision 7): the HGLRC manual does not
 * print the exact ST order-code suffix (e.g. "RG" vs "VG"); RM0090
 * Table 3's 1 MiB FLASH / 192 KiB total SRAM figures apply to the whole
 * STM32F405xx/07xx line regardless of package/suffix, so this citation
 * holds without that suffix. If a later teardown identifies a different
 * ST part on this specific board, this map should be re-cut from that
 * part's own datasheet — never silently reused for a guessed sibling
 * part (e.g. F411, F722).
 *
 * HONESTY: citing ST's own published memory map for the MCU line named
 * on this desk's own FC is NOT the same claim as flashing anything, NOT
 * a claim this .elf boots on the HGLRC stack, and NOT a claim this
 * project is (or replaces) the stack's own shipped Betaflight target
 * ("HGLRCF405V2"). This script still produces an inspectable ELF only —
 * it is never flashed, no OpenOCD/J-Link path exists anywhere in this
 * repo, and no vendor SDK/BSP (STM32Cube, CMSIS device pack) was pulled
 * in to derive these numbers — they come from RM0090's own published
 * table, transcribed by hand.
 *
 * Cited map != flashed != boots on this stack != Betaflight HGLRCF405V2.
 */
```

This directly implements the IC's own §2 "Honesty comment (normative intent)" template, in substance and largely in wording.

---

## 4. Verified — a real relink, not a stale artifact

**A genuine pitfall caught and fixed:** the first `cmake --build` after editing the linker script reported "Built target" with no relink step — CMake does not track a linker script (`-T` flag target) as an implicit dependency of the executable target, so the pre-existing `.elf` from before this edit was silently left stale (old load address, still linked against the fictional map). Caught by comparing file mtimes (`.elf` older than the edited `.ld`), not by a false "success." Fixed by deleting the stale `.elf` and rebuilding explicitly for that target — confirmed genuinely relinked afterward:

```text
$ arm-none-eabi-readelf -h build/flight_control_mcu/fc_mcu_stub.elf
  Entry point address:               0x8000045
$ arm-none-eabi-readelf -l build/flight_control_mcu/fc_mcu_stub.elf
  LOAD  0x001000 0x08000000 0x08000000 0x14098 0x14098 R E 0x1000
  LOAD  0x016000 0x20000000 0x08014098 0x00884 0x00884 RW 0x1000
$ arm-none-eabi-size build/flight_control_mcu/fc_mcu_stub.elf
  text: 82072  data: 2180  bss: 448  (well within 1024K FLASH / 128K RAM)
```

The new test suite's own `test_t9_mcu_elf_still_links_against_new_map_if_toolchain_present` re-derives this exact same "delete-then-rebuild" step before asserting, so this is not a one-off manual check — it is exercised by the test itself.

---

## 5. Integration rules vs IC §3

| Existing | This Buy |
|---|---|
| `stub_main.cpp` / `startup_cortex_m4.c` / `syscalls_stub.c` | **Unchanged** except the linker MEMORY block + comments — `git diff --stat` empty on all three |
| C16 toolchain flags | Unchanged — `-mcpu=cortex-m4 -mthumb -mfloat-abi=soft` still exact, `git diff --stat` empty |
| C28 `UartBytePort` | Unchanged; no USART registers anywhere in the linker script |
| Native CRSF lock | Holds — tree-wide grep zero matches |
| Host `ctest` | Still green (unaffected — the linker script is MCU-cross-compile-only, never used by the host build) |

---

## 6. Tests run

### 6.1 Python — new module

`tests/test_fase_c_silicon_cited_flash_map_b1.py` — **14 tests**, covering IC §4's T1-T9 (T10 is this report):

| Test | Covers |
|---|---|
| `test_t1_flash_origin_and_length` | T1 |
| `test_t2_ram_origin_and_length` | T2 |
| `test_t3_honesty_comment_cites_rm0090_and_hglrc_and_stm32f405` | T3 |
| `test_t4_no_0x00000000_flash_origin_left` | T4 |
| `test_t5_stub_main_git_unchanged` | T5 |
| `test_t6_native_tree_still_zero_crsf_elrs_tokens` | T6 |
| `test_t7_no_cmsis_stm32cube_openocd_usage_in_touched_files` | T7 |
| `test_t8_pyproject_version_is_0_5_27` | T8 |
| `test_t9_mcu_elf_still_links_against_new_map_if_toolchain_present` | T9 — real relink + `readelf -l` check for `0x08000000` |
| `test_t11_full_suite_process_gate_placeholder` | T11 marker (real gate is the full-suite run below) |
| `test_no_forbidden_claims_in_linker_or_readme` | forbidden-claims lock |
| `test_no_craft_or_core_imports_reference_linker_and_registry_still_empty` | craft/registry isolation |
| `test_default_safety_gate_still_reject_all` | Safety default unchanged |
| `test_toolchain_flags_unchanged` | C16 flags frozen |

```text
tests/test_fase_c_silicon_cited_flash_map_b1.py: 14 passed
```

**Two false-positive test bugs caught and fixed before landing** (same honesty-prose-vs-real-usage distinction every prior Fase C Buy's tests make):
1. A first draft of T7 bare-substring-checked for "cmsis"/"stm32cube"/"openocd" — which false-failed against the linker script's own honesty comment legitimately *naming* those tools to disclose their absence. Fixed by checking for usage-shaped strings (`#include "stm32f4xx...`, `HAL_Init(`, `openocd -f`, etc.) instead of bare mentions.
2. A first draft of a craft-isolation test bare-substring-checked for "HGLRC" anywhere under `src/jarvis/core/`+`adapters/` — which false-failed against a **pre-existing, unrelated** legitimate mention of "HGLRC" in `reasoning_layer.py`'s own VTX-catalog mission-suggestion code (an HGLRC-brand VTX SKU already in the craft catalog, entirely unrelated to this Buy's MCU work). Fixed by narrowing that check to the actually meaningful symbol (`linker_cortex_m4`), not the brand name.

### 6.2 Full Python suite

```text
3598 passed, 2 skipped in 5.94s
```

Baseline before this Buy: `3584 passed, 2 skipped`. Delta: **+14**, exactly matching the new test count — zero regressions.

### 6.3 Host `ctest` (unaffected, re-confirmed)

```text
100% tests passed out of 51
```

Identical to the C28 baseline — the linker script this Buy touched is never used by the host build.

### 6.4 MCU cross-compile relink (IC's own checkpoint: "MCU `.elf` still links when toolchain present")

Covered in full in §4 above — a genuine relink was performed and verified, not merely re-run against a stale artifact.

---

## 7. Honesty / forbidden — confirmed

| Forbidden (IC §5, §0 decision 13) | Verified absent |
|---|---|
| "Flashed onto the HGLRC" | Not claimed anywhere — no OpenOCD/J-Link path exists in this repo |
| "boots / flies" | Not claimed — this remains a compile/link-time fact |
| "this is Betaflight HGLRCF405V2" | Not claimed — explicitly disclaimed in the linker comment and README paragraph |
| "DShot live" | Not touched — `UartBytePort`/mixer/ESC modules all `git diff --stat` empty |
| "USART live" | Not touched — no register access anywhere in the linker script |

Honesty line, shipped verbatim in this report and in the docs updated below:

```text
cited FLASH map != flashed != boots on FC != Betaflight HGLRCF405V2
```

---

## 8. Module-boundary / forbidden-symbol grep (run at close of this Buy)

```text
$ git diff --stat -- native/flight_control/mcu/stub_main.cpp native/flight_control/mcu/startup_cortex_m4.c \
    native/flight_control/mcu/syscalls_stub.c native/flight_control/cmake/toolchains/arm-none-eabi.cmake \
    src/jarvis/capabilities/ native/flight_control/include/jarvis/fc/uart.hpp native/flight_control/src/uart.cpp
(empty)

$ grep -rin "crsf\|elrs" native/
# no match (exit 1) — the C21-C28 native-tree lock holds
```

`git status --short` at close of this Buy shows exactly the expected file set: `linker_cortex_m4.ld` (modified — MEMORY + comment), `native/flight_control/README.md` (modified — memory-map paragraph), `test_fase_c_silicon_cited_flash_map_b1.py` (new), plus `pyproject.toml` + version-checkpoint test re-pins + docs. No `stub_main.cpp`, `startup_cortex_m4.c`, `syscalls_stub.c`, toolchain file, `capabilities/`, or `uart.{hpp,cpp}` touched.

---

## 9. Files changed

**New:**
- `tests/test_fase_c_silicon_cited_flash_map_b1.py`
- `.jes/artifacts/implementation_report_fase_c_silicon_cited_flash_map_b1.md` (this file)

**Modified:**
- `native/flight_control/mcu/linker_cortex_m4.ld` (MEMORY block + honesty comment rewritten — §3)
- `native/flight_control/README.md` (memory-map paragraph rewritten — cited, not fictional)
- `pyproject.toml` (`0.5.26` → `0.5.27`)
- ~30 pre-existing test files re-pinned from `0.5.26` to `0.5.27` (literal `'version = "X.Y.Z"' in text` pattern)
- `README.md`, `docs/ARCHITECTURE.md` (new §1c paragraph after C28), `docs/PLATFORM_CAPABILITY_VISION.md`, `docs/IMPLEMENTATION_TASKS.md` (see §10)

---

## 10. Docs updated (honesty confirmed — not claiming CLOSED/tag before Engineer ACCEPT)

- `README.md` — header banner + new "What v0.5.27 includes (working tree — not yet tagged)" section, explicitly says "no `v0.5.27` tag yet."
- `docs/ARCHITECTURE.md` §1c — new C29 B0 (park-until-named, confirmed correct) + C29 B1 paragraphs after the C28 block, top banner updated to "Working tree ahead: package `0.5.27` ... awaiting Cursor review + Engineer ★ ACCEPT — no `v0.5.27` tag yet."
- `docs/PLATFORM_CAPABILITY_VISION.md` §13 — new C29 B0 + C29 B1 blocks, same "landed — awaiting ... no tag yet" phrasing, honesty line verbatim.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD banner and the C29 B1 table row both changed to "Landed — awaiting Cursor review + ★ ACCEPT (no `v0.5.27` tag yet)." (C29 B0's own row was already externally updated to ★ ACCEPT CLOSED before this Buy started — untouched here.)
- `native/flight_control/README.md` — memory-map paragraph rewritten in place (cited, not fictional), with the full "cited != flashed" disclaimer chain.

No file in this Buy claims `v0.5.27` is tagged or ACCEPT CLOSED. Confirmed via `git tag -l | sort -V | tail -3` at close of this Buy: `v0.5.24`, `v0.5.25`, `v0.5.26` — `v0.5.27` does not exist yet.

---

## 11. Residual / next steps

- Board flash (OpenOCD/J-Link), GPIO/DShot wiring, and craft↔FS all remain independently parked axes per the existing process lock — none opened by this Buy.
- If a later teardown of the HGLRC F405 8S V1 FC identifies the exact ST order-code suffix (or a different part entirely), the map should be re-cut from that part's own datasheet, per the IC's own §0 decision 7 residual disclosure — never silently reused across sibling parts.
- C16's `-mfloat-abi=soft` ABI choice was explicitly left untouched this Buy (IC §0 decision 8) — a hard-float ABI change (matching the STM32F405's actual FPU) is a later, separate decision if ever prioritized.

---

## 12. Acceptance self-check vs IC §7

- T1-T9 (linker numbers, citations, `stub_main` unchanged, native grep, no CMSIS/OpenOCD, version, relink): ✅ all pass, 14/14 new tests green.
- T10 (this report's honesty content): ✅ this section.
- Numbers match §0.6: ✅ `FLASH 0x08000000/1024K`, `RAM 0x20000000/128K` exactly.
- `stub_main` idle: ✅ `git diff --stat` empty, relinked-but-unchanged verified.
- No flash path: ✅ no OpenOCD/J-Link content anywhere.
- No CMSIS: ✅ usage-shaped grep clean.
- Version `0.5.27`: ✅ `pyproject.toml` + all checkpoint tests re-pinned.

**PASS** against every criterion in IC §7. **FAIL conditions** (OpenOCD/flash, Cube/CMSIS pack, `stub_main` peripherals, folklore numbers with no RM0090 cite, live-Betaflight claim) — none present, verified above.
