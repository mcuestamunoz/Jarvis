# Implementation Review — Top LiPo plate (`frame_plate_2`) envelope noun B1

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_geometry_frame_plate_2_lipo_envelope_b1.md](implementation_contract_geometry_frame_plate_2_lipo_envelope_b1.md)  
**Report:** [implementation_report_geometry_frame_plate_2_lipo_envelope_b1.md](implementation_report_geometry_frame_plate_2_lipo_envelope_b1.md)  
**Buy:** Engineer ★ **B1-plate2-noun** (step 3/4)  
**Role:** Claude implemented · Cursor reviews

## Verdict

**PASS WITH NOTES**

Top LiPo nouns resolve to `frame_plate_2` by exact label `top (lipo) plate`. Main Plate / bare `placa` / `respecto` regressions hold. Suite **2602**. Version **0.3.8**. No library L×W seed. No assembly-root / `ui/` change this Buy. Live smoke is Engineer’s (§6).

---

## Checklist

| Criterion | Result |
|---|---|
| #1–#3 Nouns → unique Top LiPo label | **Pass** — P1 ×4 + Cursor probe |
| #4 L×W; H from thickness; no wheelbase stitch | **Pass** — P2 |
| #5 Writer allowlist untouched | **Pass** |
| #6 Assembly root still `frame_plate` only | **Pass** — `ASSEMBLY_ROOT_ID` unchanged; no ui edit this Buy |
| #7 No auto-pose | **Pass** — P5 unlock only |
| #8 No HD Cam / other plate nouns | **Pass** |
| #9 No Rooster plate L×W seed | **Pass** — P6 |
| #10 No version bump | **Pass** |
| Optional orchestrator hint | **Skipped** — documented; OK |
| Full suite **2602** | **Pass** — Cursor re-ran |

---

## Independent checks

| Claim | Cursor |
|---|---|
| Four locked phrases → SET `frame_plate_2`, height None | **Confirmed** |
| `placa principal` → `frame_plate` | **Confirmed** |
| Bare `placa` → AMBIGUOUS both plates | **Confirmed** |
| `respecto` → NONE | **Confirmed** |
| Apply H=2 from thickness; wheelbase 230 untouched | **Confirmed** |

---

## Notes

### N1 — P2 thickness fill is test-side (same as Main Plate review)

P2 calls the writer with `thickness` from the fixture, not the orchestrator’s two-number apply branch. Matches prior battery/plate review N1 and IC wording (“Orchestrator or writer path”). Smoke will hit the live IDLE path.

### N2 — Hint copy skipped

Optional. Acceptable smaller diff.

---

## Engineer smoke (next)

| Step | Expected |
|---|---|
| `declara la placa lipo 100 x 100 mm` (not 230 unless typed) | `frame_plate_2` box; H=2; wheelbase 230 |
| Optional battery `respecto a frame_plate_2` | on Top LiPo; Main Plate still X/root |
| Forbidden | plate_2 as world origin |

Record [engineer_smoke_geometry_frame_plate_2_lipo_envelope_b1.md](engineer_smoke_geometry_frame_plate_2_lipo_envelope_b1.md).
