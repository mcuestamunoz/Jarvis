# Implementation Contract — Board CSS 3D solids B1 (declared box + flat disk)

**Project:** Jarvis  
**Date:** 2026-09-08  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTATION REVIEWED — **PASS WITH NOTES** · **CLOSED** (suite **2429**) + Engineer Board smoke **ACCEPT**  
**Parents:**
- [engineer_lock_geometry_3d_placement_horizon.md](engineer_lock_geometry_3d_placement_horizon.md) — ★ horizon (this Buy = 3D-at-scale rung only)
- [investigation_contract_geometry_3d_rendering_tech.md](investigation_contract_geometry_3d_rendering_tech.md)
- [investigation_report_geometry_3d_rendering_tech.md](investigation_report_geometry_3d_rendering_tech.md) — lean **B1 CSS 3D**
- [investigation_review_geometry_3d_rendering_tech.md](investigation_review_geometry_3d_rendering_tech.md) — **PASS WITH NOTES** (N1 layout, N2 camera, N3 keep 2D, N4 no Three.js)
- Click-inspect B1− **CLOSED** @ **2429** + smoke ACCEPT
- Glyphs B1 CLOSED @ **2344**
- Fit stub [implementation_contract_geometry_assembly_fit_compare.md](implementation_contract_geometry_assembly_fit_compare.md) — **QUEUED — DO NOT IMPLEMENT**
- Pose B1+ — **B0 DEFERRED**

**Type:** Board **visor only** — CSS 3D presentation of existing projector `geometry` `{box, disk}`.  
**Not** Three.js / r3f / WebGL / canvas meshes. **Not** new KNOW / DTO / projector. **Not** pose. **Not** `"cabe"`. **Not** 3D `mounted_on` edges. **Not** motor cylinder / ε disk height.

**Baseline:** package **`0.3.8`** · suite **2429**

**Output:** `.jes/artifacts/implementation_report_geometry_board_css3d_solids_b1.md`

---

## 0. Engineer Buy (locked)

Engineer `procede` B1 2026-09-08 after rendering-tech review PASS WITH NOTES.

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B1** | YES — CSS 3D / DOM-only solids |
| 2 | Honest product sentence | **“Veo el volumen declarado en 3D a escala; click en el sólido selecciona la card de hoy.”** |
| 3 | Technology | CSS `perspective` / `preserve-3d` only. **No** new npm dependency. `package.json` deps stay `react` + `react-dom` |
| 4 | Fuel | Existing `node.geometry` only. No geometry → no solid (card unchanged) |
| 5 | Disk | **Flat circle** (`border-radius: 50%`, one face). **No** `translateZ` thickness, **no** 6th/7th face, **no** `stator_height_mm` |
| 6 | Scale | New **uncapped** linear `mm * pxPerMm`. Do **not** reuse `GLYPH.maxPx` / `Math.min(..., 120)` |
| 7 | N1 layout | **Row of cells** in the 3D pane. Each solid at **local origin**. Gap in **CSS px**, not assembly mm. **Forbidden inputs:** `node.x/y/width/height`, `mountedOn`, `parent_key`, `localStorage` |
| 8 | N2 camera | **One** 3D camera: default tilt + drag-rotate the **scene** + wheel-zoom the **scene**. Do **not** drive 3D from `useCanvasTransform` (that stays 2D cards) |
| 9 | N3 Board | 2D cards + glyphs + SVG edges **remain**. 3D is an extra pane (toggle). Fields stay always visible |
| 10 | Selection | Same `onSelect` / `selectedId` / `boardSelection.ts`. Click solid → highlight that card **and** that solid |
| 11 | 3D edges | **Out** this Buy (2D edges stay) |
| 12 | Pose / cabe / version | **Out.** No bump |

---

## 1. You

- Do **not** add `three`, `@react-three/fiber`, cannon, or any WebGL wrapper.
- Do **not** change Python, `_geometry_from_spec`, `geometry` DTO, catalog, Continuity, or `GLYPH` (2D glyphs stay capped).
- Do **not** invent disk height or motor cylinder.
- Do **not** place solids using card layout or `mounted_on`.
- Do **not** draw 3D mount edges.
- Do **not** claim `"cabe"` / ensamblado / pose in copy or class names.
- Do **not** bump package version.
- Full pytest **2429** (add **no** Python tests).
- `cd ui/spatial-board && npm test && npm run typecheck`.
- Write the implementation report when done.

