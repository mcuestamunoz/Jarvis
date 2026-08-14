# Implementation Report — G5 Fix (DSE → component sync)

## Summary

DSE-elevated motor capacity now survives unrelated iterate turns. A single shared helper, `component_sync.sync_motors_component_from_params`, keeps `design_properties.components["motors"]` current the moment a params-only DSE apply changes `motor_count`/`per_motor_max_thrust_n`/`per_actuator_torque_nm` — so `resolve_propulsion_parameters` (called unconditionally by `IterateAction.run` and `param_definition_session.py` on every physical turn) always reads fresh data instead of a pre-DSE snapshot. **Neither of those two callers was touched** — they become correct automatically once their one shared input stops going stale, exactly as the fix direction specified. **Full suite: 1693 passed** (1683 baseline + 1 xfail promoted to pass + 9 new), zero regressions.

## Fix locus (Option A, as locked)

`orchestrator._handle_apply_exploration` — the params-only DSE apply branch — is the **only** call site touched. Right after the existing `catalog_bind.invalidate_diverged_catalog_refs` call:

```python
_invalidated_components, canonical_params = invalidate_diverged_catalog_refs(
    _base_components, canonical_params
)
_updated_components = sync_motors_component_from_params(
    _invalidated_components, canonical_params
)
```

**Order is load-bearing and documented in both files' docstrings**: `invalidate_diverged_catalog_refs` must run first, against the *still-stale* component, to correctly detect true SKU divergence (comparing the old declared thrust against the new DSE-scaled one). If sync ran first, the component would already match the new params by the time the divergence check ran, and a genuinely-diverged `catalog_ref` would incorrectly survive. `sync_motors_component_from_params` then brings `motor_count`/`thrust_n` (or `torque_nm`) up to date on whatever `invalidate_diverged_catalog_refs` produced (possibly already `catalog_ref=None`). Verified by a dedicated combined test (`test_sku_bound_motor_dse_diverge_still_clears_catalog_ref_and_syncs`).

## `sync_motors_component_from_params` (`src/jarvis/core/component_sync.py`, new)

```python
sync_motors_component_from_params(components, params) -> components
```

- Pure: returns the **same** dict object unchanged when there's no `motors` component, or when nothing diverged (no-op, no allocation) — `is`-comparable, matching the `invalidate_diverged_catalog_refs` convention.
- Touches only the three fields `component_resolver.PhysicalOverride` can derive: `motor_count`, `thrust_n` (when `output_magnitude == "thrust_n"`), `torque_nm` (when `output_magnitude == "torque_nm"` — the latent ground-vehicle path the investigation named; no `EXPLORATION_GRIDS` entry exercises it today, covered anyway by a dedicated unit test for parity). Every other property (`power_w`, `kv_rating`, `weight_g`, `catalog_ref`, ...) is left byte-for-byte untouched.
- Never invents a `motors` component that doesn't exist (honest no-op, per contract §2's closing line).
- Synced properties are tagged `source="calculated"` — an **existing, previously-unused** `PropertyValue.source` enum value (confirmed by grep: zero prior usages anywhere in the codebase), so this needed **zero schema changes**. This satisfies contract §2.4's preference for a distinct tag over silently keeping `"declared"` (which would have overstated the property — the user never typed a thrust value; DSE calculated it deterministically).

## Wiring

`orchestrator._handle_apply_exploration` (one file changed, `src/jarvis/core/orchestrator.py`): the two-line addition above, plus an inline comment explaining the ordering dependency. Nothing else in that function changed — `canonical_params`, `updated_project` rebuild logic, and the save/message-building code that follows are unaffected in shape (the existing `if _updated_components is not _base_components:` rebuild check, previously written for `invalidate_diverged_catalog_refs` alone, now correctly also catches sync-only changes because of how the two calls compose — see code comment).

**`actions/iterate.py` and `param_definition_session.py` — confirmed untouched.** `git status --short -- src/` shows exactly one modified file (`orchestrator.py`) and one new file (`component_sync.py`).

## Tests

**T1 — promoted** (`tests/test_g5_dse_iterate_dual_truth.py`): `test_unrelated_numeric_iterate_reverts_dse_elevated_motor_params` → renamed `test_unrelated_numeric_iterate_does_not_revert_dse_elevated_motor_params`, `xfail(strict=True)` marker removed, now a plain passing assertion. Docstrings across the file updated from "bug, not yet fixed" to "fixed, here's how."

**T2 — control, unchanged in intent**: `test_dse_apply_itself_does_not_revert_its_own_elevation` — still confirms `_handle_apply_exploration` itself produces correct elevated `current_parameters` (this was never the bug).

