# Implementation Review — Impl C Catalog-Aware DSE

**Date:** 2026-08-20  
**Reviewer:** Cursor (JES)  
**Contract:** [`.jes/artifacts/implementation_contract_impl_c_catalog_aware_dse.md`](implementation_contract_impl_c_catalog_aware_dse.md)  
**Report:** [`.jes/artifacts/implementation_report_impl_c_catalog_aware_dse.md`](implementation_report_impl_c_catalog_aware_dse.md)  
**Base:** tag `checkpoint-g21-g23` · commit `8dcc151`

## Verdict

**PASS WITH NOTES**

Slices C1 / C2 / C4 / C5 match the **locked IC scope** (generation + message + tests; no forbidden-file edits). Claude correctly STOP-and-reported rather than expanding scope. Full suite green (1908 passed + 1 skipped).

The two §4 findings are **real and product-blocking** for the Design exit criterion (“DSE candidates are catalog-constrained **and preserve identity through apply**”). They are **not** regressions introduced by this diff — they are pre-existing apply/bridge gaps that the investigation under-scoped. Impl C as shipped is **generation-correct**, not yet **product-complete**.

---

## Checklist

| Gate | Result |
|---|---|
| ★1 Option A (`components_delta` + `bind_motor_from_catalog`) | **Pass** |
| ★2 Strategy 3 + `build_motor_catalog_suggestions` only | **Pass** |
| ★3 motor-only goals; C3 deferred | **Pass** |
| ★4 bound-SKU exclusion | **Pass** |
| ★5 single-family / no count cross-product | **Pass** |
| ★6 `_score_candidate` untouched; labels show `[sku]` | **Pass** |
| ★7 no `bound_sku_status` | **Pass** |
| Forbidden files untouched (apply / G5 / G9-A / writers / catalog_bind) | **Pass** — `git diff --stat -- src/` = `design_explorer.py` + C4-only `orchestrator.py` |
| C1 algorithm §2.4 + explore() wiring §2.7 | **Pass** |
| C2 end-to-end chain for **first-bind** fixture | **Pass** |
| C4 exact fallback string | **Pass** |
| C3 not shipped | **Pass** |
| Full suite / zero weakened tests | **Pass** — 14 new pass + 1 honest skip |
| CLI probe 7/7 hard gates | **Pass** (with softened step-4 interpretation — see Note B) |
| Product exit: catalog identity survives real SKU-switch apply | **Fail residual** — Note A |
| Product exit: catalog candidates compete in top-5 / scored on own thrust | **Fail residual** — Notes A+B |

---

## Note A — `per_motor_max_thrust_n` bridge gap (critical residual)

**Confirmed by independent reproduction (reviewer):**

`set_motor_component` / `apply_components_delta` bridge `motor_power_w`, `motor_count`, `motor_kv_rating`, `motor_mass_kg` — **never** `per_motor_max_thrust_n`. Calc/sim read thrust only from that param (or aero/traction paths).

Consequences (all reproduced):

1. **Explore scoring of catalog candidates uses stale / missing thrust.** On a bound project (`per_motor_max_thrust_n=9.5`), applying a different catalog SKU in-memory during explore leaves params thrust at `9.5` while the candidate spec has e.g. `thrust_n=7.5`. Catalog candidates are scored as if thrust did not change — only mass/KV/power differ. With no prior thrust at all, catalog candidates get `available_total_thrust_n=None` → `can_fly=False` → never enter `.viable`.

2. **SKU-switch apply clears identity (G5 working as designed).** After forcing apply of a different catalog SKU onto a project with prior thrust:
   - `invalidate_diverged_catalog_refs` clears `catalog_ref`
   - `sync_motors_component_from_params` then overwrites component `thrust_n` back to the stale params value (`source="calculated"`)
   - Result: frankenstein unbound motor — new SKU `power_w`/`kv`/`weight_g`/`name`, old thrust, **no** `catalog_ref`, no `motor_mass_kg`

3. **First-bind / no-prior-thrust fixtures** (C2 tests + CLI Part B) preserve `catalog_ref` because invalidate’s guard requires both sides non-`None`. That is a real, narrower guarantee — correctly tested — **not** the user path “already bound → explore → apply a different SKU.”

Investigation §7 answer #2 (“cannot diverge from a fresh bind”) was correct for the case analyzed; it did **not** cover SKU-switch-against-declared-thrust, and assumed thrust would be bridged into params on component apply. That assumption is false.

**Disposition:** STOP-and-report was the correct action under §0. **Do not claim Impl C product-complete** until a follow-up IC bridges thrust on the component-driven apply path (and preferably during explore evaluation of catalog candidates so scoring is honest). Likely surface: small, deliberate change in `_handle_apply_exploration`’s component branch and/or `set_motor_component` when `output_magnitude == "thrust_n"` — requires Engineer ratification (explicitly forbidden in this IC).

---

## Note B — Catalog candidates lose top-5 under ★6 scoring

**Confirmed:** on the bound-motor fixture, top-5 `.viable` is 100% params-grid (e.g. `empuje/motor=19`, `motores=8`+thrust factor). Zero catalog SKUs in the CLI list. Abstract `per_motor_max_thrust_n_factor` wins because this physics model grants unbounded cost-free thrust; real SKUs are capped — and, per Note A, catalog candidates aren’t even scored on their own thrust.

`test_full_explore_apply_path_with_real_catalog_candidate` honest skip is appropriate.  
CLI probe step 4 asserting **generation** (`explore().candidates`) rather than **message top-5** is a soft reading of IC §7 step 4 (“List shows ≥1 candidate whose label contains `[sku]`…”). Acceptable as **observation** given ★6 lock; **not** a product win for “user sees catalog options.”

Future options (Engineer decide separately — **not** this IC):

- Prefer catalog-sourced candidates when present (tiebreak / ranking pass), or  
- Cap / de-emphasize unbounded abstract thrust factors for catalog-eligible goals, or  
- Fix Note A first so catalog candidates can earn score on real SKU thrust (necessary but not sufficient alone).

---

## What landed correctly

- `_build_catalog_motor_candidates_for_goal` matches IC §2.4 (G22 authority, ★4 exclusion, `had_library_matches` pre-exclusion semantics).
- Strategy 3 skip of synthetic motor deltas on `aumentar_payload` when search non-empty; fallback note exact string.
- Params grid always runs; `reducir_payload` / `reducir_masa` untouched.
- Label `[sku]` visibility; `ExplorationResult.catalog_motor_note`; C4 orchestrator message-only wiring.
- C2 proves first-bind apply → G9-A Scenario B → unrelated iterate preserves identity.
- No C3; no schema churn on `ExplorationCandidate`; no scoring change.

---

## Recommended next step (Engineer)

```text
Impl C generation  ✅  (this cut — OK to commit as intermediate)
        ↓
Follow-up IC — “catalog DSE thrust bridge”
  - Bridge per_motor_max_thrust_n from motors.properties.thrust_n
    on component-driven apply (and explore evaluation path)
  - Prove SKU-switch apply keeps catalog_ref + new thrust
  - Prove catalog candidates can enter .viable when SKU improves margin
  - Re-run CLI probe steps 3–6 without forcing viable[0]
        ↓
Only then: Impl C product CLOSED → Impl D
```

**Commit recommendation:** yes for this generation cut (clear residual documented). Tag only if Engineer wants an intermediate checkpoint; otherwise wait for thrust-bridge follow-up before `checkpoint-impl-c`.

---

**End of review.**
