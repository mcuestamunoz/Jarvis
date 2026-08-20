# Implementation Review — G9-A Catalog-Ref Blind Spot (Option B)

**Date:** 2026-08-20  
**Reviewer:** Cursor (JES)  
**Contract:** `.jes/artifacts/implementation_contract_g9a_catalog_ref_blind_spot.md`  
**Report:** `.jes/artifacts/implementation_report_g9a_catalog_ref_blind_spot.md`  
**Investigation:** `.jes/artifacts/investigation_g9a_catalog_ref_blind_spot.md`  
**Base:** `checkpoint-r3b` (`4608eed`)

## Verdict

**PASS**

Option B delivered as ratified. Single authority in `resolve_motor_catalog_surface`, orchestrator dedup clean, Scenarios B/C/D honest, A/F unchanged, G9-B and G5 regressions green. The Scenario B `catalog_matches` deviation is **correct and required** — not a scope slip.

---

## Contract checklist (§6)

| # | Gate | Result |
|---|---|---|
| 1 | Bound-SKU branch before generic empty-search | **Pass** — `engineering_readiness.py:245–277` runs before `:279` generic path |
| 2 | Scenario B clears gap even when generic search would be empty | **Pass** — early return at `:262`; verified with `brotherhobby_avenger_2500` + 10 N/motor |
| 3 | Scenario C names SKU; evidence `bound_sku_underspec:{sku}` | **Pass** — message + gap registry fact asserted |
| 4 | Scenario D safe lookup, no KeyError | **Pass** — `has_motor` guard at `:248` |
| 5 | Orchestrator inline deleted; delegates | **Pass** — `orchestrator.py:3584–3594` |
| 6 | `test_cli_polish.py` G9-B unchanged | **Pass** — 4/4 in regression subset |
| 7 | G5 divergence test unchanged | **Pass** — `test_dse_apply_diverging_thrust_clears_motor_catalog_ref` |
| 8 | New tests + full suite | **Pass** — **1883** (reviewer re-run) |
| 9 | No Option C typed fields / new gap types | **Pass** — third return value is evidence fact only |

## Acceptance criteria (§4)

| # | Criterion | Result |
|---|---|---|
| 1 | Scenario B → no gap | **Pass** + catalog subsystem `PASS` |
| 2 | Scenario C → SKU-named gap | **Pass** |
| 3 | Scenario D → missing-SKU message | **Pass** |
| 4 | Unbound A/F unchanged | **Pass** — existing trigger/absent tests green |
| 5 | Orchestrator dedup | **Pass** |
| 6 | Startup context matches readiness for B/C/D | **Pass** — `test_g9a_catalog_ref_gap.py` |
| 7 | G9-B demotion + Scenario C | **Pass** — `CATALOG-GAP-DEMOTED-POST-PASS` |
| 8 | G5 divergence | **Pass** |
| 9 | CLI polish insulated | **Pass** |
| 10 | Full suite, zero weakened | **Pass** |

---

## Code review highlights

### Single authority — correct locus

Bound-SKU logic lives once in `resolve_motor_catalog_surface`. Orchestrator imports and delegates; the ~48-line duplicate is gone. Dependency direction remains one-way (orchestrator → engineering_readiness).

### Predicate factoring — semantics preserved

`_motor_covers_requirements` in `library.py:66–86` mirrors the per-candidate filter from pre-G9-A `find_motors_for_requirements`. List comprehension refactor at `:275–281` preserves sort key — unbound path behavior unchanged (existing tests confirm).

### Scenario B `catalog_matches` deviation — **approved**

Contract §1.3 left "empty or informational" open. Implementer correctly discovered that empty `catalog_matches` breaks `_catalog_evidence`'s `query_attempted = catalog_gap is not None or bool(catalog_matches)` (`engineering_readiness.py:950`), yielding catalog subsystem `INCOMPLETE` on the best case.

Returning `[bound motor]` via `_motor_catalog_matches_dicts([bound])` is accurate ("here is the part that satisfies this space") and aligns with acceptance criterion 1. **Recommend documenting this invariant in a one-line comment on `_catalog_evidence`** in a future hygiene pass — not blocking.

### Evidence threading — clean

Third return value `gap_evidence_fact` flows into `_motor_catalog_gaps` without new gap types. Fallback `catalog_gap_fact or "catalog_matches.empty"` at `:1091` is safe because `_motor_catalog_gaps` only runs when `catalog_gap is not None`.

### G9-B orthogonality — verified

G9-A changes *whether* the gap fires; G9-B demotion predicate untouched. `test_g9b_demotion_still_applies_with_bound_sku_underspec` proves Scenario C gap + PASS + declared thrust ≥ floor → `WARNING` / `CATALOG-GAP-DEMOTED-POST-PASS`.

---

## Deviations (reviewer disposition)

| Deviation | Disposition |
|---|---|
| Scenario B returns bound motor in `catalog_matches` (not empty) | **Approved** — required for catalog subsystem PASS |
| Optional `test_catalog_bind_v1.py` probe skipped | **Approved** — orchestrator smoke is superset |
| `_motor_covers_requirements` as module-level fn (not method) | **Approved** — contract left implementer choice |

No unapproved deviations.

---

## Notes (non-blocking)

1. **Scenario C + alternatives — new combined state.** When underspec but `find_motors_for_requirements` finds alternatives, `catalog_matches` is populated while `catalog_gap` is non-None. Continuity evidence uses `if motor_catalog_gap: … elif motor_catalog_matches:` (`project_continuity.py:144–148`), so candidate names won't appear in evidence while the gap wins — first time both can coexist for motors. `catalog_matches` is correct for downstream consumers; `next_why` still directs to `'qué motores tenemos'`. Future CLI polish could surface alternatives when both are set — **out of G9-A scope**.

2. **Double computation per turn** — ~~`build_startup_context` calls `resolve_motor_catalog_surface` once for Continuity fields, then `build_engineering_readiness` calls it again~~ **Closed in G9-A hygiene:** orchestrator is readiness-first; catalog surface exposed on `EngineeringReadinessResult`. `derive_physical_requirements` / `build_component_bom` still computed twice (orchestrator + readiness) — separate, lower-priority follow-up.

3. **Test gap (minor):** No automated test asserts Scenario C with **non-empty** `catalog_matches` (alternatives exist). Manual probe at 12 N/motor confirms three alternatives returned. Consider one assertion in a future hygiene commit — not blocking.

4. **`catalog_ref.family == "motor"`** — strict check; fine because `CatalogRef` schema requires family literal and `bind_motor_from_catalog` always sets `"motor"`.

---

## Tests (reviewer re-run)

```
pytest tests/test_engineering_readiness_gaps.py tests/test_g9a_catalog_ref_gap.py \
       tests/test_cli_polish.py tests/test_catalog_bind_v1.py::test_dse_apply_diverging_thrust_clears_motor_catalog_ref \
       tests/test_g5_dse_iterate_dual_truth.py -q   → 44 passed

pytest -q                                           → 1883 passed
```

6 new tests (3 + 3). Zero weakened. Zero regressions.

---

## Queue

```text
G9-A PASS (uncommitted)
        ↓
batch commit + checkpoint-g9a (when Engineer asks)
        ↓
Impl C → Impl D → Phase 2
```

---

**End of review.**
