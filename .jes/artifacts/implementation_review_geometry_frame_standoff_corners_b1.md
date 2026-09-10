# Implementation Review — Frame standoff ×4 at Main Plate corners B1

**Date:** 2026-09-10  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_geometry_frame_standoff_corners_b1.md](implementation_contract_geometry_frame_standoff_corners_b1.md)  
**Report:** [implementation_report_geometry_frame_standoff_corners_b1.md](implementation_report_geometry_frame_standoff_corners_b1.md)  
**Buy:** Engineer ★ **B1-standoff-corners-4**

## Verdict

**PASS WITH NOTES**

Locks hold. Separate corner helper (not quad-X). Fixed 4. Fail-closed oversized. One BOM key. Closable after Engineer smoke §5.

---

## Checklist

| Criterion | Result |
|---|---|
| Fixed count 4 — never motors/`quad_x`/W | **Pass** |
| Gate: standoff box + literal `frame_plate` box | **Pass** — P2 |
| Formula `hx=Lp/2−Ls/2`, `hy=Wp/2−Ws/2`, Z=0 | **Pass** — P1 (±47.5) |
| Fail closed if inset &lt; 0 | **Pass** — P3 |
| `_main_plate_corner_points` ≠ `_quad_x_station_points` | **Pass** — P4/P6 |
| Copies/offsets lockstep via shared helper | **Pass** |
| Pose strip on copies | **Pass** — existing expand |
| One `frame_standoff` node | **Pass** — P5 |
| `standoff_count` / invent / ui / version | **Pass** — out / `0.3.8` |
| P1–P6 | **Pass** — Cursor 6/6 |
| Quad-X family regressions | **Pass** — P6 + targeted |
| Full pytest | **Pass** — Cursor **2652** |
| Live 5min projector | **Pass** — 4 @ ±47.5 ≠ motors X |

---

## Independent checks

| Claim | Cursor |
|---|---|
| Live offsets exact `(±47.5, ±47.5, 0)` | **Confirmed** |
| Distinct from motors `±81.317` | **Confirmed** |
| `_STANDOFF_CORNER_COUNT` separate from `_QUAD_X_STATION_COUNT` | **Confirmed** (good for B4) |

---

## Notes

### N1 — Orphan single pose on card

Card may still show Δ 30/30/4 until cleared. Visor strips when copies≥2.

### N2 — Smoke still open

Reload Board: 4 posts at Main Plate corners · not on motor X · one card.

---

## Phase

Implementation **CLOSED** for review. **Smoke pending.** Package `0.3.8` · suite **2652**. Next cola: B4 `standoff_count` generalista.
