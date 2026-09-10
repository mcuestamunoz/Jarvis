# Engineer note — Board drag / resize as situar input (concept)

**Date:** 2026-09-10  
**Authority:** Engineer — “piezas sueltas + arrastrar y ampliar → guardar posición → distancias”  
**Status:** CONCEPT — not an IC · not PRIORIDAD code until ★ investigation  
**Parents:** [Continuity spatial assembly feature](engineer_lock_continuity_spatial_assembly_feature.md) · Board B1 layout-on-disk debt · declared pose/envelope writers

---

## The insight

Typing Δx/Δy/Δz (and even L×W×H) is hard for humans; an AI assistant can invent numbers too easily.  
**Better path:** pieces start “loose” on the Board; the Engineer **drags** (pose) and **resizes** (envelope); Jarvis **persists** those millimetres into `ProjectState` via the **same** Continuity writers already used by `declara…`.

That keeps:

- LLM out of inventing geometry  
- SoT in ProjectState (not browser cosmetics)  
- Continuity spatial assembly as the product feature — UI becomes another **input surface**, not a second truth

---

## What already exists (honest)

| Surface today | Role |
|---|---|
| `declara L×W×H` / `declara … mm en ejes respecto a` | Writers → `ComponentSpec` — **engineering SoT** |
| Visor Scene3D | Read-only projection of envelopes + pose + copies |
| Card drag on the 2D map | Often **localStorage** layout overlay — **not** millimetre pose (named Board B1 debt) |

So: “arrastrar cards en el mapa 2D” ≠ “situar en mm” unless we **wire drag to the pose/envelope writers**.

---

## Recommended product shape (when investigated)

1. **Drag in the 3D / mm frame** (or a calibrated top-down mm plane), not only card pixels.  
2. On drop: compute Δ vs a chosen **box origin** (Main Plate / posed parent) → `set_component_declared_box_pose`.  
3. On resize handles: update L×W×H → `set_component_declared_box_envelope` (`source=declared`).  
4. Multiplicity (`solidCopies`) stays projector rules (motors X, standoff corners, …) — drag moves the **one** BOM subject, copies follow.  
5. Snap optional (grid mm, plate edges) — later.  
6. **Forbidden:** saving only to `localStorage` and calling it “posed”; LLM inventing drop coords.

---

## Why this is strong for “cualquier equipo”

The Engineer places what they see; Jarvis records numbers.  
No need for Jarvis to “understand” a Rooster photo first.  
Sourced dims (#4) and drag can coexist: cite when you have a datasheet; drag when you don’t.

---

## Suggested next step

★ Investigation B0 (no code): map gesture → writer → DTO → Scene3D round-trip; list UI affordances; name out-of-scope (CAD mate solver, VERIFIED fit).  
Then a thin B1 IC: drag solid → pose write only (resize later).

---

## Explicit non-goals (until ★)

Conversation Engine inventing placement · treating card layout as SoT · auto-fit VERIFIED · replacing Continuity declare grammar (keep both)
