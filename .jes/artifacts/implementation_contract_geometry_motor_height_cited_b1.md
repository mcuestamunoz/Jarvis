# Implementation Contract — Motor `height_mm` 31.7 cited B1 (EMAX only, no cylinder)

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTED · REVIEWED **PASS WITH NOTES** · CLOSED (suite **2480**) + smoke ACCEPT  
**Parents:**
- [engineer_lock_geometry_3d_mapping_path.md](engineer_lock_geometry_3d_mapping_path.md) — rung **3**
- [investigation_report_geometry_motor_envelope.md](investigation_report_geometry_motor_envelope.md) §C — EMAX “Motor Height” 31.7 mm (shaft-inclusive) **≠** SunnySky “Body Length” 18 mm
- Motor envelope B1 **CLOSED** @ **2323** — overall axial was **OUT** (lock 5 / N5). This Buy **reopens that one cited number on one SKU**
- Motor visor copies B1 **CLOSED** @ **2473** — live demo is SunnySky **without** Ø
- Fit stub — **QUEUED — DO NOT IMPLEMENT**
- Plate L×W / `"cabe"` — **out**

**Type:** Additive **catalog seed + MotorSpec + bind projection**. Representar **text**.  
**Not** a cylinder. **Not** a new glyph. **Not** 31.7 on SunnySky / live demo. **Not** the 15 mm prop shaft.

**Baseline:** package **`0.3.8`** · suite **2473** · HEAD of motor-copies Buy (uncommitted local OK)

**Output:** `.jes/artifacts/implementation_report_geometry_motor_height_cited_b1.md`

---

## 0. Engineer Buy (locked)

Engineer: `siguiente el de la altura` (mapping rung 3).

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B1** | YES — seed EMAX `height_mm` **31.7** as **cited** |
| 2 | SKU | **`emax_rs2205s_2300` only** — the row whose `source_note` already quotes Motor Height 31.7 mm |
| 3 | SunnySky R2205 Body Length 18 mm | **Still not seeded** — different physical fact (envelope §C) |
| 4 | Live demo `sunnysky_r2305_2500` | **Untouched** — no page, no 31.7, no Ø invention |
| 5 | Sibling `emax_rs2205_2300` | **No** 31.7 (unsourced; envelope N2) |
| 6 | 15 mm extended prop shaft | **Still not seeded** |
| 7 | Cylinder / 3D | **No**. `_geometry_from_spec`: diameter + `height_mm` without L×W stays **disk**. Do not stitch Ø+height. Do not change CSS 3D disk |
| 8 | Version | **No** bump |

**Product sentence:**

```text
La spec EMAX RS2205S cita Motor Height 31.7 mm como height_mm en card.
No es Body Length de SunnySky. No es cilindro. El demo SunnySky R2305
sigue sin esa cifra.
```

**Not:**

```text
Todos los motores miden 31.7 · disco + height = cilindro · 18 mm
sembrado · Ø inventado para el demo
```

---

## 1. You (Claude)

- Do **not** seed 31.7 on any SKU except `emax_rs2205s_2300`.
- Do **not** seed SunnySky Body Length 18 mm.
- Do **not** seed the 15 mm shaft length.
- Do **not** invent `diameter_mm` on `sunnysky_r2305_2500`.
- Do **not** change `_geometry_from_spec` to emit a cylinder, box-from-disk, or `height` on the disk DTO.
- Do **not** change `Solid3D` disk faces / `scene3dScale` disk `z`.
- Do **not** un-QUEUE fit. Do **not** bump version.
- Do **not** mutate live `workspace/` from tests.
- Full pytest green. UI tests still green (expect **no** UI file edits).
- Write the implementation report when done.

---

## 2. Intent

```text
library/motores/_datos.json  emax_rs2205s_2300.height_mm = 31.7
        ↓
MotorSpec.height_mm (optional)
        ↓
bind_motor_from_catalog → properties.height_mm (mm, declared)
        ↓
Board _fields text
        ↓
_geometry_from_spec still disk from diameter_mm (no L×W → not a box)
```

---

## 3. Locked behavior

### 3.1 `MotorSpec` (`library.py`)

Add optional:

```text
height_mm: float | None = None
```

Parse in `_motor_from_raw` like the other optional mm fields.

