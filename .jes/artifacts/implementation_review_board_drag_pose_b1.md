# Implementation Review — Board drag → Continuity pose B1

**Date:** 2026-09-10  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_board_drag_pose_b1.md](implementation_contract_board_drag_pose_b1.md)  
**Report:** [implementation_report_board_drag_pose_b1.md](implementation_report_board_drag_pose_b1.md)  
**Buy:** Engineer ★ **B1** (investigation lean)

## Verdict

**PASS WITH NOTES**

Locks hold. Thin bridge → same writer → save; situar top-down; singleton-only; C-113 named; no LLM; suite **2668** / UI **64**. Closable after Engineer Board smoke §6.

---

## Checklist

| Criterion | Result |
|---|---|
| Scene3D situar tilt (0,0) only | **Pass** |
| Singleton only (`solidCopies ≥ 2` never arms) | **Pass** — `isDraggableSolid` + Scene3D |
| Origin picker / existing origin — no silent Main Plate | **Pass** — report + code path |
| X/Y drag; Z not invented | **Pass** — P5; mapping documented (N1) |
| `pxToMm` inverse + round-trip | **Pass** — Cursor UI suite |
| POST → `set_component_declared_box_pose` only | **Pass** — `board_pose_bridge.py` |
| Writer reject → 4xx / no partial save | **Pass** — P2 + curl report |
| Refetch GET after success (not localStorage SoT) | **Pass** — `refetch` |
| C-113 + narrowed absences | **Pass** — Cursor fixed stale “GET only” row (N2) |
| No resize / card-px / version bump | **Pass** — `0.4.0` |
| P1–P6 / full pytest | **Pass** — Cursor **2668** + bridge 7/7 |
| Full UI suite | **Pass** — Cursor **64** |

---

## Independent checks

| Claim | Cursor |
|---|---|
| Bridge calls CLOSED writer then `save_state` | **Confirmed** |
| No orchestrator/LLM in bridge | **Confirmed** |
| C-113 registry + chronology | **Confirmed** |
| `computeDragPosePayload` preserves `z_mm` | **Confirmed** |
| Real `workspace/` untouched this Buy | **Accepted** from report + empty status claim |

---

## Notes

### N1 — Screen Δy → declared `y_mm` (not render Y↔Z)

IC allowed picking one honest map. Claude chose input-side screen Y → declared Y (simpler than unprojecting the renderer's Y↔Z). Documented and tested. Smoke: if a drag “feels inverted” vs visual depth, that is this choice — not a silent bug. Revisit only with ★.

### N2 — CONNECTIONS stale “GET only”

Absence row still said the board has GET only while C-113 adds POST. Cursor narrowed it to DEFINE/catalog still absent; pose = C-113.

### N3 — Smoke

`jarvis board` → Situar ON → drag **battery / FC / ESC** (singletons). Do **not** expect drag on motors/props/adapter/standoff copies. Confirm card Δmm matches drop; CLI `declara…` still works.

### N4 — Risks accepted

Perspective foreshortening approx; no CI HTTP integration test (manual curl OK for this Buy).

---

## Phase

Implementation **CLOSED** for review. **Smoke pending.** Package `0.4.0` · suite **2668**.
