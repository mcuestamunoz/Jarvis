# Implementation Review — Taller CSS cuboid faces (`B1-geometry-taller-css-cuboid-faces`)

**Date:** 2026-09-25  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_geometry_taller_css_cuboid_faces_b1.md) · [report](implementation_report_geometry_taller_css_cuboid_faces_b1.md)  
**Verdict:** ★ **ACCEPT CLOSED** @ **`v0.5.34`**. Independent review was **PASS WITH NOTES**; Engineer Taller smoke 2026-09-25 closed N1 (thin plates as one prism, Situar ON, edge-on). Tag **`v0.5.34`**.

---

## Summary

The box branch of `Solid3D` still draws **six** CSS faces. They no longer sit flush at `left:0; top:0` when the face is smaller (or taller) than the wrapper. `cuboidFaceLayout(w, d, h)` centers each face, then rotate + `translateZ(half)` on the IC §0.6 normals. Cylinder and disk branches are untouched. CSS file untouched (default `transform-origin: 50% 50%` on faces is the lock). `.sb-world { transform-origin: 0 0 }` untouched.

Honesty:

```text
visor cuboid ≠ CAD ≠ fit ≠ extra parts ≠ 2D card origin
```

Independent: UI vitest **136/136** (4 new). `tsc --noEmit` clean. Python **3691 passed, 2 skipped**. Package **`0.5.34`**. Tag **`v0.5.34`** on ACCEPT. Engineer Taller smoke (screenshot) closed the visual gate.

---

## Locks (IC §0)

| # | Lock | Result |
|---|---|---|
| 1 | Six faces meet on a thin plate | **Pass** (helper math + Engineer Taller smoke 2026-09-25) |
| 2 | No standoff / F460 / cylinder rewrite / `.sb-world` / Three.js | **Pass** |
| 4 | Root cause: off-center face pivot | **Pass** — helper header + T2b |
| 5 | Center, then rotate, then `translateZ(half)`; six nodes; wrapper `w×h` | **Pass** |
| 6 | Normals exact | **Pass** — vitest byte-for-byte |
| 7 | Fixture 80.5×21×1; no `translateX(-w/2)` in transform | **Pass** |
| 8 | Cylinder/disk/projector/DTO frozen | **Pass** — `Solid3D` diff is box-only; `spatial-board.css` empty. Parallel dirty `spatial_board.py` / catalog is **other track**, not this Buy |
| 9 | Pure helper | **Pass** — `cuboidFaces.ts` |
| 10 | **`0.5.34`** after `v0.5.33` | **Pass** |
| 11 | Forbidden claims | **Pass** — landed, no tag |

---

## Cursor checks (independent)

| Check | Result |
|---|---|
| T1 cube 40³, `translateZ(20)`, centered | **Pass** |
| T2 thin plate 80.5×21×1 | **Pass** |
| T2b centering `(w−fw)/2`, `(h−fh)/2` (incl. negative `top`) | **Pass** |
| §0.6 normals | **Pass** |
| T3 `Solid3D` maps helper fields | **Pass in code** (`faces.map` width/height/left/top/transform). **No dedicated Solid3D test** — see N2 |
| T4 cylinder/disk | **Pass** — zero cylinder/disk hunks in `Solid3D.tsx` diff |
| T5 no this-Buy `src/jarvis/` / `library/` | **Pass** |
| T6 `npm test` + typecheck | **Pass — 136/136** |
| T7 pytest | **Pass — 3691 + 2 skipped** |
| T8 `0.5.34` | **Pass** |
| T9 report honesty | **Pass** |
| Tag `v0.5.34` | **Present on ACCEPT** |

---

## Process note (Claude’s flag)

The IC file still said **READY** when Claude implemented. The Engineer paste began **`★ Taller CSS. Implementa ahora.`** That is ★ via chat, same pattern as C35 after we later flipped the artifact. Claude was right to proceed **and** right to flag it. Next Buys: flip the IC status line to **★ Engineer proceed** before paste. Folded here: IC status → LANDED, awaiting smoke + ACCEPT.

---

## Notes

| ID | Status |
|---|---|
| N1 | **Closed** — Engineer Taller smoke 2026-09-25 (`dron de vigilancia doméstico`, Taller 3D, Situar ON, edge-on): plates read as one thin prism, not exploding cards |
| N2 | **Residual, accept** — T3 is wiring in `Solid3D`, not a render test of the six nodes. The map is five style fields; not worth recutting |
| N3 | **Folded** — PRIORIDAD said UI vitest **140**; independent count is **136**. Banner corrected |

---

## Verdict

★ **ACCEPT CLOSED** @ **`v0.5.34`**. N1 closed by Engineer smoke. N2 residual (no Solid3D render test). N3 folded (vitest 136).

Do **not** claim CAD, fit, or extra parts.

Next: cylinder visor IC [`B1-geometry-taller-css-cylinder-faces`](implementation_contract_geometry_taller_css_cylinder_faces_b1.md). Cola: D2 docs · standoff points.
