# Implementation Review — Standoff count gate for corner copies B4-min

**Date:** 2026-09-10  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_geometry_standoff_count_gate_b4.md](implementation_contract_geometry_standoff_count_gate_b4.md)  
**Report:** [implementation_report_geometry_standoff_count_gate_b4.md](implementation_report_geometry_standoff_count_gate_b4.md)  
**Buy:** Engineer ★ **B4-min** (count gate; missing/≠4 omit)

## Verdict

**PASS WITH NOTES**

Locks hold. Count gate lives in the shared helper; corners formula unchanged; no seed invention; suite **2661**. Closable after Engineer smoke (set `count=4` on 5min or accept single solid).

---

## Checklist

| Criterion | Result |
|---|---|
| Source = `frame_standoff.properties["count"]` only | **Pass** |
| Parse via `_parse_solid_copies_count` then `== 4` | **Pass** |
| Missing / N≠4 → omit copies+offsets | **Pass** — P2/P3 |
| No default 4 (supersedes B3) | **Pass** |
| Corner formula unchanged | **Pass** — amended B3 suite + P1 |
| Copies/offsets lockstep | **Pass** — shared helper |
| No Continuity declare / no library seed | **Pass** |
| No ui / version bump | **Pass** — `0.4.0` |
| P1–P8 | **Pass** — Cursor 15/15 targeted |
| Full pytest | **Pass** — Cursor **2661** |

---

## Independent checks

| Claim | Cursor |
|---|---|
| Gate at start of `_frame_standoff_corner_offsets_mm` | **Confirmed** `spatial_board.py` ~586–588 |
| Live 5min no `count` → no `solidCopies` | **Confirmed** (prior session + report) |
| `count=4` restores ±47.5 | **Accepted** from report + formula tests |

---

## Notes

### N1 — Smoke

Board reload after putting `count=4` on `frame_standoff` (free-text / property) → 4 corner posts. Without count → one box. Expected.

### N2 — Orphan pose

Card may still show old single FR pose when copies return — same adjacent debt as B3; not this Buy.

---

## Phase

Implementation **CLOSED** for review. **Smoke optional** (regression named). Package `0.4.0` · suite **2661**.
