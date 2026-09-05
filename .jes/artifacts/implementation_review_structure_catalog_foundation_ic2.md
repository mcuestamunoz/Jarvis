# Implementation Review — Structure Catalog Foundation IC-2

**Date:** 2026-09-04  
**Reviewer:** Cursor (JES)  
**IC:** [implementation_contract_structure_catalog_foundation_ic2.md](implementation_contract_structure_catalog_foundation_ic2.md)  
**Report:** [implementation_report_structure_catalog_foundation_ic2.md](implementation_report_structure_catalog_foundation_ic2.md)  
**Baseline:** IC-1 · suite **2177** · reviewer suite **2188**

## Verdict

**PASS WITH NOTES**

IC-2 matches the contract: bind + writer identity + BOM `has_frame` +
two-axis diverge. Physics unchanged vs free-text. No assist. No
PASS-by-catalog. **IC-2 CLOSED.**

IC-3 remains **not authorized**.

---

## IC checklist

| Criterion | Result |
|---|---|
| §2.1 `bind_frame_from_catalog` + `_frame_completeness` | **Pass** — TBS → medium; Armattan → high |
| §2.1 mass_g/1000 + size_class + optional material | **Pass** |
| §2.2 `set_frame_material(..., catalog_ref=, component_name=)` | **Pass** — kwargs; free-text clears ref |
| §2.2 Single mass mirror path | **Pass** |
| §2.3 `_bom_sku_resolved` `"frame"` → `has_frame` | **Pass** |
| §2.4 Diverge: SKU gone / mass / class / override | **Pass** — all four coded; rename `_DIVERGED_FRAME_NAME` |
| Forbidden: assist / verdict / seed expand | **Pass** |
| Mandatory tests | **Pass** — 11 new in `test_catalog_bind_v1.py` |
| Full suite | **Pass** — **2188** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| Bind projects mass/class; unknown KeyError | **Confirmed** |
| Apply → `catalog_ref` + `structure_mass_override_kg` | **Confirmed** |
| Free-text after bind clears ref | **Confirmed** |
| BOM live vs missing SKU | **Confirmed** |
| LEVEL A on bound 5″ vs 10″ prop → `GAP-FRAME-PROP-SIZE` / structure INCOMPLETE | **Confirmed** |
| No production `bind_frame` caller | **Confirmed** — tests only |
| Suite | **Confirmed** — `pytest -q` → **2188** |

---

## Notes

### N1 — Mass-diverge test covers override path first

**CLOSED (Engineer procede 2026-09-04):** added
`test_invalidate_diverged_catalog_refs_frame_component_mass_diverges_from_sku`
(path a) and renamed override coverage to
`…_frame_override_diverges_from_component_mass` (path b).

### N2 — Optional doc row

**CLOSED (Engineer procede 2026-09-04):** `PHYSICAL_COMPONENT_CATALOG_V1.md`
§13 — IC-2 row added; deferred line now says assist (IC-3), not bind.

### N3 — CLI walk

**Not required.** Bind is test/API-only (ESC posture). No user-visible path
changed. A CLI walk would only matter after IC-3 assist.

---

## Slice / phase

| Item | Status |
|---|---|
| Catalog Foundation **IC-2** | **CLOSED** |
| IC-3 assist | **Not authorized** |
| IC-1 schema+seed | Already CLOSED |
| Layout / CAD | Out |