---

## 2. Intent

```text
node.geometry (projector, unchanged)
        ↓
filter nodes that have geometry
        ↓
CSS 3D pane: row of solids at linear mm→px (uncapped)
        ↓
click solid → existing onSelect(id) → card + solid highlight
```

2D world (`.sb-world`) unchanged in meaning: cards, glyphs, edges, drag = layout.

---

## 3. Locked behavior

### 3.1 Scale helper (test authority)

New `ui/spatial-board/src/scene3dScale.ts` — **no React**.

```ts
export const SCENE3D = { pxPerMm: 0.5 } as const; // linear; NO maxPx

export function mmToPx(mm: number, pxPerMm?: number): number;

export type SolidExtentPx = { x: number; y: number; z: number };

export function solidExtentPx(
  geometry: SpatialGeometry,
  pxPerMm?: number,
): SolidExtentPx;
```

Rules:

- `mmToPx(mm) = mm * (pxPerMm ?? SCENE3D.pxPerMm)`. **Never** `Math.min` with 120.
- Box: `{ x: length_mm, y: width_mm, z: height_mm }` each through `mmToPx` (display axes: length→X, width→Y, height→Z — visor convention, not a CAD frame).
- Disk: `{ x: diameter, y: diameter, z: 0 }` through `mmToPx`. `z === 0` is load-bearing.

Do **not** import `GLYPH` here.

### 3.2 Layout helper (test authority — N1)

New `ui/spatial-board/src/scene3dLayout.ts` — **no React**. Must **not** accept card `x/y`.

```ts
export function layoutSolidsRow(
  items: { id: string; geometry: SpatialGeometry }[],
  gapPx: number,
  pxPerMm?: number,
): { id: string; originX: number }[];
```

Rules:

- Preserve **input order** (caller passes projector `nodes` order, geometry-only).
- `originX` of item 0 = 0. Each next origin = previous origin + previous solid’s **max(x,y)** extent (footprint in the XZ ground plane is fine: use `max(extent.x, extent.y)` for disk/box footprint) + `gapPx`.
- `gapPx` is CSS pixels (constant, e.g. `24`). Not millimetres of assembly.
- Return value has **no** `originY` from `mountedOn` / cards.

`InfiniteCanvas` / scene component **must** call this helper; no ad-hoc `node.x`.

### 3.3 Solid (DOM)

New `Solid3D.tsx` (name may vary; one component):

- Props: `id`, `geometry`, `selected`, `onSelect(id)`, optional `originX`.
- `onMouseDown` on the solid → `onSelect(id)` then `stopPropagation` so it does **not** start scene-rotate.
- Box: one `preserve-3d` wrapper, **six** faces sized from `solidExtentPx`. No seventh slab.
- Disk: **one** circular face, `border-radius: 50%`, size `diameter`×`diameter` px, **no** extrusion. A `rotateX` on that face to lie in the scene’s ground plane is allowed (orientation of the **primitive**, not pose of the drone).
- `data-node-id={id}`. When `selected`, class `sb-solid--selected` + `aria-current="true"` (omit when not).
- No text claiming ensamblado / cabe / pose.

### 3.4 Scene pane (N2 + N3)

New scene wrapper used from `InfiniteCanvas`:

- **Sibling** of `.sb-viewport`, not inside `.sb-world`. Mixing 2D absolute cards with `preserve-3d` on the same nodes is **forbidden**.
- Toolbar button toggles visibility (`useState`, session only — do **not** persist). Default: **shown** if any node has `geometry`, else hidden.
- Default scene tilt: fixed `rotateX` + `rotateY` so boxes read as 3D on first paint (pick one pair and keep it, e.g. ~55° / −30°).
- **Drag** on empty scene background (not a solid, not the 2D viewport): add to those two angles. This is **view** chrome.
- **Wheel** over the 3D pane: scale the scene container (clamp to a small zoom range). Independent of 2D `transform`.
- Do **not** call `zoomToPoint` / `setTransform` from 3D events.
- Click empty 3D background (no drag): **do not** clear selection (rotate/zoom chrome). 2D empty-viewport clear **unchanged**. Escape still clears (existing).

