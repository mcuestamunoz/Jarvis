# Implementation Report — DSE apply honesto (nameplate W + battery SKU)

**IC:** [implementation_contract_dse_apply_honest.md](implementation_contract_dse_apply_honest.md)
**Ratification:** [engineer_ratification_dse_apply_honest.md](engineer_ratification_dse_apply_honest.md)
**Implementer:** Claude Code
**Date:** 2026-09-03

## Files changed

- `src/jarvis/core/catalog_bind.py` — two new pure helpers, added after `invalidate_diverged_catalog_refs`:
  - `catalog_motor_nameplate_watts(components, *, library=None)` — returns the bound motor SKU's real `max_watts`, or `None` when unbound or the SKU honestly declares no watts. Single `ComponentLibrary.get_motor` lookup.
  - `find_battery_skus_for_energy_wh(energy_wh, *, library=None, epsilon=1e-6)` — all catalog battery SKUs whose declared `energy_wh` matches within epsilon (same epsilon order as G5).
  - `find_unique_battery_sku_for_energy_wh(energy_wh, *, library=None, epsilon=1e-6)` — built on the list helper; returns the single matching SKU or `None` on 0 or 2+ matches.
- `src/jarvis/core/orchestrator.py` — `_handle_apply_exploration`, params-only branch (`not best.components_delta`), inserted between the `canonical_params is None` check and the existing G5 `invalidate_diverged_catalog_refs` call:
  - §2.1: if the currently-bound motor SKU declares `max_watts`, `canonical_params["motor_power_w"]` is forced to that nameplate value regardless of what `_apply_delta` wrote from `motor_power_w_factor`. A disclosure flag/SKU are captured only when the forced value actually differs from what `_apply_delta` had written (so the apply message stays silent when nothing was actually overridden).
  - §2.2: if `battery_capacity_wh` changed, look up matching catalog SKUs via `find_battery_skus_for_energy_wh`. Exactly one match → `bind_battery_from_catalog(sku)` (fresh spec, no `base=` — a switch to a different SKU must not inherit the old spec's `.name`) + `set_battery_component(project_state, spec, capacity_wh=...)`, then merge only the battery-owned keys (`battery_capacity_wh`, `battery_mass_kg`, `battery_cell_count`) from the resulting state back into `canonical_params` — preserving every other `_apply_delta`/nameplate-derived param rather than overwriting the whole dict. Zero matches → no bind, existing G5 divergence-clear and parametric mass heuristic apply as before. Two-or-more matches → immediate `status=error` return, before any calculate/simulate/save call — no state mutation.
  - §2.3: this block runs strictly before the existing G5 (`invalidate_diverged_catalog_refs`) / `sync_motors_component_from_params` call, unchanged in position and logic — a fresh unique-SKU bind writes component Wh = params Wh so G5 does not clear the new `catalog_ref`; an unmatched Wh still diverges vs the old pack's component properties so G5 still clears the stale one.
  - §2.4: appended (not replacing) the existing apply confirmation message: the nameplate-kept sentence when §2.1 actually overrode a value, the battery-bound sentence when §2.2 bound a SKU, or the parametric-Wh sentence when Wh changed but no SKU matched (never emitted when Wh did not change).
- `tests/test_dse_apply_honest.py` — new, 7 tests (see below).
- `docs/IMPLEMENTATION_TASKS.md`, `.jes/state/engineering_state.json` — synced (IC section moved from "EN CURSO" to "CERRADO (código)"; suite count 2117 → 2124).

## Behavior changed

- A params-only DSE apply candidate whose delta would lower `motor_power_w` below a catalog-bound motor's real nameplate watts now keeps the nameplate value instead — never writes invented consumption.
- A params-only DSE apply candidate whose delta lands `battery_capacity_wh` on exactly one catalog pack's energy now binds that pack (name, `catalog_ref`, catalog mass, cell count) instead of leaving a stale battery name/`catalog_ref=None` next to the new parametric Wh.
- An `battery_capacity_wh` value matching two or more catalog packs now refuses the apply entirely (informative `status=error`, zero state mutation) instead of silently picking one.
- The apply confirmation message now discloses both facts when they occur.
- Nothing else: `DesignExplorer`/`_score_candidate`/`EXPLORATION_GRIDS`/viable ranking, `apply_components_delta` (Impl C path), G5's motor `thrust_n` comparison, `set_battery_component`'s MOP-2 voltage-revalidation hook, and every other apply-path branch are untouched.

## Tests

- Added `tests/test_dse_apply_honest.py` (7 tests): walk-equivalent mixed apply (nameplate kept at 220 W, battery bound to `lipo_4s_10000mah` at 148 Wh / 0.98 kg, both disclosure sentences present); unmatched-Wh apply stays parametric with `catalog_ref=None`; Wh-only delta still binds with motor untouched; an explicitly unbound-motor fixture documents that §2.1 does not apply there while §2.2 still binds the battery independently; a monkeypatched 2-match stand-in exercises the refuse path with an unchanged-params assertion; direct unit tests for `find_unique_battery_sku_for_energy_wh` (148.0/74.0/185.0) and `find_battery_skus_for_energy_wh` (count-based).
- Executed: full suite — `python -m pytest -q` → **2124 passed**, 0 failed (baseline 2117 + 7 new).
- Targeted re-run before the full suite: `test_dse_apply_honest.py`, `test_design_explorer.py`, `test_impl_c_catalog_aware_dse.py`, `test_battery_catalog_bind_ux.py` (including `test_battery_pick_does_not_regress_already_resolved_propulsion_op`), `test_dse_motor_op_dual_truth.py` → 123 passed, confirming no regression in the directly adjacent DSE/catalog-bind/battery-voltage-coherence suites.

## Non-goals honored

`EXPLORATION_GRIDS`/`_score_candidate`/viable re-sort untouched. Impl C `components_delta` apply path (motor identity) untouched — the new logic is entirely inside the `not best.components_delta` branch. No C3 battery-catalog DSE candidates added. No Tier 3 joint search. No Option B / `_derive_overall` / Energy PASS change. No Block Closure copy change. No new explore CTA rewrite (only the apply confirmation message gained lines). No invented watts or SKUs — both new binds are catalog-exact matches only. No catalog JSON expansion. No `workspace/` mutation (all tests use `tmp_path`). No auto-calcular beyond what apply already did before this IC.

## Remaining risks

- `bind_battery_from_catalog(sku)` is called without `base=` on purpose (to avoid inheriting the old SKU's `.name`), which means any non-catalog custom properties a user might have declared on the *old* battery spec (beyond capacity/mass/chemistry/cells) do not carry forward into the new SKU's spec. This matches the walk lock exactly (fresh identity on a SKU switch) but is worth flagging since it differs from the `base=` merge pattern used elsewhere in this file for same-SKU re-binds.
- The two-or-more-matches path is exercised only via `monkeypatch` on `find_battery_skus_for_energy_wh`, since the current v1 catalog's battery energies are all unique — there is no live fixture that naturally hits it. If a future catalog addition introduces a duplicate energy, this refuse path becomes reachable without any code change, but has not been exercised against a real duplicate.
