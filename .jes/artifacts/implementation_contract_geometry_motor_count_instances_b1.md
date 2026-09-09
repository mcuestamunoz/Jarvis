# Implementation Contract — Motor visor copies from the project’s `motor_count` B1

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTATION REVIEWED — **PASS WITH NOTES** · **CLOSED** (suite **2473**) + Engineer smoke **ACCEPT**  
**Parents:**
- [engineer_lock_geometry_3d_mapping_path.md](engineer_lock_geometry_3d_mapping_path.md) — rung 2 remainder. Engineer 2026-09-09: **not 4 motors by default; take the motors the project has**
- Wheelbase-on-spec B1 **CLOSED** @ **2466** — frame card has cited `wheelbase_mm` 230; this Buy does **not** place copies on that X
- CSS 3D B1 **CLOSED** @ **2429** — 1 `ComponentSpec` = 1 solid until this named Buy
- Scene3D-from-pose B1 **CLOSED** @ **2462**
- Pre-assembly honesty — live demo currently says **3** motors; do not assemble a quadrotor the state does not have
- Fit stub — **QUEUED — DO NOT IMPLEMENT**
- Motor height 31.7 / plate L×W / `"cabe"` — **out**

**Type:** Projector **additive DTO** + Scene3D **visor copies** of the **one** `motors` identity.  
**Not** N `ComponentSpec` / N cards / N BOM nodes. **Not** a default of 4. **Not** quad-X layout. **Not** a new motor Ø. **Not** propeller copies.

**Baseline:** package **`0.3.8`** · suite **2466** · HEAD `3d4e647`

**Output:** `.jes/artifacts/implementation_report_geometry_motor_count_instances_b1.md`

---

## 0. Engineer Buy (locked)

Engineer: `redacta ic para motores` — `no hablamos de 4 motores por defecto. Coge los motores que tiene el proyecto`.

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B1** | YES — visor copies, N from the **motors spec** |
| 2 | Count SoT | `components["motors"].properties["motor_count"].value` only. **Never** default 4. **Never** `configuration=quad_x`. **Never** `current_parameters.motor_count` (may drift; live they both happen to be 3) |
| 3 | Live census (do not assume) | Demo `autonomía-de-10min`: SKU `sunnysky_r2305_2500`, `motor_count` **3** `source=calculated`, **no** `diameter_mm` → **no** `geometry` today. Frame `wheelbase_mm` 230 + `configuration` `quad_x`. Propellers **are** a disk (5 in). |
| 4 | No geometry → no copies | If `_geometry_from_spec(motors)` is `None`, omit `solidCopies`. Live smoke **must** still show **zero** motor solids. **Do not** seed SunnySky Ø to make smoke pretty |
| 5 | Cards / BOM | Still **one** `motors` card. Click any copy → `onSelect("motors")` |
| 6 | Layout | Presentation **row** (existing `layoutSolidsFromPose` slots). **Not** X of 230 mm. N=3 vs quad_x 4-station is a contradiction — do not put 3 copies on 4 arms |
| 7 | Pose | Copies **ignore** `declaredBoxPose` this Buy (would stack). Uncopied motors (N=1 / omitted) keep today’s pose path |
| 8 | Propellers | **Do not** instance. `motor_count` lives on `motors`, not on the prop spec |
| 9 | Version | **No** bump |

**Product sentence:**

```text
El visor muestra N copias del sólido de motors, N = motor_count del spec
del proyecto, mismo SKU, no N nodos BOM. No asume 4. Sin geometría, cero
sólidos motor. Aún no es X de 230 ni “cabe.”
```

**Not:**

```text
Cuatro motores en X de 230 mm · Ø inventado para SunnySky · N cards
· current_parameters manda · quad_x implica 4
```

---

## 1. You (Claude)

- Do **not** invent `diameter_mm` / `height_mm` 31.7 / plate L×W.
- Do **not** create `motors_2` … ComponentSpecs or extra cards.
- Do **not** place copies using wheelbase, `mountedOn`, card `x/y`, or `quad_x` corners.
- Do **not** instance propellers or any key other than `suggested_key == "motors"`.
- Do **not** default N=4 when `motor_count` is missing.
- Do **not** parse `fields[]` for the count.
- Do **not** bump package version. Do **not** un-QUEUE fit.
- Do **not** mutate live `workspace/` from tests. Live smoke is Engineer after report.
- Full pytest green. `cd ui/spatial-board && npm test && npm run typecheck`.
- Write the implementation report when done.
- **Stop** if you need a layout other than the row, or a catalog Ø, to “see motors” on the demo — that is outside this IC.

---

## 2. Intent

```text
ComponentSpec motors
  motor_count (int) + existing geometry DTO
        ↓
projector: optional solidCopies = N  (only if geometry and 2 ≤ N ≤ 16)
        ↓
Scene3D expandSolidCopies → N layout ids, one selectId "motors"
        ↓
row slots (layoutSolidsFromPose); click → same card
```

2D world unchanged: one motors card, one `mountedOn` edge.

---

## 3. Locked behavior

### 3.1 Count (`_solid_copies`)

Input: the `motors` `ComponentSpec` only (`suggested_key == "motors"`).

Let `raw = spec.properties["motor_count"].value` if that key exists.

Emit **nothing** (`None` / omit DTO key) unless **all** of:

1. `_geometry_from_spec(spec)` is not `None`
2. `raw` is a finite number and `float(raw).is_integer()`
3. `N = int(raw)` satisfies `2 <= N <= 16`