Update the MotorSpec docstring: overall axial height is now **optional and SKU-scoped**. EMAX `height_mm` means that page’s **Motor Height** (shaft-inclusive per envelope §C). It is **not** SunnySky Body Length. It is **not** a glyph/cylinder input.

### 3.2 Seed

**`emax_rs2205s_2300` only:**

```json
"height_mm": 31.7
```

Rewrite the `source_note` clause that currently says Motor Height 31.7 mm is **NOT seeded** so it states it **is seeded** as `height_mm` (cited Motor Height). Keep the honesty that this is **not** comparable to SunnySky Body Length. Keep the 15 mm extended prop shaft as **not seeded**.

Do **not** add `height_mm` to `sunnysky_r2205_2500`, `sunnysky_r2305_2500`, or `emax_rs2205_2300`.

Thrust / KV / mass / identity / other dims **unchanged**.

### 3.3 Bind

In `bind_motor_from_catalog`, extend the existing dim loop:

```text
("stator_diameter_mm", "stator_height_mm", "diameter_mm", "shaft_diameter_mm", "height_mm")
```

Same `PropertyValue(..., unit="mm", confidence=0.9, source="declared")` when not `None`.

No `MotorSuggestion` TypedDict change.

### 3.4 Projector / visor

`_fields` already walks properties — EMAX-bound cards show `height_mm` `31.7 mm`.

`_geometry_from_spec`: **no edit required** if behavior already is: box only with L+W+H; disk from diameter; `stator_height_mm` ignored for shape. **Required regression:** a motors spec with `diameter_mm=27.9` **and** `height_mm=31.7` (no length/width) → `geometry == {shape: disk, diameter_mm: 27.9}` — **not** a box, **not** omitted.

CSS 3D / `solidCopies`: unchanged. Disk stays flat.

---

## 4. Tests

New file `tests/test_geometry_motor_height_cited_b1.py`:

| ID | Behavior |
|---|---|
| T1 | `default_library.get_motor("emax_rs2205s_2300").height_mm == pytest.approx(31.7)` |
| T2 | `get_motor("sunnysky_r2205_2500").height_mm is None` |
| T3 | `get_motor("sunnysky_r2305_2500").height_mm is None` |
| T4 | `get_motor("emax_rs2205_2300")` has `height_mm is None` (or attribute None) |
| T5 | `bind_motor_from_catalog(motor_spec_to_suggestion(emax_rs2205s_2300))` → `properties["height_mm"].value == 31.7` and `unit == "mm"`; `diameter_mm` still 27.9 |
| T6 | bind SunnySky R2205 → **no** `height_mm` key |
| T7 | `project_spatial_nodes` on a motors spec `{diameter_mm: 27.9, height_mm: 31.7}` → `geometry.shape == "disk"` and `diameter_mm == 27.9`; fields include `height_mm` `31.7 mm` |

Do **not** weaken motor-envelope tests. Do **not** add UI tests unless a UI file must change (it must not).

---

## 5. Files (expected)

| Path | Change |
|---|---|
| `library/motores/_datos.json` | EMAX row `height_mm` + `source_note` honesty |
| `src/jarvis/knowledge/library.py` | `MotorSpec.height_mm` + loader + docstring |
| `src/jarvis/core/catalog_bind.py` | project `height_mm` in the dim loop |
| `tests/test_geometry_motor_height_cited_b1.py` | T1–T7 |
| `ui/` | **empty diff** |
| `.jes/artifacts/implementation_report_geometry_motor_height_cited_b1.md` | write |

---

## 6. Engineer smoke (after Cursor review)

Live `autonomía-de-10min` motors card: still SunnySky, **no** `height_mm` 31.7, still no motor solid.

Optional lab (tmp project / Continuity refresh of an EMAX-bound motors spec): card shows `height_mm` 31.7 mm; 3D motor stays a **flat disk** if Ø is present.

Record [engineer_smoke_geometry_motor_height_cited_b1.md](engineer_smoke_geometry_motor_height_cited_b1.md).

---

## 7. Done when

- [ ] T1–T7 green; full pytest green; UI suite unchanged-green
- [ ] Live demo not given 31.7
- [ ] No cylinder / no disk DTO height / no version bump
- [ ] Report written

---

## Explicitly not this IC

SunnySky 18 mm · 15 mm shaft · live R2305 Ø · cylinder · plate L×W · `"cabe"` · Three.js · Conversation Engine
