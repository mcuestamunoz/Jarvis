# Implementation Contract — Scene3D-from-pose B1 (visor reads `declared_box_pose`)

**Project:** Jarvis  
**Date:** 2026-09-08  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTATION REVIEWED — **PASS WITH NOTES** · **CLOSED** (suite **2462**) + Engineer Board smoke **ACCEPT**  
**Parents:**
- [investigation_review_geometry_scene3d_from_pose_b1.md](investigation_review_geometry_scene3d_from_pose_b1.md) — **PASS WITH NOTES** · Engineer ★ **B1** (`escribe IC` 2026-09-08)
- [investigation_report_geometry_scene3d_from_pose_b1.md](investigation_report_geometry_scene3d_from_pose_b1.md) — lean **B1** DTO+CSS, **not** B1+
- [engineer_lock_geometry_3d_mapping_path.md](engineer_lock_geometry_3d_mapping_path.md) — rung **1** only
- Continuity pose B1 **CLOSED** @ **2456** — writer + IDLE; this Buy **reads** it
- CSS 3D B1 **CLOSED** @ **2429** — solids already exist
- Fit stub — **QUEUED — DO NOT IMPLEMENT**
- Mapping rungs **2–5** — **out** (wheelbase / N-motors / motor height / plate L×W / `"cabe"`)

**Type:** Projector **additive DTO** + CSS 3D **single-level** placement of existing `{box, disk}` solids from `declared_box_pose`.  
**Not** chain composition. **Not** Three.js. **Not** `motor_count` instancing. **Not** new catalog KNOW. **Not** Continuity grammar. **Not** writer cycle-reject. **Not** `"cabe"`.

**Baseline:** package **`0.3.8`** · suite **2456** · HEAD `8930c0b`

**Output:** `.jes/artifacts/implementation_report_geometry_scene3d_from_pose_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B1** | YES — DTO + CSS place, **one hop** |
| 2 | Product sentence | See below |
| 3 | Machine DTO | Additive `declaredBoxPose` on the node. **Never** parse `fields` |
| 4 | Omit rule (N2) | Emit DTO **only** when pose is set **and** origin exists **and** `_geometry_from_spec(origin)` is `box`. Same gate as the writer. Stricter than today’s `_fields` (origin-in-components only) |
| 5 | Pose text | When DTO would omit, omit pose **text fields** too (shared helper). Stale shapeless origin must not keep `origen pose` on the card |
| 6 | Fuel | Existing `geometry` only. Place **whatever has geometry** (live demo today: 3 boxes + 1 disk). Do **not** assume 5 solids. Do **not** seed motor Ø / wheelbase / plate L×W |
| 7 | Single-level (N3) | Child sits relative to origin’s **row slot**, one hop. If the origin is itself posed, **that origin pose is not applied to children**. Do not recurse. Do not crash-walk cycles |
| 8 | Axis remap (N4) | CSS `translate3d(x_px, z_px, y_px)` after `mmToPx`. Declared +X→CSS X, +Y→CSS Z, +Z→CSS Y. **Not** identity `translate3d(x,y,z)` |
| 9 | Center | Wrapper top-left ≠ geometric center. Center-to-center formula below. Disk wrapper height = diameter, **not** `extent.z` (which is 0) |
| 10 | Remainder | `layoutSolidsRow` still assigns a slot to **every** solid (input order, same as today). Unposed visual = that slot. Posed visual **replaces** the slot. Holes in the row are presentation, not “unassembled” |
| 11 | Selection | Same `onSelect` / `selectedId` / `boardSelection.ts` |
| 12 | 3D edges / N-motors / Three.js / writer cycle / Continuity / fit / version | **Out** / QUEUED / **no bump** |

**Honest product sentence:**

```text
El sólido deja la fila y se coloca en mm respecto al centro de una caja
origen, ejes L→+X W→+Y H→+Z declarados. Un hop. Aún no es el Rooster ni “cabe.”
```

---

## 1. You

- Do **not** add Three.js / r3f / WebGL / new npm deps.
- Do **not** parse card `fields` for pose. Do **not** infer from `mountedOn` or card `x/y`.
- Do **not** compose origin chains. Do **not** add writer cycle detection.
- Do **not** instance `motor_count`. Do **not** seed catalog geometry.
- Do **not** change Continuity pose grammar / orchestrator IDLE order.
- Do **not** change `set_component_declared_box_pose` validation (no cycle rider).
- Do **not** draw 3D mount edges.
- Do **not** un-QUEUE fit. Do **not** bump version.
- Do **not** claim ensamblado / cabe / verificado / morro / posición real / colocado as assembly.
- Full pytest (expect **2456 + new Python tests**). `cd ui/spatial-board && npm test && npm run typecheck`.
- Write the implementation report when done.

---

## 2. Intent

```text
ComponentSpec.declared_box_pose (already written)
        ↓