Copy: toolbar hint may append `· 3D: arrastrar vista` (or equivalent). **Forbidden** words: pose, ensamblado, cabe, verificado, colocado.

### 3.5 Selection wiring

Pass the **same** `onSelect` already passed to `SpatialCard`. `selected={id === selectedId}`. No second `selectedId`.

### 3.6 Non-goals (explicit)

Three.js/r3f · WebGL · 3D mount edges · pose schema · `"cabe"` · projector/Python · `GLYPH` cap change · collapsing card fields · replacing 2D glyphs · using card `x/y` as mm · ε disk height · motor cylinder · version bump · orbit-controls library

---

## 4. Tests (required)

**Python:** none. Suite stays **2429**.

**UI** — `ui/spatial-board/src/scene3dScale.test.ts` + `scene3dLayout.test.ts` (or one file):

| # | Case |
|---|---|
| U1 | `mmToPx(127)` at 0.5 → `63.5` (not capped to 120) |
| U2 | `mmToPx(300)` at 0.5 → `150` (would be 120 under `GLYPH.maxPx` — must **not** match that cap) |
| U3 | box `50×21.6×12` → extent `{x: 25, y: 10.8, z: 6}` at 0.5 |
| U4 | disk `127` → `{x: 63.5, y: 63.5, z: 0}` |
| U5 | two items row: second `originX` = first footprint + gap; **ignore** any fake card `x` if a test stub includes it (helper must not read it) |
| U6 | empty list → `[]` |

Keep existing `boardSelection.test.ts` green.

Run: `pytest -q` (count **2429**); `cd ui/spatial-board && npm test && npm run typecheck`.

---

## 5. Files expected to change

| File | Change |
|---|---|
| `ui/spatial-board/src/scene3dScale.ts` | **new** — `SCENE3D`, `mmToPx`, `solidExtentPx` |
| `ui/spatial-board/src/scene3dLayout.ts` | **new** — `layoutSolidsRow` |
| `ui/spatial-board/src/scene3dScale.test.ts` and/or `scene3dLayout.test.ts` | **new** — U1–U6 |
| `ui/spatial-board/src/Solid3D.tsx` | **new** — box 6 faces / disk 1 face |
| `ui/spatial-board/src/Scene3D.tsx` | **new** — pane, tilt/drag/zoom, map layout → solids |
| `ui/spatial-board/src/InfiniteCanvas.tsx` | mount pane + toolbar toggle; pass `onSelect` / `selectedId` |
| `ui/spatial-board/src/spatial-board.css` | `.sb-scene3d` / `.sb-solid` / selected |
| `ui/spatial-board/src/constants.ts` | **optional** re-export `SCENE3D` only if you prefer it here instead of `scene3dScale.ts` — do **not** change `GLYPH` |
| `.jes/artifacts/implementation_report_geometry_board_css3d_solids_b1.md` | write |

**Do not change:** `src/` · `tests/` · `library/` · `package.json` dependencies · projector · `SpatialGlyph.tsx` scale · `useBoardNodes` keys · `boardSelection.ts` logic (callers only)

---

## 6. Done criteria

- [ ] 5 demo families with `geometry` show CSS 3D solids; 9 without stay cards-only
- [ ] Disks are flat (`z` extent 0); boxes use all three sourced mm
- [ ] 127 mm prop vs 50 mm ESC are proportional (no 120px cap)
- [ ] Solids laid out in a row; not at card `x/y`; not on `mounted_on`
- [ ] Click solid selects the 2D card (same `selectedId`); 2D click still selects
- [ ] 2D board (glyphs, edges, drag, Encajar) unchanged in meaning
- [ ] No new npm deps; no Python tests; suite **2429**; UI tests + typecheck green
- [ ] Implementation report written
- [ ] Engineer Board smoke recommended (toggle 3D, click ESC solid → card outline, rotate view, confirm plates have no solid)

---

## 7. Stop conditions

Stop and ask before: adding a 3D library, 3D edges, pose fields, disk thickness, using layout overlay as millimetre placement, changing the projector, or a version bump.
