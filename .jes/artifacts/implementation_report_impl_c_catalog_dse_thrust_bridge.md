# Implementation Report — Impl C Follow-up: Catalog DSE Thrust Bridge

**Contract:** [`implementation_contract_impl_c_catalog_dse_thrust_bridge.md`](implementation_contract_impl_c_catalog_dse_thrust_bridge.md)
**Parent IC:** [`implementation_contract_impl_c_catalog_aware_dse.md`](implementation_contract_impl_c_catalog_aware_dse.md) (generation cut, still uncommitted)
**Parent review:** [`implementation_review_impl_c_catalog_aware_dse.md`](implementation_review_impl_c_catalog_aware_dse.md) — PASS WITH NOTES (Note A = this residual)
**Status:** Implemented. Full suite green (1917 passed, 0 skipped — the prior honest skip is now a real pass). **Not committed** — this and the parent generation cut are meant as one combined commit, per §0.

---

## 1. Summary

`set_motor_component` now bridges `ComponentSpec.motors.properties["thrust_n"]` into `current_parameters["per_motor_max_thrust_n"]` whenever that property is present on the applied spec — the sole source (★1), never invented from power_w/KV/a library re-lookup. This one, narrow change closes both consequences traced in the parent review's Note A:

1. **Explore evaluation** now scores catalog candidates using their own real thrust (previously stale/`None`).
2. **Real SKU-switch apply** now preserves `catalog_ref` — the new spec's thrust is on the params side *before* G5's `invalidate_diverged_catalog_refs` runs, so there is nothing to diverge against; `sync_motors_component_from_params` then sees matching values and makes no further change.

A welcome side effect, not separately engineered: on a project with **no prior thrust declared at all**, every abstract params-grid entry that references `per_motor_max_thrust_n` (`per_motor_max_thrust_n_factor`, and the combo entries) is now omitted by `_apply_delta`'s own missing-param guard — while catalog candidates still evaluate correctly (their thrust comes from their own bound spec, independent of the params grid). On that fixture shape, real catalog candidates win `.viable`'s natural top-5 **without any scoring change** — the "scoring dominance" observation from the parent report was specific to *already-declared-thrust* fixtures, not universal. Confirmed with both the automated tests and the CLI probe (§6-§7).

---

## 2. Files changed

| File | What |
|---|---|
| `src/jarvis/core/component_writers.py` | `set_motor_component` — one new bridge block (7 executable lines) + docstring updates explaining the bridge and why it deliberately does *not* pop `per_motor_max_thrust_n` when `thrust_n` is absent. |
| `tests/test_impl_c_catalog_dse_thrust_bridge.py` | New — 8 tests (contract §7's full list). |
| `tests/test_impl_c_catalog_aware_dse.py` | One stale assertion fixed (`test_catalog_native_dse_apply_survives_unrelated_iterate` — previously asserted `per_motor_max_thrust_n is None` right after a component-driven apply; now correctly asserts it equals the bound SKU's thrust, since the bridge populates it). One test promoted from an honest `skip` to a real, unforced pass (`test_full_explore_apply_path_with_real_catalog_candidate` — now uses a no-prior-thrust fixture where catalog candidates are naturally viable, per §1's side effect). |
| `scripts/cli_probe_impl_c_catalog_dse.py` | Part B's step 4/5 rewritten: reads the *real* `session.last_exploration_result` from the actual "optimiza para..." turn (no manual `ExplorationResult` construction); step 5 applies a candidate already present in the natural `.viable` list (reordering only among already-viable entries when needed — never splicing in a non-viable one, per §8). Module docstring updated. |

No changes to `orchestrator._handle_apply_exploration`, `component_sync.py` (G5), `engineering_readiness.py` (G9-A), `catalog_bind.py`, `design_explorer.py`, or `_score_candidate` / `ExplorationCandidate`. No STOP was needed — the bridge alone closed the gap without touching any forbidden surface.

---

## 3. Bridge rule implemented (exact condition)

```python
thrust_prop = spec.properties.get("thrust_n")
if thrust_prop is not None and thrust_prop.value is not None:
    updated_params["per_motor_max_thrust_n"] = float(thrust_prop.value)
```

Placed in `set_motor_component`, right after the existing `kv_rating` bridge. **Deliberately no `else: pop(...)`** — unlike `motor_kv_rating`'s bridge, which does pop when the property is absent. Rationale (★1's "leave untouched" wording, and confirmed necessary by inspection): a freeform motor re-declare (e.g. updating only `power_w` on an existing spec with no `thrust_n` property) must not silently erase a numeric-wizard-declared `per_motor_max_thrust_n` that has nothing to do with this particular write. Popping unconditionally would have been a real, unwanted behavior change to the freeform/synthetic path — confirmed by `test_synthetic_motor_without_thrust_n_leaves_param_untouched`.

