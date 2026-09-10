# Engineer note — Board Situar UX follow-up (viewport + fluid drag)

**Date:** 2026-09-10  
**Authority:** Engineer smoke after Board drag → pose B1 — “he conseguido moverlo, pero es muy complicado; el mapa es muy pequeño; profundizar más; arrastre igual de fluido que las cards”  
**Status:** COLA / next Buy after B1 **ACCEPT** · not implemented  
**Parents:** [smoke](engineer_smoke_board_drag_pose_b1.md) **ACCEPT** · [IC B1](implementation_contract_board_drag_pose_b1.md) · C-113

---

## What worked

Situar + POST → writer → state works. Core Buy is done.

---

## Pain (live)

| Gap | Today | Wanted |
|---|---|---|
| **Situar pane size** | `.sb-scene3d { height: 260px }` — strip under cards | Much larger working surface (taller default and/or expand when Situar ON / user resize) |
| **Depth / zoom** | `ZOOM_MIN=0.5` · `ZOOM_MAX=2` | Wider zoom range to “profundizar” into the assembly |
| **Drag feel** | Pointer tracked; **no live solid move**; POST only on drop | Fluid like 2D cards: **live preview** while dragging; persist on drop (same writer) — never localStorage SoT |
| **2D minimap “Mapa”** (secondary) | Small corner widget | Optional larger minimap — only if Engineer still wants it after situar pane grows; do not confuse with Scene3D |

Primary product surface for this note = **Scene3D situar pane**, not the 2D card minimap label.

---

## Why drag feels hard (honest)

B1 intentionally deferred mid-drag re-layout (“on drop only”). Cards use `onPreview` every move. Engineer experience: situar feels dead until release. Fix = preview in px/mm space during drag, **one** POST on mouseup (already C-113).

---

## Suggested Buy (when ★)

Thin **Situar UX B1** IC (ui-only + tests; no new writer; no version bump):

1. Taller Scene3D default (e.g. ~40–50vh or ≥480px) and/or Situar-ON expands pane; optional drag handle to resize height.  
2. Raise `ZOOM_MAX` (and optionally lower `ZOOM_MIN`) with tests that `pxToMm` still uses zoom.  
3. Live preview: while situar-dragging, update solid `originX/Y` from the same `computeDragPosePayload` math (or optimistic layout overlay); on drop keep current POST + refetch (discard preview).  
4. Out: Three.js, card-px→pose, multi-copy drag, envelope resize, LLM.

---

## Explicit non-goals

Redoing C-113 · Conversation Engine · inventing mm · making 2D minimap the situar surface
