# Engineer Lock — Geometry 3D placement horizon (Board)

**Date:** 2026-09-08  
**Authority:** Engineer (vision after Conn walk ACCEPT + Board review)  
**Status:** ★ LOCKED — visualizar-3D **CLOSED**; Continuity pose B1 **CLOSED** @ **2456**; demo reds R1/R2 **CLOSED**; next queue = [mapping path](engineer_lock_geometry_3d_mapping_path.md)  
**Parents:**
- [engineer_lock_geometry_physical_representation_axis.md](engineer_lock_geometry_physical_representation_axis.md)
- [engineer_lock_geometry_spatial_representation_progression.md](engineer_lock_geometry_spatial_representation_progression.md)
- [engineer_lock_geometry_assembly_relation_rung_closed.md](engineer_lock_geometry_assembly_relation_rung_closed.md) — relation CLOSED; demo mounts walked
- Fit stub still [implementation_contract_geometry_assembly_fit_compare.md](implementation_contract_geometry_assembly_fit_compare.md) — **QUEUED — DO NOT IMPLEMENT**

---

## Locked product horizon

Keep **today’s Board** (cards + declared `mounted_on` edges). Evolve it, in order, to:

1. **3D at scale** — a three-dimensional image of each component/part from **already declared** physical envelope (the same fuel glyphs use today). Not CAD. Not a second model of record.
2. **Click a solid → today’s card** — identity, numbers, `"montado en"`. The card remains the inspect surface.
3. **Place in space** — move pieces to their physical location. Declared **connections guide** placement (`mounted_on` graph already shipped). Board drag/`localStorage` layout is **not** that placement.
4. **Later `"cabe"`** must be checked against that **spatial situation**, not against card-lane overlap.

Do **not** flatten the Geometry ladder. This horizon **is** the ladder, named in product language:

```text
KNOW / representar     → declared envelopes (L×W×H or diameter)
visualizar             → 2D glyph today → 3D solid at scale
relación (mounted_on)  → guide for placement   ← ★ CLOSED as relation
pose                   → put the solid in place
comparar (“cabe”)      → verify against that situation
```

**Still forbidden as a jump:** KNOW → VERIFICADO / fit PASS / FEA / “ensamblado”.

---

## As-is (do not relabel)

| Today | Honest reading |
|---|---|
| Cards + `mounted_on` text + B2 edges | Declared assembly **relation** |
| 2D glyph | Only if `_geometry_from_spec` has full box or diameter |
| Frame parts in demo (mostly `thickness_mm`) | **No glyph** — insufficient envelope, not a visor theme |
| `parent_key="frame"` | BOM composition; **no** Board edge |
| Drag / `localStorage` | Presentation layout — **not** pose |

---

## Next work queue (PRIORIDAD)

**Next artifact:** [3D mapping path](engineer_lock_geometry_3d_mapping_path.md) — rung 1 Scene3D-from-pose investigation next. Fit QUEUED.

---

## Explicit non-goals until later ★

Implementing 3D theater without envelope KNOW · treating drag as pose · `"cabe"` from card overlap · CAD/STEP/FEA · Conversation Engine · unfreezing the fit stub as default next · frame-part Continuity **subjects** · version bump without Engineer ask

---

## Mode

**Visualizar-3D CLOSED.** Continuity pose CLOSED @ **2456**. Mapping path **LOCKED** (5 rungs). Package `0.3.8`.
