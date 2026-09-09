# Engineer smoke — Motor `height_mm` 31.7 cited B1 (2026-09-09)

**Project:** `autonomía-de-10min`  
**Status:** **ACCEPT**  
**Parents:** [IC](implementation_contract_geometry_motor_height_cited_b1.md) · [review](implementation_review_geometry_motor_height_cited_b1.md) PASS WITH NOTES @ suite **2480**

Engineer rebound motors to `emax_rs2205s_2300` (optional §6 lab, not the previous SunnySky bind).

| Step | Surface | Expected | Result |
|---|---|---|---|
| 1 | Card `motors` | `height_mm` **31.7 mm**; SKU EMAX RS2205S | **PASS** |
| 2 | Glyph / 3D | still **disk** Ø 27.9 mm — not a cylinder from 31.7 | **PASS** |
| 3 | Other motor SKUs | 31.7 not copied onto hélices / sibling | **PASS** (prop card has no `height_mm`) |

**ACCEPT.** Height is card text. Disk stays disk.

### Orthogonal finding (not this Buy)

CLI `estado`: *este motor de catálogo no declara vatios* / *No inventes motor_power_w*.

That copy is **correct**. `emax_rs2205s_2300` has `max_watts` **null** (page left it unset; `source_note` already says so). Binding EMAX for geometry dropped SunnySky R2305, which **does** declare W. Do **not** invent `motor_power_w`. Continuity already lists SKUs that declare W. Prop/Energy remains **HD-004** — not Geometry PRIORIDAD.
