# Investigation Review — Spatial board viewport motor

**Date:** 2026-09-05  
**Reviewer:** Cursor  
**Verdict:** **PASS** — extract math + gestures; rewrite drag/resize/minimap; no Capa C.

Independent check: `zoomToPoint` in origin `useCanvasTransform.ts:73–86` matches the report formula. `useDrag.ts:147–148` already divides by zoom on the non-RAG path. Minimap navigation `useMinimapNavigation.ts:42–46` **does** force `zoom: 1.0` — refuse. Board pan exclusion `InteractiveTasksBoard.tsx:131–138` is the Q4 seed.

Proceed to IC + implement `ui/spatial-board/`.
