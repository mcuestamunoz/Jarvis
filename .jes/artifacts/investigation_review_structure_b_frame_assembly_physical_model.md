# Investigation Review — Structure B Frame Assembly Physical Model

**Date:** 2026-09-05  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_structure_b_frame_assembly_physical_model.md](investigation_contract_structure_b_frame_assembly_physical_model.md)  
**Report:** [investigation_report_structure_b_frame_assembly_physical_model.md](investigation_report_structure_b_frame_assembly_physical_model.md)  
**Base:** Parts Graph Fase 1 + G-N1 @ **2229** · arms `thickness_mm` B2 @ **2286** + smoke PASS · Fase 1 = product baseline

## Verdict

**PASS WITH NOTES**

Hinge answered correctly: **plate thickness alone is not a valid next IC**; multiplicity is a prerequisite. Buy **B2** accepted in principle as **ordinal plate siblings + free-text `label`**, deliberately **not** a closed cross-manufacturer role taxonomy — evidenced deviation from the contract’s sketched “role typing” wording, and the right one.

**Engineer Buy locked 2026-09-05** — see §Buy recorded. IC written; phase → **implementation**.

---

## Checklist

| Criterion | Result |
|---|---|
| Fase 1 graph treated as baseline (not greenfield) | **Pass** |
| A–G answered with `file:line` evidence | **Pass** (A3: one wording nit — **N5**) |
| Explicit plate thickness vs roles/multiplicity | **Pass** — thickness-alone disproven; B3 rejected |
| One Buy option | **Pass** — **B2** (ordinal + `label`) |
| M0 / no Σ→physics / no part `mass_kg` | **Pass** |
| MEASURE / CAD / FEA / fit / mounts out | **Pass** |
| Structure PASS * footnote unchanged (default) | **Pass** — agree leave as-is until implemented model warrants |
| Prefer existing `ComponentSpec` / writers / BOM | **Pass** — `upsert_frame_part` already key-generic; `clear_frame_part_children` already `parent_key`-based |
| No closed role enum invented | **Pass** — Cursor concurs |
| No `src/` this turn | **Pass** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| TBS RDQ: Top 2mm / Middle 2mm / Bottom 2.5mm (+ Camera plate 2mm on same page) | **Confirmed** — racedayquads Source One V5 specs |
| Armattan Specs: Main Plate 4mm / Arm 4mm; Included: 2mm LiPo top, 1.5mm front/rear (+ other carbon pieces) | **Confirmed** — armattanquads Rooster page |
| iFlight XL7 V4 (fpv24): “5mm arms, 1,5mm vertical side plates” / “2mm upper, upper and lower plate” | **Confirmed** — page still lists those lines |
| Single `frame_plate` key + flat `FrameSpec` plate scalars | **Confirmed** — `aerial.py:342`, `library.py:179-180`, `catalog_bind.py:352-353` |
| BOM one line per fixed part type | **Confirmed** — `_FRAME_PART_ORDER` (`project_closure.py:758-778`) |
| Free-text one entry per locked key | **Confirmed** — `by_key` (`aerial.py:429-441`); **longest alias wins**, not “last clause” (**N5**) |
| Rebind already clears all `parent_key=="frame"` children | **Confirmed** — `clear_frame_part_children` (`component_writers.py:218-225`) — ordinal siblings fit without a new clear path |

---

## Agreement with report core

1. **Attribute-drip rejected** — plate thickness on the single existing node would silently discard sourced values on **4/4** seed pages. Same honesty class as the material split that created the parts graph.
2. **Closed role taxonomy rejected** — manufacturers share no vocabulary; mapping TBS “bottom” ↔ Armattan “main” would be an invented equivalence (same class as `arm_count`↔`motor_count`).
3. **Scope to plates only** — arms/cage/standoff/hardware correctly OUT of this Buy; arms thickness already shipped.
4. **PASS * footnote** — leave current Spanish string until an *implemented* model justifies change.
5. **B0/B1/B3/B4** — rejections are sound; B3 is disproven by evidence.

---

## Notes (must land in IC if Buy proceeds)

### N1 — Seed inclusion policy (load-bearing)

Sources list **more** plates than the report’s illustrative quotes:

