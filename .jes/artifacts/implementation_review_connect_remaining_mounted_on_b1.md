# Implementation Review — Conn B1 (`mounted_on` parse symmetry)

**Date:** 2026-09-08  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_connect_remaining_mounted_on_b1.md](implementation_contract_connect_remaining_mounted_on_b1.md)  
**Report:** [implementation_report_connect_remaining_mounted_on_b1.md](implementation_report_connect_remaining_mounted_on_b1.md)  
**Buy:** ★ B1 — dual lock (subject before `en` + target component-noun aliases)

## Verdict

**PASS WITH NOTES**

Both investigation bugs fixed; dual IC lock held; writer untouched; suite **2429**. Closable. Fase 3 Conn complete as a parse bug-fix (remaining demo mounts are Engineer Continuity walk).

---

## Checklist

| Criterion | Result |
|---|---|
| Subject before first `en` (SET) | **Pass** |
| Target component-noun alias last-resort | **Pass** — `"motores"` → `motors` |
| T1–T3 collision phrases | **Pass** (live demo probe + tests) |
| Non-reg CLEAR / plate AMBIGUOUS / literal keys | **Pass** |
| Frame parts still not subjects | **Pass** |
| Writer unchanged | **Pass** (`component_writers.py` diff empty) |
| No invent absent keys | **Pass** (honesty test) |
| Version / Board / seeds / pose/fit | **Out** — honored |
| Full suite | **Pass** — Cursor **2429** |

---

## Independent verification

| Phrase | Result |
|---|---|
| `helices montadas en los motores` | `SET(propellers→motors)` |
| `sensor montado en el esc` | `SET(sensors→esc)` |
| `esc montado en frame_plate` | `SET(esc→frame_plate)` |
| `quita el montaje del esc` | `CLEAR` |
| `pytest` new + continuity | **27 passed** |
| `pytest -q` | **2429 passed** |
| Diff scope | assist + new tests + report only |

---

## Notes

### N1 — Shared `_SUBJECT_PATTERNS` for target aliases

As report: future subject-table edits auto-extend target aliases. Intended symmetry; document when editing.

### N2 — Demo still needs Engineer walk

Parse is fixed; `propellers`/`sensors` on demo stay `mounted_on=None` until Continuity phrases are run live. Optional smoke checklist, not a code gap.

### N3 — B1+ “qué falta” deferred

Correctly out of scope.

---

## Phase

Implementation **closable**. Mark Conn B1 CLOSED. Sequence E → G → Conn complete for this arc (aside from optional E ESC smoke / Conn Continuity walk on demo).
