# Implementation Report — #4g+ Sourced frame HGLRC MY5 B1

**IC:** [implementation_contract_geometry_sourced_frame_hglrc_my5_b1.md](implementation_contract_geometry_sourced_frame_hglrc_my5_b1.md)  
**Implementer:** Cursor (Engineer: “añadelo tú” · catalog-only)  
**Date:** 2026-09-13  
**Baseline:** package `0.4.1` · targeted tests green

---

## Files changed

- `library/frames/_datos.json` — new SKU `hglrc_my5_5in`
- `tests/test_geometry_sourced_frame_hglrc_my5_b1.py` — T1–T4
- this report · PRIORIDAD sync

No `workspace/` mutation. No live rebind. No version bump. GEP/Rooster rows untouched.

## Seed (locked bag)

| Field | Value |
|---|---|
| SKU | `hglrc_my5_5in` |
| wheelbase_mm | 225 |
| body L×W | 225×200 (envelope only) |
| mass_g | 140 |
| size_class_inch | 5 |
| configuration | quad_x |
| arm_thickness_mm | 5.0 |
| plates | Top 2.0 · Middle 3.0 · Bottom 2.0 |
| standoffs | **omitted** (no H/count/Ø on page) |
| source_url | https://www.rotorama.com/product/hglrc-my5 |

Bind projects `body_*` + plate thicknesses; **no** `length_mm`/`width_mm` on plate children. First plate child label = Top plate → `frame_plate`.

## Tests

`pytest tests/test_geometry_sourced_frame_hglrc_my5_b1.py tests/test_geometry_sourced_frame_gep_racer_b1.py` → **9 passed**. Package `0.4.1`.

## Honesty

Does **not** close `B1-plate-box`. 225×200 must never be treated as stack-plate L×W.