- TBS: also **Camera plate 2mm** on the same specs block.
- Armattan Included: also **HD Cam 1.5mm**, **Rear VTX 2mm**, etc., beyond Main / LiPo / front / rear.

IC must lock **which plate rows enter `plates`**, e.g. one of:

- **(a)** Specs-table named thicknesses only (TBS top/middle/bottom; Armattan Main from Specs + only Included rows Engineer names), or  
- **(b)** Every distinct carbon plate named with a thickness on the seed’s `source_url` page, or  
- **(c)** Explicit curated list per SKU in `source_note` (recommended for honesty + bounded N).

Cursor lean: **(c)** curated per SKU with verbatim labels — avoids unbounded Included kits and silent omission of Camera/VTX without pretending a universal rule.

### N2 — Dual seed fields: `plate_*` scalars vs `plates[]`

Report keeps `plate_count` / `plate_material` as single-plate fallback. IC must lock precedence when both exist (Armattan today has `plate_material`):

- If `plates` is non-empty → projector emits only from `plates` (ignore scalar plate fields for children), or  
- Merge rule: scalar = plate[0] material/count when `plates[0].material` is None.

Ambiguity here will fork BOM vs seed.

### N3 — One node per named plate (not coalesce-by-thickness)

TBS top+middle are both 2mm but differently named. IC must **not** merge same-thickness plates into one node. Ordinal + `label` implies **one node per curated named entry**.

### N4 — Free-text multi-plate stays debt

Agree: this IC is **catalog projection + seed + BOM** only. Name explicitly in Vision/debt: free-text ordinal / multi-clause plate parsing **out** (today longest-alias-per-key already drops a second plate clause).

### N5 — A3 wording nit (non-blocking)

Report says free-text “last-processed matching clause survives.” Code is **longest alias wins** (`aerial.py:437-438`); equal length keeps the first. Same practical conclusion (second plate lost); fix wording only if anyone reuses A3 as IC text.

### N6 — Projector / completeness honesty

Catalog `_part` still hardcodes `completeness="high"` even for thickness-only arms (`catalog_bind.py:345`) while `_structure_part_completeness` would grade thickness/label-only as `"low"`. Prior polish debt — if plate siblings can be thickness+label-only, IC should either call the real completeness helper or document the hardcode as known debt (do not let plate siblings silently change PASS/architecture).

### N7 — Bound + key pattern

Lock `frame_plate` = first curated entry, then `frame_plate_2`…`frame_plate_N` with a small explicit max (e.g. ≤8) or “only what seed lists.” BOM iteration must discover `frame_plate*` present under `parent_key="frame"`, not only the fixed 4-tuple — without treating arbitrary `frame_plate_foo` role keys as valid (role enum remains forbidden).

---

## Engineer Buy decisions (no separate ratification doc)

1. **Buy B2** as report shapes it — ordinal plate siblings + free-text `label` + `plates: list[PlateSeed]`, M0, no MEASURE, **no** closed role taxonomy?  
   Cursor recommends **yes**.
2. **N1 seed inclusion:** (a) specs-only · (b) all named on page · **(c) curated per SKU** — Cursor lean **(c)**.
3. Confirm **N2** precedence + **N4** free-text out + **PASS *** footnote unchanged.

---

## Engineer Buy recorded 2026-09-05

| Decision | Lock |
|---|---|
| B2 (`plates[]` + ordinal siblings + free `label`) | **BUY** |
| Closed role taxonomy | **NO** |
| Thickness-only single `frame_plate` | **NO** |
| N1 | **(c) curated per SKU** |
| N2 | **`plates[]` canonical** when non-empty; scalar `plate_*` legacy fallback |
| N3 | **One node per named plate** (no merge by thickness) |
| N4 free-text multi-plate | **OUT** (debt) |
| N6 completeness hardcode | **Preserve; debt explicit** |
| N7 bound | **≤8** (`frame_plate` … `frame_plate_8`) |
| M0 / PASS * footnote | **CONFIRMED** unchanged |

IC: [implementation_contract_structure_b_frame_assembly_physical_model.md](implementation_contract_structure_b_frame_assembly_physical_model.md) — **READY TO IMPLEMENT**.  
Phase: **implementation** (investigation closed for this slice).  
Then re-evaluate System optimization vs Prop/Energy vs further KNOW.
