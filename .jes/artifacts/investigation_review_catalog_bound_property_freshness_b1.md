# Investigation Review — Catalog-bound Property Freshness B1

**Date:** 2026-09-08  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_catalog_bound_property_freshness_b1.md](investigation_contract_catalog_bound_property_freshness_b1.md)  
**Report:** [investigation_report_catalog_bound_property_freshness_b1.md](investigation_report_catalog_bound_property_freshness_b1.md)

## Verdict

**PASS WITH NOTES**

Default lean **B1 — Refresh-from-`catalog_ref` (generic across five `bind_*` families)** is Buy-ready. B0 correctly rejected as unsafe; B1+/B2 correctly rejected.

Engineer ★ still required before Claude implements the IC below (Cursor authors IC READY in parallel for speed).

---

## Checklist

| Criterion | Result |
|---|---|
| Executive lean B1 generic | **Pass** |
| Evidence (seed 15 / project 26 / no ESC rebind) | **Pass** — reconfirmed |
| `base=` merge preserves `mounted_on` | **Pass** — cite + empirical claim consistent with `catalog_bind.py` |
| Free-text walk destructive | **Pass** — `set_control_component` wholesale replace |
| Buy options + rejection of B0/B1+/B2 | **Pass** |
| Fase 2/3 / fit / pose / identity out | **Pass** |
| No code this cycle | **Pass** |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| Seed ESC `mass_g=15` | **Confirmed** |
| Demo esc `mass_g=26` + `catalog_ref` + `mounted_on` | **Confirmed** (prior triage) |
| Idle rebind has no `esc` | **Confirmed** |
| `CatalogRef.family` Literal includes esc/motor/battery/propeller/frame | **Confirmed** (`action_schema.py`) |
| FC/Here3 not in bind_* | **Confirmed** — refresh cannot touch them |

---

## Notes for IC

### N1 — Dispatch by `catalog_ref.family`, write by component key

Component keys are `motors` / `propellers` but families are `motor` / `propeller`. IC must lock: resolve component by user noun → key; call binder with `family` from `catalog_ref`; never assume key == family.

### N2 — Confirmation copy

Must list changed physicals (at least mass) with before→after; forbid “corregido automáticamente” / “verificado”.

### N3 — Demo stays stale until Buy + user phrase

IC smoke: after implement, Continuity refresh on demo project → Board shows 15.

---

## Agreement

1. Refresh reuses `bind_*(sku, base=spec)` — correct.  
2. Generic five-family writer — correct (near-zero marginal cost).  
3. No-picker Continuity verb — correct for 1-SKU ESC and for “numbers stale, identity ok”.  
4. Do not walk free-text ESC — correct and load-bearing.

---

## Phase

Investigation **reviewable**. IC READY authored for ★ Buy B1 → Claude implement.
