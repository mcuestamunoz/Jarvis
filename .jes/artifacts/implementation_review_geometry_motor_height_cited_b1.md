# Implementation Review — Motor `height_mm` 31.7 cited B1 (EMAX only, no cylinder)

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_geometry_motor_height_cited_b1.md](implementation_contract_geometry_motor_height_cited_b1.md)  
**Report:** [implementation_report_geometry_motor_height_cited_b1.md](implementation_report_geometry_motor_height_cited_b1.md)  
**Buy:** Engineer ★ **B1** — seed cited EMAX Motor Height 31.7 as `height_mm`; no cylinder; no SunnySky 18 mm

## Verdict

**PASS WITH NOTES**

IC locks held. Exactly one SKU carries `height_mm` 31.7. Bind projects it as declared mm. Diameter + height still a **flat disk**. Live demo SKU untouched. Fit QUEUED. Version `0.3.8`. Closable after Engineer smoke §6.

---

## Checklist

| Criterion | Result |
|---|---|
| Seed `emax_rs2205s_2300.height_mm == 31.7` only | **Pass** — census: that key exists on **one** JSON row |
| `source_note` seeded + not comparable to Body Length + 15 mm shaft unseeded | **Pass** |
| SunnySky R2205 / R2305 / sibling `emax_rs2205_2300` no `height_mm` | **Pass** — T2–T4 + library census |
| `MotorSpec.height_mm` + `_motor_from_raw` | **Pass** |
| Docstring SKU-scoped, not glyph/cylinder | **Pass** (see N1) |
| Bind loop includes `height_mm`; same PropertyValue shape | **Pass** — Cursor probed `source=declared` `confidence=0.9` |
| No `MotorSuggestion` TypedDict change | **Pass** |
| `_geometry_from_spec` unedited; T7 disk not box | **Pass** |
| `ui/` empty **this cycle** | **Pass** — height Buy files are library/bind/tests only; Scene3D diff is prior copies B1 |
| Version `0.3.8` | **Pass** |
| Fit stub QUEUED | **Pass** |
| No `workspace/` mutation | **Pass** — report + git |
| T1–T7 | **Pass** |
| Full pytest **2480** | **Pass** — Cursor re-ran |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| JSON `height_mm` only on `emax_rs2205s_2300` | **Confirmed** |
| `default_library` motors with `height_mm is not None` | **Confirmed** `['emax_rs2205s_2300']` |
| Bind EMAX `height_mm` 31.7 mm declared 0.9; `diameter_mm` 27.9 | **Confirmed** |
| Bind SunnySky R2205 has no `height_mm` key | **Confirmed** T6 |
| T7 `geometry == {shape: disk, diameter_mm: 27.9}` + field `31.7 mm` | **Confirmed** |
| `_geometry_from_spec` hunk this Buy | **None** — spatial_board diff is `_solid_copies` from copies B1 |
| No `"cylinder"` in projector | **Confirmed** |
| T1–T7 | **7 passed** |
| Full pytest | **2480 passed** this review |
| `pyproject.toml` `0.3.8` | **Confirmed** |

---

## Notes

### N1 — Class header still says “cylinder envelope”

`MotorSpec` geometry-axis comment still opens with Motor B1’s “declared cylinder envelope.” The new `height_mm` field comment correctly says it is **not** a cylinder input. Pre-existing wording, not a reopen. Optional later copy tidy.

### N2 — T5 does not assert `source` / `confidence`

IC §3.3 requires `declared` / `0.9`. Code does. Test asserts value + unit + Ø. Cursor probed the PropertyValue. Add those two asserts if the bind loop is edited later.

### N3 — `height_mm` is also the box-triple key

`_geometry_from_spec` uses `height_mm` for a **box** when L+W+H are all present. Motors have no L/W, so T7 stays a disk. If a later seed added motor `length_mm`/`width_mm`, 31.7 would become box height, not a disk. Out of this IC; do not stitch a cylinder in that future either.

### N4 — Live visor still empty on motors

Demo remains `sunnysky_r2305_2500` (no Ø, no 31.7). §6 smoke is **Engineer**: card still no 31.7; optional EMAX-bound lab shows the text and a flat disk.

---

## Phase

Implementation **REVIEWED PASS WITH NOTES**. Engineer smoke next ([§6](implementation_contract_geometry_motor_height_cited_b1.md)). Mapping rungs 4–5 later ★. Fit still QUEUED. Package `0.3.8` · suite **2480**.
