# Implementation Contract — Taller CSS cylinder faces (`B1-geometry-taller-css-cylinder-faces`)

**Project:** Jarvis  
**Date:** 2026-09-25  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke on Taller (thin cylinder / prop hub)

**Status:** ★ ACCEPT CLOSED @ **`v0.5.35`** (Engineer Taller smoke 2026-09-25 — Situar ON; motors as one body on prop disks; N1 closed)  
**Parents:**
- [Taller CSS cuboid faces](implementation_contract_geometry_taller_css_cuboid_faces_b1.md) — six box faces meet on a thin plate @ **`v0.5.34`**  
- [Board CSS 3D solids](implementation_contract_geometry_board_css3d_solids_b1.md) + [Disk axial visor](implementation_contract_geometry_disk_axial_visor_b1.md) — cylinder already ships 2 caps + 16 slats; cap pivot was never locked  
- Cuboid report residual: if a thin-cylinder explode is found, it is a **separate** Buy — this is that Buy  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**

**Type:** **Implementation Contract** — visor **CSS 3D** only. The cylinder already exists (2 disk-caps + 16 slats). On a short axial height (prop hub, thin motor) the **caps explode** because each cap is a `D×D` circle sitting at `top:0; left:0` of a wrapper only `H` tall, then `translateY(±H/2) rotateX(±90)` about **the cap’s** center, not the cylinder’s. Lock the same construction the cuboid Buy just shipped: **center, then rotate, then `translateZ(half)`**. **Not** extra parts. **Not** CAD. **Not** fit. **Not** standoff perimeter points.  
**Package:** bump to **`0.5.35`**; tag **`v0.5.35`** only after Engineer ACCEPT.  
**Not** standoff points (cola) · not F460 · not projector / catalog / DTO · not cuboid recut · not disk rewrite · not `.sb-world` 2D origin · not Three.js · not C30 DFU · not DShot wire · not D2 docs.

