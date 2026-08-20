# Implementation Report — G9-A Catalog-Ref Blind Spot (Option B)

**Contract:** [`implementation_contract_g9a_catalog_ref_blind_spot.md`](implementation_contract_g9a_catalog_ref_blind_spot.md)
**Investigation:** [`investigation_g9a_catalog_ref_blind_spot.md`](investigation_g9a_catalog_ref_blind_spot.md)
**Checkpoint base:** `checkpoint-r3b` (`4608eed`)
**Status:** Implemented, all 3 slices, 6 new tests added, full suite green (1883). **Not committed.**

---

## Slices completed

- [x] Slice 1 — bound-SKU-aware `resolve_motor_catalog_surface`
- [x] Slice 2 — orchestrator dedup (delegate to shared function)
- [x] Slice 3 — interaction regressions (G9-B, G5) + full suite

---

## Files changed

| File | What |
|---|---|
| `src/jarvis/knowledge/library.py` | New module-level `_motor_covers_requirements(m, *, min_thrust_n, kv, prop_inch)` — the single-motor predicate `find_motors_for_requirements` already applied per-candidate, factored out for reuse against one bound `MotorSpec`. `find_motors_for_requirements` rewritten to use it (pure refactor, same filter/sort order — behavior-preserving). |
| `src/jarvis/core/engineering_readiness.py` | `resolve_motor_catalog_surface` — added bound-`catalog_ref` branch (Scenarios B/C/D) ahead of the existing generic-search path (A/F, unchanged). New return signature: `(catalog_gap, catalog_matches, gap_evidence_fact)`. `_motor_catalog_gaps` takes `gap_evidence_fact` kwarg instead of hardcoding `"catalog_matches.empty"`. `build_engineering_readiness` call site updated to unpack and pass the third value. New helper `_motor_catalog_matches_dicts` (dedup of the match→dict projection, used by both the bound and unbound paths). **Hygiene (post-review):** `EngineeringReadinessResult` exposes `motor_catalog_gap`, `motor_catalog_matches`, `motor_catalog_gap_fact` so consumers need not re-invoke the resolver. |
| `src/jarvis/core/orchestrator.py` | Deleted the ~48-line inline catalog-gap block from `build_startup_context`; **readiness-first:** calls `build_engineering_readiness` once and plucks catalog surface from the result for Continuity/startup dict (no second `resolve_motor_catalog_surface` call). |
| `tests/test_engineering_readiness_gaps.py` | 3 new tests (Scenarios B/C/D) using a real library fixture (`brotherhobby_avenger_2500`), exercising both `resolve_motor_catalog_surface` directly (message/fact assertions) and `build_engineering_readiness` (Gap Registry assertions). Existing 2 tests unchanged, still passing. |
| `tests/test_g9a_catalog_ref_gap.py` | New — 5 tests: readiness-first smoke (Scenario B/C), startup/readiness parity, **single catalog-resolver invocation** (mock call-count), G9-B demotion regression. |

No changes to `bind_motor_from_catalog`, `invalidate_diverged_catalog_refs`, `catalog_gap_covered_by_declared_thrust`, `_INCOMPATIBLE_CLASS_GAP_TYPES`, or any electrical-compatibility code.

---

## Scenario probe results

| Scenario | Probe | Result |
|---|---|---|
| B (bound, covers) | `test_gap_motor_catalog_unresolved_absent_when_bound_sku_covers` + orchestrator smoke | `catalog_gap is None`, gap absent from registry, catalog subsystem verdict `PASS` |
| C (bound, underspec) | `test_gap_motor_catalog_unresolved_bound_sku_underspec` + orchestrator smoke | Gap present, message names the SKU (`brotherhobby_avenger_2500`), does **not** contain the bare "no tengo un motor en el catálogo" string, evidence `bound_sku_underspec:{sku}` |
| D (bound, SKU deleted) | `test_gap_motor_catalog_unresolved_bound_sku_missing_from_library` | Gap present, "ya no está en el catálogo" message, evidence `bound_sku_missing:{sku}`, no exception raised |
| A/F (unbound) | Existing `test_gap_motor_catalog_unresolved_trigger` / `_absent_when_matches_found` | Unchanged, passing byte-for-byte |

---

## Deviation found and fixed during implementation (not in the contract text)

