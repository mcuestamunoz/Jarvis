# Implementation Review — Battery Catalog UX + G27 Hardening (IC 2)

**Date:** 2026-08-31  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/implementation_contract_battery_catalog_bind_ux_g27.md`](implementation_contract_battery_catalog_bind_ux_g27.md)  
**Report:** [`.jes/artifacts/implementation_report_battery_catalog_bind_ux_g27.md`](implementation_report_battery_catalog_bind_ux_g27.md)  
**Base:** tag `checkpoint-requirements-closure` · commit `e986a58`

## Verdict

**PASS WITH NOTES**

All Bat-1…Bat-8 gates met. Probe **6/6** and suite **1973/1973** re-run confirmed independently. The Bat-0 finding on **not** re-calling `set_motor_component` after battery bind is a material improvement over the contract's "unlikely" framing — correctly locked by regression test.

**Defect-first review:** No open findings that block checkpoint or IC 3.

---

## Contract checklist (§12)

| Criterion | Result |
|---|---|
| Bat-0 trace in report | **Pass** |
| Pick → bind → real Wh/mass/cells | **Pass** — probe step 3: `222.0`, `lipo_6s_10000mah` |
| Probe 6/6; suite green | **Pass** — re-run confirmed |
| G27 never 6 Wh for 6S 10000mAh | **Pass** — probe step 6 + parametrized tests |
| IC 1 / propulsion / motor / propeller regressions | **Pass** — 1960 baseline + targeted suites |
| No weakened tests | **Pass** — zero existing file edits |
| No hardcoded SKUs / parallel binder | **Pass** — `list_batteries()` via assist module |
| `_parse_value` global unchanged | **Pass** — battery branch only in `adapt()` |
| No fake PASS | **Pass** |

---

## Independent verification

```text
pytest tests/test_battery_catalog_bind_ux.py  → 13 passed (11 functions, 1 parametrized ×3)
pytest (full)                                 → 1973 passed
cli_probe_battery_catalog_bind_ux.py          → 6/6 PASS

Probe headline chain:
  ayúdame a elegir → lipo_6s_10000mah (#8)
  battery_capacity_wh=222.0
  calcular → autonomy_min=15.1364 (not 6 Wh collapse)
  estado → [lipo_6s_10000mah] resolved
  G27 adapt → 222.0 Wh, never 6.0
```

---

## Highlights

**Discipline order respected:** Bat-0 trace documented before UX; bind chain unchanged; only entry point + G27 added.

**Propulsion OP regression lock (§4.3):** `test_battery_pick_does_not_regress_already_resolved_propulsion_op` is high-value — re-calling motor writer after battery bind can **downgrade** exact→fallback when real pack voltage mismatches curated OP rows. Not refreshing is correct for a stronger reason than the IC assumed. **Ratify keeping this behavior.**

**G27 scope (★5):** `_resolve_battery_capacity_wh_from_text` + `canonical == "battery_capacity_wh"` gate; `_parse_value` untouched for other variables. Formula `mAh/1000 × cells × 3.7V` → 222.0 matches seed — acceptable per contract "acceptable outcomes."

**Battery list `limit=10`:** Correct for v1 catalog (10 seeds); `lipo_6s_10000mah` at index 8 would fail probe with `limit=5`. Disclosed deviation accepted.

---

## Notes (non-blocking)

### Note 1 — G27 post-bind test is structural

`test_g27_post_bind_adapter_is_stateless_never_touches_catalog_ref` proves `adapt()` cannot clear `catalog_ref` (no project_state). Full iterate-wizard overwrite path after a bad free-text apply is **not** re-tested here — acceptable for IC 2 gate; flag if Engineer wants iterate-integration test in IC 3 or debt backlog.

### Note 2 — Option B energy filter deferred

Documented in module docstring. No block — Option A satisfies all locked acceptance criteria.

### Note 3 — Uncommitted artifacts

IC 2 code + report + contract + probe are **local only** (not on `checkpoint-requirements-closure`). Engineer should **commit + tag** (e.g. `checkpoint-battery-catalog-bind-ux`) before IC 3, mirroring IC 1 discipline.

### Note 4 — Optional manual CLI walk

Same as IC 1: probe exercises real `handle_user_text` chain including `calcular`. Manual walk optional for product comfort (energy/autonomy feel), not required for review PASS.

---

## Next step

```text
IC 2 PASS WITH NOTES
  ↓
Engineer: commit + tag checkpoint-battery-catalog-bind-ux (recommended)
  ↓
Cursor: IC 3 — Closure policy + propeller sku_resolved
```

---

**End of review.**
