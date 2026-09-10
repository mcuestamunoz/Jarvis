# Implementation Contract — Visor assembly root (Main Plate at world origin) B1

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** READY — Engineer ★ “vamos a por el siguiente” after situar walk (battery on plate)  
**Parents:**
- [engineer_next_geometry_remaining_pieces.md](engineer_next_geometry_remaining_pieces.md) — Unify product A (box racimo) with product B (visor X)
- Visor X stations **CLOSED** + ACCEPT @ **2562** — stations around **(0,0)**; review **N1** row cursor still walks stationed copies
- Scene3D-from-pose **CLOSED** @ **2462** — single-level; origin = **row slot** of `originKey`
- Declared battery + Main Plate envelope **CLOSED** + ACCEPT @ **2583** — live `frame_plate` is a **box** 100×100×4
- Live 5min: FC `0/0/8` vs plate; battery `0/0/13` vs plate; ESC `5/0/0` vs FC; 4+4 stations at absolute (0,0)+offsets → **visual gap** X vs stack

**Type:** Visor-only layout change in `layoutSolidsFromPose` (+ tests). Prefer **no** Python DTO change.  
**Not** multi-level pose chains (ESC still single-hop vs FC’s **slot**, not FC’s posed point — out). **Not** inventing plate L×W. **Not** moving stations onto `DeclaredBoxPose`. **Not** Conversation Engine.

**Baseline:** package **`0.3.8`** · suite **2583**

**Output:** `.jes/artifacts/implementation_report_geometry_visor_assembly_root_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B1-assembly-root** — Main Plate box is the Scene3D world origin |
| 2 | Root key | Exactly `frame_plate` **and** that node’s `geometry.shape === "box"`. Missing / not a box → **today’s layout** (no silent pick of `frame_plate_2`) |
| 3 | Root placement | Centered at declared mm **(0,0,0)** — same axis remap and wrapper centering as an `offsetMm` of zeros. **Not** a row slot |
| 4 | Stations | Unchanged DTO / formula. Still around (0,0). With root at (0,0), X **shares** the plate center |
| 5 | Pose vs root | When `declaredBoxPose.originKey === "frame_plate"` and root is active, child offset is from the root’s **laid-out center at world 0**, not from `frame_plate`’s old row slot |
| 6 | Pose vs non-root | Unchanged single-level vs that origin’s **row slot** (ESC→FC stays as today — no chain) |
| 7 | Row walk (N1 tidy) | Items with `offsetMm` **do not** advance `layoutSolidsRow` cursor. Root `frame_plate` also **does not** take a row slot when active |
| 8 | No root | Behavior byte-identical to pre-Buy (stations at 0; poses vs row slots; N1 cursor still walks stations if you somehow have stations without a plate box — keep that path tested) |
| 9 | Python / writer | **No** change to `solidCopyOffsetsMm`, pose writer, or envelope writer |
| 10 | Version | **No** bump |

**Product sentence:**

```text
Si la Main Plate es una caja, el visor la pone en el origen y la X de
motores/hélices queda alrededor de esa placa. FC/batería declarados
respecto a frame_plate se apoyan ahí. Sin caja de placa, el layout
sigue como hoy.
```

**Not:**

```text
cadena ESC→FC→placa · inventar L×W · 230 como caja · pose en discos ·
elegir frame_plate_2 como root en silencio
```

---

## 1. You (Claude)

- Do **not** change `spatial_board.py` offsets / wheelbase math unless a test proves a DTO hole (you must not need it).
- Do **not** implement multi-hop pose composition.
- Do **not** treat `frame` root or `frame_plate_2` as assembly root this Buy.
- Do **not** invent plate dims. Do **not** mutate `workspace/`.
- Do **not** bump version.
- Full pytest green. `cd ui/spatial-board && npm test && npm run typecheck`.
- Write the implementation report when done.
- **STOP** if the only fix is stitching wheelbase into the plate box.

---

## 2. Intent

```text
expandSolidCopies (unchanged DTO)
        ↓
