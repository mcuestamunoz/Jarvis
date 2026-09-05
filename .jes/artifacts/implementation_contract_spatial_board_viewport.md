# Implementation Contract — Spatial board viewport (fixture cards)

**Project:** Jarvis  
**Date:** 2026-09-05  
**Author:** JES / Cursor  
**Implementer:** Cursor (Engineer “hazlo”)  
**Status:** IMPLEMENTING  
**Parents:** investigation report + review **PASS**; [design_spatial_board_ui.md](design_spatial_board_ui.md) Q1–Q11

**Type:** New visor app under `ui/spatial-board/`. Not a Python subsystem. Not projector. Not version bump.

---

## 0. You

- Implement the infinite board: pan, zoom-to-cursor, drag, 4-corner resize, minimap (keep zoom on click), fit-to-screen, layout persist (`localStorage`).
- Fixture SpatialNodes (motors, propellers, esc slot, battery, frame, arm, plate, FC) — component-shaped payload, not tasks.
- Vitest for transform math (Q8). Full Python suite must stay green (no `src/` edits required).
- Do **not** copy RAG, templates, phases, Ctrl+R, FastAPI, JWT.
- Do **not** write engineering fields from the board.
- Do **not** bump Jarvis version.

---

## 1. Done

- Q1–Q8, Q10–Q11 held in the visor  
- Q9: no RAG/templates/phases  
- `npm test` in `ui/spatial-board` green  
- Report: `implementation_report_spatial_board_viewport.md`

---

## 2. Files

`ui/spatial-board/**` (new). `.gitignore` `node_modules`. No `src/jarvis` unless a one-line docs pointer is needed — skip docs unless necessary.
