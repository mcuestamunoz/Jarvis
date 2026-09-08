# Implementation Review — Board CSS 3D solids B1

**Date:** 2026-09-08  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_geometry_board_css3d_solids_b1.md](implementation_contract_geometry_board_css3d_solids_b1.md)  
**Report:** [implementation_report_geometry_board_css3d_solids_b1.md](implementation_report_geometry_board_css3d_solids_b1.md)  
**Buy:** ★ B1 — CSS 3D / DOM-only; no Three.js; no pose

## Verdict

**PASS WITH NOTES**

IC locks held. Visor-only. **CLOSED** — Engineer Board smoke ACCEPT.

---

## Checklist

| Criterion | Result |
|---|---|
| CSS 3D only; `package.json` deps unchanged | **Pass** — diff empty |
| Fuel = `node.geometry` only | **Pass** — `Scene3D` filters |
| Disk flat, `z === 0`, one face | **Pass** — U4 + `Solid3D` |
| Uncapped `mm * 0.5`; no `GLYPH.maxPx` | **Pass** — U1/U2; `GLYPH` untouched |
| N1 row layout; no card `x/y` / `mountedOn` | **Pass** — U5 decoy `x: 9999` |
| N2 own tilt/zoom; not `useCanvasTransform` | **Pass** |
| N3 2D cards/glyphs/edges remain | **Pass** — sibling `.sb-scene3d` |
| Same `onSelect` / `selectedId` | **Pass** |
| No 3D edges / pose / cabe / Python | **Pass** |
| U1–U6 + prior UI tests | **Pass** — Cursor **22** |
| pytest | **Pass** — Cursor **2429** |
| Version | **None** — `0.3.8` |

---

## Independent verification

| Check | Result |
|---|---|
| `pytest -q` | **2429 passed** |
| `npm test` / `typecheck` | **22** / clean |
| `git diff -- src/ tests/ library/ package.json` | **empty** (spatial-board `package.json`) |
| Scene sibling of `.sb-viewport` | **Confirmed** `InfiniteCanvas.tsx:214` |
| Disk one `rotateX(90deg)` face | **Confirmed** |
| Box six faces | **Confirmed** |
| Forbidden UI copy (cabe/ensamblado) | **Pass** — “pose” only in comments denying it |

---

## Notes

### N1 — Selected border-width 2px

IC asked color-only / no layout shift. `.sb-solid--selected` also sets `border-width: 2px` (was 1px). Tiny. Not a FAIL. Prefer `outline` later if it bothers smoke.

### N2 — Pane height 260px

Fixed strip under the 2D viewport can squeeze a short window. Presentational; retune without touching scale/layout helpers.

### N3 — Tilt constants

`55° / −30°` and drag `0.5 °/px` are view chrome, as the report said.

### N4 — Horizon

This is **not** pose, **not** `"cabe"`, **not** “ensamblado”. Solids sit in a presentation row.

---

## Phase

Implementation **CLOSED**. Engineer smoke ACCEPT ([smoke](engineer_smoke_geometry_board_css3d_solids_b1.md)). Next = not an IC — pose still B0; fit QUEUED. Package `0.3.8` · suite **2429**.
