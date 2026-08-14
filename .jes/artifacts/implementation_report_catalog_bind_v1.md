# Implementation Report — Catalog Bind v1 (Impl B)

## Summary

A catalog pick no longer disappears after the turn it's made in. Both catalog-pick entry points (the iterate wizard's mid-session pick and the DEFINE_MISSING wizard's first pick) now converge on one shared helper, `catalog_bind.bind_motor_from_catalog`, which sets `ComponentSpec.catalog_ref` alongside the properties it already projected — fixing the exact identity-discard bug the Impl A audit found. SKU-bound motors and batteries now causally affect physics: motor mass (`weight_g × motor_count`) enters `total_mass_kg` only when `catalog_ref` is set; battery mass comes from the SKU's real `mass_g` instead of the 150 Wh/kg heuristic, also only when bound. A single shared invalidation rule, `catalog_bind.invalidate_diverged_catalog_refs`, clears `catalog_ref` the moment a later mutation — DSE params-only apply or a plain iterate numeric edit — moves a bound component's physical number away from what the SKU actually is, so no stale SKU label can survive next to diverged numbers. Unbound projects are bit-compatible with pre-Impl-B physics by construction (verified: full suite green, zero changed expectations anywhere). **Full suite: 1630 passed** (1616 baseline + 14 new).

## Bind entry points wired (iterate / DEFINE_MISSING / battery / prop)

