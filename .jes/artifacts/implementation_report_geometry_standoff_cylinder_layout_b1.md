# Implementation Report — Standoff cylinder visor layout B1

**Status:** Done (implementation) — awaiting independent review + Engineer smoke  
**IC:** `implementation_contract_geometry_standoff_cylinder_layout_b1.md`  
**Implementer:** Cursor (Engineer “procede tu” 2026-09-24 — JES exception)  
**Baseline:** package **`0.5.30`** (unchanged) · suite **3650** → **3658** (+8) · UI untouched

## Summary

`frame_standoff` with a **cylinder** glyph (Ø×H) now uses the same 4/6/8 Main-Plate perimeter as box posts. Inset math treats Ø as both footprint axes (`hx = Lp/2 − Ø/2`). The glyph stays a cylinder. L×W are never written onto the spec or catalog. A disk (Ø, no axial H) still omits copies.

MY5 desk: plate 161×42 box + Ø6×30 + `count=8` → **eight** copies at corners `(±77.5, ±18, 0)` and edge mids `(±77.5, 0, 0)` / `(0, ±18, 0)`.

## Files changed

- `src/jarvis/workspace/spatial_board.py`
  - New `_standoff_layout_footprint`: box pass-through; cylinder → local `{length_mm: Ø, width_mm: Ø}`; disk/None → `None`.
  - `_frame_standoff_layout_offsets_mm` feeds that footprint into the existing corner/mid helpers (those helpers still only read `length_mm`/`width_mm`).
  - Comments: “box, or cylinder using Ø as both axes”.
- `tests/test_geometry_standoff_cylinder_layout_b1.py` — P1–P7 + catalog bind does not invent standoff L×W
- `tests/test_geometry_sourced_frame_hglrc_my5_b1.py` — `test_t5` now asserts `solidCopies==8` and the §0.1 point set

**Not touched:** `library/` · `ui/` · version · C33 · workspace JSON

## Tests

| ID | Result |
|---|---|
| P1 MY5 Ø6×30 count=8 | pass |
| P2 B7 box count=8 @ 47.5 | pass (new file + existing B7) |
| P3 cylinder count=4 corners | pass |
| P4 Ø50 vs plate width 42 omit | pass |
| P5 disk omit | pass |
| P6 one node | pass |
| P7 offsets ≠ quad-X (W=225) | pass |
| P8 full suite | **3658 passed, 2 skipped** |
| B7 / B4-min / corners | 39 targeted + peers green |

## Honesty

```text
count=8 cylinder ≠ 8 BOM cards
Ø as inset ≠ catalog L×W
8 visor copies ≠ measured hole pattern
```

## Smoke (Engineer)

Reload Taller on **dron de vigilancia doméstico**: eight yellow cylinders on the Top-plate perimeter, one `frame_standoff` card, motors/props X unchanged.
