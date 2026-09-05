# Structure Block — Notes ledger + pre-close code audit

**Date:** 2026-09-04  
**Authority:** Cursor (JES) — Engineer requested expanded notes + global code check before ★ close  
**Suite:** **2223** (full) · targeted Structure packs **92**  
**Independent audit:** [explore agent](3eb31a16-5600-41f0-b239-65c67d073656)

**Verdict:** **READY TO CLOSE** — G-N1 absorbed; no blocking code defects. Suite **2229**.

---

## 1. What this block shipped (closed slices)

| Slice | Suite at close | Status |
|---|---|---|
| Structure A (LEVEL A class) + N1 hotfix | ~2143 | CLOSED |
| Structure Foundations (BOM/Continuity claim-copy) | 2171 | CLOSED |
| Catalog Foundation IC-1 schema+seed | 2177 | CLOSED |
| Catalog Foundation IC-2 bind+BOM+diverge | 2188 | CLOSED |
| Catalog Foundation IC-3 assist | 2197 | CLOSED |
| Structure honesty `PASS *` | 2200 | CLOSED |
| Structure B Parts Graph Fase 1 | 2223 | CLOSED |
| Structure B G-N1 free-text root+parts | **2229** | CLOSED |

**Locked wall (still true in code):** Structure PASS ≠ chassis verified / motors fit / clearance / FEA / CAD. MEASURE out.

---

## 2. Expanded notes ledger

Legend: **Carry** = still true after close · **Absorbed** = fixed by a later IC · **Cosmetic** = docs/filenames · **Debt** = optional follow-on

### A. Structure B Parts Graph (current)

| ID | Note | Class | Meaning |
|---|---|---|---|
| **G-N1** | Free-text part extractor exists; **not** wired into live chat wizard | **Absorbed (2026-09-04)** | G-N1 IC: root+parts one message + parts-only path. Suite **2229**. |
| **G-N2** | Armattan page *Included* lists `4x Arms` etc.; seed left counts unset | **Carry / Debt** | Conservative (avoids inventing from config name). Optional seed enrichment from Included list. |
| **G-N3** | `compressed-x` missing from free-text `CONFIGURATION_MAP` | **Carry / Debt** | Catalog seed maps Armattan → `quad_x`. Free-text “compressed-x” may not match until alias added. |
| **G-N4** | Frame catalog diverge clears `catalog_ref` but **leaves** `frame_*` children | **Carry** | IC allowed “leave children.” Possible orphan parts after frankenstein clear — low severity. |
| **G-N5** | Report filename vs contract filename mismatch | **Cosmetic** | No product impact. |

### B. Structure honesty `PASS *`

| ID | Note | Class | Meaning |
|---|---|---|---|
| **H-N1** | Control test docstring still says “no other subsystem is marked” | **Cosmetic** | Assertions correct (Propulsion/Energy); Structure also marks now. |
| **H-N2** | Working tree Continuity dirty from *prior* claim-hygiene / Foundations | **Ops** | Not introduced by honesty; commit hygiene when Engineer commits the arc. |
| **H-N3** | Report linked `…pass_asterisk` vs contract `…pass_star` | **Cosmetic** | |
| **H-N4** | Control non-PASS test narrowed from blanket `"*" not in text` | **Absorbed** | Correct adaptation for Structure `PASS *`. |

### C. Catalog Foundation (IC-1→3)

| ID | Note | Class | Meaning |
|---|---|---|---|
| **C3-N1** | Assist list may omit visible sku key on some lines | **Carry** | Pick still works; UX polish. |
| **C3-N2** | Assist `limit=10` | **Carry** | Fine with 4 seed rows; revisit if catalog grows. |
| **C3-N3** | CLI walk done by implementer | **Absorbed** | Engineer walk also done earlier. |
| **C2-N1** | Mass-diverge test via override path | **Absorbed** | Extra coverage landed. |
| **C1-N1** | Some seed URLs are retailer not OEM | **Carry** | Honest sourcing; noted in IC-1. |
| **C1-N2** | Legacy deferred prose in docs | **Cosmetic / Debt** | Doc hygiene. |

### D. Structure Foundations / Structure A (earlier)

| ID | Note | Class | Meaning |
|---|---|---|---|
| **F-N1** | Catalog / layout as *options*, not reopen | **Absorbed into B** | B opened as KNOW+CLAIM graph, not layout MEASURE. |
| **F-N2** | Broader Continuity “PASS + any gap” audit | **Debt** | Out of Structure block; phase-level if ever. |
| **A residuals** | Completeness ≠ class check; Continuity/BOM suffixes | **Absorbed** | Foundations + honesty closed the claim-copy holes that mattered for this arc. |

### E. Investigation notes superseded (do not reopen as bugs)

| Source | Was | Now |
|---|---|---|
| Scalar Fase 1 (3 properties) | Proposed then **rejected** by Engineer ★ B | Superseded by graph |
| “Write-only layout params” fear | High for MEASURE-adjacent wheelbase | Mitigated by honesty `PASS *` + declared-only claims + no clearance |
| BOM children as peers | Investigation review N1 | **Fixed** in graph IC |

---

## 3. Global code audit (pre-close)

Independent check (read-only) of close invariants:

| Invariant | Result |
|---|---|
| `_structure_evidence` = frame + mass calc + sim only; `catalog_bound` unused for PASS | **Pass** |
| `BLOCK_TO_COMPONENTS["structure"] == ["frame"]` | **Pass** |
| `_frame_completeness` = mass + material only | **Pass** |
| BOM skips `parent_key`; `└` under frame only | **Pass** |
| `parent_key` default `None` | **Pass** |
| No `mounts_on` / sum-of-parts / arm↔motor cross-check | **Pass** |
| Config never from `motor_count`; wheelbase keyword-gated; bare mm ≠ size_class | **Pass** |
| `engineering_readiness.py` Structure B widen | **Pass** (zero product widen for PASS) |
| Bind: Armattan children / TBS none / root wheelbase+config | **Pass** |
| Honesty footnotes Structure + Control | **Pass** |
| Seed: no fabricated `arm_count`; materials + wheelbases + notes | **Pass** |
| Free-text part extractor unwired | **Pass (intentional residual G-N1)** |

**Tests re-run for this audit:** targeted **92** · full suite **2223**.

**Unexpected blocking risks:** none.

---

## 4. What “cerrar el bloque” means

**In scope to ★-close now:**
- Structure representation arc through Catalog + honesty + parts-graph Fase 1 + **G-N1**
- Claim wall: PASS / BOM / Continuity do not claim chassis verification
- Residuals G-N2…N4 and C3-N1/N2 carried as **optional debt**, not open ICs

**Explicitly not closed / not started:**
- MEASURE (fit, clearance, strength, FEA, CAD)
- Hardware / per-instance nodes / `mounts_on`
- Sum-of-parts mass
- Widening Structure PASS evidence bits

---

## 5. Suggested Engineer ★ close line

> Structure block (Foundations claim-copy · Catalog Foundation IC-1–3 · Structure honesty `PASS *` · Structure B Parts Graph Fase 1 · G-N1 free-text root+parts) **CLOSED** at suite **2229**. Residuals G-N2 (Armattan counts), G-N3 (`compressed-x` alias), G-N4 (diverge orphans), C3-N1/N2 (assist UX) are **debt**, not open work. MEASURE remains out. Next focus = Engineer-named.

On ★, Cursor updates `engineering_state.json` + `IMPLEMENTATION_TASKS.md` PRIORIDAD and stops treating Structure as active queue.