projector: optional declaredBoxPose DTO (omit if origin missing / not box)
        ↓
Scene3D: layoutSolidsRow → slots
        ↓
posed + resolvable origin → center-to-center from origin SLOT (not visual)
unposed / unresolvable → stay on slot
        ↓
Solid3D translate3d(originX, originY, originZ)  // CSS; axes remapped
        ↓
click → existing onSelect(id)
```

---

## 3. Locked behavior

### 3.1 Projector DTO

`src/jarvis/workspace/spatial_board.py`

One helper, used by **both** `_fields` and `_emit` (do not fork the omit rule):

```python
def _declared_box_pose_dto(spec, components) -> dict | None:
    pose = spec.declared_box_pose
    if pose is None:
        return None
    origin = components.get(pose.origin_key)
    if origin is None:
        return None
    geom = _geometry_from_spec(origin)
    if geom is None or geom.get("shape") != "box":
        return None
    dto = {"originKey": pose.origin_key}
    if pose.x_mm is not None:
        dto["xMm"] = pose.x_mm
    if pose.y_mm is not None:
        dto["yMm"] = pose.y_mm
    if pose.z_mm is not None:
        dto["zMm"] = pose.z_mm
    return dto
```

- `_emit`: third optional kwarg (name may vary). If dto is not `None`, set `node["declaredBoxPose"] = dto`. If `None`, **omit the key** (same class as `mountedOn`).
- `_fields`: emit `origen pose` / `ejes pose` / `Δ* mm` **only** when this helper returns a dto. Today’s `origin_key in components` check is **replaced** by this helper.
- Do **not** put millimetres on `mountedOn`. Do **not** change card `x/y`.

`ui/spatial-board/src/types.ts` — additive on `SpatialNode`:

```ts
declaredBoxPose?: {
  originKey: string;
  xMm?: number;
  yMm?: number;
  zMm?: number;
};
```

### 3.2 Wrapper size (test authority — disk ≠ `extent.z`)

`scene3dScale.ts` — **no React**. Keep `SCENE3D` / `mmToPx` / `solidExtentPx` unchanged in meaning.

```ts
export function solidWrapperPx(
  geometry: SpatialGeometry,
  pxPerMm?: number,
): { width: number; height: number };
```

- Box: `{ width: extent.x, height: extent.z }` (CSS width = L, CSS height = H).
- Disk: `{ width: extent.x, height: extent.x }` (wrapper is diameter×diameter; **never** `extent.z`, which is 0).

### 3.3 Placement helper (test authority)

`scene3dLayout.ts` — **no React**. Keep `layoutSolidsRow` as the slot/remainder helper. Fix its docstring (N5): pose exists in `ProjectState`; this function still does **not** read it.

New:

```ts
export type SolidLayout = {
  id: string;
  originX: number;
  originY: number;
  originZ: number;
};

