# Implementation Review — Continuity declared box-local pose B1 (CLI / IDLE)

**Date:** 2026-09-08  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_continuity_declared_box_pose_b1.md](implementation_contract_continuity_declared_box_pose_b1.md)  
**Report:** [implementation_report_continuity_declared_box_pose_b1.md](implementation_report_continuity_declared_box_pose_b1.md)  
**Buy:** Engineer ★ B1 — thin IDLE declare/clear → existing `set_component_declared_box_pose`

## Verdict

**PASS WITH NOTES**

IC locks held. Parser is thin; writer is the box/self/missing gate; orchestrator sits **after** catalog refresh and **before** FN-005/FN-014. Scene3D not moved. Fit still QUEUED. Closable after Engineer CLI smoke.

---

## Checklist

| Criterion | Result |
|---|---|
| New `declared_box_pose_declare_assist.py` — no mutation | **Pass** |
| SET gate `declara(r)` + `mm` + `respecto`; never `fija` | **Pass** |
| CLEAR `quita[r] [la] pose`; not `quita el montaje` | **Pass** |
| Axes closed to `x/y/z/largo/ancho/alto` | **Pass** — `adelante` → `INCOMPLETE` |
| Subject before `respecto`; origin after; no split on `en` | **Pass** |
| Public wrappers only; no private `_SUBJECT_PATTERNS` import | **Pass** |
| Parser does not pre-check box | **Pass** — T8 SET on `frame_plate` |
| IDLE order mount → refresh → pose → FN-005 → FN-014 | **Pass** — Cursor read `orchestrator.py` ~960–1025 |
| Confirm copy: `POSE_AXES_HONESTY_LABEL` verbatim | **Pass** |
| Writer not forked this Buy | **Pass** — this IC only *calls* it (N3) |
| No `ui/` 3D layout change this Buy | **Pass** |
| T1–T12 + extras; mount suite green | **Pass** |
| Version | **None** — `0.3.8` |
| Demo `state.json` | **Pass** — no non-null pose |

---

## Independent verification

| Check | Result |
|---|---|
| `pytest -q` | **2456 passed** (Cursor re-ran) |
| `tests/test_continuity_declared_box_pose_b1.py` + mount file | **34 passed** |
| Dispatch after refresh, before FN-005 @ ~989 | **Confirmed** |
| `pyproject.toml` | **0.3.8** |
| Live demo pose values | all `null` / `None` (CLI not yet walked) |

---

## Agreement with report core

1. **T11 reshape is honest.** `"declarar el esc"` is pose `NONE`. With ESC already `completeness=high`, FN-014 has nothing to offer and the phrase can reach the LLM — **pre-existing**, not this Buy. Asserting `_try_handle_declared_box_pose(...) is None` is the fact this IC owns. Not a FAIL.  
2. **`morro` in confirm copy.** Verbatim label contains `no morro` / `no gravedad`. Treating both as exemption (positive claim forbidden) matches IC §3.6’s gravity sentence. Correct; do not “fix” by stripping the locked label.  
3. **`INCOMPLETE` vs fall-through.** Gate-shaped phrases missing an axis stay in the pose bridge. Required so FN-014 cannot swallow `"declara el esc a 5 mm respecto al fc"`.

---

## Notes

### N1 — T12 weaker than mount T9

Only `status in {interactive, ok}`. Mount T9 also checks `frame` in message/action. Enough for this IC; not a FAIL.

### N2 — T11 wording vs IC table

IC table said “still acquisition-shaped.” Implementation asserts non-steal. Review accepts. Future IC tables should say “pose dispatch returns None,” not name FN-014 as the guaranteed next handler.

### N3 — `component_writers.py` vs git HEAD

`git diff` still shows `set_component_declared_box_pose` as uncommitted from the **writer** Buy (suite 2438). This Continuity IC did not change those rules. Do not read that hunk as a fork of this cycle.

### N4 — Smoke is now CLI

Unlike writer-only B1, Engineer can type:

```text
declara el esc a 5 mm en x respecto al fc
```

Board card ESC should show `origen pose` / `ejes pose` / `Δx mm`. 3D row still a presentation row.

---

## Phase

Implementation **CLOSED**. Engineer ACCEPT ([smoke](engineer_smoke_continuity_declared_box_pose_b1.md)). Scene3D-from-pose later ★. Package `0.3.8` · suite **2456**.
