# Investigation Review — Mapping rung 2 first cut: wheelbase on the bound frame spec

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_geometry_wheelbase_on_spec_b1.md](investigation_contract_geometry_wheelbase_on_spec_b1.md)  
**Report:** [investigation_report_geometry_wheelbase_on_spec_b1.md](investigation_report_geometry_wheelbase_on_spec_b1.md)

## Verdict

**PASS WITH NOTES**

Lean **B1** is Buy-eligible: the millimetre already exists in the seed and binder; the hole is stale `ProjectState` plus a missing refresh regression. **B1+** catalog overlay rejected. **B2** visor glyph later. **4-motor** later ★. **B0** walk-only is weaker than a named test.

**IC READY.** Engineer ★ **B1** (`procede con wheelbase` 2026-09-09). Fit stub stays **QUEUED**.

---

## Checklist

| Criterion | Result |
|---|---|
| Executive lean + one paragraph | **Pass** |
| Binder / seed cited, not remembered | **Pass** — `_datos.json` 230 + `catalog_bind.py:318` + existing bind test |
| Live census | **Pass** — frame properties mass/size/material only; `catalog_ref` rooster |
| Refresh vs children | **Pass** — single-key writer (precedent) |
| Projector no backfill | **Pass** |
| Code vs state hole | **Pass** |
| Leans scored; 4 motors out | **Pass** |
| No implementation in the report | **Pass** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| Seed `armattan_rooster_5in.wheelbase_mm` 230 | **Confirmed** |
| `bind_frame_from_catalog` projects it | **Confirmed** |
| Bind test already asserts 230 | **Confirmed** `test_frame_parts_graph_v1.py` |
| Live frame lacks `wheelbase_mm` | **Confirmed** `state.json` |
| `"actualiza la frame"` → `frame` | **Confirmed** `test_t4_parse_set` |
| `_fields` walks `spec.properties` only | **Confirmed** `spatial_board.py` |
| Catalog-refresh tests do not cover stale-frame wheelbase growth | **Confirmed** (grep) |
| Auto-refresh on Board load still absent | **Confirmed** — projector read-only |

---

## Notes for IC

### N1 — Refresh will also add `configuration`

Do not write an IC that asserts “only `wheelbase_mm` changed.” Diff may include `quad_x`.

### N2 — Frame still has no 3D solid

Wheelbase is not L×W×H. IC must not require a Scene3D change.

### N3 — Live demo mutation is smoke, not the test

Tests use fixtures. Saving `workspace/autonomía-de-10min-…` is Engineer smoke (gitignored).

---

## Phase

Investigation **CLOSED**. ★ **B1**. IC next.