Chose "bridge whenever `thrust_n` is present" over "only when `output_magnitude == 'thrust_n'`" (the contract's optional refinement) — every real catalog bind already sets both together (`bind_motor_from_catalog` sets `output_magnitude="thrust_n"` in the same call that sets the `thrust_n` property), so the two conditions are equivalent in practice for every actual caller; checking `thrust_n` presence alone is the simpler, sufficient condition and matches ★1's literal wording ("when that property is present").

---

## 4. Confirm G5 order / G9-A / scoring / `catalog_bind` untouched

```
$ git diff --stat -- src/
 src/jarvis/core/component_writers.py |  22 +++++
 src/jarvis/core/design_explorer.py   | 155 ++++++++++++++++++++++++++++++++++-
 src/jarvis/core/orchestrator.py      |  12 ++-
```

`design_explorer.py` and `orchestrator.py` are the **pre-existing, already-approved** generation-cut diffs from the parent IC — unchanged by this follow-up. `component_writers.py` (22 lines) is the only new production change. No STOP was triggered; §9's conditions never arose.

---

## 5. SKU-switch evidence

`tests/test_impl_c_catalog_dse_thrust_bridge.py::test_catalog_native_sku_switch_preserves_identity_and_new_thrust` runs the exact §4 chain: project bound to SKU A (`brotherhobby_avenger_2500`, 9.5N) → manual catalog candidate for SKU B (`sunnysky_r2305_2500`, 7.5N, `base=` the existing A spec) → `_handle_apply_exploration()` → saved state has `catalog_ref.sku == B`, `properties["thrust_n"].value == 7.5`, `current_parameters["per_motor_max_thrust_n"] == 7.5`, `motor_count` unchanged (6), and `build_engineering_readiness` reports **zero** `GAP-MOTOR-CATALOG-UNRESOLVED`. `..._survives_unrelated_iterate` extends the same chain through a `safety_factor` iterate turn — identity, thrust, and motor_count all still match SKU B afterward. Independently re-verified via a standalone script (not just the test suite) before writing these tests — see the session's own working notes; SKU-switch now applies with `catalog_ref` intact end to end.

---

## 6. Viability evidence

`test_real_catalog_candidate_can_be_viable_with_correct_thrust` — a project with `motor_count` declared but *no* prior thrust anywhere (no bound/freeform motor, no manual declare) — asserts `explore(..., goal).viable` contains ≥1 real-SKU candidate with `can_fly=True`, for both `aumentar_payload` and `mejorar_estabilidad`. Confirmed empirically (and in this test) that for this fixture shape **all 5** natural top-5 `.viable` entries are catalog candidates, not just "at least one" — the params-grid entries that would otherwise compete are omitted outright (no declared thrust to reference), not merely outscored.

---

## 7. Scoring observation (top-5 catalog visibility)

**Not modified, as locked (★3/★8).** Two distinct fixture shapes now behave differently, and both are correct/expected given the locked scoring formula:

- **Already-declared-thrust project** (e.g. a motor bound via acquisition, `per_motor_max_thrust_n` already on record): abstract params-grid entries (`per_motor_max_thrust_n_factor: 2.0`, etc.) still out-score real catalog candidates, because this simulator's physics model gives declared-thrust increases unbounded, cost-free upside while a real SKU is bounded by the library's actual numbers — unchanged from the parent report's finding, since the bridge doesn't touch scoring.
- **No-prior-thrust project**: params-grid thrust-referencing entries are omitted entirely (missing-param guard fires), so catalog candidates face less competition and win the natural top-5 — demonstrated in §6 and in the CLI probe (§9).

No scoring change was made or considered necessary to satisfy this contract's exit criterion — §10's wording ("demonstrate via tests + CLI that a catalog candidate can be viable without splicing a non-viable candidate into `viable[0]`") is satisfied by the no-prior-thrust fixture shape, which required no scoring intervention.

---

## 8. Tests + suite count

`tests/test_impl_c_catalog_dse_thrust_bridge.py` — 8 tests, all from contract §7's list (one additional: `test_synthetic_motor_without_thrust_n_leaves_param_untouched`, proving the deliberate no-pop behavior §3 explains):

- `test_component_driven_catalog_thrust_bridges_to_params`
- `test_synthetic_motor_without_thrust_n_leaves_param_untouched`
- `test_catalog_dse_evaluation_uses_candidate_thrust`
- `test_catalog_native_sku_switch_preserves_identity_and_new_thrust`
- `test_catalog_native_sku_switch_survives_unrelated_iterate`
- `test_real_catalog_candidate_can_be_viable_with_correct_thrust`
- `test_first_bind_c2_regression_still_preserves_catalog_ref`
- `test_params_only_diverging_apply_still_clears_catalog_ref`

```
python -m pytest tests/test_impl_c_catalog_dse_thrust_bridge.py -v   # 8 passed
python -m pytest tests/test_impl_c_catalog_aware_dse.py -v           # 15 passed (0 skipped, was 14+1 skip)
python -m pytest -q                                                   # 1917 passed
```

1909 baseline (parent IC: 1894 + 14 pass + 1 skip) − 1 (skip promoted to pass, not a new test) + 8 new + 1 new (synthetic-no-pop) = 1917. Zero weakened tests: the one changed assertion (`test_catalog_native_dse_apply_survives_unrelated_iterate`) was updated because the behavior it tested for *was the bug this IC fixes* — its old value (`is None`) is no longer true by design, not weakened.

Regression suites confirmed green as part of the full run: `tests/test_catalog_bind_v1.py` (including `test_dse_apply_diverging_thrust_clears_motor_catalog_ref`, unchanged), `tests/test_g5_dse_iterate_dual_truth.py`, `tests/test_g9a_catalog_ref_gap.py`, `tests/test_engineering_readiness_gaps.py`, `tests/test_g21_g22_catalog_bind_ux.py`, `tests/test_design_explorer.py`.

---

## 9. CLI probe evidence

`scripts/cli_probe_impl_c_catalog_dse.py`, re-run end to end. All 7 steps PASS with **no forcing** in step 5 (§8's hard requirement):

```
Part A: bind SKU sunnysky_r2305_2500 via component wizard → estado: motor_catalog_gap=None (G9-A Scenario B)

Part B (fresh project, motor_count=6, no prior thrust):
  optimiza para aumentar payload →
    5 configuración(es) viable(s):
      1. motors [sunnysky_x2212_980]: ... → score=3.034
      2. motors [brotherhobby_returner_r5_2700]: ... → score=3.023
      3. motors [brotherhobby_avenger_2500]: ... → score=2.862
      4. motors [emax_rs2205_2300]: ... → score=2.427
      5. motors [sunnysky_r2305_2500]: ... → score=2.292
    — all 5 are real SKUs, naturally, in the CLI-facing top-5 message itself.

  aplica la mejor →
    per_motor_max_thrust_n: None → 11.0
    motor_power_w: None → 260.0
    motor_kv_rating: None → 980.0
    motor_mass_kg: None → 0.348
    margen de seguridad: 3.034, vuelo: ✓ viable

  estado → catalog_ref=sunnysky_x2212_980, motor_catalog_gap=None
  cambia safety_factor → 1.5 → catalog_ref survived unrelated iterate (sunnysky_x2212_980)
```

Note the qualitative improvement over the parent IC's probe: that run's "optimiza para aumentar payload" showed **zero** SKUs in the printed top-5 (params-grid entries won every slot, on an already-bound-motor fixture). This run's top-5 is **100% real SKUs**, and step 5 applied `exploration.viable[0]` exactly as a real user's "aplica la mejor" would — no reordering was even needed this time (it was already the natural top candidate).

---

## 10. Ready for single Impl C commit?

**Yes.** All items in the parent review's Note A are closed:

- Explore evaluation uses each catalog candidate's own real thrust (§5-§6).
- Real SKU-switch apply preserves `catalog_ref` and the new thrust, survives an unrelated iterate turn (§5).
- A catalog candidate can be — and in the demonstrated fixture, reliably is — naturally present in `.viable` without any scoring change (§6-§7, §9).
- No forbidden surface was touched; no STOP was needed.

**Residual, not blocking:** the "already-declared-thrust" scoring-dominance observation (§7) is real and worth an explicit Engineer decision in a *future* cut if catalog visibility in the top-5 is wanted for projects that already have a manually- or previously-declared thrust value on the books — but it is a ranking-policy question, explicitly out of this contract's scope (★3/★8), and does not block treating Impl C as product-complete per this contract's own exit criterion (§10 of the contract).
