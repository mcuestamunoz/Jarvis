# Investigation Report — G5 (DSE params vs iterate component dual-truth)

**Verdict: CONFIRMED, reproduced, root cause isolated to one call pattern in two files. Hypothesis in the contract was correct.**

## Summary

After a params-only DSE apply raises `motor_count`/`per_motor_max_thrust_n` in `current_parameters`, **any subsequent physical iterate turn — even one mutating a completely unrelated variable like `safety_factor`** — silently reverts both fields back to whatever `design_properties.components["motors"]` still declares. The CLI evidence (`iter_010` → `iter_011`) is reproduced exactly by a new automated test: DSE elevates `motor_count` 4→6 and `per_motor_max_thrust_n` 20.0→30.0, then `"cambia safety_factor" ... "1.4"` silently drops both straight back to 4 / 20.0 while correctly applying `safety_factor=1.4`.

Root cause: `component_resolver.resolve_propulsion_parameters` is called **unconditionally** on every physical iterate turn (`actions/iterate.py:197-200`) and on every `param_definition_session` recalculation (`param_definition_session.py:765-768`), always deriving from `design_properties.components` — which DSE's params-only apply path (`orchestrator._handle_apply_exploration`) never updates, by design (DA2: params-only deltas operate purely on the `current_parameters` dict). The component becomes stale the instant DSE elevates the params past it; the next unrelated physical turn re-derives from that stale component and clobbers the fresher DSE values.

## §2 Investigation questions — answered

### 1. Exact code path producing iter_011's params

```
iterate_interactive_session (step 2, numeric-param fast path)
  → draft.value="1.4", operation=aumentar, variable="safety_factor"
  → user confirms (step 5)
IterateAction.run(parameters)                                    actions/iterate.py:84
  mutation_engine.apply_mutation(mutable_state, draft)
    → apply_numeric_param_mutation                                mutation_engine.py:182-194
      → returns ({"current_parameters": {"safety_factor": 1.4}}, {})
  updated_parameters = _apply_mutation_to_parameters(
      project_state.current_parameters,   # ALREADY has DSE-elevated motor_count=6, thrust=30.0
      mutated_state,                       # only {"current_parameters": {"safety_factor": 1.4}}
  )                                                                actions/iterate.py:146
      → updated_parameters still has motor_count=6, thrust=30.0, safety_factor=1.4 — correct so far
  updated_design_properties = _apply_design_property_mutation(...)  actions/iterate.py:147
      → no design_properties patch in mutated_state → components untouched (still 4 / 20.0, stale)
  invalidate_diverged_catalog_refs(...)                             actions/iterate.py:156-163
      → catalog_ref is None on this component → no-op (see Q4)
  structural_confirm_needed(project_state.current_parameters, updated_parameters.get("motor_count"))
                                                                     actions/iterate.py:172-174
      → compares 6 (old, pre-turn) vs 6 (current updated_parameters, UNCHANGED so far) → no diff → gate does NOT fire
  propulsion_override = resolve_propulsion_parameters(
      {k: v.model_dump() for k, v in project_state.design_properties.components.items()}
  )                                                                 actions/iterate.py:197-199
      → derives motors=4 (from stale components["motors"].properties["motor_count"].value)
      → derives per_motor_max_thrust_n=20.0 (thrust_n property, output_magnitude="thrust_n", source="declared")
  updated_parameters = propulsion_override.apply_to(updated_parameters)   actions/iterate.py:200
      → THIS IS THE REVERT: unconditionally overwrites
        updated_parameters["motor_count"] = 4      (was 6)
        updated_parameters["per_motor_max_thrust_n"] = 20.0  (was 30.0)
  calculations = self.calculation_engine.build(updated_parameters)  # now computes on stale motor data
  → saved via record_action(state=project_state.model_copy(update={"current_parameters": updated_parameters, ...}))
```

`PhysicalOverride.apply_to` (`component_resolver.py:55-66`) has no concept of "don't overwrite if the current value already differs from what I'm about to write" — it always wins when `self.motors`/`self.per_motor_max_thrust_n` resolve to a value at all.

### 2. Does iterate read from ComponentSpec when recalculating after a partial param mutation?

**Yes, unconditionally**, on every physical (non-DEFINE) turn regardless of which variable is being mutated — confirmed at `actions/iterate.py:197-199`. This is not gated on `draft.variable` being motor-related in any way.

### 3. Does DSE params-only apply fail to update `components["motors"]`?

