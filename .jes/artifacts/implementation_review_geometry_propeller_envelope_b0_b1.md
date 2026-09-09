# Implementation Review — Propeller B0 honesty + B1 cited bag (`gf_5045x3` only)

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_geometry_propeller_envelope_b0_b1.md](implementation_contract_geometry_propeller_envelope_b0_b1.md)  
**Report:** [implementation_report_geometry_propeller_envelope_b0_b1.md](implementation_report_geometry_propeller_envelope_b0_b1.md)  
**Buy:** Engineer ★ **B0+B1**

## Verdict

**PASS WITH NOTES**

IC locks held. Unsourced helix `mass_g` gone. HBN is `partially_verified`. Bag + seed only on `gf_5045x3`. Disk still Ø from `diameter_in`. `tmotor_22x6_7` not renamed. Fit QUEUED. Version `0.3.8`. Closable after Engineer smoke §6.

---

## Checklist

| Criterion | Result |
|---|---|
| B0: `mass_g` only on `gf_5045x3` | **Pass** — JSON + T9 + Cursor census |
| HBN `partially_verified`; no hub/blades/mass | **Pass** — T1 + foundation rename |
| HQ still `partially_verified`, no mass | **Pass** — T2 |
| `tmotor_22x6_7` key + pitch 6.7, no mass | **Pass** — T8 |
| B1 schema + loader | **Pass** |
| `gf_5045x3` bag 3 / ABS / hub 5 / 9.5 / mass 4.5 | **Pass** — T3 |
| Bind projects bag; `source_note` not a property | **Pass** — T4; units `None`/`mm`; `declared` 0.9 |
| No shaft_bore duplicate of hub Ø | **Pass** |
| `_geometry_from_spec` disk Ø 127 + hub text | **Pass** — T7 |
| No seed on 6040 / DAL / APC / other T-Motor | **Pass** |
| Foundation HBN test updated, not weakened | **Pass** |
| Suite **2489** | **Pass** — Cursor re-ran |
| Version `0.3.8` | **Pass** |
| Fit QUEUED; no STEP / no `diameter_mm` SoT | **Pass** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| 17 propellers; only `gf_5045x3` has `mass_g` / hub | **Confirmed** |
| JSON `"mass_g"` once | **Confirmed** |
| Bind `gemfan_5030` / `tmotor_15x5` omit `mass_g` | **Confirmed** T5/T6 |
| Bind `gf_5045x3` `blade_count.unit is None`, hub `mm` | **Confirmed** |
| T1–T9 | **9 passed** |
| Foundation file + new tests | **69 passed** |
| Full pytest | **2489 passed** this review |
| `dal_7040` still Ø×paso only (Cyclone next IC) | **Confirmed** |
| `pyproject.toml` `0.3.8` | **Confirmed** |

---

## Notes

### N1 — `part_number` vs EMAX Product Code

Row keeps `PMAB5045-3`; page quotes `0106003102`. IC said keep unless the page **contradicts**. Honest `source_note`. Do not silently pick one this Buy. Later identity tidy.

### N2 — HBN `tags` still say `tri-blade`

`blade_count` correctly omitted. Tags are leftover, not a seeded field. Optional later hygiene.

### N3 — `spatial_board.py` in `git diff`

That hunk is prior motor-copies B1, not this Buy. `_geometry_from_spec` unedited for hub.

### N4 — Live demo card

Still `gemfan_5045_hbn`: Ø 127 disk, no grams/hub. `gf_5045x3` bag appears only after bind/refresh of that SKU. §6 smoke.

---

## Phase

Implementation **REVIEWED PASS WITH NOTES**. Engineer smoke next ([§6](implementation_contract_geometry_propeller_envelope_b0_b1.md)). Next helix seeds (Cyclone, 10×6EP) later ★. Fit QUEUED. Package `0.3.8` · suite **2489**.