**Outputs (required):**
1. Face-layout helper used by `Solid3D` cylinder branch (testable without a screenshot)  
2. Tests: `ui/spatial-board/src/cylinderFaces.test.ts` (or equivalent next to `cuboidFaces.test.ts`)  
3. Report + docs honesty: **visor cylinder ≠ CAD ≠ fit ≠ extra parts ≠ round metal**  
4. `pyproject.toml` → **`0.5.35`**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-geometry-taller-css-cylinder-faces`** — caps + slats meet on a declared Ø×H |
| 2 | One front | Do **not** open standoff points, plate-box catalog, F460, cuboid recut, disk rewrite, 2D `.sb-world`, Three.js, silicon, D2 docs |
| 3 | What this Buy demonstrates | Today a short cylinder (prop hub) looks like green disks flying off the axis. After: the same 2 caps + 16 slats form **one** body. **Human:** “el cilindro ya no explota; sigue siendo pintura, no torno.” |
| 4 | Root cause (locked) | Caps are `D×D` on a wrapper `D×H` and sit at CSS default `top:0; left:0` (`.sb-solid__disk-face`). `transform-origin: 50% 50%` pivots each cap about **its** center. When `H ≪ D` that pivot is far from the cylinder mid-height; `translateY(±H/2)` only moves a tiny axial step, so the cap swings out. **Same class of bug as cuboid top/bottom.** Slats already re-center horizontally (`left: (D − chord)/2`); lock that in the helper, do not invent a new ring. **Not** extra DOM nodes. **Not** `.sb-world { transform-origin: 0 0 }` |
| 5 | Construction | Wrapper stays `width: D; height: H`. **Caps:** centered in the wrapper (`left: (D−D)/2 = 0`, `top: (H−D)/2` — **negative** when `H < D`), `transform-origin: 50% 50%`, then **rotate then `translateZ(H/2)`**: top `rotateX(90deg) translateZ(H/2)` · bottom `rotateX(-90deg) translateZ(H/2)`. **No `translateY` / `translateX` in any cap or slat transform** — centering lives in `left`/`top` only (cuboid T2 rule). **Slats:** N=**16** frozen; chord `2·(D/2)·sin(π/16)`; `left: (D − chord)/2`; `top: 0`; `height: H`; `transform: rotateY(i·22.5deg) translateZ(D/2)`. Still **exactly 2** `.sb-solid__disk-face` + **exactly 16** `.sb-solid__face` slats |
| 6 | Axis (unchanged) | Cylinder wrapper: `extent.x = D` (CSS width), `extent.z = H` (CSS height = axial). Caps lie in the plane ⊥ axis after `rotateX`. Do **not** remap onto cuboid `w/d/h` names inside the helper — arguments are `diameterPx, heightPx` |
| 7 | Thin-cylinder fixture | Declared **Ø 130.72 × H 6.8 mm** (Gemfan 51466-class hub as visor cylinder). After `mmToPx` (`pxPerMm = 0.5`): `D=65.36`, `H=3.4`. Cap `top = (3.4 − 65.36)/2 = −30.98`. Cap `translateZ` is **`H/2 = 1.7`**, never `D/2`. Second fixture (tall post, H > D): **Ø 6 × H 30 mm** (standoff visor size) → px `D=3`, `H=15`; cap `top = (15−3)/2 = 6`. Cube-like: `D=H=40` → cap `top=0`, `translateZ(20)` |
| 8 | Frozen | `cuboidFaces.ts` **byte-unchanged**. Disk branch **byte-unchanged**. Projector / `geometry` DTO / catalog / `spatial_board.py` **byte-unchanged**. N=16 **unchanged**. No 17th slat, no invented Ø or H |
| 9 | Extract | Pure helper e.g. `cylinderSolidLayout(diameterPx, heightPx) → { caps, slats }` so vitest can lock §0.5–§0.7 without Chromium. `Solid3D` cylinder branch consumes it (same pattern as `cuboidFaceLayout`) |
| 10 | Version | **`0.5.34` → `0.5.35`**. Parent tag `v0.5.34` exists |
| 11 | Forbidden | “CAD” · “round stock” · “fit VERIFIED” · “extra parts” · “we fixed 2D cards” · thickening the hub in the DTO · moving standoff copies · recutting the box helper |

**Product sentence:**

```text
Dos tapas y dieciséis listones, un cuerpo; en un buje de 6,8 mm se tocan.
Sigue siendo el visor, no el aluminio.
```

**Defaults locked by Cursor:**
- Center caps, then rotate, then `translateZ(H/2)` — **not** keep `translateY(±H/2)` after centering (that would double-move)  
- Helper + vitest; no screenshot gate  
- Cylinder only this Buy (disk and box frozen)  

---

## 1. Package layout (normative intent)

```text
ui/spatial-board/src/cylinderFaces.ts      # NEW helper (or equivalent name)
ui/spatial-board/src/cylinderFaces.test.ts # NEW
ui/spatial-board/src/Solid3D.tsx           # cylinder branch consumes the helper
ui/spatial-board/src/cuboidFaces.ts        # FROZEN
ui/spatial-board/src/spatial-board.css     # face transform-origin only if required
```

Do **not** add Python under `src/jarvis/` or `library/` unless a test cannot call the helper (then **STOP**).

---

## 2. Non-goals

Standoff perimeter points, plate-box catalog seed, F460, cuboid recut, disk rewrite, 2D `.sb-world` origin, Three.js, fit/CAD, silicon, D2 docs maps.

---

## 3. Integration rules

| Existing | This Buy |
|---|---|
| `Solid3D` cylinder | **Same 2 caps + 16 slats**, new layout math |
| `Solid3D` box / `cuboidFaces.ts` | **Byte-unchanged** |
| Disk | **Byte-unchanged** |
| `SCENE3D.pxPerMm` | **Unchanged** (0.5) |
| Projector / DTO | **Unchanged** |
| Grafo cards | **Unchanged** — Taller ≠ Grafo |
| Standoff layout copies | **Unchanged** — this is visor faces, not XY points |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | Helper on `D=H=40`: two caps; each `left=0`, `top=0`; each `translateZ` is `20`; 16 slats; slat `left = (40 − chord)/2` with `chord = 2·20·sin(π/16)` |
| T2 | Helper on thin hub `D=65.36, H=3.4`: both caps `width=height=65.36`, `top=−30.98`, `translateZ(1.7)`; **no** `translateX` / `translateY` in any transform string |
| T2b | Tall post `D=3, H=15`: cap `top=6`; `translateZ(7.5)` |
| T2c | Centering formula `top: (H−D)/2` (including negative) stated and asserted |
| T3 | `Solid3D` cylinder branch maps helper fields onto the 2 cap nodes and 16 slat nodes (width/height/left/top/transform) |
| T4 | Box helper `cuboidFaces.ts` + disk branch in `Solid3D.tsx` git-unchanged (or equivalent freeze) |
| T5 | No `src/jarvis/` / `library/` edits |
| T6 | `cd ui/spatial-board && npm test && npm run typecheck` green |
| T7 | Full pytest green (no new Python tests required) |
| T8 | `pyproject` **`0.5.35`** |
| T9 | Report: visor cylinder ≠ CAD ≠ fit ≠ extra parts ≠ round metal |

---

## 5. Honesty / forbidden

```text
visor cylinder ≠ CAD ≠ fit ≠ extra parts ≠ round metal ≠ standoff hole pattern
```

**Exists:** 2 CSS caps + 16 CSS slats that meet on a declared Ø×H.  
**Impossible:** a turned standoff; a prop hub from the mill; a fit verdict; a 17th face.

---

## 6. Docs

PRIORIDAD · PLATFORM / ARCHITECTURE visor note if they still describe exploding cylinders · README “What v0.5.35 includes”

---

## 7. Acceptance

**PASS when:** T1–T9 · 2 caps + 16 slats · thin-hub fixture · box+disk frozen · projector frozen.  
**FAIL if:** extra faces · DTO Ø/H invented · `.sb-world` retargeted · standoff points moved · Three.js · cuboid recut · keep `translateY(±H/2)` on centered caps.

---

## 8. Handoff

```text
Engineer → ACCEPT Taller cuboid + tag v0.5.34  (done)
Engineer → ★ this IC
Claude   → helper + Solid3D cylinder branch + vitest + 0.5.35
Cursor   → independent review
Engineer → Taller smoke (thin hub / motors) + ACCEPT + tag visor v0.5.35  (done 2026-09-25)
Cola     → D2 docs (retargeted 0.5.36) · then standoff points
```

**STOP** if cuboid is not tagged `v0.5.34`.

---

## 9. PRIORIDAD blurb (paste on ★)

```text
Taller CSS: B1-geometry-taller-css-cylinder-faces READY —
caps + 16 slats meet on Ø×H; visor bug, not extra parts. Not CAD.
```

---

## 10. Engineer ★ checklist

1. Buy = **visor cylinder faces only** (no standoff points / no F460 / no DTO / no cuboid recut) OK?  
2. Center + rotate + `translateZ(H/2)` · **no `translateY`** in transforms OK?  
3. Fixture Ø 130.72 × 6.8 / px `65.36×3.4` plus tall post Ø6×30 OK?  
4. Version **`0.5.35`** after `v0.5.34` OK?  