**Yes, confirmed, and this is existing, documented, by-design behavior** — not itself new or accidental. `orchestrator._handle_apply_exploration`'s params-only branch (`best.components_delta` empty) calls `design_explorer._apply_delta(base_params, best.params_delta)`, which operates purely on the flat `current_parameters` dict; `design_properties` is untouched unless `best.components_delta` is non-empty (a *different*, component-driven candidate shape). `_handle_apply_exploration` never calls `resolve_propulsion_parameters` itself — confirmed by grep — so the DSE apply step's own persisted result is internally correct (verified: `test_dse_apply_itself_does_not_revert_its_own_elevation` passes today). The staleness is a precondition for the bug, not the bug itself; the bug is that a *later, unrelated* call re-derives from that known-stale source and treats it as authoritative.

### 4. Is `invalidate_diverged_catalog_refs` (Catalog v1 Impl B) involved?

**No — confirmed unrelated.** It runs earlier in the same function (`actions/iterate.py:156-163`) but only inspects/clears `ComponentSpec.catalog_ref`, comparing `properties["thrust_n"].value` against `params["per_motor_max_thrust_n"]` *before* the revert at line 200 happens. In the CLI session and in the repro test, `catalog_ref` was already `None` (motors were declared, never SKU-bound), so this call is a documented no-op (`test_catalog_ref_invalidation_unrelated_to_this_revert` passes). Its own divergence logic is sound for what it's scoped to (identity), and it is not the source of the `motor_count`/`per_motor_max_thrust_n` revert.

### 5. Other param pairs with the same hazard?

**No other pairs today — the hazard is fully confined to the three fields `component_resolver.PhysicalOverride` carries: `motors`(→`motor_count`), `per_motor_max_thrust_n`, `per_actuator_torque_nm`.** Confirmed by grep: `.apply_to(` is called from exactly two sites (`actions/iterate.py:200`, `param_definition_session.py:768`), both feeding from the same `resolve_propulsion_parameters`. No equivalent "component re-derives and overwrites params" mechanism exists for `battery_capacity_wh`/`battery_mass_kg` (energy) or `propeller_diameter_in`/`propeller_pitch_in` — those fields have no analogous override call anywhere in the codebase, so they cannot exhibit *this* dual-truth pattern (a different absence of protection, not a fix).

One **latent, currently-inactive** instance of the same class: `per_actuator_torque_nm` (ground/robot torque path) is carried by `PhysicalOverride` exactly like thrust, but no `EXPLORATION_GRIDS` entry references `per_actuator_torque_nm` today (confirmed by grep — zero hits). If a future DSE grid or F-1b-style contract ever adds a torque-scaling candidate for ground vehicles, the identical revert would trigger on the next physical iterate turn for a torque-declaring project. Worth naming in any fix's test coverage, not just the thrust/aerial case.

**A second call site with the identical hazard, not previously flagged**: `param_definition_session.py:765-768` (used when answering a `DEFINE_MISSING_PARAMETERS` prompt — e.g. completing a missing energy parameter after a prior DSE apply) has the exact same unconditional `resolve_propulsion_parameters` → `apply_to` pattern. A `filtered_updates` re-apply happens *after* it (line 771: `updated_params = {**updated_params, **filtered_updates}`), which protects only the specific mirrored param the user is actively answering (e.g. `battery_capacity_wh`) — it does **not** protect `motor_count`/`per_motor_max_thrust_n` if those aren't what the user is currently answering. This is the same bug, reachable from a second, independent entry point.

### 6. Minimal fix options

