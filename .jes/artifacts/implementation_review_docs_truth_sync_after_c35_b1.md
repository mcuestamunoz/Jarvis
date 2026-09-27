# Implementation Review — Docs truth-sync after C35 / Taller (`B1-docs-truth-sync-after-c35`)

**Date:** 2026-09-25  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_docs_truth_sync_after_c35_b1.md) · [inventory](inventory_docs_truth_sync_after_c35_b0.md) · [report](implementation_report_docs_truth_sync_after_c35_b1.md)  
**Verdict:** **PASS WITH NOTES** (N1–N2 residual, accepted) — awaiting Engineer **spot-check** (system_map tip + native README + USER_GUIDE §8.4) + ★ ACCEPT. **No `v0.5.36` tag.**

---

## Summary

This Buy is **docs only**. Base maps and the native README no longer name C5/`v0.5.3` / “no C++ tree” / “C++ (future IC)” as **current**. Tip in `docs/system_map/README.md` and `JARVIS_SYSTEM_MAP.md` is **`v0.5.35`**. CONNECTIONS gained **one** changelog paragraph (C6–C35 + Taller cuboid/cylinder); the canonical table still ends at **C-113**. Native README names `dshot` / `spi.hpp` / `ScriptedSpi` / `probe_rx` / C35 `test_loop`; C30 is tagged **`v0.5.28`**. USER_GUIDE §8.4 has the one-prism / one-cylinder-body line. Craft tip stays **`v0.4.3`**. Isolation: no new `C-xxx`.

Honesty:

```text
docs tip ≠ flying ≠ gyro live ≠ DShot pin ≠ new C-xxx ≠ standoff ×8 shipped
```

Independent: Python **3691 passed, 2 skipped**. Host `ctest` **76/76**. Package **`0.5.36`**. Tag **`v0.5.36` does not exist**. Parent tag **`v0.5.35` exists** locally. Visual/map spot-check is **not** substituted by pytest.

---

## Locks (IC §0)

| # | Lock | Result |
|---|---|---|
| 1 | Docs match tagged product after cylinder ACCEPT | **Pass** (maps/native/guide; living quartet retarget only) |
| 2 | Docs only — no standoff / MY5 / silicon / visor recut | **Pass** |
| 4 | Tagged code > PRIORIDAD > old maps; never “fix” via `src/` | **Pass** |
| 5 | Epoch `v0.5.35`; craft `v0.4.3`; live suite 3691 / UI 142 / ctest 76 | **Pass** |
| 6 | No C-114 | **Pass** — grep empty |
| 7 | C++ exists and isolated; C3 “future IC” left as historical | **Pass** — ARCHITECTURE §1c C3 quote untouched (`git diff` 4 lines, banner/Next only) |
| 8 | Phase 0 inventory before bulk edits | **Pass** — inventory artifact exists with 8+9+4+22 rows. Git cannot prove write-order; accepted on artifact claim + Phase 1 matching the rows |
| 9 | Stamp, don’t delete archives | **Pass** — VISION / BUGS / Continuity / C3 quote left |
| 10 | **`0.5.36`** after `v0.5.35` | **Pass** |
| 11 | Forbidden claims | **Pass** — landed, no tag; no MY5 mm / standoff ×8 as shipped |

---

## Cursor checks (independent)

| Check | Result |
|---|---|
| T1 inventory one row per §1.1 + remaining docs | **Pass** — 8 must-fix + 9 must-not + 4 living + 22 stamp-only |
| T2 maps tip `v0.5.35`, not current `v0.5.3` | **Pass** — system_map README header + JARVIS_SYSTEM_MAP “Fase C tagged tip `v0.5.35`” |
| T3 “no C++/CMake” / “future IC” not **current** | **Pass** — JARVIS_SYSTEM_MAP frames docstring as pre-C13; canvas C1–C5 Callout says “accurate as of this date” + pointer to `v0.5.35`. Product-queue Callout is `v0.5.35` |
| T4 CONNECTIONS table ends C-113; one new paragraph | **Pass** — new block after C1–C5 note; registry row C-113 last; no C-114 |
| T5 native README spi / ScriptedSpi / probe_rx / dshot / test_loop; C30 `v0.5.28` | **Pass** — `not yet tagged` gone |
| T6 USER_GUIDE §8.4 prism + cylinder body; no 161×42×2 / ×8 | **Pass** — Spanish paragraph; “un standoff” as tall-post example, not ×8 shipped |
| T7 no this-Buy `src/` / `ui/` / `library/` | **Pass** — this-Buy `git diff` is docs + native README + pyproject + pins. Parallel dirty catalog/`spatial_board.py` is **other track** |
| T8 `0.5.36` | **Pass** |
| T9 pytest + ctest | **Pass — 3691 + 76/76** (sandbox PTY errors folded; rerun with full perms) |
| T10 report lists §1.1 + stamp-only | **Pass with N2** — §1.1 named in report; 22 stamp-only live in the inventory, not copied into the report |
| Tag `v0.5.36` | **Absent** (correct until ACCEPT) |

---

## Process note

The IC file still said **READY** when Claude implemented. The Engineer paste began **`★ D2 docs. Implementa ahora.`** That is ★ via chat. Claude was right to proceed after seeing local `v0.5.35`. Folded here: IC status → LANDED, awaiting spot-check + ACCEPT.

---

## Notes

| ID | Status |
|---|---|
| N1 | **Residual, accept** — Engineer spot-check of map tip + native README + USER_GUIDE §8.4 is still the human gate |
| N2 | **Residual, accept** — T10 stamp-only 22 files are enumerated in the inventory, not restated in the report. Not worth recutting |

---

## Verdict

**PASS WITH NOTES** (N1–N2 residual). Ready for Engineer **open the map / native README / guía §8.4**, then ★ ACCEPT + tag **`v0.5.36`**.

Do **not** claim flying, gyro live, DShot pin, C-114, or MY5/standoff ×8 as shipped.

Next after ACCEPT: cola standoff perimeter points (still no ACCEPT).
