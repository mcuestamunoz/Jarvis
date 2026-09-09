# Investigation Review — Plate L×W / Rooster envelope

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_geometry_plate_lw_sourced_b1.md](investigation_contract_geometry_plate_lw_sourced_b1.md)  
**Report:** [investigation_report_geometry_plate_lw_sourced_b1.md](investigation_report_geometry_plate_lw_sourced_b1.md)

## Verdict

**PASS WITH NOTES** · recommended Buy **B0** (no frame box for Rooster; no IC)

Neither manufacturer nor retailer listing supplies plate/airframe L×W. `_geometry_from_spec` does not and must not stitch `wheelbase_mm` or thickness into a box. Closable as **gap holds**. Optional text-only plate list is **not** the 3D step. Engineer-`declared` L×W remains the only way a Rooster box appears this cycle.

---

## Checklist

| Criterion | Result |
|---|---|
| Armattan live quotes; footprint no | **Pass** — Cursor re-fetched `armattanquads.com/products/rooster-1` 2026-09-09: 125 g, 230 mm @5in, Compressed X, Main/Arm 4 mm, Max Stack Height 22 mm. No L×W. |
| GetFPV 403 disclosed | **Pass** |
| Wheelbase ≠ footprint | **Pass** |
| `_geometry_from_spec` box triple / disk Ø only | **Pass** — code |
| iFlight `body_*` ≠ box keys | **Pass** — bind projects `body_length_mm`/`body_width_mm`; FrameSpec docstring: not a full box glyph alone |
| No `src/` / seed | **Pass** (report only) |
| Single lean | **Pass** — **B0** |

---

## Independent checks

| Claim | Cursor |
|---|---|
| Rooster `plates[]` = four thickness rows, no L×W | **Confirmed** `_datos.json` |
| Bind does not alias `body_*` → `length_mm` | **Confirmed** `catalog_bind.py` |
| No frame in catalog yields a box today | **Agree** — no row has `length_mm`/`width_mm`/`height_mm` |

---

## Notes

### N1 — HD / VTX plates are also on Armattan **Included**, not GetFPV-only

Claude used a 2023 Wayback GetFPV snapshot (honest 403). Cursor’s **live** Armattan page **Included** already lists `1.5mm HD Cam plate` and `2mm Rear VTX plates (Standard and TBS)` plus nylon standoffs. Optional B1 (extra `plates[]`) can cite **manufacturer Included**, not the archive. Still thickness-only → **not a box**.

### N2 — Live demo census

Contract asked whether the live frame card already has a solid. Report omitted workspace. Does not change B0: seed has no box triple.

### N3 — Wayback ≠ live GetFPV

Flagged correctly. Do not treat 2023 HTML as 2026 shop SoT. For footprint, Armattan live is enough: **no**.

---

## Buys (locked ranking)

1. **B0 (default)** — leave Rooster frame-box **gap**. Mapping rung 4 **closed as UNKNOWN footprint**, not as a failed 3D stack.  
2. Optional text B1 — extra named plates + `max_stack_height_mm` 22 — **card/BOM only**. Separate ★.  
3. Engineer-**declared** Main Plate L×W (`source=declared`) — only 3D path for this SKU without a new drawing. You supply the millimetres.  
4. Wait for a dimensioned drawing — later.

Do **not** IC a `_geometry_from_spec` wheelbase path. Do **not** copy iFlight 202×202 onto Rooster.

---

## Phase

Investigation **REVIEWED PASS WITH NOTES**. No implementation until Engineer ★ a Buy other than B0. Package `0.3.8` · suite **2497**.
