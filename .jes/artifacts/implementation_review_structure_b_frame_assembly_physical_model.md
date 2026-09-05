# Implementation Review — Structure B Frame Assembly Physical Model B2

**Date:** 2026-09-05  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_structure_b_frame_assembly_physical_model.md](implementation_contract_structure_b_frame_assembly_physical_model.md)  
**Report:** [implementation_report_structure_b_frame_assembly_physical_model.md](implementation_report_structure_b_frame_assembly_physical_model.md)  
**Buy:** B2 · N1(c) curated · N2 `plates[]` > scalar · N3 · N4 OUT · N6 debt · N7 ≤8

## Verdict

**PASS WITH NOTES**

IC locks held. Suite **2294** reconfirmed (baseline 2286). Plate multiplicity is catalog/BOM representation only — no closed roles, no free-text architecture parser, no mass/Σ, no PASS widen.

---

## Checklist

| Criterion | Result |
|---|---|
| `PlateSeed` + `FrameSpec.plates` + loader bound >8 raises | **Pass** — T1 |
| Seed §3.2 curated lists (4 SKUs) + curated `source_note` | **Pass** — Cursor re-read `_datos.json` |
| N2: `plates` non-empty → ignore scalar plate_* | **Pass** — T4 |
| N3: equal thickness → distinct nodes | **Pass** — T5 (Top/Middle both 2mm) |
| N7: `frame_plate`…`frame_plate_8`; reject role keys | **Pass** — helpers + T1 over-max |
| N6: completeness hardcode preserved | **Pass** — comment names debt |
| BOM ordinal labeled `└ plate` lines | **Pass** — T6 |
| T7 twin Structure evidence/PASS unchanged | **Pass** |
| T8 rebind clears ordinal siblings | **Pass** — updated idle rebind test |
| T9 free-text multi-plate stays single-key | **Pass** |
| M0 / PASS * footnote / no version bump | **Pass** |
| Full suite | **2294 passed** (Cursor re-run) |

---

## Independent verification

| Check | Result |
|---|---|
| Targeted graph/freetext/catalog/rebind/foundation | **119 passed** |
| `pytest -q` full | **2294 passed** |
| Seed Top/Middle/Bottom vs IC §3.2 | **Exact match** |
| Armattan 4 plates + cage/standoff; scalar `plate_material` retained | **Confirmed** |
| PASS footnote string | **Unchanged** (`main.py:147`) |
| No role keys (`frame_plate_top` etc.) | **Confirmed** — `is_frame_plate_key` rejects |

---

## Notes

### N1 — Dual “max 8” constants (non-blocking)

Loader uses `ComponentLibrary._MAX_PLATES = 8`; runtime helpers use `FRAME_PLATE_MAX_SIBLINGS = 8`. Both locked to 8 and tested; optional later polish is one shared import. **Not blocking.**

### N2 — Completeness hardcode / upsert divergence (known debt, N6)

As the report states: projector returns `"high"`; after `upsert_frame_part` a label+thickness-only plate recomputes `"low"`. Pre-existing since arms B2; **explicitly out of this IC**. Do not treat as a new bug from plate multiplicity.

### N3 — Stale docstring in `frame_part_specs_from_catalog`

Docstring still says part children are empty “except armattan” — false now that all four rows project plates/arms. Cosmetic; fix when next touching that file.

### N4 — Pre-existing test premise updates were correct

TBS “arm-only child” → “arm + 3 plates” and Armattan 4 → 7 children match the IC’s own regression targets; assertions strengthened, not weakened.

---

## Phase

Implementation **closed** for this slice @ suite **2294**.  
Next = Engineer CLI smoke optional (`cambiar frame` → TBS → three `└ plate — …` lines) then re-evaluate System optimization vs Prop/Energy vs further KNOW.  
No ratification artifact.
