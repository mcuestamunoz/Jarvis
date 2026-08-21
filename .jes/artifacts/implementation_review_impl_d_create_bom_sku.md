# Implementation Review — Impl D Create → BOM / SKU BOM

**Date:** 2026-08-21  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/implementation_contract_impl_d_create_bom_sku.md`](implementation_contract_impl_d_create_bom_sku.md)  
**Report:** [`.jes/artifacts/implementation_report_impl_d_create_bom_sku.md`](implementation_report_impl_d_create_bom_sku.md)  
**Base:** tag `checkpoint-impl-c` · commit `c99fec6`

## Verdict

**PASS WITH NOTES**

D1–D4 match the ratified ★ locks. Diff is minimal and correctly scoped. Scenario D honesty is proven with the real G5 invalidate path. ★6 D4 is presentation-local (one boolean). No Continuity / G9-A / ERF verdict / new gap type drift.

**Defect-first review:** No findings.

## Checklist

| Gate | Result |
|---|---|
| ★1 Option A — extend `build_component_bom`, no parallel BOM | **Pass** |
| ★2 family-agnostic schema; motors+battery resolve via `has_*` | **Pass** |
| ★3 no Continuity / Create-handoff | **Pass** — `project_continuity.py` untouched |
| ★4 no `GAP-BOM-SKU-UNRESOLVED` | **Pass** |
| ★5 `catalog_bound` / verdict untouched | **Pass** — `engineering_readiness.py` untouched |
| ★6 D4 presentation-only or STOP | **Pass** — shipped; `if bom_lines:` only |
| `sku_resolved` never from `.name` | **Pass** — `_bom_sku_resolved` takes only `catalog_ref` dict |
| Field `name` kept (not renamed) | **Pass** |
| ESC `quantity is None` | **Pass** |
| Tests D3 (6) + named regressions | **Pass** — re-ran `test_impl_d_sku_bom` + closure: 18 passed |
| Report claims vs `git diff --stat -- src/` | **Pass** — only `project_closure.py` + `cli/main.py` |
| G5 / `catalog_bind.py` untouched | **Pass** |

## Code review highlights

**D1 helpers are correctly shaped.** `_bom_sku_resolved` never receives `.name`, so frankenstein cannot lie through the resolve path. Scenario C uses the same `default_library.has_motor` / `has_battery` surface as G9-A — no second catalog reader.

**D2 formatting is honest.** `[sku]` only when `sku_resolved`; unbound/frankenstein get neither bracket nor `(SKU sin resolver)`; bound-but-unresolved gets `(SKU sin resolver)`.

**D4 is the exact allowed change.** Diff is the Continuity-evidence gate removal on BOM lines only. Sibling `req_lines` gate left alone per IC §5.2.

**Frankenstein test is the spine.** Uses real `invalidate_diverged_catalog_refs`, asserts `.name == sku` while `catalog_ref is None`, and asserts formatted line has no `[sku]`.

## Notes (non-blocking)

1. **Scenario C unit coverage gap:** code + format path for “`catalog_ref` set but SKU missing from library” exists (`(SKU sin resolver)`), but there is no dedicated automated test that stubs/removes a SKU and asserts the marker. Frankenstein (D) and bound (B) are covered. Optional one-liner follow-up — **do not block checkpoint**.

2. **`req_lines` suppression** remains (intentional sibling debt). Flag again for a future tiny presentation IC.

3. **Untracked deliverables** at review time: `tests/test_impl_d_sku_bom.py`, `scripts/cli_probe_impl_d_sku_bom.py`, investigation/IC/report artifacts — include them in the Impl D commit when Engineer asks (do not commit `workspace/`).

## Next step

Engineer: CLI walk optional → commit (+ tag `checkpoint-impl-d` if desired) → queue Create-handoff / req_lines gate / Phase 2 as separate work. G24–G27 still deferred.
