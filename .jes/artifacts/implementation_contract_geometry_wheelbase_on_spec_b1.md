# Implementation Contract — Mapping rung 2 first cut: wheelbase on the bound frame spec B1

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Cursor (same session — Engineer `procede`)  
**Reviewer:** Cursor against this IC after the edit

**Status:** IMPLEMENTATION REVIEWED — **PASS WITH NOTES** · **CLOSED** (suite **2466**) + Engineer smoke **ACCEPT**  
**Parents:**
- [investigation_review_geometry_wheelbase_on_spec_b1.md](investigation_review_geometry_wheelbase_on_spec_b1.md) — **PASS WITH NOTES** · Engineer ★ **B1**
- [investigation_report_geometry_wheelbase_on_spec_b1.md](investigation_report_geometry_wheelbase_on_spec_b1.md) — lean **B1** test lock + live smoke
- [engineer_lock_geometry_3d_mapping_path.md](engineer_lock_geometry_3d_mapping_path.md) — rung **2 first cut**
- Catalog-bound refresh B1 **CLOSED** — reuse `refresh_component_from_catalog`; **no** auto-refresh
- Scene3D-from-pose B1 **CLOSED** — do **not** move solids for this Buy
- Fit stub — **QUEUED — DO NOT IMPLEMENT**
- 4-motor sketch — **out**

**Type:** Regression tests + live Continuity refresh of the bound frame. **No new writer. No projector overlay. No Scene3D glyph.**  
**Not** N-motor copies. **Not** plate L×W. **Not** motor height 31.7. **Not** `"cabe"`.

**Baseline:** package **`0.3.8`** · suite **2462** · HEAD `ca7a290`

**Output:** `.jes/artifacts/implementation_report_geometry_wheelbase_on_spec_b1.md`

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy **B1** | YES — lock existing bind/refresh; smoke live frame |
| 2 | New binder / new field | **No** — `wheelbase_mm` already on `FrameSpec` + `bind_frame_from_catalog` |
| 3 | Projector | Walks `spec.properties` only. Stale state **must not** show 230 from the seed |
| 4 | Board load | **No** silent refresh (refresh IC lock 6 holds) |
| 5 | Scene3D | **Unchanged** — wheelbase is not an envelope |
| 6 | 4 motors | **Out** |
| 7 | Version | **No** bump |
| 8 | Refresh side-effect | `configuration` (`quad_x`) may appear too — honest, not a bug |

**Product sentence:**

```text
La card del frame bound muestra wheelbase_mm citado del seed (230 mm
Rooster). Aún no hay 4 motores en X ni “cabe.”
```

---

## 1. You

- Do **not** add a visor path that reads `library/frames` when `ProjectState` lacks the key.
- Do **not** auto-refresh on projector / Board read / save.
- Do **not** instance `motor_count`. Do **not** add a Scene3D wheelbase solid/line.
- Do **not** bump package version.
- Do **not** un-QUEUE fit.
- Prefer **zero** `src/` edits. If a real hole appears, stop and name it — do not invent overlay.
- Full suite green. Zero weakened tests.
- Write the implementation report when done.

---

## 2. Intent

```text
stale bound frame (mass/size/material only, catalog_ref=rooster)
  → refresh_component_from_catalog(state, "frame")
  → properties.wheelbase_mm = 230 mm (seed)
  → Board _fields shows it
  → Scene3D still has no frame solid
```

Continuity IDLE: existing `"actualiza la frame"` / `"actualiza el frame desde catálogo"`.

---

## 3. Locked tests

New file `tests/test_geometry_wheelbase_on_spec_b1.py`:

| ID | Behavior |
|---|---|
| T1 | Stale rooster-like `frame` (only mass_kg / size_class_inch / material + `catalog_ref`) → `refresh_component_from_catalog` → `wheelbase_mm` **230**, `configuration` **quad_x**; mass/material survive; a sibling `frame_plate` with `parent_key=frame` is **byte-identical** |
| T2 | Same stale state **before** refresh: `project_spatial_nodes` frame card fields do **not** contain `230` or label `wheelbase_mm` |
| T3 | After T1 refresh: projector frame fields include `wheelbase_mm` value **230 mm** (existing `_format_property`) |
| T4 | Orchestrator IDLE on a fixture project with that stale frame: `"actualiza la frame"` persists 230 and the message is free of `cabe` / `ensamblado` / `corregido automáticamente` |

Do **not** modify live `workspace/` from tests (`tmp_path` only).

---

## 4. Files

| Path | Change |
|---|---|
| `tests/test_geometry_wheelbase_on_spec_b1.py` | T1–T4 |
| `src/` `ui/` | **Expect empty diff** |
| `.jes/artifacts/implementation_report_geometry_wheelbase_on_spec_b1.md` | write |
| docs / mapping lock / `engineering_state.json` | PRIORIDAD: first cut closable after smoke |

---

## 5. Engineer smoke (after tests)

On live `autonomía-de-10min`: Continuity **`actualiza el frame desde catálogo`** (or the writer equivalent). Board card `frame` shows `wheelbase_mm` **230 mm**. 3D pane **unchanged** (still no frame solid). Plates/arms still present.

Record [engineer_smoke_geometry_wheelbase_on_spec_b1.md](engineer_smoke_geometry_wheelbase_on_spec_b1.md).

---

## 6. Done when

- [ ] T1–T4 green
- [ ] `src/` `ui/` empty unless a named hole forced a stop
- [ ] Full pytest green; UI tests still 34
- [ ] No version bump
- [ ] Report written
- [ ] Live smoke recorded

---

## Explicitly not this IC

4-motor X · Scene3D wheelbase glyph · plate L×W · motor 31.7 · auto-refresh · fit · Here3 · Conversation Engine
