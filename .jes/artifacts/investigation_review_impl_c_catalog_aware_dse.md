# Investigation Review — Impl C Catalog-Aware DSE

**Date:** 2026-08-20  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/investigation_contract_impl_c_catalog_aware_dse.md`](investigation_contract_impl_c_catalog_aware_dse.md)  
**Report:** [`.jes/artifacts/investigation_report_impl_c_catalog_aware_dse.md`](investigation_report_impl_c_catalog_aware_dse.md)  
**Base:** tag `checkpoint-g21-g23` · commit `8dcc151`

## Verdict

**PASS**

Investigation complete, all 14 required sections present, zero `src/` changes (investigation-only, as scoped). Central finding confirmed by independent code trace: **Impl C's work is candidate generation in `design_explorer.py`, not apply-path surgery.**

## Checklist

| Gate | Result |
|---|---|
| §1.1 pipeline audit (explore → apply → persist) | **Pass** — sequence + goal table |
| §1.2 catalog API inventory | **Pass** — reuse `build_motor_catalog_suggestions` (G22 authority) |
| §1.3 goal × family matrix + v1 scope | **Pass** |
| §1.4 candidate shape options (≥2) | **Pass** — A/B/C with trade-offs |
| §1.5 grid strategy options (≥2) | **Pass** — Strategies 1/2/3 |
| §1.6 apply + identity (4 direct answers) | **Pass** — reviewer re-traced `set_motor_component` |
| §1.7 G9-A / G5 / G21 interaction | **Pass** |
| §1.8 unbound vs bound matrix | **Pass** |
| §1.9–1.10 scoring + cache | **Pass** |
| §1.11 test inventory + CLI probe | **Pass** — gap identified (no test for catalog-ref survives component apply) |
| §1.12 slice outline | **Pass** — C1–C5 |
| ★ decisions numbered for Engineer | **Pass** — ★1–★8 |
| No production fix in this cut | **Pass** |
| No LLM SKU selection / dual search authority | **Pass** |

## Code review highlights

**Apply path already sufficient.** `set_motor_component` writes the full `ComponentSpec` verbatim (`component_writers.py:207`), including `catalog_ref`. G5's `invalidate_diverged_catalog_refs` is a no-op for a self-consistent catalog bind (thrust in params derived from the same spec's `thrust_n`). Same contract acquisition already relies on — no orchestrator changes required for identity preservation.

**Real gap surfaced:** `test_catalog_bind_v1.py` covers params-only divergence clearing; **no test** proves `components_delta` catalog apply preserves `catalog_ref`. C2 (test-only slice) is correctly scoped.

**Grid strategy recommendation accepted:** Strategy 3 on Strategy 1's generation function — catalog branch via `build_motor_catalog_suggestions`, skip synthetic `COMPONENT_VARIATION_RULES` when catalog returns matches, honest fallback when empty. Resolves dual-authority risk without scoring tiebreak hacks.

**Minor implementer note (non-blocking):** `bind_motor_from_catalog(..., base=existing)` may leave stale `spec.name` — one-line fix in generation function (`name=sku` on copy). Does not affect DSE labels (`_build_label_components` reads properties, not `.name`).

**★8 (frame component-rule mismatch):** valid discovery, correctly deferred out of Impl C scope.

## Notes (non-blocking)

1. C3 (battery) should stay optional unless Engineer explicitly folds it into v1 — no acquisition-side battery ranking precedent yet (`find_batteries` is threshold-only).  
2. Slice C4 (fallback messaging) is small but user-visible — include in IC, not optional polish.  
3. CLI probe script can mirror `scripts/cli_probe_g21_g22_post_checkpoint.py` pattern from checkpoint-g21-g23.

## Next step

Engineer ratifies ★1–★7 (★8 is informational only) → Cursor drafts `implementation_contract_impl_c_catalog_aware_dse.md`.
