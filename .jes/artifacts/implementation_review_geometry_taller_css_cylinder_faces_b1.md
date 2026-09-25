# Implementation Review — Taller CSS cylinder faces (`B1-geometry-taller-css-cylinder-faces`)

**Date:** 2026-09-25  
**Reviewer:** Cursor (independent — not implementer)  
**Against:** [IC](implementation_contract_geometry_taller_css_cylinder_faces_b1.md) · [report](implementation_report_geometry_taller_css_cylinder_faces_b1.md)  
**Verdict:** ★ **ACCEPT CLOSED** @ **`v0.5.35`**. Independent review was **PASS WITH NOTES**; Engineer Taller smoke 2026-09-25 closed N1 (motors as one cylinder body on prop disks, Situar ON). Tag **`v0.5.35`**.

---

## Summary

The cylinder branch of `Solid3D` still draws **2** `.sb-solid__disk-face` caps and **16** `.sb-solid__face` slats. Caps no longer sit flush at `left:0; top:0` when `H ≠ D`. `cylinderSolidLayout(diameterPx, heightPx)` centers each cap (`top: (H−D)/2`, negative when `H < D`), then rotate + `translateZ(H/2)` on the IC §0.5 normals. Slats keep the pre-existing chord / `left: (D−chord)/2` math, moved into the helper. Box helper and disk branch are untouched. CSS file untouched (default `transform-origin: 50% 50%` on faces/caps is the lock). `.sb-world { transform-origin: 0 0 }` untouched.

Honesty:

```text
visor cylinder ≠ CAD ≠ fit ≠ extra parts ≠ round metal ≠ standoff hole pattern
```

Independent: UI vitest **142/142** (6 new). `tsc --noEmit` clean. Python **3691 passed, 2 skipped**. Package **`0.5.35`**. Tag **`v0.5.35`** on ACCEPT. Engineer Taller smoke (screenshot) closed the visual gate.

---

## Locks (IC §0)

| # | Lock | Result |
|---|---|---|
| 1 | Caps + slats meet on declared Ø×H | **Pass** (helper math + Engineer Taller smoke 2026-09-25) |
| 2 | No standoff points / F460 / cuboid recut / disk / `.sb-world` / Three.js / D2 | **Pass** |
| 4 | Root cause: off-center cap pivot | **Pass** — helper header + T2c |
| 5 | Center, then rotate, then `translateZ(H/2)`; 2 caps + 16 slats; wrapper `D×H`; no `translateY`/`translateX` in transforms | **Pass** |
| 6 | Args `diameterPx, heightPx` (not cuboid `w/d/h`) | **Pass** |
| 7 | Fixtures 65.36×3.4 and 3×15; cube-like 40² | **Pass** |
| 8 | `cuboidFaces.ts` + disk + projector frozen; N=16 | **Pass** — cuboid hash matches HEAD; disk return block not in `Solid3D` diff; CSS empty. Parallel dirty `spatial_board.py` / catalog is **other track**, not this Buy |
| 9 | Pure helper | **Pass** — `cylinderFaces.ts` |
| 10 | **`0.5.35`** after `v0.5.34` | **Pass** |
| 11 | Forbidden claims | **Pass** — landed, no tag |

---

## Cursor checks (independent)

| Check | Result |
|---|---|
| T1 cube-like `D=H=40`, `translateZ(20)`, cap `top=0`, 16 slats chord/left | **Pass** |
| T2 thin hub 65.36×3.4, `top≈−30.98`, `translateZ(1.7)`, no `translateX`/`translateY` | **Pass** |
| T2b tall post 3×15, `top=6`, `translateZ(7.5)` | **Pass** |
| T2c `(H−D)/2` including negative | **Pass** |
| §0.5 normals byte-for-byte | **Pass** — `rotateX(±90deg) translateZ(H/2)` |
| T3 `Solid3D` maps helper fields | **Pass in code** (`caps.map` / `slats.map` width/height/left/top/transform). **No dedicated Solid3D test** — see N2 |
| T4 cuboidFaces + disk | **Pass** — `cuboidFaces.ts` hash identical to HEAD; disk branch hunk-free |
| T5 no this-Buy `src/jarvis/` / `library/` | **Pass** |
| T6 `npm test` + typecheck | **Pass — 142/142** |
| T7 pytest | **Pass — 3691 + 2 skipped** |
| T8 `0.5.35` | **Pass** |
| T9 report honesty | **Pass** |
| Tag `v0.5.35` | **Present on ACCEPT** |

---

## Process note (Claude’s flag)

The IC file still said **READY** when Claude implemented. The Engineer paste began **`★ Taller CSS cilindros. Implementa ahora.`** That is ★ via chat. Claude was right to proceed **and** right to hold D2 earlier when the checkout had no `v0.5.34`. Folded here: IC status → LANDED, awaiting smoke + ACCEPT.

---

## Notes

| ID | Status |
|---|---|
| N1 | **Closed** — Engineer Taller smoke 2026-09-25 (`dron de vigilancia doméstico`, Taller 3D, Situar ON): motors read as one cylinder body on prop disks, not exploding caps |
| N2 | **Residual, accept** — T3 is wiring in `Solid3D`, not a render test of the 18 nodes. Same fold as cuboid N2; not worth recutting |

---

## Verdict

★ **ACCEPT CLOSED** @ **`v0.5.35`**. N1 closed by Engineer smoke. N2 residual (no Solid3D render test).

Do **not** claim CAD, round stock, fit, or extra parts.

Next: D2 docs [`B1-docs-truth-sync-after-c35`](implementation_contract_docs_truth_sync_after_c35_b1.md) (package **`0.5.36`**). Cola: standoff points.