| Option | Description | Assessment |
|---|---|---|
| **A — Sync components on DSE apply** | When a params-only DSE apply changes `motor_count`/`per_motor_max_thrust_n` (or `per_actuator_torque_nm`), also write the same values into `design_properties.components["motors"].properties` (via `component_writers`-style logic), keeping the component current so the *next* re-derivation produces the *same* value instead of a stale one. | **Recommended as the primary direction.** Restores the codebase's own stated invariant (components are the declarative source of truth `resolve_propulsion_parameters` is built to trust) instead of fighting it. Cost: needs a decision on how to tag these properties (`source="declared"` would overstate it — the user never typed a thrust value; a DSE-derived origin should probably read differently in BOM/Continuity later, though that's presentation, not correctness, and out of scope here). Touches `orchestrator._handle_apply_exploration`'s params-only branch only — narrow blast radius, same shape as the `invalidate_diverged_catalog_refs` precedent Impl B already established for a different field. |
| **B — Iterate never downgrades already-diverged params** | `PhysicalOverride.apply_to` (or its callers) skip overwriting `motor_count`/`per_motor_max_thrust_n` when the current `updated_parameters` value already differs from the component-derived value, treating that divergence as evidence of a more-recent, deliberate change. | Fixes the symptom without touching DSE, but requires guessing "is this divergence *deliberate and newer*, or genuinely *stale in the other direction* (e.g. a user typed a smaller thrust value earlier and the component just hasn't caught up yet)?" — no timestamp/generation marker exists to disambiguate. Weaker guarantee than A; flagged as workable but fuzzier. |
| **C — Shared reconciliation helper** | A single pure function (mirroring `catalog_bind.invalidate_diverged_catalog_refs`'s shape exactly) called after any params-only mutation, reconciling components↔params in one documented place instead of scattering the fix across `_handle_apply_exploration`/`iterate.py`/`param_definition_session.py`. | This is really **A's implementation shape**, not a fourth alternative — recommending A *as* this kind of shared helper (one function, both call sites of `resolve_propulsion_parameters` benefit automatically since they'd simply be reading an always-current component). Preferred packaging if/when a fix contract is written. |
| **D — Continuity/narration only** | Surface a message explaining the revert after the fact, without changing what gets computed/persisted. | **Insufficient alone, as the contract already suspected.** The revert doesn't just misinform the user — it **persists physically wrong data**: a configuration DSE proved viable at 6 motors gets silently recomputed and saved as if it only ever had 4, which can flip `can_fly`/`safety_margin_ratio` results into the new "current truth" for every subsequent turn. Narration describes a bad write after it already happened; it doesn't prevent the bad write. Could be a *complementary* addition once A/B lands (to make the (now correct, no-op) case where a real divergence-driven revert *is* intentional legible to the user), never a standalone fix. |

**Recommendation for the Engineer's fix contract**: Option A, packaged as a small shared helper analogous to `invalidate_diverged_catalog_refs` — sync `design_properties.components["motors"]`'s `motor_count`/`thrust_n` (and, if ever exercised, `per_actuator_torque_nm`'s equivalent) immediately after a params-only DSE apply changes them, so `resolve_propulsion_parameters` always reads current data on every subsequent turn. Both `actions/iterate.py:197-200` and `param_definition_session.py:765-768` then need no changes at all — they become correct automatically once their one shared input (the component) stops going stale.

## Sequence diagram — params vs components truth

```text
                    current_parameters                  design_properties.components["motors"]
                    ──────────────────                  ───────────────────────────────────────
create_project      motor_count=4                       motor_count=4  thrust_n=20.0
                     per_motor_max_thrust_n=20.0         (source="declared")

DSE apply            motor_count=6      ← updated        motor_count=4  thrust_n=20.0   ← UNTOUCHED
(mejorar_estabilidad) per_motor_max_thrust_n=30.0                        (by design — DA2 params-only)
                      ✅ correct, persisted                ⚠ now STALE relative to params

iterate               safety_factor=1.4  ← updated        motor_count=4  thrust_n=20.0   (still untouched)
(safety_factor,        motor_count=4      ← REVERTED!
 unrelated variable)   per_motor_max_thrust_n=20.0 ← REVERTED!
                       ❌ silent physics cliff, persisted   (component "wins" — treated as ground truth
                                                             by resolve_propulsion_parameters, even
                                                             though it's the STALE side of the split)
```

The FN-004 structural-confirm safety net (`actions/iterate.py:166-194`, specifically built to require explicit Sí/No before silently changing a *defined* `motor_count`) does **not** catch this: it compares `project_state.current_parameters.motor_count` (already 6, pre-turn) against `updated_parameters.get("motor_count")` (also still 6 at that point in the function — the revert happens *after* this check, at line 200) and sees no difference, so it never fires. The exact mechanism designed to prevent a silent motor_count change is blind to this bug purely because of call ordering.

## Repro test

`tests/test_g5_dse_iterate_dual_truth.py` — 3 tests:

- `test_unrelated_numeric_iterate_reverts_dse_elevated_motor_params` — **`xfail(strict=True)`**, the investigation's proof. Fails (as `xfail`) on current `main`, reproducing the exact CLI sequence (DSE apply → elevated motor_count/thrust → unrelated `safety_factor` iterate → silent revert) end to end via the real orchestrator, no mocks. `strict=True` means this test will loudly fail-for-real (not silently XPASS) the moment a fix contract makes it pass — a deliberate tripwire so nobody has to remember to update this file when G5 is fixed.
- `test_dse_apply_itself_does_not_revert_its_own_elevation` — passes today; control case proving the DSE apply step's own output is correct (isolates the bug to the *next* turn, not the apply itself).
- `test_catalog_ref_invalidation_unrelated_to_this_revert` — passes today; documents the Q4 finding (Impl B's invalidation logic is not implicated).

```
pytest tests/test_g5_dse_iterate_dual_truth.py -v   → 1 xfailed, 2 passed
pytest -q (full suite)                              → 1683 passed, 1 xfailed (1681 baseline + 2 passed + 1 xfailed)
```

Zero other tests affected — no production code was changed in this investigation (`git status --short -- src/` is empty for this contract).

## Out of scope, confirmed untouched

H5/G1, G3, Catalog Impl C, MIRRORED PARAM CONTRACT refactor, and no production fix — this contract is investigation + repro only, per §4/§6.