layoutSolidsFromPose:
  if frame_plate has box geometry:
    place frame_plate at world (0,0,0) centered
    skip frame_plate + offsetMm items from row cursor
    pose with originKey==frame_plate → offset from that world center
    offsetMm stations → still around (0,0)  → X around plate
  else:
    today's layout
```

---

## 3. Locked behavior

### 3.1 Detect root

In `layoutSolidsFromPose` (or a tiny helper in the same file):

```text
root = item with id === "frame_plate" AND geometry.shape === "box"
```

Copies use `layoutId` like `motors#0` — root id is exactly `frame_plate` (uncopied).

### 3.2 Placement

| Item | With root active | Without root |
|---|---|---|
| `frame_plate` | world 0,0,0 centered | row slot (today) |
| `offsetMm` copies | world 0 + station mm (today) | same |
| pose `originKey=frame_plate` | plate world center + Δmm | plate **row** center + Δmm (today) |
| pose other origin | origin **row** center + Δmm (today) | today |
| other unposed | remaining row (no station footprints) | today (stations still advance cursor) |

Axis remap unchanged: +X→`originX`, +Z→`originY`, +Y→`originZ`.

### 3.3 Row construction

Build the row from items that are **neither** the active root **nor** carrying `offsetMm`. Then assign slots only to those. Active root and stationed copies never receive `slotX` from the row (root uses world 0; stations use `offsetMm`).

### 3.4 Copy / chrome

No new CLI strings. Board cards unchanged. `clusterCenterPx` unchanged (still AABB of laid wrappers).

---

## 4. Tests

### UI — `ui/spatial-board/src/scene3dLayout.test.ts`

| ID | Behavior |
|---|---|
| U10 | `frame_plate` box present + 4 motor copies with quad-X offsets → plate center at world 0 (wrapper-centered); motor#0 FR station ≈ `(+a,+a)` in declared mm around same origin; plate **not** at a large row `originX` caused by 8 disk footprints |
| U11 | Child with `declaredBoxPose` origin `frame_plate`, Δz=8 → child’s layout near plate world center + 8 mm on CSS Y axis (same remap as today) |
| U12 | No `frame_plate` box (only motors with offsets + unposed FC) → layout matches pre-Buy pattern (stations at 0; FC on row; stations still may advance cursor — document actual assertion) |
| U13 | `frame_plate_2` box alone does **not** become root; `frame_plate` without box does **not** activate root |

### Python

No new Python file required if DTO untouched. If you only touch `ui/`, still run full pytest to prove no accidental `src/` drift.

---

## 5. Files (expected)

| Path | Change |
|---|---|
| `ui/spatial-board/src/scene3dLayout.ts` | assembly-root placement + row skip |
| `ui/spatial-board/src/scene3dLayout.test.ts` | U10–U13 |
| `src/` | **empty** unless proven necessary |
| `library/` / `workspace/` | **empty** |
| `.jes/artifacts/implementation_report_geometry_visor_assembly_root_b1.md` | write |

---

## 6. Engineer smoke (after Cursor review)

Live `autonomía-de-5min` (plate box + poses + X already present):

| Step | Expected |
|---|---|
| Reload Board / 3D | Main Plate at center; 4+4 X around it; FC/battery stack on plate |
| Visual gap X-vs-racimo | **Gone or much smaller** (same origin) |
| ESC vs FC | May still look slightly off (single-level slot) — **ACCEPT** this Buy; not a reopen |
| 10min N=3 | Still a **row** of disks; if no plate box, no root behavior |

Record [engineer_smoke_geometry_visor_assembly_root_b1.md](engineer_smoke_geometry_visor_assembly_root_b1.md) after review.

---

## 7. Done when

- [ ] U10–U13 green; `npm test` + `typecheck` green; full pytest green
- [ ] No Python offset formula change; no version bump
- [ ] Report written

---

## Explicitly not this IC

Multi-hop pose · `frame_plate_2` as root · invent L×W · wheelbase→box · disk-origin · sensors/kit · sourced auto-fill dims · Conversation Engine · version bump
