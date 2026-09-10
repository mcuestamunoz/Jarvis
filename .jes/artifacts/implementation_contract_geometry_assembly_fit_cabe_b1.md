# Implementation Contract — Geometry assembly fit B1-min (posed box–box screening)

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** CLOSED — REVIEWED PASS WITH NOTES @ **2540** + smoke **ACCEPT**  
**Parents:**
- Engineer ★ **`B1-min`** (2026-09-09)
- [investigation_review_geometry_assembly_fit_cabe_b0.md](investigation_review_geometry_assembly_fit_cabe_b0.md) **PASS WITH NOTES**
- [investigation_report_geometry_assembly_fit_cabe_b0.md](investigation_report_geometry_assembly_fit_cabe_b0.md)
- [implementation_contract_geometry_assembly_fit_compare.md](implementation_contract_geometry_assembly_fit_compare.md) — **stub; do not implement that file.** This IC **supersedes** it.
- Pose writer **CLOSED** @ **2456** · Scene3D-from-pose **CLOSED** @ **2462**
- Plate L×W **B0** — Rooster still no box (**out**)
- Frame class `GAP-FRAME-PROP-SIZE` — **not** this Buy; do not merge
- Kit SKUs D / adapter — **out** (no geometry)

**Type:** Backend AABB screening of **one posed child box vs its pose-origin box**, in declared mm. Board text + IDLE answer.  
**Not** `"cabe"`/`VERIFIED`. **Not** visor pixels. **Not** a Continuity HIGH. **Not** a collision engine.

**Baseline:** package **`0.3.8`** · suite **2532**

**Output:** `.jes/artifacts/implementation_report_geometry_assembly_fit_cabe_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Shape | **B1-min** — AABB in the pose’s own mm frame; fail-closed if any axis missing |
| 2 | Named live pair | Smoke / fixtures: `esc` (child) vs `flight_controller` (origin). Helper is **generic** for any posed box child vs box origin — not an `if key==esc` engine, not “all `mounted_on` edges” |
| 3 | Frame | Declared L→+X W→+Y H→+Z (`POSE_AXES_HONESTY_LABEL`). **No** CSS Y↔Z. **No** `scene3dLayout.ts` |
| 4 | Missing axis | **Not** 0. Incomplete → “pose incompleta”; **no** overlap boolean |
| 5 | Copy | Screening only. Forbidden: `cabe`, `no cabe`, `VERIFIED`, `ensamblado`, `misfit geométrico` |
| 6 | PASS | `_block_progress_status` / `ASSEMBLY_READY` / hover / `engineering_readiness.py` gap set **unchanged** (no new Gap type) |
| 7 | Surface | Child Board `fields` + IDLE whole-word `cabe` → helper text. **No** new UI chrome. **`ui/` empty** |
| 8 | Version | **No** bump |

**Product sentence:**

```text
Si el ESC tiene pose completa (x,y,z) respecto a una caja origen, la card
dice si los sobres se solapan — screening, no verificado. Si falta un eje,
dice pose incompleta. El visor puede pintar 0; Jarvis no compara con 0.
```

**Not:**

```text
cabe / no cabe · overlap de cards · px del visor · Rooster L×W
· cilindro · GAP HIGH · Conversation Engine · stub 2026-09-07
```

---

## 1. You (Claude)

- **STOP** if you import or port `layoutSolidsFromPose` / `yMm ?? 0` / Y↔Z.
- **STOP** if you add a Gap, touch `ASSEMBLY_READY`, or write `"cabe"` in Jarvis copy.
- **STOP** if you invent Rooster L×W or treat `mounted_on` as the compare origin.
- Pose writer **REPLACE** (not merge) stays. Do not change `declared_box_pose_declare_assist`.
- `ComponentLibrary` unchanged. Full pytest green. `ui/spatial-board` **no** test/typechange required (`git diff` empty under `ui/`).
- Write the report.

---

## 2. Intent

```text
declared_box_pose (raw mm) + _geometry_from_spec (both boxes)
        ↓
pose_envelope_screening (Python)  — never TS, never CSS px
        ↓
Board child field  +  IDLE “cabe” message
        ↓
