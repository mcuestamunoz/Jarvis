# Investigation Contract — Geometry 3D placement horizon (first slice)

**Project:** Jarvis  
**Date:** 2026-09-08  
**Author:** JES / Cursor (Engineer Interface)  
**Formulation:** Engineer `procede` after ★ lock [engineer_lock_geometry_3d_placement_horizon.md](engineer_lock_geometry_3d_placement_horizon.md)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_geometry_3d_placement_horizon.md`

**Status:** INVESTIGATION REVIEWED — **PASS WITH NOTES** · ★ **B1− CLOSED** (suite **2429** + smoke ACCEPT) · 3D = [rendering-tech investigation](investigation_contract_geometry_3d_rendering_tech.md)  
**Parents:**
- [engineer_lock_geometry_3d_placement_horizon.md](engineer_lock_geometry_3d_placement_horizon.md) — ★ product horizon + queue (mandatory)
- [engineer_lock_geometry_spatial_representation_progression.md](engineer_lock_geometry_spatial_representation_progression.md)
- [engineer_lock_geometry_assembly_relation_rung_closed.md](engineer_lock_geometry_assembly_relation_rung_closed.md) — relation CLOSED; Conn walk ACCEPT
- Glyphs B1 CLOSED @ **2344** — `geometry: {box, disk}` via `_geometry_from_spec` → `SpatialGlyph.tsx`
- Geometry-for-all B1 CLOSED @ **2418** — sourced **text**; plates still no L×W; standoff height text on some SKUs
- Fit stub [implementation_contract_geometry_assembly_fit_compare.md](implementation_contract_geometry_assembly_fit_compare.md) — **QUEUED — DO NOT IMPLEMENT**
- Pose B1+ — **B0 DEFERRED** (no pose schema)

**Type:** Investigation only — minimum honest **first Buy** toward 3D solids at **declared** scale + click → today’s card.  
**Not** an Implementation Contract. **Do not implement.**  
**Not** pose / “colocar en su lugar”. **Not** `"cabe"` / fit. **Not** CAD/STEP/FEA. **Not** Conversation Engine. **Not** treating Board drag as pose.

**Checkpoint base:** package **`0.3.8`** · suite **2429**

**Single objective (locked):**

> Determine the **minimum honest path** from today’s cards + `mounted_on` edges + 2D glyphs toward **3D solids at declared scale** and **click → card**, without a second geometric SoT, without inventing envelopes, and without claiming pose or `"cabe"`.

**Product sentence this must enable (after a later Buy, not this investigation):**

```text
Veo el volumen declarado en 3D a escala; click abre la card de hoy; las uniones montado-en siguen siendo la guía — aún no está colocado ni “cabe.”
```

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ Buy before any IC.

**Do not implement. Do not bump version. Do not weaken tests. Do not add Three.js / r3f / meshes. Do not invent plate L×W, motor axial height, or Here3 footprint. Do not unfreeze Here3/Pixhawk. Do not open pose/fit ICs. Do not recommend reading `localStorage` x/y as physical pose.**

---

## 0. Role split

```text
Engineer  → 3D horizon lock; procede
Cursor    → this contract; review; IC only after ★
Claude    → investigation_report_geometry_3d_placement_horizon.md
Engineer ★ → Buy lean / Defer / re-scope
```

---

## 1. Why this investigation exists

The Engineer named the Board’s product horizon after the Conn walk:

```text
cards + edges today
  → 3D at scale (declared envelope)
  → click solid opens today’s card
  → later: place in physical location (mounted_on guides)
  → later: “cabe” must match that spatial situation
