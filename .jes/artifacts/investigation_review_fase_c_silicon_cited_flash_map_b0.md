# Investigation Review — Fase C silicon + cited FLASH map (`B0-fase-c-silicon-cited-flash-map`)

**Date:** 2026-09-24  
**Reviewer:** Cursor (independent — not investigator)  
**Against:** [contract](investigation_contract_fase_c_silicon_cited_flash_map_b0.md) · [report](investigation_report_fase_c_silicon_cited_flash_map_b0.md)  
**Verdict:** **PASS WITH NOTES** · investigation ★ ACCEPT CLOSED (no version bump; tip remains **`v0.5.26`**)

---

## Summary

C29 B0 is an **investigation**, not a linker rewrite. The live C18 map is still fiction: FLASH `0x00000000` / 256 KiB, RAM `0x20000000` / 64 KiB — quoted verbatim from disk, `git diff` on `native/` empty. Recommendation **park until a named MCU** was the only honest option **on the evidence this report had**. Honesty line present:

```text
cited FLASH map ≠ flashed ≠ boots on FC ≠ this desk’s MCU
```

Package still **`0.5.26`**. No tag.

---

## Contract checklist (E1–E5)

| Gate | Result |
|---|---|
| E1 Quote live `linker_cortex_m4.ld` MEMORY + honesty comment | **Pass** — matches disk byte-for-byte (this review) |
| E2 Contrast ARM `0x00000000` vs labeled vendor remap, not adopted | **Pass with N1** |
| E3 What a later B1 would touch / must not touch | **Pass** — linker MEMORY+comment, README; not `stub_main`, CMSIS, GPIO/USART, flash |
| E4 One of three locked options | **Pass** — park (not provisional class, not forever) |
| E5 Honesty line | **Pass** |
| No linker rewrite · no version bump · no native/ writes | **Pass** — independent `git diff --stat -- native/ pyproject.toml` empty |
| No silent part pick · no “boots on STM32” | **Pass** |

---

## Notes (not a recut of the report)

| ID | Note |
|---|---|
| **N1** | E2 names RM0090 §2.3 but the report **discloses it did not open that PDF** and cites no table/page. Acceptable for a **labeled contrast** that then **parks**. A B1 must cite a table actually read (B1 IC already locks RM0090 **Table 3**). |
| **N2** | After this report was written, the Engineer named desk silicon: **HGLRC F460 6S V1** / FC **HGLRC F405 8S V1** / MCU **STM32F405**. That is exactly the report’s own un-park trigger (§4). It does **not** make the park recommendation a fail — the report had no named part in its evidence window. |
| **N3** | Report §8 said “do not draft a B1 until naming.” Naming happened the same day. B1 IC: [implementation_contract_fase_c_silicon_cited_flash_map_b1.md](implementation_contract_fase_c_silicon_cited_flash_map_b1.md). |

---

## Lean (Cursor)

Agree with the report **for its evidence**: park, do not guess F405, do not keep fiction “forever.”

The Engineer has now named the MCU. **C18’s linked map is still fictional** until a B1 rewrites it. Next front is that B1, not flash, not Betaflight.

---

## Verdict

**PASS WITH NOTES** · investigation ACCEPT CLOSED. Tip stays **`v0.5.26`**.

**Pass to Claude:** [C29 B1 IC](implementation_contract_fase_c_silicon_cited_flash_map_b1.md) — linker cites RM0090 Table 3 for STM32F405; still not flashed.
