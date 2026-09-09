# Investigation Contract — Mapping rung 2 first cut: wheelbase on the bound frame spec

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Formulation:** Engineer `procede con wheelbase` after Scene3D-from-pose CLOSED (`ca7a290`)  
**Investigator:** Cursor (this session)  
**Reviewer:** Cursor (Investigation Review, same session — Engineer already named the rung)  
**Output:** `.jes/artifacts/investigation_report_geometry_wheelbase_on_spec_b1.md`

**Status:** INVESTIGATION REVIEWED — **PASS WITH NOTES** · Engineer ★ **B1** (`procede con wheelbase` 2026-09-09) · IC READY  
**Parents (mandatory):**
- [engineer_lock_geometry_3d_mapping_path.md](engineer_lock_geometry_3d_mapping_path.md) — rung **2 first cut only** (`project wheelbase_mm onto the bound frame spec`)
- Catalog-bound refresh B1 **CLOSED** @ **2406** — `refresh_component_from_catalog` + IDLE `actualiza … desde catálogo`; **no** auto-refresh on Board load
- Structure B parts graph — `bind_frame_from_catalog` already projects seed `wheelbase_mm`
- Scene3D-from-pose B1 **CLOSED** @ **2462**
- Fit stub — **QUEUED — DO NOT IMPLEMENT**
- 4-motor sketch / motor height 31.7 / plate L×W / `"cabe"` — **out**

**Type:** Investigation only — how `wheelbase_mm` 230 (Armattan Rooster seed) reaches the **bound** `ComponentSpec` that the Board already walks as text.  
**Not** an Implementation Contract. **Do not implement in the report.**  
**Not** N-motor copies. **Not** a Scene3D line/silhouette. **Not** plate L×W. **Not** auto-refresh on visor load.

**Checkpoint base:** package **`0.3.8`** · suite **2462** · commit `ca7a290`

**Single objective (locked):**

> Decide the **minimum honest path** so a catalog-bound frame spec actually **has** `wheelbase_mm` (and the card can show it via the existing `_fields` walk) — without inventing millimetres, without instancing motors, without a second SoT in the projector.

**Product sentence this would enable (only after a later ★ Buy ≠ B0):**

```text
La card del frame bound muestra wheelbase_mm citado del seed (230 mm
Rooster). Aún no hay 4 motores en X ni “cabe.”
```

**Not:**

```text
Cuatro sólidos motor en X de 230 mm · el visor lee library/frames
saltándose ProjectState · auto-refresh al abrir el Board
```

---

## 0. Role split

```text
Engineer  → procede (rung 2 after Scene3D CLOSED + push)
Cursor    → this contract; report; review; IC only after ★ B1 (same session: named)
```

---

## 1. Why this investigation exists now

Mapping-path lock: Rooster seed **has** `wheelbase_mm` 230; live demo **frame card does not**. That was named a bind/projection hole, not missing KNOW.

Wrong next moves:

```text
instance motor_count=4 because the visor “looks empty”
draw a 230 mm line in Scene3D before the spec has the number
projector overlay from library.frames (second SoT)
silent refresh on Board load (catalog-refresh IC lock 6)
seed a fake plate L×W so the frame becomes a box
```

---

## 2. Questions the report must answer

1. Does `bind_frame_from_catalog("armattan_rooster_5in")` already project `wheelbase_mm` 230? Cite test if any.  
2. What are the **live** `frame` properties + `catalog_ref` on `workspace/autonomía-de-10min-9ada1a1b0cca/state.json`?  
3. Would `refresh_component_from_catalog(state, "frame")` add `wheelbase_mm` without touching `frame_plate*` children? Dry-run; **do not save in the report**.  
4. Does the projector invent wheelbase from the seed when ProjectState lacks it?  
5. Is there a **code** hole (binder / refresh / `_fields`) or only a **stale ProjectState** hole?  
6. Score leans: **B0** walk-only (`actualiza el frame`) · **B1** lock the refresh path with a regression test + live smoke · **B1+** visor overlay from catalog · **B2** Scene3D wheelbase glyph · **out** 4-motor copies.

---

## 3. Do not

Implement. Bump version. Instance `motor_count`. Auto-refresh on load. Un-QUEUE fit. Touch motor height 31.7 / plate L×W. Parse card `fields` as millimetres.
