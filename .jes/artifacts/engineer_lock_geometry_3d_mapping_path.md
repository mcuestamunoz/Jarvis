# Engineer Lock — 3D mapping path (five rungs, do not lose)

**Date:** 2026-09-08  
**Authority:** Engineer (`Viuelvo con lo de antes` — solutions for 3D mapping; document then work)  
**Status:** ★ LOCKED — ordered queue. Items **1–3 CLOSED**. Rung **4 B0**. Kit / adapter / SKUs D **CLOSED**. `"cabe"` B1-min **CLOSED**.  
**Parents:**
- [engineer_lock_geometry_3d_placement_horizon.md](engineer_lock_geometry_3d_placement_horizon.md)
- [engineer_lock_geometry_pre_assembly_honesty.md](engineer_lock_geometry_pre_assembly_honesty.md) — R1/R2 **CLOSED** CLI; envelope ≠ reconstructed part
- Continuity pose B1 **CLOSED** @ **2456** — writer + IDLE; visor now reads pose (rung 1 CLOSED)
- CSS 3D B1 smoke: **1 ComponentSpec = 1 solid** (not 4 motor copies) until a later ★

**Not an IC. Do not implement items 2–5 in item 1.**

---

## Locked reading

The visor already draws **declared** envelopes. Rungs 1–3 **CLOSED**. Rung 4 **B0**. Kit template **B1-min CLOSED**. Rooster Included plates **B2 CLOSED**. Prop adapter ask **CLOSED** + ACCEPT ([smoke](engineer_smoke_kit_prop_adapter_ask_b1.md)). `"cabe"` investigation **OPEN** ([contract](investigation_contract_geometry_assembly_fit_cabe_b0.md)).

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

**Remainder CLOSED** @ **2473** + [smoke](engineer_smoke_geometry_motor_count_instances_b1.md) **ACCEPT**. Visor copies, N = `components.motors.motor_count` (live demo **3**, `calculated`). Same SKU, not N BOM nodes. **Not** default 4. **Not** quad-X of 230. Live SunnySky has **no** Ø → still zero motor solids until a later envelope ★.

### 3. Motor `height_mm` 31.7 cited — **CLOSED** @ **2480** + smoke ACCEPT

[IC](implementation_contract_geometry_motor_height_cited_b1.md) · [smoke](engineer_smoke_geometry_motor_height_cited_b1.md) **ACCEPT**. EMAX card `31.7 mm`; disk stays disk.

### 3b. Propeller cited envelope — **CLOSED** @ **2489** + smoke ACCEPT

[IC](implementation_contract_geometry_propeller_envelope_b0_b1.md) · [smoke](engineer_smoke_geometry_propeller_envelope_b0_b1.md) **ACCEPT**. Unsourced grams omitted. `gf_5045x3` bag in catalog. Live HBN still Ø-only.

### 3c. Propeller cited seeds B2 — **REVIEWED** @ **2497** (Engineer smoke)

[IC](implementation_contract_geometry_propeller_cited_seeds_b2.md) · [review](implementation_review_geometry_propeller_cited_seeds_b2.md) **PASS WITH NOTES**. Cyclone + `apc_10x6_ep`. GetFPV URL kept; implementer hit 403 and cross-checked (N1).

### 4. Plate L×W sourced search (GetFPV vs Armattan) — **REVIEWED B0** @ 2026-09-09

[Review](investigation_review_geometry_plate_lw_sourced_b1.md) **PASS WITH NOTES**. Rooster: **no** cited footprint. Gap holds. No wheelbase-as-box. Optional text plates / Engineer-declared L×W = later ★. [Kit-template frontier](engineer_lock_assembly_kit_template.md) is a **different** product (novice assemble list), not this rung.

### 5. `"cabe"` last — **CLOSED** @ **2540** + smoke ACCEPT

[Smoke](engineer_smoke_geometry_assembly_fit_cabe_b1.md) **ACCEPT**. Stub [fit IC](implementation_contract_geometry_assembly_fit_compare.md) remains historical.

---

## Explicitly not this queue’s first cut

Full catalog refresh · Here3 unfreeze · battery L/W/H remap · `istand` · STEP in core · Three.js unless investigation 1 proves CSS 3D cannot place · Conversation Engine

---

## Mode

Rung **1–3 CLOSED**. Rung 4 **B0**. `"cabe"` investigation OPEN. Package `0.3.8` · suite **2532**.
