# Investigation Contract — Spatial board viewport motor

**Project:** Jarvis  
**Date:** 2026-09-05  
**Author:** JES / Cursor (Engineer Interface)  
**Investigator:** Cursor (Engineer “hazlo” — investigate in-place, then IC + implement)  
**Reviewer:** same session (board-first slice; no RAG)  
**Output:** [investigation_report_spatial_board_viewport.md](investigation_report_spatial_board_viewport.md)

**Status:** EXECUTED same turn → IC + implement  
**Parents:** [design_spatial_board_ui.md](design_spatial_board_ui.md) — Q1–Q11, B1–B3 locked

**Type:** Know the SolveSphere Capa A motor well enough to extract a **correct** Jarvis board (fixture cards).  
**Not** projector `state.json`. **Not** RAG. **Not** PRODUCT_SCOPE rewrite.

**Do not copy Capa C. Do not reopen Structure. Do not bump Jarvis version.**

---

## 1. Governing question

> Which files and math from SolveSphere’s infinite canvas must Jarvis take, which bugs must it refuse, and what is the smallest board that satisfies Q1–Q11 with fixture component cards?

---

## 2. Locked stances

1. Slice = pan / zoom-to-cursor / drag / resize / minimap / fit / layout persist.  
2. Cards = SpatialNode (id, rect, payload). Fixture components, not tasks.  
3. Layout write is `{x,y,width,height}` only.  
4. Tests of transform math ship with the motor (origin has zero).  
5. No Ctrl+R hijack. No RAG cards. No global CSS soup if avoidable.

---

## 3. Report must cite

- Exact origin paths under `frontend/src/components/interactive-tasks/`  
- Zoom-to-cursor formula (Q1)  
- Drag/resize screen→world (Q2/Q3)  
- Pan exclusion selectors (Q4)  
- Minimap bugs to **not** copy (zoom reset on click)  
- Recommended Jarvis tree `ui/spatial-board/`