- **Iterate assisted motor pick** (`iterate_interactive_session._handle_motor_suggestion_selection`) — now calls `bind_motor_from_catalog(s, base=existing_spec)`, which merges the projected catalog properties onto the existing draft spec (preserving `motor_count` etc., exactly as the old inline splice did) and additionally sets `catalog_ref`. **Wired and tested end to end** (`test_iterate_motor_pick_sets_and_persists_catalog_ref`).
- **DEFINE_MISSING catalog motor pick** (`param_definition_session._apply_catalog_motor_pick`) — the old local `_make_motor_spec_from_catalog` was deleted; the call site now uses the same shared `bind_motor_from_catalog(suggestion)` (no `base`, fresh-spec shape, identical to the function it replaced plus `catalog_ref`). **Wired and tested end to end** (`test_define_missing_catalog_pick_sets_catalog_ref`).
- **Battery** — no CLI/UX catalog-pick entry point exists yet (Impl A's 5A lock: no battery Continuity/assist redesign). Per contract §2.1.C, implemented as a deterministic bind helper (`bind_battery_from_catalog`) applied through the existing sole write point, `set_battery_component` — **helper + tests only**, no new UX. Tests apply the bind exactly as the contract suggests (`test_battery_bind_uses_sku_mass_not_heuristic`, plus the natural-language divergence test that starts from a pre-bound battery).
- **Propeller** — same status as battery: `bind_propeller_from_catalog` helper, **no wiring into a pick UX** (none exists), **no mass wired into calc** (contract §2.1.D explicitly allows deferring this since motor + battery already prove the causality chain). Tested at the helper level only (`test_bind_propeller_from_catalog_sets_catalog_ref`).

## Shared bind helper(s)

New module `src/jarvis/core/catalog_bind.py`:

- `bind_motor_from_catalog(suggestion, *, base=None) -> ComponentSpec`
- `bind_battery_from_catalog(sku, *, library=None, base=None) -> ComponentSpec`
- `bind_propeller_from_catalog(sku, *, library=None, base=None) -> ComponentSpec`
- `invalidate_diverged_catalog_refs(components, params, *, epsilon=1e-6) -> tuple[components, params]`

All four are pure (no I/O beyond the `ComponentLibrary` lookups the battery/propeller helpers make through the existing single reader) and family-symmetric — the `base=None` vs `base=<spec>` split is the one shared shape both motor entry points needed, generalized to all three families for consistency even though only motor currently has two live callers.

## Writers / mirrored params

- `component_writers.set_motor_component` — new: writes `motor_mass_kg = round(weight_g/1000 × motor_count, 4)` into `current_parameters` **only when** `spec.catalog_ref is not None and spec.catalog_ref.family == "motor"` and both `weight_g` and the current `motor_count` are available; pops the key otherwise (unbound — today's exact behavior, verified no test anywhere expects `motor_mass_kg` on an unbound project).
- `component_writers.set_battery_component` — extended: when `capacity_wh is not None`, `battery_mass_kg` now comes from the SKU's `mass_g/1000` **only when** `spec.catalog_ref is not None and spec.catalog_ref.family == "battery"` and a `mass_g` property is present; falls back to `estimate_battery_mass_kg(capacity_wh)` in every other case — including the entire unbound path, byte-for-byte the pre-Impl-B behavior.
- `system_architecture_catalog.COMPONENT_MIRRORED_PARAMS` — added `motor_mass_kg` with a comment documenting its SKU-bound-only conditionality (this set is also used by `design_explorer._apply_delta` to filter mirrored params out of raw grid deltas — a correct, forward-looking inclusion since no existing grid entry references it, zero behavior change today).
- MIRRORED PARAM CONTRACT discipline preserved: writers remain the sole write points; `catalog_ref` itself needs no writer-level bridging at all since it's a normal field on the `ComponentSpec` object the writers already pass through wholesale (`updated_components[key] = spec`) — confirmed by the round-trip test.

## CalculationEngine mass causality

`calculation_engine.py`: `total_mass = payload + structure_mass_kg + battery_mass_kg + motor_mass_kg`, where `motor_mass_kg = round(float(parameters.get("motor_mass_kg") or 0.0), 4)` — identical `.get(...) or 0.0` pattern already used for `battery_mass_kg`, so an absent key (every unbound project) contributes exactly `0.0`, reproducing pre-Impl-B physics exactly.

Demonstrated causality chain (`test_bound_motor_mass_increases_total_mass_vs_unbound`): a 4×SKU-bound motor fleet (`weight_g=62`) adds `+0.248 kg` to `total_mass_kg` versus an identical unbound baseline, which propagates to a strictly higher `weight_n` and `required_thrust_n` — the exact chain the contract's §0 diagram specifies.

## `catalog_ref` invalidation rules + call sites

One shared pure function, `invalidate_diverged_catalog_refs(components, params)`, called from both places the contract names as the minimum covered paths:

1. **`orchestrator._handle_apply_exploration`** (DSE apply) — right after `canonical_params` is resolved (params-only or component-driven), compares the current bound motor's/battery's SKU-projected number against the just-computed `canonical_params`; on divergence, rebuilds `updated_project` with the cleared component so the save reflects it. A **component-driven** DSE candidate needs no extra handling — `apply_components_delta` already replaces the whole component spec with a delta spec that never carries a prior `catalog_ref`, so the divergence check is a safe, cheap no-op there (verified: identity-preserving no-op, `is`-comparison confirms nothing was rebuilt unnecessarily).
2. **`actions/iterate.py::IterateAction.run`** (physical/non-DEFINE mutation) — right after `_apply_mutation_to_parameters`/`_apply_design_property_mutation` compute the new params/components; a numeric mutation patches `current_parameters` directly (`mutated_state["current_parameters"]`) without ever touching the component spec, so this is the one place that reconciles the two.

Rule (both call sites, identical logic): compare `components["motors"].properties["thrust_n"].value` against `params["per_motor_max_thrust_n"]`, and `components["battery"].properties["battery_capacity_wh"].value` against `params["battery_capacity_wh"]`, with a `1e-6` float epsilon (documented in the function's own signature — no fuzzy/approximate retention). On divergence: clear that component's `catalog_ref`; for motor, drop `motor_mass_kg` entirely (falls back to zero contribution, same as unbound); for battery, set `battery_mass_kg` to the heuristic (`estimate_battery_mass_kg`), same fallback an unbound battery already uses.

Tested via both the low-level pure-function API (`test_invalidate_diverged_catalog_refs_battery`, `test_invalidate_diverged_catalog_refs_no_op_when_unchanged`) and full natural-language/DSE integration (`test_dse_apply_diverging_thrust_clears_motor_catalog_ref`, `test_iterate_numeric_mutation_diverging_capacity_clears_battery_catalog_ref`).

**Note on the motor-divergence natural-language test**: the contract's own example phrasing ("empuje por motor") collides with `goal_planner`'s keyword detection (`"empuje"`/`"thrust"` are `mejorar_estabilidad` keywords, and `per_motor_max_thrust_n` contains the substring `"thrust"`), routing the turn into the FN-022 engineering-intent gate instead of iterate. The motor-side divergence path is instead proven via the DSE-apply route (which doesn't go through that gate at all), and the shared invalidation function is proven identical for both families at the unit level — so the rule itself is fully covered; only the *natural-language phrasing choice* for motor-via-iterate specifically was swapped for battery-via-iterate to avoid an unrelated, pre-existing intent-routing collision.

## Persistence

`catalog_ref` round-trips through `ProjectState.model_dump()` → `ComponentLibrary`-independent `ProjectState.model_validate()` with no special-casing needed — it's a normal Pydantic field on `ComponentSpec`, and every write path already passes the whole `ComponentSpec` object through `.model_dump()` (`mutation_engine.py:201`) or wholesale assignment (`component_writers.py`). Verified directly (`test_catalog_ref_survives_save_load_round_trip`) and indirectly through every integration test that reloads state after a bind.

## BOM/Continuity touch (or deferred)

**Deferred labeling** — per contract §2.6's explicit permission ("skip Continuity text changes if they require non-trivial UX redesign... note 'deferred labeling' in report"). `project_closure.build_component_bom`/`project_continuity.build_project_continuity` were not touched. Identity persistence and calc causality (the two mandatory items) are both done; a BOM/Continuity line showing "SKU-bound: sunnysky_x2216_11" vs "declared only" is a presentation-layer addition with no physics dependency and was judged non-trivial enough (BOM entry shape, Continuity evidence-line copy) to defer rather than rush into this cut.

## Files changed

| File | Change |
|---|---|
| `src/jarvis/core/catalog_bind.py` (new) | `bind_motor_from_catalog`, `bind_battery_from_catalog`, `bind_propeller_from_catalog`, `invalidate_diverged_catalog_refs`. |
| `src/jarvis/core/param_definition_session.py` | Deleted local `_make_motor_spec_from_catalog`; call site now uses shared `bind_motor_from_catalog`. |
| `src/jarvis/core/iterate_interactive_session.py` | `_handle_motor_suggestion_selection` now uses shared `bind_motor_from_catalog(s, base=existing_spec)`. |
| `src/jarvis/core/component_writers.py` | `set_motor_component` writes `motor_mass_kg` (SKU-bound only); `set_battery_component` sources `battery_mass_kg` from SKU when bound. |
| `src/jarvis/core/calculation_engine.py` | `total_mass` includes `motor_mass_kg` (defaults to 0.0, same pattern as `battery_mass_kg`). |
| `src/jarvis/core/system_architecture_catalog.py` | `COMPONENT_MIRRORED_PARAMS` gains `motor_mass_kg`. |
| `src/jarvis/core/orchestrator.py` | `_handle_apply_exploration` calls `invalidate_diverged_catalog_refs` after resolving `canonical_params`. |
| `src/jarvis/actions/iterate.py` | `IterateAction.run` calls `invalidate_diverged_catalog_refs` after `_apply_mutation_to_parameters`/`_apply_design_property_mutation`. |
| `tests/test_catalog_bind_v1.py` (new) | 14 tests — see below. |

`schemas/action_schema.py` (the `CatalogRef`/`catalog_ref` schema itself) — **not touched**, already shipped in Impl A.

## Tests run

```
pytest tests/test_catalog_bind_v1.py -v                                                     → 14 passed
pytest tests/test_component_library.py tests/test_motor_component.py \
       tests/test_assisted_acquisition.py tests/test_iterate_session.py \
       tests/test_orchestrator.py tests/test_design_explorer.py \
       tests/test_da2_components_delta.py tests/test_project_closure_v1.py \
       tests/test_calculation_engine.py tests/test_fn022_engineering_intent.py \
       tests/test_fn024_handoff_context_dse.py tests/test_fn025_help_goal_intent.py \
       tests/test_fn026_lever_iterate_preseed.py tests/test_catalog_foundation_v1.py \
       tests/test_catalog_bind_v1.py -q                                                     → 387 passed
pytest -q (full suite)                                                                       → 1630 passed (1616 baseline + 14 new)
```

## Regression results

Zero failures, zero changed expectations. `git status --short -- src/` confirms exactly the 7 modified files + 1 new module listed above — `schemas/action_schema.py`, `knowledge/library.py`, and every `library/**/_datos.json` file (Impl A's territory) are untouched. `test_single_json_reader_guard` (Impl A's guard test) re-run and still green — `catalog_bind.py` consumes `ComponentLibrary`'s public API only, never constructs a `_datos.json` path itself.

## CLI probe script for Engineer

```text
1) Open a closed-architecture project (motors/battery/frame/control all defined).
2) Trigger the DEFINE_MISSING or iterate assisted motor pick — e.g. after
   "definir componentes" → "motor 4x 920KV" → pick a numbered suggestion.
3) `estado` / inspect the project — components["motors"].catalog_ref should
   show the picked SKU (family="motor", sku=<picked name>).
4) `calcula`/`simula` — compare total_mass_kg / safety_margin_ratio against a
   baseline run before the bind: mass should be strictly higher by the SKU's
   weight_g × motor_count (in kg), margin should move accordingly.
5) `explora opciones` → `aplica la mejor` (or manually iterate a numeric
   per_motor_max_thrust_n / battery_capacity_wh value away from the bound
   SKU's own number) — re-inspect: catalog_ref should now be None on that
   component, and its mass mirror should have reverted to the unbound
   fallback (dropped for motor, heuristic for battery). No stale SKU name
   should appear anywhere once the numbers have diverged.
```

## Explicitly deferred (C/D/H5/material)

- **Impl C** (Catalog-aware DSE) — not started; the identity field now exists and is actively bound/invalidated, satisfying the hard dependency Impl A/the audit named, but no DSE grid reads or generates catalog-constrained candidates yet.
- **Impl D** (Create→BOM / SKU BOM) — untouched.
- **H5 / C-081** — untouched.
- **Material ES/EN alias micro-fix (3A)** — untouched, still tracked separately.
- **Battery/propeller Continuity gap redesign** — untouched (5A, reaffirmed).
- **BOM/Continuity SKU-bound labeling** — deferred, see above.
- **Propeller mass in calc** — deferred per contract §2.1.D; helper exists, no writer/calc wiring.

## Risks

- The invalidation rule's divergence check compares against the component's *own stored property value* (`properties["thrust_n"].value` / `properties["battery_capacity_wh"].value`), not a fresh `ComponentLibrary` lookup by SKU — deliberate (cheaper, doesn't require the SKU to still resolve, and the stored value was itself copied from the SKU at bind time so it's an equivalent comparison) but means if some future code path ever mutates a bound component's property *without* going through a writer or clearing `catalog_ref`, the divergence check could be silently bypassed. No such path exists today (writers are the sole write point per the MIRRORED PARAM CONTRACT), but worth flagging for whoever designs Impl C's candidate-generation code.
- Only motor and battery participate in the invalidation rule; propeller has no bound mass/property to diverge from in this cut (no propeller pick UX, no propeller mass in calc) — if Impl C or a future UX cut adds a propeller pick path, `invalidate_diverged_catalog_refs` will need a third `if propeller is not None...` block mirroring the existing two before propellers can safely participate in DSE.
- `motor_mass_kg`'s SKU-bound-only gate means two visually-similar projects — one with a manually-declared 62 g/motor and one bound to a real SKU with the identical `weight_g=62` — will compute *different* `total_mass_kg` (0 vs the real contribution) purely because one is catalog-bound and the other isn't. This is the contract's own explicit, deliberate choice (2A: "never rewrite free-text-declared motors' physics") — flagged here only so it doesn't read as an inconsistency during the CLI probe.

## Addendum — Cursor review fix (PASS WITH NOTES → gap closed)

**Gap (Cursor's spot-check, verified reproducible before this fix):** after the iterate wizard's catalog pick flow completed, `components["motors"].catalog_ref` and `weight_g` were correctly persisted, but `current_parameters["motor_mass_kg"]` stayed absent — identity-only, not atomic with mass. Root cause: the iterate wizard's DEFINE/declarative apply path (`mutation_engine.apply_component_definition` → `actions/iterate.py::IterateAction._run_declarative_iteration`) persists `draft.component_patch` by dumping each `ComponentSpec` straight into `design_properties` (`{key: spec.model_dump() for key, spec in draft.component_patch.items()}`) — this never calls `component_writers.set_motor_component`/`set_battery_component` at all, so none of the MIRRORED PARAM CONTRACT's `current_parameters` bridges (not just `motor_mass_kg` — the same gap applied to `motor_power_w`/`motor_count`/`motor_kv_rating`/battery fields) ever ran for this specific path. **DEFINE_MISSING's own catalog pick was never affected** — `param_definition_session._apply_catalog_motor_pick` already calls `set_motor_component` directly.

**Fix:** `_run_declarative_iteration` now inspects `draft.component_patch` after merging it into `design_properties`; for any patched `motors`/`battery` component whose `catalog_ref` is set, it re-runs the same writer (`set_motor_component`/`set_battery_component`) the DEFINE_MISSING path already uses, on the merged state — so `current_parameters` (including `motor_mass_kg` / SKU-derived `battery_capacity_wh`+`battery_mass_kg`) lands atomically with the identity write. **Unbound components take zero extra writer calls** — `updated_parameters` starts as an exact copy of `project_state.current_parameters` and is only touched inside the two `catalog_ref is not None` branches, so a non-catalog declarative patch (the overwhelming majority of DEFINE iterations) produces byte-identical `current_parameters` to before this fix.

**Files changed:** `src/jarvis/actions/iterate.py` only (`_run_declarative_iteration` + one new import line for `set_battery_component`/`set_motor_component`).

**New assert (extends `test_iterate_motor_pick_sets_and_persists_catalog_ref`, `tests/test_catalog_bind_v1.py`):**

```python
motor_count = saved.current_parameters.get("motor_count")
assert motor_count is not None
assert saved.current_parameters.get("motor_mass_kg") == pytest.approx(
    suggestions[0]["weight_g"] / 1000.0 * motor_count
)
```

Reproduces the reviewer's own spot-check exactly (picked SKU `sunnysky_x2212_980`, `weight_g=58`, `motor_count=4` → `motor_mass_kg == 0.232`), now passing.

**Tests:** `tests/test_catalog_bind_v1.py` — 14 passed (no new test functions; the fix's assertion was added to the existing iterate-pick test, per the note's own suggestion to *extend* the existing test). Regression sweep (component library, motor, assisted acquisition, iterate, orchestrator, DSE, DA2, project closure, calculation engine, FN-022/024/025/026, catalog Foundation + Bind) — 387 passed. Full suite — **1630 passed**, unchanged count from before this fix (assertions added to an existing test, no new test added), zero regressions.

**Scope discipline confirmed:** no Impl C, Create→BOM, H5, Continuity redesign, or material ES/EN work touched — `git status --short -- src/` for this fix shows exactly one file, `src/jarvis/actions/iterate.py`. No commit/push made.