PASS / hover / ASSEMBLY_READY byte-identical
```

---

## 3. Locked behavior

### 3.1 Helper (`src/jarvis/core/pose_envelope_screening.py`)

New thin module. Name may vary; behavior locked.

```text
screen_posed_envelope(child: ComponentSpec, components: dict) -> Screening
```

`Screening.status` ∈:

| status | When |
|---|---|
| `no_pose` | `declared_box_pose is None` |
| `origin_unusable` | origin missing **or** `_geometry_from_spec(origin)` is not `box` (same gate as `_declared_box_pose_dto`) |
| `child_not_box` | child geometry missing or not `box` (disk → this, never cylinder) |
| `pose_incomplete` | DTO would exist but any of `x_mm`/`y_mm`/`z_mm` is `None`. Payload: missing axis names |
| `overlap` | all three axes present; AABB overlap (inclusive touch) |
| `no_overlap` | all three axes present; no overlap |

**AABB (declared mm, center-to-center, single-level):**

- Origin box centered at `(0,0,0)`; half-extents `(length_mm/2, width_mm/2, height_mm/2)`.
- Child box centered at `(x_mm, y_mm, z_mm)`; same half-extents from **child** L/W/H.
- Overlap iff for every axis `|c_child − c_origin| ≤ half_child + half_origin` (touch = overlap).
- Do **not** read `mounted_on`. Do **not** compose origin chains. Do **not** default missing mm to 0.

### 3.2 Locked Spanish (`format_screening` or equivalent)

Never those forbidden tokens. Use:

| status | Copy (must include “screening, no verificado” on overlap/no_overlap/incomplete) |
|---|---|
| `pose_incomplete` | `Pose incompleta (faltan {y, z}); no se compara — screening, no verificado.` (list the missing axes) |
| `overlap` | `Los sobres se solapan en los ejes declarados — screening, no verificado.` |
| `no_overlap` | `Los sobres no se solapan en los ejes declarados — screening, no verificado.` |
| `origin_unusable` / `child_not_box` / `no_pose` | Honest absence; still **no** `"cabe"`. IDLE may say Jarvis no verifica ensamblaje; falta pose completa y dos cajas. |

Mount vs pose (review N2): do **not** say the ESC is mounted on the FC or “cabe en la placa”.

### 3.3 Board

In `spatial_board._fields`, **after** existing pose Δ fields, if the child has a pose DTO (same gate as today) **or** a raw pose that is incomplete but origin is a box: append one field:

```text
label: "sobres"
value: <format_screening>
```

Show incomplete text when pose exists, origin is box, axes missing. Omit the field when `no_pose`. Disk child with a pose DTO: origin-box gate already omits pose text today if origin isn’t box; if origin is box and child is disk, still omit overlap math (`child_not_box`) — you may omit the field or show honest absence; **do not** invent a disk AABB.

**Do not** add `declaredBoxPose` keys for screening. Machine DTO unchanged.

### 3.4 IDLE

In `_try_handle_declared_box_pose`’s neighborhood (IDLE, before LLM): if the phrase is a **whole-word** `cabe` question/command (`cabe`, `¿cabe?`, `cabe el esc`, …) and **not** a pose declare/clear:

- Load project; run helper on the named subject if parsed, else on the **only** posed component if exactly one, else ask which component (no LLM).
- Return the formatted screening string. `_RefuseLLM` must not be called.

Do **not** add `cabe` to acquisition aliases. Do **not** open a wizard.

### 3.5 Untouched

`ui/` including `scene3dLayout.ts`. `engineering_readiness.py`. `project_continuity.py` (no new rank, no new gap). `project_closure.py` class-compatibility copy. Pose parser/writer. `KIT_TO` / `BLOCK_TO`. Version.

---

## 4. Tests (new file)

`tests/test_geometry_assembly_fit_cabe_b1.py`

Use a synthetic 10min-shaped fixture: ESC box 50×21.6×12, FC box 44×84×12, pose origin `flight_controller`.

| ID | Behavior |
|---|---|
| T0 | Pose `x_mm=5` only → `pose_incomplete`; no overlap status; formatted text has `incompleta` and **not** `cabe`/`VERIFIED` |
| T1 | Pose `(5, 0, 0)` → `overlap` (live-shaped numbers; inclusive) |
| T2 | Pose `(200, 0, 0)` → `no_overlap` |
| T3 | Origin disk / missing origin → `origin_unusable` |
| T4 | Child disk → `child_not_box` (no cylinder path) |
| T5 | `project_spatial_nodes` ESC `fields` include `sobres` with incomplete copy; **no** new `declaredBoxPose` keys |
| T6 | `_block_progress_status` propulsion/energy **and** readiness `overall` twin: incomplete vs complete pose, same PASS / not flipped by screening |
| T7 | Orchestrator IDLE `"cabe"` / `"¿cabe el esc?"` with `_RefuseLLM` returns screening text; LLM not called |
| T8 | `git diff` empty on `ui/` and `scene3dLayout.ts` (assert in report; no need to parse git in pytest) |

No `workspace/` writes. No network.

---

## 5. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/core/pose_envelope_screening.py` | **new** helper + copy |
| `src/jarvis/workspace/spatial_board.py` | one Board field |
| `src/jarvis/core/orchestrator.py` | IDLE `cabe` bridge |
| `tests/test_geometry_assembly_fit_cabe_b1.py` | T0–T7 |
| `ui/` | **empty** |
| `.jes/artifacts/implementation_report_geometry_assembly_fit_cabe_b1.md` | write |

Do **not** edit `implementation_contract_geometry_assembly_fit_compare.md` into READY.

---

## 6. Engineer smoke (after Cursor review)

Project **`autonomía-de-10min`** (5min ESC has no box).

1. `estado` / Board ESC: `sobres` = pose incompleta (today `x=5` only). Hover unchanged.  
2. Re-declare **all three** axes in **one** phrase (writer replaces, does not merge), e.g.  
   `declara el esc a 5 mm en x y 0 mm en y y 0 mm en z respecto al fc`  
   → `sobres` = se solapan — screening, no verificado.  
3. Far pose (e.g. `200 mm en x` + y + z) → no se solapan.  
4. Type `cabe` / `¿cabe el esc?` → same screening text, not an LLM yes/no.  
5. Architecture / margen / `NOT ASSEMBLY READY` (energy) unchanged.

Record `engineer_smoke_geometry_assembly_fit_cabe_b1.md`.

---

## 7. Done when

- [x] T0–T7 green; full pytest green (**2540**)  
- [x] `ui/` / `scene3dLayout.ts` empty diff  
- [x] No forbidden tokens in helper copy  
- [x] No new Gap / no version bump  
- [x] Report written  
- [x] Engineer smoke §6 **ACCEPT**  

---

## Explicitly not this IC

Card-lane overlap · visor px as SoT · missing-axis-as-0 · Rooster L×W · cylinder · Continuity HIGH · FEA/STEP · Conversation Engine · unfreezing the 2026-09-07 stub · version bump
