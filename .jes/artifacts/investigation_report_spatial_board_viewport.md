# Investigation Report — Spatial board viewport motor

**Date:** 2026-09-05  
**Investigator:** Cursor  
**Contract:** [investigation_contract_spatial_board_viewport.md](investigation_contract_spatial_board_viewport.md)  
**Origin:** `/Users/marccuestamunoz/repos/multiagent_problem_solving/frontend/src/components/interactive-tasks/`

**Status:** KNOW complete — extract Capa A, refuse Capa C and known bugs.

---

## A. Origin inventory (Capa A)

| File | Role | Take? |
|---|---|---|
| `utils/transformUtils.ts` | world↔screen, delta / zoom, bounds, visibility | **Yes** — drop `InteractiveTask`; use `SpatialRect` |
| `hooks/useCanvasTransform.ts` | zoom/pan state, `zoomToPoint`, `fitToScreen`, CSS string | **Yes** — wire fit (origin unused) |
| `hooks/useDrag.ts` | move card, screen delta / zoom | **Yes, rewrite** — too coupled to task/API integers |
| `hooks/useResize.ts` | 4 corners, world delta | **Yes, rewrite** — same |
| `CanvasMinimap.tsx` + `useMinimapData` / `useMinimapNavigation` | SVG 200×150 | **Yes, rewrite** — navigation **resets zoom to 1.0** (refuse) |
| `InteractiveTasksBoard.tsx` wheel + pan-on-background | Gesture shell | **Reimplement** — do not copy 743-line god file |
| RAG / phases / templates / JWT service | Capa C | **No** |

Wheel (board ~90–114): cursor relative to board rect; `newZoom = zoom * 1.1` or `/ 1.1`; `zoomToPoint`. Keep. Do **not** bind Ctrl+R.

Pan start ignores `[data-task-id]`, buttons, inputs, `.resize-handle`. Keep as `[data-node-id]` + `.sb-handle`.

---

## B. Math to lock (Q1–Q3)

```text
screen = (world + pan) * zoom
world  = screen / zoom - pan
worldDelta = screenDelta / zoom

zoomToPoint(screen, z'):
  world = screen/z - pan
  pan'  = screen/z' - world
```

CSS: `transform-origin: 0 0`; `scale(zoom) translate(panXpx, panYpx)`.

Drag/resize **must** use `worldDelta`. Origin RAG path used zoom=1 — we have no RAG path.

---

## C. Bugs not to copy

1. Minimap `navigateToPoint` sets `zoom: 1.0`. **Keep current zoom**; pan so the world point is viewport-centered.  
2. Minimap viewport uses `-pan * zoom` instead of `screenToWorld` of the viewport corners. **Use screenToWorld(0,0) and (W,H).**  
3. Zero tests. **Vitest on transform.ts is the first deliverable.**  
4. Global handle CSS. **Scope under `.spatial-board`.**  
5. Integer rounding for FastAPI. Jarvis layout may stay floats; round only for display if needed.

---

## D. Jarvis tree

`ui/spatial-board/` — Vite + React + TS + Vitest. Fixture cards. `localStorage` for layout (Q7) until a later projector writes `views/spatial_layout.json`.

## E. Buy for implement

Proceed. Fixture board. No `state.json` projector in this IC.
