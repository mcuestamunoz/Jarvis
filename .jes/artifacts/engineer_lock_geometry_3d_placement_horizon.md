# Engineer Lock — Geometry 3D placement horizon (Board)

**Date:** 2026-09-08  
**Authority:** Engineer (vision after Conn walk ACCEPT + Board review)  
**Status:** ★ LOCKED — visualizar + Continuity place **SHIPPED**. Product feature: [Continuity spatial assembly](engineer_lock_continuity_spatial_assembly_feature.md). Next = arms X / loose / sourced dims.  
**Parents:**
- [engineer_lock_geometry_physical_representation_axis.md](engineer_lock_geometry_physical_representation_axis.md)
- [engineer_lock_geometry_spatial_representation_progression.md](engineer_lock_geometry_spatial_representation_progression.md)
- [engineer_lock_geometry_assembly_relation_rung_closed.md](engineer_lock_geometry_assembly_relation_rung_closed.md) — relation CLOSED; demo mounts walked
- Fit stub still [implementation_contract_geometry_assembly_fit_compare.md](implementation_contract_geometry_assembly_fit_compare.md) — **QUEUED — DO NOT IMPLEMENT**

---

## Locked product horizon

Keep **today’s Board** (cards + declared `mounted_on` edges). The horizon below is **largely landed** as Continuity spatial assembly — see [feature lock](engineer_lock_continuity_spatial_assembly_feature.md). Remaining work is completeness (arms X, loose parts, sourced dims), not inventing the placement idea.

1. **3D at scale** — ✅ CSS 3D solids from declared/cited envelopes. Not CAD.
2. **Click a solid → today’s card** — ✅
3. **Place in space** — ✅ Continuity pose + multi-hop + Main Plate assembly root; `mounted_on` remains guide only.
4. **Later `"cabe"`** — B1-min screening ✅; full VERIFIED fit still QUEUED.

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

**Next artifact:** [3D mapping path](engineer_lock_geometry_3d_mapping_path.md) — rung 2 first cut **CLOSED**; 4-motor sketch later ★. Fit QUEUED.

---

## Explicit non-goals until later ★

Implementing 3D theater without envelope KNOW · treating drag as pose · `"cabe"` from card overlap · CAD/STEP/FEA · Conversation Engine · unfreezing the fit stub as default next · frame-part Continuity **subjects** · version bump without Engineer ask

---

## Mode

**Visualizar-3D CLOSED.** Continuity pose CLOSED @ **2456**. Scene3D-from-pose CLOSED @ **2462**. Wheelbase-on-spec first cut CLOSED @ **2466**. Package `0.3.8`.