export function layoutSolidsFromPose(
  items: {
    id: string;
    geometry: SpatialGeometry;
    declaredBoxPose?: {
      originKey: string;
      xMm?: number;
      yMm?: number;
      zMm?: number;
    };
  }[],
  gapPx: number,
  pxPerMm?: number,
): SolidLayout[];
```

**Forbidden inputs:** `x`/`y`/`width`/`height` of cards, `mountedOn`, `parent_key`, `fields`.

**Algorithm (locked, do not improvise):**

1. `slots = layoutSolidsRow(items, gapPx, pxPerMm)` — **all** geometry items, same order as today. Every solid keeps a slot even if it will be placed.
2. Index items and slots by `id`.
3. For each item, in **input order**:
   - Let `slot` be its row slot. Default visual: `{ originX: slot.originX, originY: 0, originZ: 0 }`.
   - Resolvable pose iff `declaredBoxPose` is present **and** the `originKey` item exists in this list **and** that origin’s `geometry.shape === "box"`. Otherwise keep the default (remainder).
   - If resolvable: **do not** look at the origin’s `declaredBoxPose`. Use the origin’s **slot** only.

**Center-to-center (px):** omitted `xMm`/`yMm`/`zMm` count as **0** for the visor (sit on that axis at the origin center). This is display of an optional offset, not a new schema default.

```text
originWrap = solidWrapperPx(origin.geometry)
childWrap  = solidWrapperPx(child.geometry)

originCenterX = originSlot.originX + originWrap.width / 2
originCenterY = 0 + originWrap.height / 2
originCenterZ = 0

