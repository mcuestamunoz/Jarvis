# Implementation Report — Geometry Assembly Board Edges B2

**IC:** [implementation_contract_geometry_assembly_board_edges_b2.md](implementation_contract_geometry_assembly_board_edges_b2.md)  
**Implementer:** Cursor (Engineer ★ queue + start first)  
**Date:** 2026-09-07  
**Baseline:** package `0.3.8` · suite 2380

---

## Files changed

- `src/jarvis/workspace/spatial_board.py` — when `spec.mounted_on` is set **and** that key is still in `components`, emit `node["mountedOn"]`; stale targets omit the machine field but keep the `"montado en"` text field. No layout/`kind`/`geometry` changes.
- `ui/spatial-board/src/types.ts` — optional `mountedOn?: string`.
- `ui/spatial-board/src/mountEdgeGeometry.ts` (**new**) — pure `mountEdgeSegments` (source mid-bottom → target mid-top).
- `ui/spatial-board/src/MountEdges.tsx` (**new**) — SVG layer under cards.
- `ui/spatial-board/src/InfiniteCanvas.tsx` — render `<MountEdges />` before cards.
- `ui/spatial-board/src/spatial-board.css` — `.sb-mount-edges` / `.sb-mount-edge` stroke; cards `z-index: 1`.
- `ui/spatial-board/src/mountEdgeGeometry.test.ts` (**new**) — U1–U3.
- `tests/test_geometry_assembly_board_edges_b2.py` (**new**) — T1–T5.

## Behavior changed

- Board draws a straight line for each drawable declared mount when both endpoints are projected nodes.
- Drag overlay still drives endpoint positions (edges recompute from current node rects).
- No Continuity / writer / schema / glyph changes.

## Tests

- `pytest tests/test_geometry_assembly_board_edges_b2.py` → **5 passed**
- `cd ui/spatial-board && npm test` → **7 passed** (3 new + 4 prior)
- `npm run typecheck` → clean
- Full `pytest -q` → **2385 passed** (2380 + 5)

## Non-goals honored

No pose fields · no fit · no auto-layout from mounts · no parsing of `"montado en"` text for edges · no version bump · minimap unchanged (no edges)

## Remaining

Engineer Board smoke recommended before closing queue item 1. Pose B1+ and fit stubs remain **QUEUED — DO NOT IMPLEMENT**.
