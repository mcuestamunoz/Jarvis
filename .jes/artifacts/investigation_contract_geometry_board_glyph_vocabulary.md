# Investigation Contract — Minimum Board Glyph Vocabulary (Geometry · visualizar B1)

**Project:** Jarvis  
**Date:** 2026-09-07  
**Author:** JES / Cursor (Engineer Interface)  
**Formulation:** Engineer (Geometry Progression Lock B1) — adopted as locked framing  
**Investigator:** Claude Code  
**Reviewer:** Cursor (Investigation Review)  
**Output (you write this):** `.jes/artifacts/investigation_report_geometry_board_glyph_vocabulary.md`

**Status:** OPEN — awaiting Claude report  
**Parents (mandatory):**
- [engineer_lock_geometry_spatial_representation_progression.md](engineer_lock_geometry_spatial_representation_progression.md) — ★ Geometry Progression Lock B1
- [engineer_lock_geometry_physical_representation_axis.md](engineer_lock_geometry_physical_representation_axis.md)
- Geometry `representar` CLOSED: Battery **2316** · Motor **2323** · ESC **2327** · FC **2332** · live suite **2336**
- Board: `ui/spatial-board/` + `workspace/spatial_board.py` + B3 slots @ **2310**

**Type:** Minimum visual vocabulary for **declarative visualization** on the Board.  
**Not** an Implementation Contract. **Do not implement.**

**Checkpoint base:** package **`0.3.8`** · suite **2336**

**Single objective (locked):**

> Determine the **minimum glyph vocabulary** needed to represent on the Board the physical components Jarvis already knows, using **only** dimensions that already exist or that can be declared with physical evidence — **without** introducing pose or spatial relations.

**You are Claude Code.** Write the report only. Cursor reviews. Engineer ★ locks Buy before any IC.

**Do not implement. Do not bump version. Do not weaken tests. Do not introduce position/orientation/`mounted_on`/fit/clearance/CAD/FEA. Do not invent missing dimensions. Do not create a second geometric SoT beside `ProjectState`. Do not claim glyph ≡ assembly or fabricability.**

---

## 0. Role split (do not invert)

```text
Engineer  → Geometry Progression Lock B1; this investigation
Cursor    → contract; review; IC only after ★
Claude    → investigation_report_geometry_board_glyph_vocabulary.md
Engineer ★ → Buy B1 glyphs / Defer / re-scope
```

---

## 1. Why this investigation exists

`Representar` put verified dims on cards as **text**. The Board canvas exists. Engineer wants the next **visible capability jump**:

```text
Sé qué componente es + sé qué volumen físico declarado ocupa
```

…without mixing in assembly or “cabe.”

Wrong:

```text
invent plate L×W · draw motor with guessed height · mounted_on · fit check · STEP
```

Right: closed glyph set + honest behavior when dims are insufficient.

---

## 2. Candidate family map (investigate; do not rubber-stamp)

Engineer starting table — **re-verify against live schema/seeds** and mark each row: **glyph-ready today** / **partial** / **blocked pending representar**.

| Family | Candidate glyph | Minimum data (intent) | Code reality to check |
|---|---|---|---|
| Motor | cylinder | diameter + height | `diameter_mm`, `stator_diameter_mm`, `stator_height_mm` exist on some SKUs; **overall axial height was rejected** in Motor B1 (EMAX vs SunnySky). Report must say which height (if any) may feed a cylinder glyph without resurrecting the rejected field. |
| Battery | box | L × W × H | `length_mm`/`width_mm`/`height_mm` on sourced rows |
| Propeller | disk | diameter | `diameter_in` (unit honesty vs mm canvas) |
| Plate | rectangle | L × W × thickness | Often **thickness only** today — L×W typically absent |
| Arm | bar / rectangle | L × W × thickness | Often **thickness only**; length often absent |
| ESC | box | L × W × H | One seeded SKU |
| Flight Controller | plate/box | L × W × H | Pixhawk 4 identity-linked 44×84×12 |

Leave **explicitly out** anything that requires a mounting interpretation.

---

## 3. Absence policy (locked question — report must choose default lean)

```text
dimensión verificada
      ↓
glyph específico

dimensión insuficiente
      ↓
glyph parcial / envelope incompleto  OR  no glyph
      ↓
NO inventar geometría
```

Absence of geometry must **never** silently become fictional geometry. Recommend one default for B1 and name alternatives.

---

## 4. Baseline to inventory (cite live tree)

| Surface | Check |
|---|---|
| Projector DTO | `project_spatial_nodes` — fields available to UI today |
| UI cards | `ui/spatial-board/` — where a glyph attaches without mutation / new SoT |
| Per-family dims | As in §2 table — cite `library.py` / seeds / `FLIGHT_CONTROLLER_DIMENSIONS` |
| Units | mm vs `diameter_in` on one canvas — honesty rule |
| Slots | B3 `kind: "slot"` must not grow fake geometry |

---

## 5. Governing questions

1. As-is Board path (`ProjectState` → DTO → React).  
2. Which families are **honestly glyph-ready today** with zero new dims?  
3. Closed vocabulary (`box` / `cylinder` / `disk` / `bar` / …) — minimum set for B1.  
4. Motor height / cylinder semantics given Motor B1’s rejection of overall axial height.  
5. Partial-dim policy (default lean).  
6. Smallest implementation shape: DTO hint from projector vs UI inference from existing `_fields` — trade-offs.  
7. Honesty matrix: “Board shows the drone,” “glyph = CAD,” “card layout = assembly,” “visualizar verifies fit.”  
8. Buy options: B0 docs-only · **B1 glyphs for ready families only** · B2+ pose/assembly · Defer.  
9. **Default lean** (required).

---

## 6. Out of scope

Pose · `mounted_on` · fit/clearance · STEP/STL/FEA · inventing plate/arm L×W · Control/sensors claim changes · Prop/Energy unlock · System Optimization · Conversation Engine · version bump · weakened tests · Board as write surface for engineering fields

---

## 7. Deliverable format

Write `.jes/artifacts/investigation_report_geometry_board_glyph_vocabulary.md`:

- **A.** Executive answer (≤15 lines)  
- **B.** As-is Board + dim inventory (glyph-ready / partial / blocked)  
- **C.** Minimum glyph vocabulary  
- **D.** Absence / partial-dim policy + default lean  
- **E.** Motor cylinder special case  
- **F.** Honesty / ladder matrix  
- **G.** Buy options + **default lean**  
- **H.** Non-goals for first visualizar IC  

No code. No version bump. No test changes.

---

## 8. Success criterion

Engineer can ★ **Buy B1** knowing which families light up with glyphs first, what happens when dims are missing, and that assembly/fit remain frozen — enabling the honest product sentence:

> “Sé qué componente es y sé qué volumen físico declarado ocupa.”
