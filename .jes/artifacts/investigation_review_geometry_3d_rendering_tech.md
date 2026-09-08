# Investigation Review — Board 3D rendering technology (box + disk)

**Date:** 2026-09-08  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_geometry_3d_rendering_tech.md](investigation_contract_geometry_3d_rendering_tech.md)  
**Report:** [investigation_report_geometry_3d_rendering_tech.md](investigation_report_geometry_3d_rendering_tech.md)  
**Parents:** 3D horizon investigation (B1 gated here) · click-inspect B1− CLOSED + smoke ACCEPT

## Verdict

**PASS WITH NOTES**

Lean **B1** (CSS 3D / DOM-only solids; keep no-Three.js **this Buy**) is Buy-eligible. **B1+** WebGL is honestly viable and correctly **not** this Buy. **B0** remains available. Engineer ★ picks B1 / B0 / B1+ / re-scope. **No IC until ★.**

The parent’s CSS-3D worry was “can’t honestly draw a cylinder.” This report’s move is correct: the DTO never had a cylinder. A flat `border-radius: 50%` disk given `rotateX` is the same shape Glyph B1 already draws, in a 3D camera — not an N-gon claimed as sourced height.

---

## Checklist

| Criterion | Result |
|---|---|
| Executive lean + B0 named | **Pass** |
| Visor stack (deps, DOM+SVG, no 3D today) | **Pass** |
| Glyph cap ≠ 3D scale | **Pass** |
| Disk = flat; no ε height; motor cylinder still out | **Pass** — DTO `{shape: disk, diameter_mm}` only |
| Candidates A/B/C/D compared | **Pass** — B dominated by A |
| Three.js: keep vs lift + reversal criterion | **Pass** — keep now; lift if count/orbit pain |
| `onSelect` reuse, no second model | **Pass** |
| 3D as sibling pane, cards stay inspect | **Pass** (sketch) |
| Later rungs; fit stub still QUEUED | **Pass** |
| No code / no new dep / no IC in the report | **Pass** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| `package.json` deps = react + react-dom | **Confirmed** — `git diff` empty on that file |
| No `perspective` / `preserve-3d` / `rotateX` in visor | **Confirmed** grep empty |
| `GLYPH` `{pxPerMm: 0.5, maxPx: 120}` | **Confirmed** `constants.ts:32-35` |
| Disk glyph is `border-radius: 50%` | **Confirmed** `spatial-board.css:215-218` |
| Projector disk payload has no height key | **Confirmed** `spatial_board.py:273-274` + `types.ts:23-25` |
| `onSelect` already on `InfiniteCanvas` / `SpatialCard` | **Confirmed** |
| UI diff this tree = click-inspect only | **Confirmed** — `boardSelection*` + canvas/card/css; no new 3D files |
| Fit stub QUEUED | **Confirmed** |

---

## Notes for ★

### N1 — 3D pane still needs a **presentation** layout (not pose)

Five solids cannot all sit at the scene origin (unreadable) and **must not** take `localStorage` card `x/y` or `mounted_on` as millimetre placement (that is pose / layout-as-truth — locked out).

Any B1 IC must lock an explicit **non-pose** arrangement: e.g. a row/grid of solids, each at its own local origin, same honesty class as today’s card lanes. Edges in 3D, if any, stay relation indicators — or stay 2D-only in this Buy.

### N2 — Camera: two sketches, one IC

§2 points at reusing 2D zoom/pan (`useCanvasTransform`). §6 points at container `rotateX`/`rotateY` drag. Both are visor chrome, not pose — but a real IC picks **one** (or a tight combo) and does not ship two competing cameras.

### N3 — Keep today’s 2D Board

Sketch: additional pane/toggle; cards remain inspect; click solid → same `selectedId`. Do not replace glyphs or collapse fields in this Buy unless you ★ that separately.

### N4 — Horizon ≠ orbit

Free-orbit / Three.js is named as a **reversal criterion**, not a silent extra in B1. ★ B1 means CSS 3D only.

---

## Agreement

| Report lean | Reviewer |
|---|---|
| B1 CSS 3D now | **Agree** if Engineer wants the 3D half of the horizon |
| Keep no-Three.js this Buy | **Agree** |
| B1+ later on count/orbit pain | **Agree** |
| B0 still valid | **Agree** |

---

## Phase

Engineer ★ **B1 CSS 3D** (`procede` 2026-09-08). IC: [implementation_contract_geometry_board_css3d_solids_b1.md](implementation_contract_geometry_board_css3d_solids_b1.md) — **READY FOR CLAUDE**. No Three.js. No pose/`cabe`.
