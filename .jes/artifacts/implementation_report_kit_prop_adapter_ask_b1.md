# Implementation Report — Prop adapter ask B1 (after hélices; gated kit hole)

**IC:** [implementation_contract_kit_prop_adapter_ask_b1.md](implementation_contract_kit_prop_adapter_ask_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-09
**Baseline:** package `0.3.8` · suite 2514

---

## Files changed

- `src/jarvis/core/system_architecture_catalog.py` — **§3.1**: `prop_adapter` added to `KIT_TO_COMPONENTS["dron"/"uav"]` and `KIT_HOME_BLOCK["prop_adapter"] = "propulsion"`. New `KIT_REQUIRES_COMPONENTS = {"prop_adapter": ("motors", "propellers")}` (flat, one-off dict — not a generic predicate language). New `_kit_requirements_met` (fails closed on `components is None`). `kit_component_keys`/`bom_and_board_expected_keys` gained an optional `components` parameter, forwarded through to the requirement check. New `prop_adapter_is_due` and `splice_prop_adapter_ask` — the one hardcoded splice helper, never a generic "insert conditionally" engine (see its own docstring for the "never fires on an already-empty list" guard added during implementation — see "Deviation" below). `BLOCK_TO_COMPONENTS` itself has zero diff (confirmed via `git diff`, empty inside the dict body).
- `src/jarvis/core/project_closure.py` — `build_component_bom` now forwards `components` into `bom_and_board_expected_keys`.
- `src/jarvis/workspace/spatial_board.py` — `_expected_keys_by_column`/`project_spatial_nodes` now forward `components` into `kit_component_keys`.
- `src/jarvis/core/acquisition_target.py` — `COMPONENT_TERM_ALIASES` gained `prop_adapter`/`adaptador`/`adapter` → `prop_adapter` (whole-word only, no bare `hélice`/`buje`/`eje` alias). `COMPONENT_PROMPTS["prop_adapter"]` added with the locked Spanish text.
- `src/jarvis/core/orchestrator.py` — several coordinated changes (see "Deviation" below for why the final shape differs from the IC's literal §3.3 in one respect):
  - `_try_start_kit_component_from_mention` now passes `project_state.design_properties.components` into `kit_component_keys` (needed for `prop_adapter`'s gate to ever resolve `True`).
  - New `_with_prop_adapter_ask(still_missing, expected_keys, project_state)` — the one orchestrator-level wrapper around `splice_prop_adapter_ask`, scoped to `"esc" in expected_keys` (the one component key unique to propulsion's own `BLOCK_TO_COMPONENTS` entry among every block) so an unrelated wizard (battery/frame/control) is never touched even though the same helper is called from every catalog-pick handler too. When the splice actually inserts `prop_adapter`, it also persists the spliced list onto the current runtime session's `pending_missing_params`/`pending_param_definitions` — otherwise those fields are never rewritten mid-wizard (confirmed by reading every existing `still_missing` branch), so the next turn's `expected_keys[0]` would not actually be `"prop_adapter"`.
  - Applied at all 6 existing `still_missing` computation sites: the motor/propeller/battery/frame catalog-pick handlers and both `_handle_component_description` branches (the G-N1 frame-parts-only shortcut and the main freeform-save path) — a harmless no-op everywhere `"esc"` isn't in `expected_keys`.
  - New module-level `_PROP_ADAPTER_SKIP_PHRASES` (exact-phrase set, both accented/unaccented forms, per the IC's own list). New skip-handling block in `_handle_component_description`, checked right after `_maybe_refuse_different_target` and before the motors/propellers catalog-help gating: when `expected_keys[0] == "prop_adapter"` and the whole normalized input is a skip phrase, writes nothing, rewrites `pending_missing_params`/`pending_param_definitions` to drop `prop_adapter` from the current turn's remaining list, and shows the follow-up for whatever's left (`esc`, typically) — or closes the wizard via `_set_pending_next_block()` if nothing remains.
  - The kit-key relabel condition (`len(expected_keys) == 1 and expected_keys[0] in KIT_HOME_BLOCK`) widened to `expected_keys and expected_keys[0] in KIT_HOME_BLOCK` — a spliced propulsion scope is `["prop_adapter", "esc"]`, not a singleton, but the free-text answer is still always about `expected_keys[0]`.
- `tests/test_kit_prop_adapter_ask_b1.py` (**new**) — T0–T8 per the IC's own table.
- Existing tests updated — see below.

## Deviation from the IC's literal §3.3, found via full-suite regression and fixed (reported per §1)

The IC's §3.3 says: "`_set_pending_next_block` composite Phase A for **any** block must keep `missing_component_keys` sourced from `BLOCK_TO_COMPONENTS` only, then **`splice_prop_adapter_ask`** the result... Same for `_fresh_pending_keys_for_block` when it returns component keys." I implemented this literally first, then ran the **full** suite (not just the new tests) and found real regressions in five files never named in the IC's own §3.8 list: `test_propulsion_composite_wizard_flow.py` (Phase A→B transition test — once motors+propellers+esc were ALL present, the splice kept reopening Phase A just for `prop_adapter`, permanently blocking the transition to the numeric-params wizard), `test_fn011_propulsion_declare_routing.py`, `test_fn013_active_block_declare_routing.py`, `test_fn_esc_acquisition.py` (an **explicit** `"definir esc"` mention was silently redirected to the adapter Brief instead of ESC's own prompt), and `test_battery_catalog_bind_ux.py` (4 tests — a catalog-driven propeller pick also now correctly triggers the adapter ask, which the test's own turn sequence didn't account for).

Root cause: `_set_pending_next_block`/`_fresh_pending_keys_for_block` are called from many re-entry points (FN-013 reprompts, FN-014 explicit-mention continuation, Phase A→B transitions) — not only "right after hélices was just saved." Splicing there made `prop_adapter` a **standalone** reason to keep propulsion's component wizard open even once its own three real `BLOCK_TO_COMPONENTS` keys were fully satisfied, overriding explicit user requests and blocking an already-tested, unrelated transition.

Fix, in two parts:
1. **Removed** the splice from `_set_pending_next_block` and `_fresh_pending_keys_for_block` entirely — the IC's own core requirement (T3/T4/T5: ask right after hélices save, before ESC) is already fully satisfied by the splice living **only** in `_handle_component_description`'s and each catalog-pick handler's own `still_missing` computation (the "just saved something" moment), which never depended on those two functions to work — verified end-to-end, empirically, before and after this fix.
2. **Added a guard to `splice_prop_adapter_ask` itself**: it now returns `still_missing` unchanged when it is already empty — "the ask exists to be inserted into a real component still pending, never to become, by itself, a new reason to reopen a finished wizard." This one-line guard is what actually fixed the Phase A→B transition test; removing the two call sites above fixed the FN-011/013/FN-ESC/battery tests.

Both changes are documented in `splice_prop_adapter_ask`'s own docstring in `system_architecture_catalog.py`. The IC's own explicit tests (T3/T4/T5, verified via a live throwaway orchestrator run reproducing the exact "motors → hélices → adapter Brief → va directa/no lo sé → ESC Brief" sequence) behave exactly as locked both before and after this correction — the correction only removes an unintended side effect the IC's literal instruction would have introduced into flows outside this Buy's own scope.

## Behavior changed

- Once `motors` and `propellers` are both declared (non-`"low"`) on a `dron`/`uav` project, a `prop_adapter` slot appears on the Board (in the propulsion column) and in BOM `missing` — confirmed live against the demo project (`autonomía-de-10min`): `power_connector`/`signal_harness` are already resolved there (an Engineer smoke from the prior cycle), and `prop_adapter` is now the one remaining kit hole, architecture still `4/4`, hover/margin numbers in `latest_results` completely unread/unchanged (read-only check).
- Inside the propulsion composite wizard, saving `propellers` (via free text or catalog pick) while `motors` is already present now shows the adapter Brief as the **immediate** next question, before ESC — verified live: `"helices 10x4.5"` → `"¿Cómo montas la hélice?..."`, never `"Describe el ESC..."`.
- `"va directa"` (or any non-trivial description) saves a `prop_adapter` `ComponentSpec` (`completeness` promoted to at least `"medium"`, no `catalog_ref`, no geometry-relevant keys) and the follow-up becomes ESC's own Brief.
- `"no lo sé"`/any of the locked skip phrases writes nothing, advances the wizard straight to ESC's Brief, and the Board/BOM hole for `prop_adapter` stays open — confirmed live: `bom["missing"]` still contains `"prop_adapter"` immediately after a skip.
- An explicit `"definir esc"` mid-architecture, a Phase A→B transition once all three real propulsion components are done, and every other pre-existing wizard flow are byte-identical to before this Buy — confirmed by the full suite going green with zero assertion weakened (only fixture *additions*, documented below).
- `robot`/`coche`/`rover` domains and any project with no `vehicle_type` get **zero** `prop_adapter` visibility — `KIT_TO_COMPONENTS` has no entry for those domains at all (confirmed T6, T8).
- Architecture/PASS/hover/autonomy byte-identical — `_block_progress_status` (both the orchestrator and `engineering_readiness.py` copies) has zero diff; T7 directly proves a kit-aware state and its no-`vehicle_type` clone report the same `"complete"` status for `propulsion`.

## Existing-test updates (reported, not silently weakened)

- `tests/test_impl_d_sku_bom.py::test_architecture_complete_bound_motor_still_bom_pass_no_new_gap_type` — added a third stub `ComponentSpec` (`prop_adapter`, completeness `"high"`, no properties → `classify_component` returns `"declared"`, never `"missing"`/`"incomplete"`), same pattern as the two kit-B1-min stubs already there. Test's own subject (bound-motor BOM/gap-type behavior) unaffected.
- `tests/test_engineering_readiness_subsystems.py` — all 3 call sites of the shared `_fully_closed_components()`-derived fixture (`test_assembly_ready_true_when_everything_pass_no_gaps`, `::test_assembly_ready_true_when_pass_but_quality_risky`, `::test_demoted_catalog_gap_warns_catalog_propulsion_but_bom_keeps_not_ready`) — added the same third stub component alongside the two already there.
- `tests/test_requirements_closure.py` — the shared `_assembly_ready_shape_state()` helper (used by 7 tests total, 2 of which assert full closure) — added the third stub component to its `dp.components` dict, same reasoning as the kit-B1-min cycle's own fix to this file.
- `tests/test_battery_catalog_bind_ux.py::_drive_to_battery_wizard` (a shared helper, fixes all 4 failing tests in that file at once) — inserted one `"no lo sé"` turn between the propeller catalog pick and `"ESC 30A"`, since motors+propellers are now both catalog-bound at that point and the propulsion wizard correctly interleaves the adapter Brief there — skipping it restores the exact same "ESC saved, propulsion closed, energy auto-opens" state the helper produced before this Buy existed. This is a genuine, correct product-behavior change (the adapter question now legitimately appears in this flow too), not a workaround for a bug.
- `tests/test_frame_parts_graph_v1.py`, `tests/test_idle_frame_rebind_b2.py`, `tests/test_catalog_foundation_v1.py` — **not touched by this cycle**; their prior modifications are from the earlier Rooster Included plates B2 cycle, listed here only to confirm they were re-checked and needed no further change.

No test was deleted or had an assertion removed/loosened.

## Tests

- `python -m pytest -q tests/test_kit_prop_adapter_ask_b1.py tests/test_assembly_kit_template_b1.py` → **20 passed** (9 new T0–T8 + 11 kit-B1-min tests, all growing to the third hole where the IC calls for it).
- `python -m pytest -q` (full suite) → **2523 passed**, 0 failed (baseline 2514 + 9 new).
- `git diff -- src/jarvis/core/system_architecture_catalog.py` shows **zero** lines changed inside the `BLOCK_TO_COMPONENTS` dict body itself (confirmed via a targeted diff scoped to that block).
- `git status --short -- ui/ library/` shows only unrelated prior-cycle changes — this IC touched neither.
- No version bump (`pyproject.toml` still `0.3.8`).
- Live demo (`autonomía-de-10min`) re-verified directly (read-only): Board slots now `['prop_adapter']` (power_connector/signal_harness already resolved from a prior Engineer smoke), BOM `missing == ['prop_adapter']`, architecture still `4/4`, `latest_results.simulation` untouched.

## Non-goals honored

- No hub/shaft/bore millimetre ever read to decide whether to ask — confirmed by construction: `prop_adapter_is_due`/`_kit_requirements_met` only ever check `completeness != "low"` on `motors`/`propellers`, never any property value.
- `KIT_TO_COMPONENTS`/`BLOCK_TO_COMPONENTS`/`PASS`/hover/`_block_progress_status` — all confirmed byte-identical or additive-only via `git diff`.
- `create`/architecture-A never lists `prop_adapter` before hélices exist — confirmed T0/T8: `kit_component_keys` fails closed (`components=None` or motors/propellers absent) at every point before both are declared.
- `"no lo sé"` never writes a fake SKU and never blocks the ESC turn — confirmed T5, and the live throwaway reproduction.
- No catalog seed (`library/` empty diff), no version bump, `ui/` empty diff.
- `OUT_OF_SCOPE_EXPLICIT_SAVE_KEYS` untouched — `prop_adapter` was not added there, per lock.
- XT60/harness catalog SKUs, VTX/RX, `"cabe"`, 3D — none touched.

## Remaining risks / notes for review

- The deviation described above (removing the `_set_pending_next_block`/`_fresh_pending_keys_for_block` splice, adding the empty-list guard) is the one place this implementation's final shape differs from the IC's own literal §3.3 wording. Flagging explicitly for Cursor's review: the IC's own T3/T4/T5 (the tests that actually encode the locked behavior) all pass unmodified either way — the deviation exists specifically to avoid an unauthorized regression in five files the IC never named, discovered only by running the **full** suite rather than trusting the new tests alone.
- `test_battery_catalog_bind_ux.py`'s helper now embeds one extra "no lo sé" turn — a real, intended product-behavior acknowledgment, not a suppression; a future Buy that seeds an actual XT60-style adapter catalog could instead have that helper pick a real adapter, but that is explicitly out of this IC's scope.
