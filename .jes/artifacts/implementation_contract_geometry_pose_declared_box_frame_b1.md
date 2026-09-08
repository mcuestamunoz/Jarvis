# Implementation Contract — Geometry pose declared box-local frame B1

**Project:** Jarvis  
**Date:** 2026-09-08  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTATION REVIEWED — **PASS WITH NOTES** · **CLOSED** (suite **2438**) + Engineer **ACCEPT**  
**Parents:**
- [investigation_review_geometry_pose_box_anchor.md](investigation_review_geometry_pose_box_anchor.md) — **PASS WITH NOTES** (point solved; unlabeled L/W/H ≠ manufacturer axes)
- [investigation_report_geometry_pose_box_anchor.md](investigation_report_geometry_pose_box_anchor.md) — reversal #3: written risk-acceptance of center + **explicitly declared** local axes
- [engineer_lock_geometry_3d_placement_horizon.md](engineer_lock_geometry_3d_placement_horizon.md)
- Plate/front-arm path remains B0 (do **not** individuate `frame_arm`; do **not** use `frame_plate` as millimetre origin)
- Stub [implementation_contract_geometry_assembly_pose_b1plus.md](implementation_contract_geometry_assembly_pose_b1plus.md) — **still DEFERRED** (airframe pose). This IC is a **different** Buy.
- Fit stub — **QUEUED — DO NOT IMPLEMENT**

**Type:** First **declared box-local pose** slice — origin = geometric center of an existing `geometry: box` node; axes = **Jarvis-declared** mapping of DTO L/W/H → +X/+Y/+Z, labeled honest (not catalog heading, not gravity, not airframe forward). Optional millimetre offsets in that frame. Board **text** only.  
**Not** Scene3D layout. **Not** Continuity parse. **Not** `"cabe"`. **Not** arm individuation. **Not** plate L×W.

**Baseline:** package **`0.3.8`** · suite **2429**

**Output:** `.jes/artifacts/implementation_report_geometry_pose_declared_box_frame_b1.md`

---

## 0. Engineer Buy (locked)

Engineer `procede` with honest step 1 (not option 3 / not manufacturer-diagram search this cycle).

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B1** | YES — declared box-local frame + optional offsets |
| 2 | Origin point | Geometric **center** of origin’s declared box: `(L/2, W/2, H/2)` from the min corner in the declared triad. Function of sourced L×W×H. **Not** stored as extra KNOW |
| 3 | Axes | **Declared** (risk accepted): `length_mm → +X`, `width_mm → +Y`, `height_mm → +Z`. `source` of this mapping is **declared**, never `catalog`. Copy must say so |
| 4 | Origin key | Any existing component whose projector `geometry.shape === "box"` (live demo: FC, ESC, battery). **Not** disk. **Not** shapeless frame parts |
| 5 | Offsets | Optional `x_mm` / `y_mm` / `z_mm` in that local frame. Omit = no displacement declared (not “at the center”) |
| 6 | Orthogonal | Does **not** replace `mounted_on`. Guide vs millimetre frame stay two facts |
| 7 | Board | Projector **text fields** only. **Do not** move CSS 3D solids / `layoutSolidsRow` |
| 8 | Continuity | **Out** — no IDLE “pon a 5 mm” parser this Buy (same sequencing as relation B1) |
| 9 | Fit / airframe +X / four arms | **Out** |
| 10 | Version | **No** bump |

**Honest product sentence:**

```text
Puedo declarar un origen en el centro de una caja ya medida y un desplazamiento
en ejes locales declarados (L→+X, W→+Y, H→+Z). Eso no es el morro del drone ni “cabe.”
```

---

## 1. You

- Do **not** treat DTO L/W/H as manufacturer heading or gravity.
- Do **not** use `frame_plate` / `frame_arm` / disks as origin (writer **ValueError**).
- Do **not** change `Scene3D`, `layoutSolidsRow`, `scene3dScale`, `Solid3D`.
- Do **not** add Continuity pose assist.
- Do **not** un-QUEUE fit; do **not** implement the 2026-09-07 pose stub.
- Do **not** invent plate L×W or motor cylinder.
- Do **not** bump package version.
- Reuse `_geometry_from_spec` to decide “has box” — do **not** duplicate LWH rules.
- `refresh_component_from_catalog` must **preserve** the new field (same as `mounted_on`).
- Full pytest (expect **2429 + new tests**). `cd ui/spatial-board && npm test && npm run typecheck` if you touch visor types; prefer **no UI logic change** (cards already render `fields`).
- Write the implementation report when done.

---

## 2. Intent

