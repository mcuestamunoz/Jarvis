# Investigation Contract — Geometry Assembly Espacial B1 (minimum pose / `mounted_on`)

**Project:** Jarvis  
**Date:** 2026-09-07  
**Author:** JES / Cursor (Engineer Interface)  
**Formulation:** Engineer ★ — next after catalog hygiene close: option **A** (Geometry progression)  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_geometry_assembly_espacial_b1.md`

**Status:** OPEN — awaiting report  
**Parents (mandatory):**
- [engineer_lock_geometry_spatial_representation_progression.md](engineer_lock_geometry_spatial_representation_progression.md) — ★ Progression Lock (dims → glyphs → **pose / assembly** → fit)
- [engineer_lock_geometry_physical_representation_axis.md](engineer_lock_geometry_physical_representation_axis.md)
- Board glyphs B1 CLOSED @ suite **2344** — [implementation_review_geometry_board_glyphs_b1.md](implementation_review_geometry_board_glyphs_b1.md)
- Catalog hygiene CLOSED @ suite **2350** — ESC mass + motor thrust not intrinsic (orthogonal; do not reopen)
- Structure B parts graph CLOSED — parent/child frame parts exist; **not** spatial pose
- Board: `ui/spatial-board/` + `workspace/spatial_board.py` (card layout ≠ physical pose)

**Type:** Minimum **assembly espacial** capability after `visualizar` — what pose / attachment relation may exist **without** claiming fit.  
**Not** an Implementation Contract. **Do not implement.**

**Checkpoint base:** package **`0.3.8`** · suite **2350**

**Single objective (locked):**

> Determine the **minimum honest model** for “where / how a declared component sits relative to another” on Jarvis’s Geometry ladder — enough to support a first **assembly espacial** Buy — **without** clearance, intersection, “cabe”, CAD, or treating Board card drag positions as physical truth.

**Product sentence this rung must enable (honest):**

```text
Sé qué es + qué volumen declarado ocupa + (mínimo) a qué se declara montado / con qué pose declarada
```

**Not:**

```text
Cabe · no choca · ensamblado verificado · el layout del Board es la geometría del drone
```

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ locks Buy before any IC.

**Do not implement. Do not bump version. Do not weaken tests. Do not open fit/clearance/intersection/CAD/FEA/MEASURE. Do not invent mount patterns or mm offsets without a cited source or an explicit “declared by user / unknown” honesty path. Do not make Board `localStorage` layout the geometric SoT. Do not reopen ESC mass, motor thrust H2/H3, Here3/Pixhawk variant, or HD-004. Do not claim pose ≡ verification.**

---

## 0. Role split (do not invert)

```text
Engineer  → chose option A after hygiene close
Cursor    → this contract; review; IC only after ★
Claude    → investigation_report_geometry_assembly_espacial_b1.md
Engineer ★ → Buy B1 assembly / Defer / re-scope (e.g. relation-only vs pose+relation)
```

---

## 1. Why this investigation exists

Shipped:

| Rung | Status |
|---|---|
| KNOW / representar (dims) | Battery · Motor · ESC · FC |
| visualizar (glyphs `{box,disk}`) | CLOSED @ **2344** |
| Catalog hygiene (variant ↔ number; thrust ↔ condition) | CLOSED @ **2350** |

Progression Lock next rung: **ASSEMBLY ESPACIAL** (`pose` + `mounted_on`) — **later ★**, now opened for investigation only.

Wrong next step:

```text
drag cards = pose · auto-stack ESC under FC · fit check · STEP · invent arm motor mount coords
```

Right question:

> What is the **smallest durable relation + optional pose bag** that lives in `ProjectState` (or an honest overlay of it), projects to Board without becoming a second SoT, and never implies “fits”?

---

## 2. Locked stances (inherit)

1. Board remains a **projection** of `ProjectState` — card x/y/width/height (pixels / layout) ≠ physical pose.
2. Glyphs stay envelope-only; assembly must not overload glyph drawing into false CAD.
3. Structure parts graph (`parent_key`, plates/arms) is **identity/topology of frame BOM**, not spatial assembly of propulsion/electronics — report must say reuse vs diverge.
4. No fit / clearance / collision / “cabe” in any recommended Buy.
5. Prefer **declared** relations (user or catalog-sourced when evidence exists) over invented engineering defaults.
6. Catalog hygiene closed; do not expand this investigation into more mass/thrust seed edits.

---

## 3. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| `ComponentSpec` / `ProjectState` | Any existing pose, mount, parent, attachment fields beyond Structure `parent_key`? |
| Structure parts graph | What `parent_key` means today; can it carry motor→arm or only frame parts? |
| `spatial_board.py` + UI layout | Confirm layout overlay is non-authoritative for physics |
| Glyphs | What assembly would need from `geometry` (if anything) |
| Continuity / CLI | Any “montado en” / mount language already? |
| Prior locks / ICs | Quotes forbidding pose in glyph B1 — still binding |

---

## 4. Governing questions the report must answer

### Know

1. As-is: zero vs partial assembly spatial state in schema, Structure graph, Board.
2. What **cannot** be reused from Structure `parent_key` without lying (e.g. motor “child of” arm as BOM vs spatial mount).
3. What Board layout already stores that engineers might **mistakenly** treat as pose — honesty matrix.

### Claim — minimum assembly model

4. Field bag candidates (accept/reject with evidence):
   - `mounted_on` (component key / part key / slot id?)
   - pose: position (mm? frame frame?), orientation (enum vs quaternion?), “face” / “side”
   - “declared unknown” / absent honesty
5. Which families can honestly participate in B1 (e.g. FC on plate, ESC on plate, battery tray, motor on arm) vs blocked pending more KNOW.
6. Source rules: user declaration only vs catalog mount pattern vs never invent.

### Honesty / ladder

7. Phrase matrix: “montado en,” “pose declarada,” “Board position = pose,” “ensamblado,” “cabe,” “glyph proves mount.”
8. Ladder rung of recommended Buy: still **assembly espacial**, not comparar/verificar.

### Buy shape

9. Rank:
   - **B0** doc-only / defer
   - **B1** relation-only (`mounted_on` declared, no numeric pose)
   - **B1+** relation + minimal pose bag (define exact fields)
   - **B2** Board visualization of relations (edges/labels) without fit
   - **Defer** full pose / multi-body
10. **Default lean** (required) — smallest Buy that makes the product sentence true without fit theater.

---

## 5. Out of scope

- Fit / clearance / intersection / MEASURE / CAD / FEA  
- Treating Board drag layout as physical SoT  
- Auto-layout “pretty assembly” from physics  
- Here3 / Pixhawk variant · ESC mass reopen · thrust H2/H3  
- HD-004 · System Optimization · Conversation Engine  
- Version bump · weakening tests · inventing mount mm  

---

## 6. Deliverable format

Write `.jes/artifacts/investigation_report_geometry_assembly_espacial_b1.md` with:

- **A.** Executive answer (≤15 lines)  
- **B.** As-is inventory (schema / Structure / Board / glyphs)  
- **C.** Reuse vs diverge from Structure `parent_key`  
- **D.** Minimum field bag + source rules  
- **E.** Honesty / ladder matrix  
- **F.** Buy options + **default lean**  
- **G.** Non-goals for the first assembly IC  

No code. No version bump. No test changes.

---

## 7. Success criterion

Engineer can ★ **Buy B1** (relation-only vs relation+pose vs defer) knowing exactly what lands in `ProjectState`, what Board may show, and what remains forbidden (fit / layout-as-truth) — without licensing CAD theater.
