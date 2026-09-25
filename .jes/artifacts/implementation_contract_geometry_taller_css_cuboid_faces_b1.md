# Implementation Contract — Taller CSS cuboid faces (`B1-geometry-taller-css-cuboid-faces`)

**Project:** Jarvis  
**Date:** 2026-09-25  
**Author:** JES / Cursor (Engineer Interface) — **IC only**  
**Implementer:** **Claude Code** (Cursor does not implement) — after Engineer ★  
**Reviewer:** Cursor against this IC · Engineer smoke on Taller (thin plate)

**Status:** **READY** — awaiting Engineer ★ (parent: C35 ★ ACCEPT CLOSED @ **`v0.5.33`**)  
**Parents:**
- [C35](implementation_contract_fase_c_step_failsafe_hold_ticks_b1.md) — denser `step` tests @ **`v0.5.33`**  
- [situation after C33](engineer_note_fase_c_situation_after_c33_2026_09_25.md) §3 — front **3** of the four no-pin attacks  
- [Board CSS 3D solids](implementation_contract_geometry_board_css3d_solids_b1.md) — six-face cuboid shipped; face pivot was never locked  
- [scene3d-from-pose investigation](investigation_report_geometry_scene3d_from_pose_b1.md) — wrapper top-left ≠ cuboid center  
- MY5 caliper bag — [engineer_bag_my5_caliper_2026_09_24.md](engineer_bag_my5_caliper_2026_09_24.md) — Top plate **161×42×2** (the thin case)  
- [Process lock after C6](engineer_note_fase_c_process_lock_after_c6_2026_09_20.md) — **one front**

**Type:** **Implementation Contract** — visor **CSS 3D** only. The six faces of a `box` already exist; on a thin plate they **explode** because each face rotates about **its own** center (`top:0; left:0` + default `transform-origin: 50% 50%` of the *face*), not about the cuboid center. Lock the construction so faces meet at the declared L×W×H edges. **Not** extra parts. **Not** CAD. **Not** fit.  
**Package:** bump to **`0.5.34`**; tag **`v0.5.34`** only after Engineer ACCEPT.  
**Not** standoff points (cola 4) · not F460 · not projector / catalog / DTO · not cylinder rewrite · not `.sb-world` 2D `transform-origin: 0 0` · not Three.js · not C30 DFU · not DShot wire.

**Outputs (required):**
1. Face-layout helper used by `Solid3D` box branch (testable without a screenshot)  
2. Tests: `ui/spatial-board/src/cuboidFaces.test.ts` (or extend an existing UI test file)  
3. Report + docs honesty: **visor cuboid ≠ CAD ≠ fit ≠ extra parts**  
4. `pyproject.toml` → **`0.5.34`**

---

## 0. Engineer Buy (locked when ★)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **`B1-geometry-taller-css-cuboid-faces`** — six faces meet on a thin plate |
| 2 | One front | Do **not** open standoff points, plate-box catalog, F460, cylinder rewrite, 2D `.sb-world`, Three.js, silicon |
| 3 | What this Buy demonstrates | Today a 2 mm plate looks like six cards flying apart. After: the same six faces form **one** thin box. **Human:** “la placa ya no explota; sigue siendo pintura, no CAD.” |
| 4 | Root cause (locked) | Faces sit at `top:0; left:0` of a `w×h` wrapper and rotate about **the face’s** center. Top/bottom are `w×d` on a wrapper only `h` tall — when `h` is tiny (plate), that pivot is far from the cuboid center and the face swings out. **Not** extra DOM nodes. **Not** `.sb-world { transform-origin: 0 0 }` (2D cards) |
| 5 | Construction | Each of the six faces is **centered** in the cuboid wrapper (`left: (w−fw)/2`, `top: (h−fh)/2`), `transform-origin: 50% 50%`, then **rotate then `translateZ(half-extent along that face’s normal)`**. Wrapper size stays `width: w; height: h`. Still **exactly six** `.sb-solid__face` nodes. Axis remap unchanged: `w=+X/L`, `d=+Y/W`, `h=+Z/H` |
| 6 | Normals (locked) | front `translateZ(d/2)` · back `rotateY(180deg) translateZ(d/2)` · left `rotateY(-90deg) translateZ(w/2)` · right `rotateY(90deg) translateZ(w/2)` · top `rotateX(90deg) translateZ(h/2)` · bottom `rotateX(-90deg) translateZ(h/2)` |
| 7 | Thin-plate fixture | Declared **161×42×2** (MY5 Top). After `mmToPx` (`pxPerMm = 0.5`): `w=80.5`, `d=21`, `h=1`. Top/bottom `translateZ` is **`h/2`**, not `d/2`. Faces must not use `translateX(-w/2) rotateY(...)` with `left:0` (that is the bug) |
| 8 | Frozen | Cylinder + disk branches **byte-unchanged**. Projector / `geometry` DTO / catalog / `spatial_board.py` **byte-unchanged**. No 7th face, no invented thickness |
| 9 | Extract | Pure helper e.g. `cuboidFaceLayout(w, d, h) → 6 × {name, width, height, left, top, transform}` so vitest can lock §0.5–§0.6 without Chromium |
| 10 | Version | **`0.5.33` → `0.5.34`**. Parent tag `v0.5.33` exists |
| 11 | Forbidden | “CAD” · “fit VERIFIED” · “extra parts” · “we fixed 2D cards” · thickening the plate in the DTO |