**T3 — new**: `test_dse_apply_syncs_motors_component_to_match_elevated_params` — confirms `components["motors"]` matches the elevated params immediately after DSE apply (not just "eventually, after the next turn"), both fields tagged `source="calculated"`, and `power_w` (untouched field) still reads `source="declared"`. This test *replaces* the old control assertion that used to prove the component stayed stale (`test_dse_apply_itself_does_not_revert_its_own_elevation` had that stale-check removed — it's now factored into this dedicated test instead, since "component stays stale right after DSE apply" is no longer true post-fix).

**T4 — covered by the promoted T1**: the promoted test *is* "unrelated iterate after sync does not cliff."

**T5 — new**: `test_sku_bound_motor_dse_diverge_still_clears_catalog_ref_and_syncs` — SKU-bound motor + DSE thrust divergence still clears `catalog_ref` (Impl B regression) **and** the component is still kept current with the new params in the same turn — proves the two mechanisms compose correctly rather than fighting each other.

**T6 — full suite green**, no weakened assertions anywhere (confirmed: no existing assertion was loosened; the one assertion that changed, in T2, was moved to a *new*, *stronger* test (T3) rather than deleted).

**New unit-test file** `tests/test_component_sync.py` (7 tests) — direct coverage of the helper in isolation: no-op when no motors component; no-op when nothing diverged (identity-preserving, no allocation); both fields synced + tagged; motor_count-only divergence leaves thrust untouched (and vice versa is implied by symmetry); missing params key is a no-op; the latent torque path (`output_magnitude == "torque_nm"`); and a component with no pre-existing `motor_count` property still gets one created correctly (no crash on a missing base `PropertyValue` to copy from).

```
pytest tests/test_component_sync.py tests/test_g5_dse_iterate_dual_truth.py -v          → 12 passed
pytest tests/test_catalog_bind_v1.py tests/test_catalog_foundation_v1.py \
       tests/test_design_explorer.py tests/test_da2_components_delta.py \
       tests/test_fn022_engineering_intent.py tests/test_fn024_handoff_context_dse.py \
       tests/test_fn025_help_goal_intent.py tests/test_fn026_lever_iterate_preseed.py \
       tests/test_f1_reducir_payload.py tests/test_g5_dse_iterate_dual_truth.py \
       tests/test_component_sync.py tests/test_iterate_session.py tests/test_orchestrator.py \
       tests/test_motor_component.py tests/test_assisted_acquisition.py -q               → 414 passed
pytest -q (full suite)                                                                    → 1693 passed (1683 baseline incl. 1 xfail → now passing + 9 new)
```

## Files changed

| File | Change |
|---|---|
| `src/jarvis/core/component_sync.py` (new) | `sync_motors_component_from_params`. |
| `src/jarvis/core/orchestrator.py` | Two-line wiring + comment in `_handle_apply_exploration`. |
| `tests/test_g5_dse_iterate_dual_truth.py` | xfail → plain pass (T1); module/test docstrings updated; T2's stale-check assertion moved into new T3; new T5. |
| `tests/test_component_sync.py` (new) | 7 unit tests for the helper. |

`.jes/artifacts/cli_findings_post_catalog_bind_v1.md` — **not touched by this contract**. It arrived already updated (G5 🔴→🟡 "Investigado — fix READY", by Cursor/Engineer between the investigation and this fix contract) — per contract §7 ("Update cli_findings G5 → 🟢 when Engineer confirms"), the final 🟢 flip is left to the Engineer's own confirmation step, not done here.

## Acceptance criteria — self-check

1. G5 cliff closed: DSE-elevated motor params survive an unrelated iterate turn — **yes**, T1 (promoted, passing).
2. Sync helper is the fix locus; iterate/DEFINE_MISSING callers untouched — **yes**, confirmed by `git status`.
3. G5 xfail removed / promoted to green regression — **yes**.
4. Impl B catalog invalidation still green — **yes**, T5 plus the full `test_catalog_bind_v1.py` suite (unchanged, all passing).
5. No G3/H5/Impl C scope creep — **yes**, `git status --short -- src/` shows exactly the two files above.

## Risks / notes

- `source="calculated"` is now a live, meaningful value for the first time. Any future code that filters/displays properties by `source` (BOM, Continuity, catalog UX) should be aware a motors component can now carry this tag — no such consumer exists today (confirmed by grep before this change), so nothing downstream needed updating, but it's a new observable state worth knowing about for whoever designs the deferred "Continuity/BOM copy for DSE-derived source tags" item.
- The sync is one-directional (params → component) and scoped to the three `PhysicalOverride` fields — it does not attempt to reconcile any other component/param pair, matching the investigation's Q5 finding that no other pair exhibits this specific hazard today.
- `per_actuator_torque_nm` sync is implemented and unit-tested but has no live trigger (no `EXPLORATION_GRIDS` entry references it) — dormant-but-ready, per the investigation's own recommendation to cover it in fix test coverage even though inactive.