```text
ComponentSpec.declared_box_pose: DeclaredBoxPose | None
        ↓
writer set/clear (declared only; origin must exist + box; ≠ self)
        ↓
project_spatial_nodes → text fields (honesty labels + optional Δmm)
        ↓
2D card shows it; 3D row unchanged
```

---

## 3. Locked behavior

### 3.1 Schema

In `src/jarvis/schemas/action_schema.py` (additive, default `None`):

```python
class DeclaredBoxPose(BaseModel):
    """Geometry pose B1 — declared millimetre offset in a box-local frame.

    Origin point is always the geometric center of origin_key's declared box.
    Axes are Jarvis-declared: length_mm=+X, width_mm=+Y, height_mm=+Z —
    not manufacturer heading, not gravity, not airframe forward.
    """
    origin_key: str
    x_mm: float | None = None
    y_mm: float | None = None
    z_mm: float | None = None
```

On `ComponentSpec`, **after** `mounted_on`:

```python
declared_box_pose: DeclaredBoxPose | None = None
```

Update the `mounted_on` comment: relation still has **no** pose; pose is this orthogonal field.

Constant for Board copy (one module, e.g. next to writer or `spatial_board.py`):

```text
locales declarados (L→+X, W→+Y, H→+Z); no morro; no gravedad
```

Forbidden field labels / values: `ensamblado`, `cabe`, `verificado`, `posición real`, `adelante`, `morro`.

### 3.2 Writer

`set_component_declared_box_pose(project_state, component_key, pose: DeclaredBoxPose | None) -> ProjectState`

- `pose is None` → clear (idempotent).
- `component_key` missing → `ValueError`.
- `pose.origin_key == component_key` → `ValueError` (no self-origin).
- `origin_key` missing from `components` → `ValueError`.
- `_geometry_from_spec(origin spec)` is not `box` → `ValueError` (disk / None / missing LWH).
- Do **not** require `mounted_on` to be set.
- Do **not** infer origin from `mounted_on`.
- Returns updated state; caller persists (same as `set_component_mounted_on`).

### 3.3 Projector / Board

When `declared_box_pose` is set:

| Label | Value |
|---|---|
| `origen pose` | `origin_key` |
| `ejes pose` | the locked honesty string above |
| `Δx mm` / `Δy mm` / `Δz mm` | only for offsets that are not `None` (plain number, no “real”) |

If origin key vanished from `components`, omit pose fields (do not crash; same class as stale `mountedOn` edge omit). Do **not** invent a fallback origin.

**No** new node DTO keys required for 3D. **No** `layoutSolidsRow` inputs.

### 3.4 Tests (minimum)

New `tests/test_geometry_pose_declared_box_frame_b1.py`:

| ID | Behavior |
|---|---|
| T1 | Set pose ESC → FC with `x_mm=5`; round-trip `model_dump`; Board/`_fields` show origin + honesty + Δx |
| T2 | Reject origin `frame_plate` (no box) |
| T3 | Reject origin `motors` (disk) |
| T4 | Reject missing origin key / self-origin |
| T5 | Clear pose → `None` |
| T6 | Catalog refresh preserves `declared_box_pose` (extend existing refresh test or sibling) |
| T7 | Existing `mounted_on` tests still pass (full suite) |

Do **not** add Python tests that move 3D solids.

---

## 4. Explicit non-goals

Scene3D placement · Continuity pose phrases · fit/`cabe` · arm ordinals · airframe +X · treating print-order as catalog physics · version bump · Conversation Engine

---

## 5. Files expected to change

| File | Change |
|---|---|
| `src/jarvis/schemas/action_schema.py` | `DeclaredBoxPose` + field |
| `src/jarvis/core/component_writers.py` | writer |
| `src/jarvis/workspace/spatial_board.py` | `_fields` (+ maybe omit-if-origin-gone) |
| `tests/test_geometry_pose_declared_box_frame_b1.py` | new |
| `tests/test_catalog_bound_refresh_b1.py` | preserve new field if you touch refresh assertions |
| `.jes/artifacts/implementation_report_geometry_pose_declared_box_frame_b1.md` | write |

**Do not change:** `Scene3D.tsx`, `scene3dLayout.ts`, catalog seeds, Continuity assist, fit stub, package version.

---

## 6. Done criteria

- [ ] Schema + writer + projector text as locked  
- [ ] T1–T7 + full pytest green  
- [ ] `ui/` 3D files **unchanged** (`git diff -- ui/spatial-board/src/Scene3D.tsx ui/spatial-board/src/scene3dLayout.ts` empty)  
- [ ] Report written  
- [ ] Cursor review next

---

## 7. Stop conditions

Stop and ask before: moving 3D solids from these numbers; Continuity mm parser; using plate/arm/disk as origin; claiming airframe heading; opening fit; bumping version.
