# Engineer Lock — 3D mapping path (five rungs, do not lose)

**Date:** 2026-09-08  
**Authority:** Engineer (`Viuelvo con lo de antes` — solutions for 3D mapping; document then work)  
**Status:** ★ LOCKED — ordered queue. Item **1 CLOSED** @ **2462**. Item **2 first cut CLOSED** @ **2466** + smoke ACCEPT (`wheelbase_mm` on bound spec). 4-motor sketch later ★. Items 3–5 later ★. Fit still **QUEUED**.  
**Parents:**
- [engineer_lock_geometry_3d_placement_horizon.md](engineer_lock_geometry_3d_placement_horizon.md)
- [engineer_lock_geometry_pre_assembly_honesty.md](engineer_lock_geometry_pre_assembly_honesty.md) — R1/R2 **CLOSED** CLI; envelope ≠ reconstructed part
- Continuity pose B1 **CLOSED** @ **2456** — writer + IDLE; visor now reads pose (rung 1 CLOSED)
- CSS 3D B1 smoke: **1 ComponentSpec = 1 solid** (not 4 motor copies) until a later ★

**Not an IC. Do not implement items 2–5 in item 1.**

---

## Locked reading

The visor already draws **declared** envelopes. Rung 1 **CLOSED**: Scene3D reads `declared_box_pose` (one hop, CSS place). Visor chrome (2026-09-09): the solid cluster is centered in the 3D pane (AABB of wrappers → pane center), not pose. Rung **2 first cut CLOSED**: bound Rooster spec now carries cited `wheelbase_mm` 230 (refresh of stale ProjectState; card text). Next missing pieces are mapping rungs **2 remainder (4-motor sketch, later ★)** and **3–5**, not another visor DTO.

Two products (do not collapse):

| Product | Honest result |
|---|---|
| **A — racimo** | The 5 solids (3 boxes + 2 disks) sit in millimetre relation. Not a quadrotor. |
| **B — silueta quadrotor** | Needs wheelbase / instancing / or sourced plate L×W. Separate ★. |

If a manufacturer page is silent: other viewpoints (not “impossible”): visor instancing from `motor_count` + cited wheelbase · Engineer-**declared** plate L×W (`source=declared`) · STEP as visor-only never SoT · leave the gap.

---

## The five rungs (work queue)

### 1. Scene3D-from-pose — **CLOSED** @ **2462** + smoke ACCEPT

[IC](implementation_contract_geometry_scene3d_from_pose_b1.md) · [smoke](engineer_smoke_geometry_scene3d_from_pose_b1.md) **ACCEPT**.

Place **existing** solids that already have `geometry` (live demo today: 3 boxes + 1 disk; do not assume 5). Zero new catalog. `mounted_on` stays the **guide**, not millimetres. Disks stay flat. **Still 1 identity = 1 solid**. Row slots remain; posed nodes leave their slot. Do not invent 4 arms.

Product sentence after a later Buy:

```text
El sólido deja la fila y se coloca en mm respecto al centro de una caja
origen, ejes L→+X W→+Y H→+Z declarados. Aún no es el Rooster ni “cabe.”
```

### 2. Wheelbase on the spec + optional 4-motor sketch

**First cut CLOSED** @ **2466** + [smoke](engineer_smoke_geometry_wheelbase_on_spec_b1.md) **ACCEPT**. Rooster seed had `wheelbase_mm` 230; live demo frame was stale (mass / 5" / material only). Bind already projected; refresh applied it. Card shows `230 mm`. Frame still has **no** 3D solid.

**Remainder (later ★):** instance `motor_count=4` on an X of 230 mm, copy: “boceto de distancias, mismo SKU, no 4 nodos BOM.” That **reverses** CSS 3D B1 “one solid per spec” — allowed only as a named Buy.

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

Rung **1 CLOSED**. Rung **2 first cut CLOSED** (wheelbase on spec). Next = Engineer names 4-motor sketch ★ or rungs 3–5. Package `0.3.8` · suite **2466**.
