# Implementation Review — G24 Viable Selection + Honest CTA (IC C)

**Date:** 2026-08-31  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/implementation_contract_g24_viable_selection_honest_cta.md`](implementation_contract_g24_viable_selection_honest_cta.md)  
**Report:** [`.jes/artifacts/implementation_report_g24_viable_selection_honest_cta.md`](implementation_report_g24_viable_selection_honest_cta.md)  
**Base:** tag `v0.3.1` / `checkpoint-next-engineering-block` · commit `30c9aec`

## Verdict

**PASS WITH NOTES**

All G24C-1…G24C-6 contract gates met for IC C scope. Hardest constraint verified independently: **`_score_candidate` function body — zero diff**. Primary gate (investigation §5.1 repro) fixed on real `explore()` without G24-TF. G24-A + G24C compose end-to-end on the product path the investigation identified as broken on baseline.

**Defect-first review:** No open findings that block IC C closure or checkpoint planning (pending IC D review).

---

## Contract checklist (§6)

| Criterion | Result |
|---|---|
| `aumentar_payload` / `mejorar_estabilidad` → ≥1 catalog-native in `.viable` | **Pass** — parametrized primary gate + live repro (catalog at index 5, score 2.1063 unchanged) |
| `_score_candidate` zero diff | **Pass** — `def _score_candidate` absent from diff; helper never calls it |
| G24-A probe 6/6; new probe 6/6 | **Pass** — independent subprocess verification |
| Full suite green | **Pass** — **2025/2025** (current tree; includes IC D WIP landed in parallel — see Note 1) |
| CTA when `#1` abstract + catalog at `N>1` | **Pass** — probe step 3 + orchestrator branch |
| `"aplica la N"` preserves `catalog_ref` without G24-TF | **Pass** — `test_apply_by_index_on_real_viable_output_no_hand_built_reorder` + probe step 4 |
| No scores mutated to force inclusion | **Pass** — `id()`-keyed score assertions in unit test |
| No G24-A regressions | **Pass** — `"aplica la mejor"` → `#1`; apply-by-index probe unchanged |
| IC C touch set (no IC D / no scoring rewrite) | **Pass** — IC C `src/` delta is `design_explorer.py` + `orchestrator.py` only |

---

## Independent verification

```text
pytest tests/test_g24_viable_selection.py              → 11 passed
pytest tests/test_g24_apply_by_index.py                → 5 passed
pytest tests/ (full)                                   → 2025 passed
cli_probe_g24_viable_selection_honest_cta.py           → 6/6 PASS
cli_probe_g24_apply_by_index.py                        → 6/6 PASS

git diff HEAD -- src/jarvis/core/design_explorer.py
  → _finalize_viable_list, _is_catalog_native_motor_candidate added;
    explore() tail uses helper; def _score_candidate not in diff

Live repro (bound motor + declared thrust):
  aumentar_payload:    catalog_positions=[5]  (was [])
  mejorar_estabilidad: catalog_positions=[5]  (was [])
  reducir_masa:        catalog_positions=[]   (unchanged no-op)
```

---

## Code review highlights

**G24C-1 — selection-only, goal-agnostic.** `_finalize_viable_list` implements locked ★3(a) algorithm: sort by existing `.score`, reserve one slot for best catalog-native when truncated out. Called once at `explore()` return — replaces bare `sort + [:MAX_VIABLE]` without touching generation or scoring paths.

**Predicate single authority.** `_is_catalog_native_motor_candidate` matches contract §2.1 verbatim and is reused by both selection and CTA — avoids divergent "catalog-native" definitions across subsystems.

**Identity vs equality hardening — accepted.** Report disclosure is correct: Pydantic value equality could duplicate or mis-match objects under the locked `in head` check. Implementation uses `is` throughout; unit test locks score preservation via `id()` lookup. Strictly a correctness refinement of the locked algorithm, not a semantic deviation.

**G24C-5 — honest CTA without mutating state.** Message branches append after the frozen `"aplica la mejor"` line. Points to real catalog index when `#1` is abstract; secondary branch for generated-but-not-viable catalog rows. `reducir_masa` correctly silent (zero catalog dimension).

**G24 arc closure.** Investigation gap is real and now closed on the primary path:

```text
Impl C generates catalog candidates
        ↓
_finalize_viable_list (★3a)
        ↓
≥1 catalog-native in .viable
        ↓
honest CTA → "aplica la N"
        ↓
G24-A preserves catalog_ref
```

No G24-TF required for the §5.1 repro gate.

---

## Disclosed additions — accepted

1. **Extra unit tests beyond contract minimum** — multiple-catalog reservation, short-input length, freeform motor delta predicate. Append-only; strengthen regression without scope creep.

2. **Import of `_is_catalog_native_motor_candidate` in orchestrator** — pragmatic shared predicate; acceptable given contract's single-definition intent.

3. **"Generated but unflyable" CTA branch** — logic present; no live seed found for end-to-end exercise this session. Verified by code inspection against same predicate tested elsewhere. Non-blocking.

---

## Notes (non-blocking)

### Note 1 — Working tree includes IC D in parallel

At review time the workspace also contains IC D (`catalog_bind.py`, `test_impl_d_sku_bom.py`) and a disclosed assertion update in `test_bound_motor_aplica_la_mejor_clears_catalog_ref`. These are **outside IC C scope** but explain why the tree is ahead of the IC C report's "exactly 2 `src/` files" snapshot. IC C review scoped to `design_explorer.py` + `orchestrator.py` CTA delta remains clean.

### Note 2 — G24-B still deferred

Reservation fixes **visibility**, not ranking philosophy. Abstract `#1` can still outscore every catalog row; user must explicitly choose catalog via `aplica la N`. Matches Engineer ★3(a) — not a defect.

### Note 3 — Only one catalog slot guaranteed

When multiple catalog-native candidates exist, only the best-scoring survives truncation. Contract-locked; test `test_finalize_viable_only_reserves_best_of_multiple_catalog_candidates` documents intent.

---

## Queue

```text
IC C — PASS WITH NOTES (this review)
  ↓
IC D (Frankenstein .name) — separate review in flight
  ↓
Both PASS → Engineer checkpoint + 0.3.x (★6)
```

No tag, no version bump in this review.

---

**End of review.**
