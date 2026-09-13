# Implementation Report — Catalog sourced-only purge + battery rebind P0

**IC:** [implementation_contract_catalog_sourced_only_purge_battery_rebind_b1.md](implementation_contract_catalog_sourced_only_purge_battery_rebind_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-13
**Baseline:** package `0.4.1` · suite 2796 (was ~2785 before this cycle; net +11 after purge-driven redirects/consolidations — see §Suite arithmetic below)

---

## ★1–★6 confirmed as ratified

Engineer confirmed ★1–★6 as written before implementation began.

## §2 inventory verified against live data before deleting anything

Read all three files directly and confirmed every KEEP/DROP row and `source_url` presence matched the IC's own table exactly (12→5 batteries, 23→3 motors, 19→6 propellers; frames/esc/kit_hardware already fully sourced, 6/2/2 respectively — untouched). Checked for cross-references (motor `operating_points[].propeller_sku`, `compatible_prop_ids`) between DROP and KEEP rows before deleting — none found; deletion was safe with zero orphaned references.

## Files changed

### Data (★1/★2)

- `library/baterias/_datos.json` — 7 DROP rows removed (12 → 5)
- `library/motores/_datos.json` — 20 DROP rows removed (23 → 3)
- `library/helices/_datos.json` — 13 DROP rows removed (19 → 6)
- `library/frames/_datos.json`, `library/esc/_datos.json`, `library/kit_hardware/_datos.json` — **untouched** (already fully sourced)
- `library/materiales/_datos.json` — **untouched** (★3, out of scope)

KEEP rows verified byte-identical (diff shows only the DROP entries removed, insertion order preserved for survivors).

### Code (★4 — Bat-list/Bat-sku/Bat-help)

- **`src/jarvis/core/battery_catalog_assist.py`** — `build_battery_catalog_suggestions`'s `limit` default changed from `10` to `None` (no truncation); `limit` stays an available override, not removed. Old "10 = full v1 catalog" framing in the docstring replaced with the actual root-cause explanation (alphabetical sort put Tattu 12th, past the old cutoff).
- **`src/jarvis/core/orchestrator.py`**:
  - **Bat-sku** (new): `_try_handle_component_battery_catalog_help`'s battery block now checks `detect_battery_sku_token(user_input)` — a live SKU named *anywhere* in free text (not just a bare/near-exact match against the currently-offered list, which `battery_match_suggestion_by_input` alone requires) — and binds directly via `battery_spec_to_suggestion` + the existing `_apply_component_battery_catalog_pick`. Mirrors the SKU-token discipline `param_definition_session.py` already uses for the older `battery_capacity_wh` scalar wizard path, applied here to the newer COMPONENT-mode battery wizard for the first time.
  - **Bat-help fix** (real bug found and fixed, not just re-verified): `battery_wants_help` gained the same `_battery_only_redefine and battery_is_help_choose_phrase(user_input)` clause motors already had (G18). Without it, a bare "ayúdame a elegir" **after** "cambiar bateria" (battery already catalog-bound) fell through the entire battery block and looped back to a fresh "Vamos a definir la batería..." Brief instead of re-showing the list — reproduced directly (§ below) before fixing, exactly the field note's bug #2.

### Tip/report copy (★ none new, honesty upkeep — §3.3)

- **`src/jarvis/core/reasoning_layer.py`** — docstring's "declares watts" example motor updated from the deleted `sunnysky_r2305_2500` (220W) to the real KEEP `sunnysky_r2205_2500` (756W).
- **`src/jarvis/core/project_closure.py`** — same docstring fix in `catalog_bound_motor_lacks_nameplate_watts`. Neither function hardcodes a SKU in actual logic (both read `max_watts` from the library dynamically) — these were documentation-only staleness, not functional bugs.
- Searched the rest of `src/jarvis/` for DROP-SKU mentions: three more hits in `motor_catalog_assist.py` are generic illustrative regex-shape comments ("MN3508, sunnysky_x2216, T-Motor 2306…") unrelated to any specific catalog row — left as-is, not a recommendation of a real product.

### Tests

- **`tests/test_catalog_sourced_only_purge_battery_rebind_b1.py`** (new, 17 tests) — the guardrail (§3.4) + Bat-list/Bat-sku/Bat-help coverage (§4.1).
- **48 pre-existing test files redirected** (see §Redirect log below) — every test that referenced a DROP SKU now uses an analogous KEEP SKU, a monkeypatch-injected synthetic fixture (for scenarios no surviving real SKU can reproduce), or was removed with an explicit disclosure comment (for scenarios whose entire subject was the now-deleted row itself).

## A real bug found and fixed mid-cycle (Bat-help)

Before touching `orchestrator.py`, I empirically verified the field note's two reported bugs against the *pre-purge* catalog:
1. **Bat-list truncation** — confirmed: alphabetically-sorted 12-battery list with `limit=10` cut off Tattu (12th) and `lipo_6s_6000mah` (11th).
2. **Bat-sku/Bat-help "loops the define Brief"** — traced to two independent causes:
   - The list truncation itself (Tattu literally wasn't a valid answer).
   - **A separate, real bug**: even with Tattu visible, a bare "ayúdame a elegir" *after* the battery was already catalog-bound (the exact "cambiar bateria" rebind flow) fell through because `battery_wants_help`'s re-offer condition required `_wants_catalog_help` (which reads any bound `catalog_ref` as "done"), lacking the redefine-only escape motors already got from G18. Reproduced the exact symptom (a fresh "Vamos a definir la batería..." Brief instead of the list) before fixing, then re-verified after — this is a genuine fix, not just a purge-driven redirect.

## Redirect log (§4.2 disclosure — every golden changed, by category)

**Simple SKU swap (DROP → analogous KEEP, no other change):** `test_g24_apply_by_index.py`, `test_g24_viable_selection.py`, `test_impl_d_sku_bom.py`, `test_electrical_compatibility.py` (prop-motor mismatch pair), `test_engineering_readiness_erf2_gaps.py` (mismatch pair), `test_catalog_bind_v1.py` (propeller bind), `test_component_library.py` (5 lookups), `test_idle_catalog_rebind_b3.py` / `test_idle_frame_rebind_b2.py` (shared propeller fixture), `test_geometry_esc_visor_rebind_b1.py`, `test_geometry_propeller_envelope_b0_b1.py`, `test_geometry_propeller_cited_seeds_b2.py`, `test_dse_motor_op_dual_truth.py`, `test_block_closure_prop_energy.py`, `test_cli_feasibility_semantics.py`, `test_energy_params.py`, `test_cli_catalog_assist_watts_recovery.py`, `test_g21_g22_catalog_bind_ux.py`, `test_project_closure_v1.py`.

**Numeric recompute (DROP SKU's own real numbers replaced by the KEEP substitute's real numbers, every downstream assertion updated to match):** `test_impl_c_catalog_aware_dse.py`, `test_impl_c_catalog_dse_thrust_bridge.py`, `test_dse_apply_honest.py` (battery-factor target recomputed to `lipo_6s_6000mah`'s real 133.2 Wh via a 1.8× factor instead of 2.0×, since no KEEP pair shares the old exact-double relationship), `test_assisted_acquisition.py` (FN-007 bundle assertions recomputed for `sunnysky_r2205_2500`'s real thrust/watts/kv/weight).

**Fixture recalibration (same qualitative scenario — e.g. "motor underspec" — reproduced against real KEEP hardware by adjusting `motor_count`/`payload_kg`, since KEEP motors are uniformly stronger than the deleted ones):** `test_cli_catalog_assist_t1.py`, `test_cli_catalog_assist_t1_plus_2.py`, `test_cli_fail_routing_coherence.py` (two "thrust fails, autonomy demonstrably met/not-met" scenarios — one reproduced with real physics at a heavier payload, the other needed a disclosed, explicit `warnings`/`autonomy_min` override after confirming the real thrust-fail state first, since no real KEEP battery can sustain 10+ minutes at the power draw needed to fail a KEEP motor's thrust — documented inline as a synthetic-`SimulationResult` pattern already precedented in `test_impl_c_catalog_aware_dse.py`).

**Monkeypatch-injected synthetic fixture (no surviving real SKU can reproduce the exact scenario at all — e.g. "zero operating_points", "kv-excluded-from-strict-but-relaxed-still-finds-it", "no diameter_mm", "no max_continuous_current_a"):** `test_phase2_lookup_operating_point.py` (`legacy_motor_sku` fixture), `test_cli_catalog_assist_t1_plus_2.py` (`relaxed_only_motor_sku` fixture), `test_g9a_catalog_ref_gap.py` / `test_engineering_readiness_gaps.py` (`_brotherhobby_in_library` fixture, identical synthetic row in both), `test_geometry_motor_visor_rebind_b1.py` (`_mute_sku_in_library` fixture), `test_geometry_declared_battery_plate_envelope_b1.py` (inline synthetic `BatterySpec`), `test_engineering_readiness_erf2_gaps.py` / `test_electrical_compatibility.py` (`replace()`-based fake `max_continuous_current_a=None` on a real KEEP battery spec — reuses the SAME real `c_rating`/`capacity_mah` so the derived value matches that row's own stated `max_continuous_current_a`, only the "field present" precondition is faked). All monkeypatch fixtures use `monkeypatch.setitem`/`setattr`, auto-reverted at test teardown, and **never write to `library/` on disk**.

**Removed with explicit disclosure (the test's entire subject was the deleted, unsourced row itself — e.g. "prove this unsourced sibling never inherited its neighbor's dims"):** `test_catalog_foundation_v1.py` (`test_motor_envelope_omitted_for_unsourced_sibling_sku`, `test_battery_envelope_omitted_when_unsourced`), `test_catalog_bind_v1.py` (`test_battery_bind_omits_envelope_when_unsourced`), `test_geometry_sourced_dims_b1.py` (`test_t4_generic_lipo_3s_2200mah_byte_stable`). Every removal's replacement comment explains *why* — the row's non-existence is this Buy's own intended outcome, not a coverage gap — and cross-references the still-standing test that covers the same underlying schema-default mechanism (`test_motor_optional_enrichment_fields_default_none`'s new synthetic single-row library) where one exists.

**Consolidated (two near-duplicate tests reduced to one when both would have needed the identical single surviving KEEP substitute):** `test_geometry_motor_height_cited_b1.py`'s `test_t3`/`test_t4` merged into one `test_t3_sunnysky_r2205_2500_height_mm_none` (both DROP subjects — `sunnysky_r2305_2500` and `emax_rs2205_2300` — needed the same one remaining "no height_mm" KEEP sibling, `sunnysky_r2205_2500`; asserting the same fact twice against the same substitute added nothing).

**KV-band redirect (920KV/1100KV had no real match; every KEEP motor is 2300+KV):** `test_iterate_session.py` (2 tests), `test_orchestrator.py` (2 tests) — `920KV` → `2300KV`, verified empirically to still produce a real, non-empty suggestion list before locking in the new number.

## Suite arithmetic

Baseline suite was 2785 (from the immediately prior, unrelated `estimated_temporary_plate_b1` cycle) at the moment this IC's work began; that count already included concurrent in-flight work from another session (an `hglrc_my5` frame cycle) not authored by this one. This cycle's own net delta: +40 rows deleted from `library/`, 17 new tests added (`test_catalog_sourced_only_purge_battery_rebind_b1.py`), 3 tests removed (unsourced-sibling premise gone), 1 test-pair consolidated into 1 (−1). Full suite now **2796 passed, 1 skipped** (the 1 skip is pre-existing and unrelated — `test_component_library.py`'s `test_find_motors_by_kv_empty_for_very_tight_tolerance`-adjacent skip path, unchanged by this cycle).

## Tests executed

`python -m pytest -q` → **2796 passed, 1 skipped**, 0 failed. Ran the new guardrail file alone first (17 passed), then every redirected file individually as each was fixed (all reported inline above), then the full suite as the final gate.

## Non-goals honored

Sensors/`cambiar sensor` rebind untouched (B3, separate). Frame rebind untouched (B4). Continuity ASSEMBLY READY/bloque copy untouched beyond the two DROP-SKU docstring fixes explicitly in scope. Estimated-temporary plate / layout cola untouched (separate, prior cycle). No KEEP `lipo_*` key renamed to a branded SKU id (§9's own explicit "not this IC unless ★ expands" — never expanded). No live page fetched or verified HTTP 200 — every `source_url` was trusted as-authored by the KEEP rows' own prior citation work. No live `workspace/` project auto-rebound off a DROP ref — confirmed both live `state.json` files already reference only KEEP SKUs (`emax_rs2205s_2300`, `tattu_2300mah_4s_75c_xt60`, `iflight_xing_e_pro_2207_2450`, `hglrc_my5_5in`, etc.) coincidentally already; only the immutable `history/iterations/*.json` audit trail for `autonomía-de-5min` still names DROP SKUs (`lipo_3s_2200mah`, `emax_rs2205_2300`) from past turns — a historical record, not live state, left untouched per lock #3 ("not auto-migrated this Buy"). No test weakened or deleted solely to make the suite pass — every removal is disclosed above with a stated reason tied to the row's deletion, never to dodge a failure. No version bump (`pyproject.toml` still `0.4.1`).

## Remaining risks / notes for review

- **Motor/prop suggestion pool is now small** (3 motors, 6 propellers, 5 batteries). Several "relaxed search" / "underspec" UX paths that used to show 3-5 alternatives now show 1-2, or occasionally 0 (honest "no tengo un motor" refusal) — this is the correct, honest behavior post-purge, but Engineer smoke should confirm the resulting UX still feels usable with such a small live catalog, not just correct.
- **Two monkeypatch-based synthetic-fixture patterns** (`legacy_motor_sku`, `_brotherhobby_in_library`, `relaxed_only_motor_sku`, `_mute_sku_in_library`) now exist across 5 test files, each independently defined (not a shared conftest helper). They're small, well-documented, and auto-reverting, but if a *sixth* similar gap surfaces in a future cycle, promoting this to one shared `tests/conftest.py` fixture would be worth considering rather than defining a sixth copy.
- **`test_dse_apply_honest.py`'s battery-factor redirect uses 1.8× instead of the original 2.0×** — the exact multiplier was never a locked contract value, only a vehicle to reach a real catalog Wh figure; flagging in case a future reader assumes 2.0× is significant.
- The Bat-help fix (`_battery_only_redefine` clause) mirrors motors' own G18 escape exactly — if propellers/ESC/frame ever gain an equivalent "already-bound, redefine-only, help-choose-must-still-re-offer" requirement, the same pattern applies there too (not needed today; propellers/frame don't currently expose an analogous rebind-then-underspec path in the field note).
