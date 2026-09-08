# Engineer Lock — 3D mapping path (five rungs, do not lose)

**Date:** 2026-09-08  
**Authority:** Engineer (`Viuelvo con lo de antes` — solutions for 3D mapping; document then work)  
**Status:** ★ LOCKED — ordered queue. Item **1** is next investigation. Items 2–5 are named later ★. Fit still **QUEUED**.  
**Parents:**
- [engineer_lock_geometry_3d_placement_horizon.md](engineer_lock_geometry_3d_placement_horizon.md)
- [engineer_lock_geometry_pre_assembly_honesty.md](engineer_lock_geometry_pre_assembly_honesty.md) — R1/R2 **CLOSED** CLI; envelope ≠ reconstructed part
- Continuity pose B1 **CLOSED** @ **2456** — writer + IDLE; visor still `layoutSolidsRow`
- CSS 3D B1 smoke: **1 ComponentSpec = 1 solid** (not 4 motor copies) until a later ★

**Not an IC. Do not implement items 2–5 in item 1.**

---

## Locked reading

The visor already draws **declared** envelopes. Catalog dump is **not** the first missing piece. The first missing piece is: **Scene3D does not read `declared_box_pose`.**

Two products (do not collapse):

| Product | Honest result |
|---|---|
| **A — racimo** | The 5 solids (3 boxes + 2 disks) sit in millimetre relation. Not a quadrotor. |
| **B — silueta quadrotor** | Needs wheelbase / instancing / or sourced plate L×W. Separate ★. |

If a manufacturer page is silent: other viewpoints (not “impossible”): visor instancing from `motor_count` + cited wheelbase · Engineer-**declared** plate L×W (`source=declared`) · STEP as visor-only never SoT · leave the gap.

---

## The five rungs (work queue)

### 1. Scene3D-from-pose — **NEXT** (investigation, then ★, then IC)

Place the **existing** 5 solids using `declared_box_pose` (Continuity already writes it). Zero new catalog. `mounted_on` stays the **guide**, not millimetres. Disks stay flat. **Still 1 motor / 1 propeller solid** (identity). Row layout is replaced **only** for nodes that participate in a declared pose graph; do not invent 4 arms.

Product sentence after a later Buy:

```text
El sólido deja la fila y se coloca en mm respecto al centro de una caja
origen, ejes L→+X W→+Y H→+Z declarados. Aún no es el Rooster ni “cabe.”
```

### 2. Wheelbase on the spec + optional 4-motor sketch

Rooster seed **has** `wheelbase_mm` 230 (Armattan motor-to-motor). Live demo **frame card does not** (only mass / 5" / material) — bind/projection hole, not missing KNOW in the library file.

Path: project `wheelbase_mm` onto the bound frame spec. Then a **separate ★** may instance `motor_count=4` on an X of 230 mm, copy: “boceto de distancias, mismo SKU, no 4 nodos BOM.” That **reverses** CSS 3D B1 “one solid per spec” — allowed only as a named Buy, not smuggled into rung 1.

### 3. Motor `height_mm` 31.7 cited

EMAX `source_note` already quotes Motor Height 31.7 mm and excludes it from the seed (not comparable to SunnySky Body Length). Optional ★: seed `height_mm` as **cited**. **No** cylinder (Ø+height stitch) until a shape investigation.

### 4. Plate L×W sourced search (GetFPV vs Armattan)

Class A envelope for frame parts. Investigation: classify sources; seed only what a page **affirms**. Armattan page used for the seed had **no** plate L×W. GetFPV kit extras are a **different** source. No scrape-in-product. No invented Main Plate 150×150.

### 5. `"cabe"` last

Fit stub stays **QUEUED**. Compare against a **spatial situation** (after 1, and whatever of 2–4 shipped), never card-lane overlap.

---

## Explicitly not this queue’s first cut

Full catalog refresh · Here3 unfreeze · battery L/W/H remap · `istand` · STEP in core · Three.js unless investigation 1 proves CSS 3D cannot place · Conversation Engine

---

## Mode

Rung **1** investigation next. Package `0.3.8` · suite **2456**.