Missing, `1`, `0`, `3.5`, `None`, `>16` → omit. Visor then behaves as today (0 or 1 solid from geometry).

**Never** substitute 4. **Never** read frame `configuration`. **Never** read `current_parameters`.

### 3.2 Projector DTO

Additive optional `solidCopies?: number` on the **motors** node only, next to `geometry` / `mountedOn` / `declaredBoxPose`.

Omit the key when §3.1 is `None` (including live demo today: no geometry).

Do not emit `solidCopies` on propellers, FC, ESC, frame, parts, slots.

### 3.3 Visor expand (pure, no React)

New helper in `scene3dLayout.ts`, e.g. `expandSolidCopies`:

Input: the geometry-bearing nodes Scene3D already filters, plus optional `solidCopies`.

Output: list of `{ layoutId, selectId, geometry, declaredBoxPose? }` in **input order**.

- If `solidCopies` is a number `N >= 2`: emit N items, `selectId = node.id`, `layoutId = `${id}#${i}`` (`i` 0..N-1), **`declaredBoxPose` stripped**.
- Else: emit one item, `layoutId = selectId = node.id`, pose unchanged.

`layoutSolidsFromPose` / `clusterCenterPx` must use **`layoutId`** as `id` (unique). Collision of three `id: "motors"` is forbidden.

`Solid3D`: `onSelect(selectId)`; `selected={selectedId === selectId}`; `data-node-id` may stay `selectId` (all copies highlight together — intended). React `key={layoutId}`.

### 3.4 Pose / row

Uncopied solids: today’s `layoutSolidsFromPose` (one hop, remainder row).

Copied motors: each copy is an unposed row occupant (own slot, `originY=originZ=0`). Do not compose pose onto copies.

### 3.5 Copy

No `"cabe"`, `"ensamblado"`, `"cuatro motores"`, `"X de 230"` in new UI strings. Existing card field `motor_count` stays the number the project has.

---

## 4. Tests

### Python — `tests/test_geometry_motor_count_instances_b1.py`

Fixture: a motors spec with a disk (`diameter_mm` 27.9) plus `motor_count`, and a prop disk **without** `motor_count`. Use `project_spatial_nodes`.

| ID | Behavior |
|---|---|
| P1 | `motor_count=3` + disk → motors node `geometry` present and `solidCopies === 3`. Propellers node has **no** `solidCopies`. **One** node with `id=="motors"` (not 3 cards) |
| P2 | `motor_count=3` **without** diameter → no `geometry`, no `solidCopies` |
| P3 | no `motor_count` + disk → `geometry` present, **no** `solidCopies` key |
| P4 | `motor_count=4` + disk → `solidCopies === 4` (4 is allowed **when the spec has 4**, not as a default) |
| P5 | frame with `configuration=quad_x` and motors `motor_count=3` + disk → still `solidCopies === 3` (quad_x does not win) |
| P6 | `motor_count=1` + disk → no `solidCopies` key |
| P7 | `motor_count=3.5` + disk → no `solidCopies` key |

### UI — `scene3dLayout.test.ts` (or sibling)

| ID | Behavior |
|---|---|
| U1 | one disk `solidCopies: 3` → three layout ids `motors#0..#2`, all `selectId "motors"`, row `originX` increasing |
| U2 | omitted `solidCopies` → one item, `layoutId === "motors"` |
| U3 | `declaredBoxPose` on a `solidCopies: 3` node is **not** present on the expanded items |
| U4 | `clusterCenterPx` after expand of two copies still returns a finite midpoint (unique ids) |

Keep existing pose / `clusterCenterPx` / U8 tests green.

---

## 5. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/workspace/spatial_board.py` | `_solid_copies` + emit `solidCopies` |
| `ui/spatial-board/src/types.ts` | `solidCopies?: number` |
| `ui/spatial-board/src/scene3dLayout.ts` | `expandSolidCopies` |
| `ui/spatial-board/src/Scene3D.tsx` | expand before layout; pass `selectId` / `layoutId` |
| `ui/spatial-board/src/Solid3D.tsx` | only if needed for select vs key (prefer keep `id` = selectId, `key` = layoutId from parent) |
| `tests/test_geometry_motor_count_instances_b1.py` | P1–P7 |
| `ui/spatial-board/src/scene3dLayout.test.ts` | U1–U4 |
| `.jes/artifacts/implementation_report_geometry_motor_count_instances_b1.md` | write |

---

## 6. Engineer smoke (after Cursor review)

Live `autonomía-de-10min`:

| Step | Expected |
|---|---|
| Card `motors` | still one card; `motor_count` **3**; SKU SunnySky |
| 3D pane | **no** new motor solids (no Ø) |
| Prop disk | still **one** (do not triple the propeller) |
| Frame card | still `wheelbase_mm` 230 — unused by this Buy’s layout |

That empty 3D result is **ACCEPT**, not a bug. Visible N-copies need a later ★ that gives `motors` a disk **or** a different SKU that already has Ø.

Record [engineer_smoke_geometry_motor_count_instances_b1.md](engineer_smoke_geometry_motor_count_instances_b1.md) after review.

---

## 7. Done when

- [ ] P1–P7 and U1–U4 green
- [ ] Full pytest green; UI tests + typecheck green
- [ ] Live census: still 1 motors card; still 0 motor solids
- [ ] No version bump; fit still QUEUED
- [ ] Report written

---

## Explicitly not this IC

Default 4 · quad-X / wheelbase placement · SunnySky Ø seed · motor cylinder 31.7 · N BOM nodes · propeller copies · auto-refresh · `"cabe"` · Three.js · Conversation Engine
