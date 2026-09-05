# Investigation Review — Structure B additive enrichment

**Date:** 2026-09-05  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_structure_b_additive_enrichment.md](investigation_contract_structure_b_additive_enrichment.md)  
**Report:** [investigation_report_structure_b_additive_enrichment.md](investigation_report_structure_b_additive_enrichment.md)  
**Base:** Structure B Fase 1 + G-N1 CLOSED @ **2229** · ontology not reopened

## Verdict

**PASS WITH NOTES**

Ontology correctly left closed. Mass policy **M0** accepted. Buy **narrow B2 =
`thickness_mm` only on `frame_arm`/`frame_plate`, display-only** accepted in
principle — with IC locks on multi-plate ambiguity and child projection.

Still **investigation** — no implementation until Engineer Buy on the notes below,
then Implementation Contract.

---

## Checklist

| Criterion | Result |
|---|---|
| Ontology not re-derived | **Pass** |
| Root-only physics mass (`structure_mass_override_kg`) | **Pass** — `component_writers.py:119-130` |
| Part fields today = count/material only | **Pass** — `_structure_part_completeness` |
| BOM `└` only count/material today | **Pass** — `_frame_part_sublines` |
| Per-part `mass_kg` / arm length OUT | **Pass** — no seed support |
| M0 (no Σ into physics / no dual mass authority) | **Pass** |
| Thickness sourced for arm + plate | **Pass** — Cursor re-checked TBS RDQ + Armattan pages |
| Structure PASS * unchanged | **Pass** |
| No `src/` | **Pass** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| TBS RDQ: Arm Thickness 6mm; plates 2 / 2.5 / 2 mm | **Confirmed** — racedayquads Source One V5 specs |
| Armattan: Main Plate 4mm; Arm 4mm | **Confirmed** — armattanquads Rooster specs table |
| Armattan Included also lists 2mm LiPo top plate + other thin plates | **Confirmed** — multi-plate reality (see **N1**) |
| `frame_part_specs_from_catalog` creates children only if count or material | **Confirmed** — `_part` returns if both None (`catalog_bind.py:321-323`) |
| TBS seed has no part materials → **no** `└` children today | **Confirmed** — thickness-only seed would still create **zero** children unless IC changes the gate |

---

## Notes (must land in IC if Buy proceeds)

### N1 — Which plate thickness when the page lists several?

TBS: top 2mm / bottom 2.5mm / middle 2mm.  
Armattan: “Main Plate 4mm” **and** Included “2mm Top (LiPo) plate” (+ other thin plates).

A single `frame_plate.thickness_mm` cannot honestly mean “all plates.” IC must lock one of:

- **(a)** Store **main/primary structural plate** only (page’s “Main Plate” / bottom plate — name the rule per SKU in `source_note`), or  
- **(b)** Ship **arm `thickness_mm` only** in the first IC; defer plate until a multi-value or split model exists, or  
- **(c)** Optional later: two properties on one node (`main_thickness_mm` / `top_thickness_mm`) — still no new node type.

Cursor lean for smallest honest slice: **(b) arms-only**, or **(a) with explicit source_note rule** if Engineer wants plates in the same IC.

### N2 — Thickness must be allowed to create part children

Today `_part(..., count, material)` skips when both absent. TBS/iFlight have thickness on the page but **no** part materials in seed → without changing the projector gate, B2 seed fields would never appear in BOM.

IC must: create `frame_arm` / `frame_plate` when `thickness_mm` (or seed arm/plate thickness) is present, even without material/count; and `_frame_part_sublines` must render a thickness-only line (today thickness-only would be skipped at the count/material guard).

### N3 — Completeness must stay non-blocking

Agree with report: thickness must **not** become required for part `"high"`. Additive only.

### N4 — Free-text `mm` extraction

IC must keep keyword-gated extraction (arm/plate clause) so bare `wheelbase 230mm` / stack sizes do not become arm thickness.

---

## Engineer Buy decisions (no separate ratification doc)

1. **Buy narrow B2?** (thickness display-only, M0) — Cursor recommends **yes**  
2. **N1 plate policy:** (a) main plate only · **(b) arms-only first** · (c) dual props — Cursor lean **(b)** or **(a)** with notes  
3. Confirm **M0** (no sum-of-parts physics)

After Buy → Cursor writes **Implementation Contract** only (no `engineer_ratification_*`).

---

## Engineer Buy recorded 2026-09-05

| Decision | Lock |
|---|---|
| B2 | **BUY** |
| N1 | **(b) arms-only first** |
| M0 | **CONFIRMED** |

IC: [implementation_contract_structure_b_thickness_arms_b2.md](implementation_contract_structure_b_thickness_arms_b2.md) — READY TO IMPLEMENT.  
Phase: **implementation** (investigation closed for this slice).
