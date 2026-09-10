# Investigation Contract — `"cabe"` / fit vs spatial situation (mapping rung 5)

**Project:** Jarvis  
**Date:** 2026-09-09  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_geometry_assembly_fit_cabe_b0.md`

**Status:** INVESTIGATION REVIEWED — PASS WITH NOTES · Engineer ★ **B1-min** · IC [implementation_contract_geometry_assembly_fit_cabe_b1.md](implementation_contract_geometry_assembly_fit_cabe_b1.md)  
**Parents:**
- Engineer ★ **rung 5** (2026-09-09) after Kit SKUs D **CLOSED** + ACCEPT
- [engineer_lock_geometry_3d_mapping_path.md](engineer_lock_geometry_3d_mapping_path.md) §5 — compare against a **spatial situation**, never card-lane overlap
- [engineer_lock_geometry_3d_placement_horizon.md](engineer_lock_geometry_3d_placement_horizon.md) — `"cabe"` last; KNOW → VERIFICADO still forbidden
- [implementation_contract_geometry_assembly_fit_compare.md](implementation_contract_geometry_assembly_fit_compare.md) — **QUEUED stub**; **do not implement that file**. This investigation is the gate it named
- Pose writer **CLOSED** @ **2456** · Scene3D-from-pose **CLOSED** @ **2462**
- Plate L×W **B0** — Rooster still has **no** frame box
- Kit B1-min / adapter / SKUs D **CLOSED** — **out** (no kit geometry, no `current_a`)
- Frame class compatibility (Ø vs `size_class_inch`) is **LEVEL A screening** — already shipped; it is **not** `"cabe"`

**Type:** Minimum honest **comparar/verificar** investigation.  
**Not** an IC. **Do not implement. Do not add a fit engine. Do not bump version. Do not invent millimetres.**

**Checkpoint:** package **`0.3.8`** · suite **2532**

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ locks Buy before any IC.

---

## 0. Role split

```text
Engineer  → “cabe” against the spatial situation, not card overlap
Cursor    → this contract; review; IC only after ★ on Buy shape
Claude    → investigation_report_geometry_assembly_fit_cabe_b0.md
```

---

## 1. Why this exists

The 3D horizon is:

```text
KNOW / representar  → visualizar  → mounted_on  → pose  → comparar (“cabe”)
```

Rungs 1–3 **CLOSED**. Rung 4 **B0** (no sourced Rooster footprint). The queued fit stub is **not** a READY IC: it was written when pose was still deferred.

Wrong next step:

```text
AABB de las cards en el Board (drag / localStorage)
· “cabe” / “no cabe” / VERIFIED / fit PASS
· FEA · STEP-in-core · cilindro
· inventar L×W del Rooster para tener un sólido contra el que caber
· tratar Ø-hélice vs size_class como si ya fuera este Buy
· Conversation Engine · System Optimization
```

Right question:

> On the **live tree + live demo**, what spatial situation actually exists (which identities have envelope **and** a machine `declaredBoxPose`)? What is the **minimum honest first Buy** — including **B0 leave the gap** — that compares against that situation without claiming CAD fit?

---

## 2. Locked stances

1. **Situation, not lanes.** Fit (if any) reads posed solids (`declaredBoxPose` + `_geometry_from_spec`), never Board CSS card order, never `localStorage` layout.  
2. **Fail closed.** Missing envelope, missing origin box, incomplete pose (e.g. only `x_mm`), disk vs box, or `mounted_on` without pose → **no** “cabe” / “no cabe”. Honest absence / screening copy only.  
3. **Never VERIFIED.** Forbidden strings in product copy and gap titles: `cabe`, `no cabe`, `VERIFIED`, `misfit geométrico`, `ensamblado`. Existing `project_closure` / `engineering_readiness` / Continuity bans stay. A first Buy may add **screening** language (“solapamiento de sobres no comprobado”) — it must **not** flip `ASSEMBLY_READY` or Structure/Propulsion PASS.  
4. **Frame class ≠ this Buy.** `GAP-FRAME-PROP-SIZE` / LEVEL A is Ø vs declared inch class. Do not merge, replace, or relabel it as geometric fit.  
5. **Rooster has no box.** Do not propose stitching `wheelbase_mm` + thickness into a prism so something can “fit in the frame.” Plate L×W B0 holds.  
6. **Disk stays disk.** Ø+height is **not** a cylinder. Do not recommend propeller/motor as the first AABB pair unless you prove both are **boxes** with pose. Prefer box–box if a pair exists.  
7. **Kit SKUs have no geometry.** Connector/harness/adapter are identity. Out.  
8. **One pair or B0.** Do not design a generic collision engine, octree, or “all mounted_on edges.” Name **at most one** concrete compare (two keys + what numbers) or recommend B0.  
9. **No version bump. No `ui/` theater** (new Three.js, new badge chrome) unless the Buy is “surface an already-computed screening fact on the existing card” — and even that waits for the IC.  
10. Reuse Continuity / Board fields / CLI refuse. **No** Conversation Engine.

---

## 3. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| `_geometry_from_spec` / `project_spatial_nodes` | Who gets a solid today; slots vs posed nodes |
| `_declared_box_pose_dto` | Gate: origin must itself have geometry; which axes required |
| `ComponentSpec.declared_box_pose` / Continuity pose writer | What CLI can already declare |
| Live demo (`autonomía-de-5min` and/or `autonomía-de-10min` if readable) | Table: key × envelope (box/disk/none) × `mounted_on` × pose DTO yes/no × Board solid yes/no |
| Frame `armattan_rooster_5in` | Confirm still **no** box (rung 4 B0) |
| `engineering_readiness._frame_class_gaps` + Continuity copy | Quote the existing “never cabe” ban |
| Queued stub IC | One paragraph: what it asked vs what is now true post-pose |

Do **not** mutate `workspace/`. Read-only.

---

## 4. Report sections (required)

### A. Spatial situation as-is

Table of live identities. Count how many **posed box–box pairs** exist (child box + origin box + DTO). If **zero**, say so in one sentence — that is evidence for B0, not a bug to “fix” with invented mm.

### B. What “comparar” could mean without CAD

At most three mechanics, each fail-closed:

| Mechanic | Inputs | Honest output | Forbidden output |
|---|---|---|---|
| e.g. AABB overlap of two posed boxes | … | screening fact | cabe / VERIFIED |

Do **not** recommend disk–box or cylinder.

### C. Honest Buys (ranked)

Recommend **exactly one**:

| ★ | Meaning |
|---|---|
| **`B0`** | Leave the gap. Not enough situation (or first compare would be theater). No IC. |
| **`B1-min`** | One named box–box screening on an **existing** posed pair; copy never VERIFIED; PASS/hover/`ASSEMBLY_READY` byte-identical. |
| **`B1-copy`** | CLI/Continuity **refuse or honest absence** for “¿cabe?” — no geometry math this Buy. |

You may list **parked** B2+ (clearance mm, Continuity HIGH, frame-in-silhouette) as **out**.

### D. Out of scope (explicit)

Invent Rooster L×W · card-lane overlap · FEA · STEP · cylinder · kit SKU boxes · GetFPV crawl · Conversation Engine · unfreezing the 2026-09-07 stub as-is.

---

## 5. Done when

- [ ] Report written; live demo table filled (or explicit “workspace unreadable”)  
- [ ] No `src/` / `ui/` / library edit in this investigation  
- [ ] Single recommended next Buy (`B0` / `B1-min` / `B1-copy`)  
- [ ] Queued stub IC is **not** treated as READY

---

## Explicitly not this investigation

Implement intersection · seed plate L×W · relabel class-compatibility as fit · version bump
