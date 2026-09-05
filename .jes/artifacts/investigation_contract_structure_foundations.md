# Investigation Contract — Structure Foundations (Fase 1)

**Project:** Jarvis  
**Date:** 2026-09-04  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_structure_foundations.md`

**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · IC drafted · awaiting Engineer `procede`  
**Review:** [investigation_review_structure_foundations.md](investigation_review_structure_foundations.md)  
**Report:** [investigation_report_structure_foundations.md](investigation_report_structure_foundations.md)  
**IC:** [implementation_contract_structure_foundations.md](implementation_contract_structure_foundations.md)  
**★ decision:** [engineer_ratification_structure_foundations.md](engineer_ratification_structure_foundations.md)  
**Prior structure:** Structure A CLOSED (code + review; N1 hotfix closed)  
**Prior phase closed:** knowledge / block parity (claim hygiene + control parity)

**Type:** Product / knowledge investigation. Determine **Structure Fase 1
foundations** on top of Structure A: explicit variables, deterministic
completeness, honest claims — **without** CAD or generative geometry.
**Not** an Implementation Contract. **Do not implement.**

**Checkpoint base:** tag **`v0.3.6`** / **`checkpoint-experimental-prop-energy-closed`** · commit `f70b278`  
**Live tree:** claim hygiene + control parity in product (suite **2164**). Preserve them.

**You are Claude Code.** Write the report only. Cursor reviews. Engineer
`procede` on a later IC ratifies Buy (no separate Buy ★ file required).

**Do not implement. Do not bump version. Do not weaken tests. Do not open CAD,
FEA, STL/STEP generators, tip-clearance physics, or “cabe físicamente.”**

---

## 0. Role split

```text
Engineer  → closed knowledge parity; opened Structure Foundations (this ★)
Cursor    → this contract; later IC after review + procede
Claude    → investigation_report_structure_foundations.md
Cursor    → investigation review
Engineer  → procede on IC (or edit IC directly if no)
Claude    → implements from IC only
```

---

## 1. Locked stances (do not contradict)

1. **Structure A remains the foundation.** LEVEL A class compatibility
   (\(D\) vs `size_class_inch`), mass/material paths, no class→thrust, no
   geometric FIT VERIFIED — do **not** re-litigate unless a seam **blocks**
   Foundations.
2. **CAD / piezas / chasis generators / FEA** are **explicitly out** of this
   investigation’s Buy recommendations.
3. **Frame catalog** and **minimal parametric layout** are **candidate
   options** to evaluate — not pre-authorized Buys.
4. First-phase bar: same maturity class as current prop/energy/control-claims
   loops — visible limits, honest language — **not** OEM structural analysis.
5. Do **not** invent densities, arm lengths, or clearances as physics truth.

---

## 2. Objective

Answer:

> What Structure Fase 1 foundations must be built on Structure A so Jarvis can
> **represent, evaluate, and communicate** structure with explicit variables,
> deterministic completeness, and honest claims — without CAD or generative
> geometry?

---

## 3. Questions the report must answer

### Vocabulario y completitud

1. What **minimum structural vocabulary** is still missing beyond mass,
   material, `size_class_inch`?
2. What does **`structure complete`** mean exactly today (architecture block,
   `_frame_completeness`, ERF structure, Continuity)? Where do those disagree?

### Claims

3. What may Structure **claim** today, and what must it **forbid** (matrix)?
4. What residual gaps did Structure A leave (review notes N2+, Continuity,
   `get_block_in_progress_reason`, dual `_block_progress_status`, etc.) that
   **block** Foundations vs that are **hygiene-only**?

### Catálogo (opción)

5. What information would a **frame catalog-bound** row actually buy
   (identity, mass, class, config) — and what would it **not** buy?
6. What **evidence** would be required to declare those catalog fields honestly
   (manufacturer sheet vs guess vs lab)?

### Layout paramétrico (opción)

7. Does a **minimal parametric layout** (e.g. wheelbase / arm / declared tip
   clearance) make sense in Fase 1?
8. What does **“declarado” vs “verificado”** mean for layout numbers so Jarvis
   does not imply CAD proof?

### Buy

9. What is the **minimum Buy** that produces a real capability jump (B0 docs /
   B1 claim-copy / B2 completeness+guide / B3 thin frame catalog / B4
   declared layout params / B5 split…)? Prefer one primary.
10. What stays **explicitly out** — CAD / piezas / FEA / generative geometry /
    class→thrust / geometric fit verified?

**Do not** open a large “re-close Structure A” workstream unless you name a
**blocking** gap with `file:line` that Foundations cannot proceed without.

---

## 4. Surfaces to trace (file:line)

| Area | Trace |
|---|---|
| Structure A live | `set_frame_material`, `size_class_inch`, `GAP-FRAME-*`, class vs \(D\) |
| Completeness | `_frame_completeness`, `component_presence_tier`, architecture `structure` block |
| ERF | `_structure_evidence`, structure verdict vs ASSEMBLY_READY |
| Continuity / CLI | structure next-missing, class-incompatible copy, in-progress reasons |
| Invasion | Confirm CalculationEngine / thrust still ignore frame class |
| Catalog precedent | How motor/battery/prop bind + BOM ✓ differ from frame today |
| Layout absences | Any wheelbase/arm/clearance fields already present or absent |

Cite Structure A IC/report/review only as context; **verify on live tree**.

---

## 5. Field reconstruction

At least one in-memory / `tmp_path` fixture:

```text
frame mass + material + size_class compatible with prop D
→ structure architecture status, ERF structure verdict, Continuity lines, BOM
```

Optional contrast: class missing / class incompatible — what Jarvis claims.

Do not mutate Engineer `workspace/`.

---

## 6. Required report shape

### A. Executive answer (≤20 lines)

Foundations recommendation in one paragraph + primary Buy.

### B. As-is map (Know)

Vocabulary present vs absent; completeness authorities table.

### C. Claim matrix (Claim)

| Sentence / verdict | Allowed today | Over-claim? | Proposed Fase 1 meaning |

### D. Structure A residuals

Blocking vs non-blocking for Foundations.

### E. Option analysis

| Option | What it buys | Evidence needed | Fase 1 fit? |
|---|---|---|---|
| Claim/completeness only | | | |
| Thin frame catalog | | | |
| Declared layout params | | | |
| CAD / FEA | | | **No** |

### F. Buy (exactly one primary)

Justify minimum real capability jump. If catalog or layout wins, state
**evidence rules** and forbidden over-claims. If only claim-copy, say so.

### G. Explicit non-goals

CAD, generative parts, FEA, geometric FIT VERIFIED, class→thrust, control
catalog, HD-*, reopening claim-hygiene/control parity.

### H. IC skeleton (if Buy ≠ B0)

≤25 lines: files, behavior, tests, forbidden — **not** an IC.

---

## 7. Constraints

- No `src/` / catalog JSON authored as “the deliverable” of this investigation
  (you may **propose** schema fields in the report).
- No weakening Structure A LEVEL A rules.
- No `_derive_overall` change unless you prove claim-copy cannot stop a lying
  structure PASS / 4/4 — that is an Engineer stop, not a default.
- Full honesty with first-phase bar (not OEM FEA).

---

## 8. Done criteria

- Report at the path above with A–H  
- Every factual claim cites `file:line` or named test on live tree / `v0.3.6`+  
- Primary Buy chosen; CAD rejected with reason  
- No `src/` edits  

---

## 9. After review

Cursor writes investigation review. Engineer `procede` on IC (or edits IC).
Only then implementation.