child.originX = originCenterX + mmToPx(xMm) - childWrap.width / 2
child.originY = originCenterY + mmToPx(zMm) - childWrap.height / 2   // declared +Z → CSS Y
child.originZ = originCenterZ + mmToPx(yMm)                         // declared +Y → CSS Z
```

That is CSS `translate3d(x_px, z_px, y_px)` of the **declared** triple. Cuboid CSS-Z is already symmetric about wrapper 0 (`±d/2` faces) — do **not** subtract half origin/child width_mm from `originZ`.

### 3.4 Solid3D / Scene3D

- `Solid3D`: add `originY` / `originZ` (default `0`). Wrapper transform = `translate3d(${originX}px, ${originY}px, ${originZ}px)`. Do **not** change face construction (the remap is already baked into those faces).
- `Scene3D`: call `layoutSolidsFromPose` with `{ id, geometry, declaredBoxPose }` from nodes that have `geometry`. Pass the three origins into `Solid3D`. Do **not** call `layoutSolidsRow` directly for the visual map (the new helper must call it internally).
- Click / tilt / zoom / pane sibling / no 3D edges — **unchanged**.
- Copy: no new toolbar claim of ensamblado / cabe / pose-as-airframe. Updating the stale Scene3D comment is required (it still says pose is deferred).

### 3.5 Tests (minimum)

**Python** — new `tests/test_geometry_scene3d_from_pose_b1.py` (fixtures with explicit L×W×H / diameter; **do not** use live `motors` as “the disk”):

| ID | Behavior |
|---|---|
| P1 | ESC pose → FC box, `x_mm=5` → node has `declaredBoxPose: { originKey, xMm: 5 }` (no `yMm`/`zMm` keys) |
| P2 | No pose → key omitted |
| P3 | Origin missing from `components` → key omitted **and** no `origen pose` in `fields` |
| P4 | Origin present but shapeless (`frame_plate`) → key omitted **and** no pose text (N2; may require constructing state the writer would reject — allowed in the test fixture) |
| P5 | Origin is a disk → omit DTO + text |
| P6 | `mountedOn` still independent (pose DTO does not require / invent mount) |
| P7 | Existing pose-writer tests still pass (full suite) |

**UI** — extend `scene3dScale.test.ts` / `scene3dLayout.test.ts` (pxPerMm `0.5`, gap `24` unless noted):

| ID | Behavior |
|---|---|
| U1 | Box wrapper `50×21.6×12` → `{ width: 25, height: 6 }` |
| U2 | Disk wrapper Ø127 → `{ width: 63.5, height: 63.5 }` (**not** height 0) |
| U3 | Unposed two solids → `originY=0`, `originZ=0`, `originX` matches today’s `layoutSolidsRow` |
| U4 | ESC `xMm=5` vs FC `44×84×12` at slot 0: `originX = 11 + 2.5 - 12.5 = 1`, `originY = 0`, `originZ = 0` (ESC wrapper `25×6`; FC wrapper `22×6`; `11 = 22/2`) |
| U5 | Same as U4 plus `zMm=4` → `originY = 3 + 2 - 3 = 2` (declared Z → CSS Y; FC wrap height 6 → center 3; ESC wrap height 6 → half 3; `mmToPx(4)=2`) |
| U6 | Same as U4 plus `yMm=10` → `originZ = 5` (declared Y → CSS Z; `mmToPx(10)=5`; **no** half-width subtract) |
| U7 | Disk Ø127, `xMm=5` vs same FC: `originX = 11 + 2.5 - 31.75 = -18.25`, `originY = 3 - 31.75 = -28.75` (wrapper height = diameter) |
| U8 | **No compose:** ESC posed vs FC **and** battery posed vs ESC → battery uses ESC’s **row slot** center, **not** ESC’s visual `originX` from U4 |
| U9 | Missing / non-box origin on the item list → child stays on its row slot |
| U10 | Helper ignores a fake card `x` if a stub includes it |

Keep `layoutSolidsRow` U5/U6 green. Keep `boardSelection.test.ts` green.

Run: `pytest -q`; `cd ui/spatial-board && npm test && npm run typecheck`.

---

## 4. Explicit non-goals

B1+ chain composition · writer cycle-reject · Three.js · `motor_count` copies · seed SunnySky `diameter_mm` / wheelbase / plate L×W / motor 31.7 mm · Continuity grammar · 3D `mountedOn` edges · fit/`cabe` · airframe +X · Conversation Engine · version bump

---

## 5. Files expected to change

| File | Change |
|---|---|
| `src/jarvis/workspace/spatial_board.py` | helper + DTO + `_fields` omit alignment |
| `ui/spatial-board/src/types.ts` | `declaredBoxPose?` |
| `ui/spatial-board/src/scene3dScale.ts` | `solidWrapperPx` |
| `ui/spatial-board/src/scene3dLayout.ts` | `layoutSolidsFromPose`; docstring on row helper |
| `ui/spatial-board/src/scene3dScale.test.ts` | U1–U2 |
| `ui/spatial-board/src/scene3dLayout.test.ts` | U3–U10 |
| `ui/spatial-board/src/Solid3D.tsx` | `originY`/`originZ` + `translate3d` |
| `ui/spatial-board/src/Scene3D.tsx` | call `layoutSolidsFromPose`; fix stale comment |
| `tests/test_geometry_scene3d_from_pose_b1.py` | P1–P6 |
| `.jes/artifacts/implementation_report_geometry_scene3d_from_pose_b1.md` | write |

**Do not change:** `component_writers.py` pose validation · `declared_box_pose_declare_assist.py` · `orchestrator.py` IDLE order · `library/` · `package.json` deps · fit stub · `boardSelection.ts` logic

---

## 6. Done criteria

- [ ] Projector emits `declaredBoxPose` iff helper says so; visor never parses `fields`
- [ ] Posed solid leaves its row slot via the locked formula (axis swap + center correction, px)
- [ ] Unposed solids stay on `layoutSolidsRow` slots; unresolvable pose stays on slot
- [ ] U8: battery vs posed ESC uses ESC **slot**, not ESC visual
- [ ] Disks stay flat; position uses wrapper diameter for CSS Y half-extent
- [ ] Click solid still selects the card; 2D board unchanged in meaning
- [ ] Live census not assumed: no motor Ø seed; 1 spec = 1 solid
- [ ] pytest green (2456 + new); UI tests + typecheck green
- [ ] Implementation report written
- [ ] Engineer Board smoke recommended: `declara el esc a 5 mm en x respecto al fc` → ESC solid moves in +X vs FC; cards still show text; `quita la pose del esc` → row again

---

## 7. Stop conditions

Stop and ask before: composing chains; writer cycle-reject; Three.js; instancing motors; seeding envelopes; parsing `fields`; placing by `mounted_on`; opening fit; bumping version.