**Scenario B's "empty or informational `catalog_matches`" choice matters for the catalog subsystem's own verdict — empty breaks it.**

`_catalog_evidence` (unmodified by this IC) derives `query_attempted = catalog_gap is not None or bool(catalog_matches)`, and `_derive_subsystem_verdict` returns `INCOMPLETE` whenever `evidence.defined` is `False`. The contract's §1.3 step 2 allowed "return early with empty or informational `catalog_matches`" for Scenario B without specifying which — an empty list makes `query_attempted = False`, which would have made the **best-case** scenario (bound, sufficient, no gap) read as catalog subsystem `INCOMPLETE` instead of `PASS`, contradicting the contract's own acceptance criterion 1 (Scenario B should be the clean case) and creating exactly the kind of rollup contradiction §0/investigation §3 asked to avoid.

**Fix:** Scenario B returns `catalog_matches = [the bound motor itself]` (via the existing `_motor_catalog_matches_dicts` projection) instead of an empty list — an accurate, non-fabricated statement ("here is the part that satisfies this space"), not a search result. Verified directly: `test_gap_motor_catalog_unresolved_absent_when_bound_sku_covers` asserts `result.subsystems["catalog"].verdict == "PASS"`.

---

## G9-B / G5 regression confirmation

- **G9-B:** `test_g9b_demotion_still_applies_with_bound_sku_underspec` — Scenario C gap (`bound_sku_underspec:{sku}` evidence) + PASS + declared thrust covering the physics floor → catalog subsystem verdict is `WARNING` with `warning_type == "CATALOG-GAP-DEMOTED-POST-PASS"`, exactly as it would be for a plain Scenario-A gap. G9-A only changed *why* the gap fired, not G9-B's independent demotion predicate (`catalog_gap_covered_by_declared_thrust`, untouched).
- **G5:** `tests/test_catalog_bind_v1.py::test_dse_apply_diverging_thrust_clears_motor_catalog_ref` — unchanged, passing. Divergence clears `catalog_ref` before this code ever sees it, so a diverged motor is Scenario A/F by construction, unaffected by the new bound-SKU branch.
- **`test_cli_polish.py` (G9-B):** unchanged, passing — those tests pass `motor_catalog_gap` as a pre-built string literal directly into `build_project_continuity`, insulated from the computation change (confirmed in the investigation, verified again here).

---

## Test count / suite result

```
python -m pytest tests/test_engineering_readiness_gaps.py tests/test_g9a_catalog_ref_gap.py -v   # 25 passed
python -m pytest -q                                                                                # 1885 passed
```

1877 baseline (post-`checkpoint-r3b`) + 8 new tests (3 in `test_engineering_readiness_gaps.py`, 5 in `test_g9a_catalog_ref_gap.py`) = 1885. Zero weakened tests — no existing assertion was loosened or removed.

---

## Deviations from the contract

1. **Scenario B `catalog_matches` content** — documented above; the contract left this open ("empty or informational") and the informational choice was required for correctness, not optional.
2. **Optional thin probe in `tests/test_catalog_bind_v1.py`** (§2 Slice 1, "Optional") — **not added**. `test_build_startup_context_motor_catalog_gap_delegates_to_shared_resolver` (Slice 2, this report) already exercises the identical bind → `resolve_motor_catalog_surface` → `catalog_gap is None` path end-to-end through the full orchestrator, which is a superset of what the optional probe would add. Skipped to avoid a redundant test per the project's "no premature duplication" discipline.
3. No other deviations. `_motor_covers_requirements` was implemented as a plain module-level function in `library.py` (not a `ComponentLibrary` method) since it operates on a single already-loaded `MotorSpec` with no library I/O — the contract left this implementer's choice open explicitly.
4. **Readiness-first catalog surface (post-review hygiene, bundled in G9-A commit):** orchestrator no longer calls `resolve_motor_catalog_surface` separately; catalog fields exposed on `EngineeringReadinessResult`. Documented in review §Notes item 2 — closed here, not deferred.

---

## Remaining risks

- Same as the investigation flagged: no equivalent gap computation exists for battery/propeller `catalog_ref` — confirmed still true, out of scope here by design (contract §0).
- Option C's typed `bound_sku_status` field remains unimplemented, as directed — any future consumer wanting to branch on bound-SKU state programmatically (rather than displaying the message) still has to string-match, same as before this IC.