```

Glyphs already draw **2D** `box`/`disk` at a fixed mm→px scale (`SpatialGlyph.tsx`). Frame-part cards on the live demo often have **no glyph** (`thickness_mm` only). Drag is layout overlay, not placement.

Wrong next moves without evidence:

- Drop in a 3D engine and fake boxes for plates/arms
- Treat card stack / `localStorage` as the 3D pose
- Jump to `"cabe"` because solids “look assembled”
- Reopen Geometry-for-all to invent plate footprints
- Stitch motor `diameter_mm` + `stator_height_mm` into a cylinder (glyph B1 already rejected)

Right: prove what can be a **honest 3D extrusion/solid of existing `geometry` DTO**, what stays absent, and whether click-inspect is a visor-only Buy.

---

## 2. Locked stances

1. Board remains a **projection of `ProjectState`**. No second geometric model of record.  
2. 3D uses the **same fuel as glyphs**: `_geometry_from_spec` box (full L×W×H) or disk (one diameter). Absence = no solid.  
3. `mounted_on` is the placement **guide** (already shipped). Do not invent frame-internal joints or infer from card proximity.  
4. `parent_key="frame"` stays BOM composition — not a 3D edge unless the report argues a **separate** presentation Buy (likely **out** of first slice).  
5. Pose / place-in-space / `"cabe"` are **later rungs**. Name them; do not Buy them here.  
6. Click → card is **UI on the visor**, not a writer/Continuity change.  
7. Here3 / Pixhawk identity **FROZEN**.  
8. Fit stub stays QUEUED.

---

## 3. Baseline to inventory (cite live tree)

Re-verify; do **not** rubber-stamp prior reports.

| Surface | Check |
|---|---|
| Demo `workspace/autonomía-de-10min-9ada1a1b0cca/state.json` | Which keys have glyph-ready dims vs thickness/material only |
| `spatial_board._geometry_from_spec` + `project_spatial_nodes` | Exact DTO `geometry` / `mountedOn` / `kind` |
| `ui/spatial-board/src/SpatialGlyph.tsx` + `constants.ts` mm→px | How 2D scale works; collision with card `width`/`height` pixels |
| `SpatialCard.tsx` / click / selection | Is the card already the inspect surface? What would “click solid → open card” add vs today? |
| Glyph B1 report §A–B | Motor cylinder still dishonest? box/disk still the only honest shapes? |
| Geometry-for-all B1 report | Plate L×W still unsourced? Standoff height text vs still no solid |
| `DeclaredMountEdges` | Edges are card-rect presentation — implication for 3D (still not pose) |

Live demo snapshot (Engineer Board 2026-09-08 — **re-confirm in code**):

| Key | Glyph today (expected) | Notes |
|---|---|---|
| motors / propellers | disk | Ø from `diameter_mm` / `diameter_in` |
| battery / esc / FC | box | L×W×H |
| frame root / arm / plates / cage / standoff | none or text-only | thickness / material / size_class — **not** box |
| sensors Here3 | none | identity freeze |

---

## 4. Questions the report must answer

These are the lock’s six questions. Answer with file:line / live DTO evidence.

### 1 — Glyph fuel → 3D without new KNOW

Which live families can appear as 3D **only** by rendering the existing `geometry` object (e.g. box → rectangular prism, disk → flat disk or thin cylinder **only if** that does not invent height)? List keys on the demo.

Motor: confirm cylinder still **forbidden** unless new sourced axial height exists (expect: still forbidden).

### 2 — Frame parts: envelope KNOW first vs 3D-only-for-ready families

Lean must choose:

- **3D first** only for families that already emit `geometry`, frame parts stay text cards; **or**
- **Envelope KNOW first** for plates/arms (only if **sourced** L×W or equivalent appeared since G B1 — if still unsourced, **reject** KNOW-first as this Buy).

Do not recommend inventing Main Plate 150×150.

### 3 — Visor = projection

How would a 3D view consume `geometry` without a parallel mesh store? Name the existing pipeline (`project_spatial_nodes` → `/api/projects/:id/nodes` → React). Any 3D library is a **contingency sketch**, not a Buy of a new SoT.

### 4 — Click opens card

What exists today (fields always on `SpatialCard`)? Gap: inspect overlay / hide fields until click / 3D object pick? Keep mutation off the Board (CLI remains I/O).

### 5 — `mounted_on` as guide

In a 3D-first slice, edges still mean **declared relation**, not fastener pose. Do not place ESC “on” the plate in mm.

### 6 — Later rungs (name only)

Write the later sequence explicitly: pose (place solids; drag-as-layout still not pose) → `"cabe"` vs that situation. Point at the fit stub. **Do not** un-QUEUE it.

---

## 5. Minimum Buy options (must include)

| Option | Intent |
|---|---|
| **B0 — Defer** | 3D is premature; 2D glyphs + cards + edges already match the first visualizable sentence; wait for envelope KNOW or pain |
| **B1 — 3D visor for existing `geometry` DTO + click-inspect** | Project box/disk to 3D solids at the same declared scale; no-geometry cards stay as today; click picks a node and shows today’s card; **no pose, no cabe, no new dims** |
| **B1− — Click-inspect only** | No 3D yet; visor UX only |
| **B2 — Frame-part envelope KNOW** | Only if live sources now state plate L×W (or honest equivalent). Else **reject** inside this contract |

Reject: CAD import, inferred joints, motor cylinder from stator height, `"cabe"` from overlapping cards, Board-layout-as-pose.

---

## 6. Report format (mandatory sections)

1. **Executive recommendation** — one lean (B0 / B1 / B1− / B2) + one sentence.  
2. **Live glyph/3D-fuel matrix** — demo keys.  
3. **Visor as-is** — glyph renderer, click, edges, layout overlay.  
4. **Buy options** — costs, honesty risks, rejection of invention.  
5. **Contingency sketch** (if lean ≠ B0) — DTO reuse, UI surface, tests; **not** an IC.  
6. **Later rungs** — pose / cabe named, not bought.  
7. **Explicit non-goals honored.**

---

## 7. Done criteria (investigation)

- [ ] Live demo + `_geometry_from_spec` + `SpatialGlyph` cited  
- [ ] Frame-part / motor-cylinder honesty settled (no invention)  
- [ ] Click→card gap described vs current card UI  
- [ ] Clear lean; B0 allowed  
- [ ] No code; no 3D library added; no pose/fit IC  

---

## 8. Stop conditions

Stop and ask before: proposing fabricated envelopes, recommending STEP/mesh as SoT, unfreezing Here3, or bundling pose/`cabe` into the first IC.