**Product sentence:**

```text
Seis caras, un prisma; en una placa de 2 mm se tocan los cantos.
Sigue siendo el visor, no el aluminio.
```

**Defaults locked by Cursor:**
- Center faces, then rotate, then `translateZ(half)`  
- Helper + vitest; no screenshot gate  
- Box only this Buy  

---

## 1. Package layout (normative intent)

```text
ui/spatial-board/src/cuboidFaces.ts      # NEW helper (or equivalent name)
ui/spatial-board/src/cuboidFaces.test.ts # NEW
ui/spatial-board/src/Solid3D.tsx         # box branch consumes the helper
ui/spatial-board/src/spatial-board.css   # face transform-origin only if required
```

Do **not** add Python under `src/jarvis/` or `library/` unless a test cannot call the helper (then **STOP**).

---

## 2. Non-goals

Standoff perimeter points, plate-box catalog seed, F460, cylinder/disk rewrite, 2D `.sb-world` origin, Three.js, fit/CAD, silicon.

---

## 3. Integration rules

| Existing | This Buy |
|---|---|
| `Solid3D` box | **Same six faces**, new layout math |
| Cylinder / disk | **Byte-unchanged** |
| `SCENE3D.pxPerMm` | **Unchanged** (0.5) |
| Projector / DTO | **Unchanged** |
| Grafo cards | **Unchanged** — Taller ≠ Grafo |

---

## 4. Tests (minimum)

| ID | Check |
|---|---|
| T1 | Helper on cube `w=d=h=40`: six faces; each `left`/`top` centers the face; each `translateZ` is `20` |
| T2 | Helper on thin plate `w=80.5, d=21, h=1`: top/bottom `fw=w`, `fh=d`, `translateZ(0.5)`; left/right `fw=d`, `fh=h`, `translateZ(40.25)`; **no** `translateX(-w/2)` / `translateY(-h/2)` in the transform string |
| T3 | `Solid3D` box branch maps helper fields onto the six face nodes (width/height/left/top/transform) |
| T4 | Cylinder + disk source in `Solid3D.tsx` git-unchanged (or equivalent freeze) |
| T5 | No `src/jarvis/` / `library/` edits |
| T6 | `cd ui/spatial-board && npm test && npm run typecheck` green |
| T7 | Full pytest green (no new Python tests required) |
| T8 | `pyproject` **`0.5.34`** |
| T9 | Report: visor cuboid ≠ CAD ≠ fit ≠ extra parts |

---

## 5. Honesty / forbidden

```text
visor cuboid ≠ CAD ≠ fit ≠ extra parts ≠ 2D card origin
```

**Exists:** six CSS faces that meet on a thin declared box.  
**Impossible:** a machined plate; a fit verdict; a seventh part.

---

## 6. Docs

PRIORIDAD · PLATFORM / ARCHITECTURE visor note if they still describe exploding plates · README “What v0.5.34 includes”

---

## 7. Acceptance

**PASS when:** T1–T9 · six faces · thin-plate fixture · cylinder/disk frozen · projector frozen.  
**FAIL if:** extra faces · DTO thickness invented · `.sb-world` retargeted · standoff points · Three.js · cylinder rewrite.

---

## 8. Handoff

```text
Engineer → ACCEPT C35 + tag v0.5.33  (done)
Engineer → ★ this IC
Claude   → helper + Solid3D box branch + vitest + 0.5.34
Cursor   → independent review
Engineer → Taller smoke (thin plate) + ACCEPT + tag v0.5.34
Cola     → 4 standoff points
```

**STOP** if C35 is not tagged `v0.5.33`.

---

## 9. PRIORIDAD blurb (paste on ★)

```text
Taller CSS: B1-geometry-taller-css-cuboid-faces READY —
six faces meet on a thin plate; visor bug, not extra parts. Not CAD.
```

---

## 10. Engineer ★ checklist

1. Buy = **visor faces only** (no standoff / no F460 / no DTO) OK?  
2. Center + rotate + `translateZ(half)` OK?  
3. Fixture 161×42×2 / px `80.5×21×1` OK?  
4. Version **`0.5.34`** after C35 tag OK?  
