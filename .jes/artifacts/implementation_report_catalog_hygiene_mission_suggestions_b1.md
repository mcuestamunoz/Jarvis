# Implementation Report — Catalog hygiene + SuggestionEngine mission gate (`B1-catalog-hygiene-mission-suggestions`)

**IC:** `implementation_contract_catalog_hygiene_mission_suggestions_b1.md`
**Implementer:** Claude Code
**Date:** 2026-09-17
**Checkpoint:** package `0.4.1` (unchanged) · suite **3027 passed, 1 skipped** (was 3006) · UI unaffected

---

## 1. Scope delivered

All three parts (A, B, C) in one Buy, exactly as locked. No new catalog families, no invented mm, no axial prop geometry, no version bump, no `workspace/` mutation (tests-only; all live-project reads below were in-memory verification via a real `JarvisOrchestrator(workspace_root=tmp_path)` in a temp directory or `ProjectState.model_validate(json.load(...))`, never `save_state` against the live `workspace/` tree).

---

## 2. Part A — bind omit-key hygiene

### A1/A2 — the bug and the fix

**Files:** `src/jarvis/core/catalog_bind.py`

Added one shared helper, `_merge_base_properties_dropping_stale_catalog_keys(base, sku, projected, catalog_projected_keys)`, and applied it to **all 8** `bind_*_from_catalog` functions (`motor`, `battery`, `propeller`, `esc`, `flight_controller`, `sensors`, `kit_hardware`, `frame`) — each with its own `_<FAMILY>_CATALOG_PROJECTED_KEYS` frozenset naming exactly the keys that family's own `projected` dict can ever contain (documented per-function; exact sets in §7).

**Critical refinement found during implementation** (not in the original IC text, discovered via the existing regression suite): the first draft dropped any catalog-owned key absent from the new `projected` dict whenever its stored value had `source == "declared"`. This **broke two pre-existing, intentionally-locked tests**:
- `test_p9_refresh_from_catalog_preserves_declared_dims` (battery)
- `test_replace_path_refresh_preserves_estimate_while_catalog_still_lacks_h` (ESC)

Root cause: `source == "declared"` is used identically by (a) a prior catalog projection **and** (b) an Engineer's own manual `set_component_declared_box_envelope` call — there is no schema-level way to tell them apart by `source` alone. Both `refresh_component_from_catalog` (same SKU, re-projecting today's catalog data) and a genuine rebind (different SKU) call the same `bind_*_from_catalog(..., base=...)` function — the correct distinguishing signal is **whether the SKU is actually changing**, not the property's `source` tag.

**Final design:** the helper only drops stale catalog-owned keys when `base.catalog_ref is None or base.catalog_ref.sku != sku` (a genuine SKU change). A same-SKU refresh (`sku_changed == False`) never drops anything — preserving the Engineer's own manual declares and `estimated_temporary` values exactly as the pre-existing tests require. Both previously-broken tests pass unmodified; a new regression test locks this distinction explicitly (`test_esc_same_sku_refresh_preserves_estimated_temporary_height`).

### A3 — scope: ESC + FC + sensors (required) + motor/battery/propeller/kit_hardware/frame (extended, "iff cheap")

The IC allowed deferring motor/battery/propeller/frame as residual debt "iff cheap and shared helper." Since the shared helper was already built for ESC/FC/sensors, applying it to the remaining 5 bind functions was mechanical (one frozenset + one merge-call swap each) — so **all 8** were fixed in this Buy rather than leaving 5 identical latent bugs as residual debt. No test regressions from this broader application (full suite green).

### A4 — clear-on-geometry-change unaffected

`_clear_fit_attestations_after_geometry_change` and `_cleared_fit_attestation` (fit-attestation clearing on envelope/pose writes) were not touched — they operate on a completely different write path (`set_component_declared_box_envelope`/`set_component_declared_box_pose`), not the catalog-bind `base=` merge this Buy fixes.

### Empirical verification

```
SpeedyBee ESC (height_mm=8.0) → rebind Skystars (no height_mm) → height_mm ABSENT (was leaking before this fix)
SpeedyBee ESC → same-SKU refresh                                → height_mm=8.0 SURVIVES
SpeedyBee FC (height_mm=7.8) → rebind Skystars F4 V4 (no height) → height_mm ABSENT
ESC estimated_temporary(9.5mm) declared on Skystars → same-SKU refresh → 9.5mm SURVIVES, source unchanged
```

---

## 3. Part B — IDLE FC/GPS rebind + refresh

### B1 — rebind vocabulary

**File:** `src/jarvis/core/catalog_rebind_assist.py`

`CatalogRebindKey` extended with `"flight_controller"`/`"sensors"`; `_FAMILY_NOUN_PATTERNS` and `_PURE_PHRASE_STRIP_RE` extended with the exact same vocabulary `mounted_on_declare_assist._SUBJECT_PATTERNS` already uses for these two keys (`fc`/`flight controller`/`controladora`/`pixhawk` → `flight_controller`; `gps`/`sensores`/`sensor` → `sensors`) — reused rather than a second, possibly-diverging list.

### B2 — orchestrator dispatch

**File:** `src/jarvis/core/orchestrator.py`

Two new `elif` branches in the existing IDLE-rebind dispatch block, calling the **existing** `_offer_flight_controller_identity_catalog`/`_offer_sensor_identity_catalog` methods — the same numbered identity-suggestion offer (`library/fc`/`library/sensors`, via `control_identity_catalog_assist.py`) the first-time `DEFINE_MISSING_PARAMETERS` acquisition path already uses. No new picker invented. The pick-application path (`_apply_control_identity_catalog_pick`, triggered on the *next* turn once `session.flight_controller_suggestions`/`session.sensor_suggestions` is set) required zero changes — it's already wired for exactly this session shape.

### B3 — refresh

**Files:** `src/jarvis/core/component_writers.py`, `src/jarvis/core/catalog_refresh_assist.py`

`_REFRESH_BINDERS` dict gained two entries (`"flight_controller": bind_flight_controller_from_catalog`, `"sensors": bind_sensor_from_catalog`) — both binds have existed since `B1-library-fc-sensors`; only the refresh-dispatch table entry was missing. `catalog_refresh_assist._SUBJECT_PATTERNS` extended with the same FC/GPS vocabulary as B1. `actualiza el fc`/`actualiza el gps` now resolve and succeed (previously would have raised `ValueError: Familia de catálogo 'flight_controller' no soportada`) — the **success path** was achieved, not a documented refusal.

### Empirical verification

```
resolve_idle_catalog_rebind("cambiar controladora") → "flight_controller"
resolve_idle_catalog_rebind("cambiar fc")            → "flight_controller"
resolve_idle_catalog_rebind("cambiar gps")           → "sensors"
resolve_idle_catalog_rebind("cambiar sensores")      → "sensors"

orch.handle_user_text("cambiar controladora", ...) → numbered list (Pixhawk 4, SpeedyBee F405 V4)
orch.handle_user_text("cambiar gps", ...)          → numbered list (Holybro M10)

resolve_catalog_refresh_component("actualiza el fc")  → "flight_controller"
resolve_catalog_refresh_component("actualiza el gps") → "sensors"
refresh_component_from_catalog(state, "flight_controller") → succeeds (was ValueError before this Buy)
refresh_component_from_catalog(state, "sensors")            → succeeds (was ValueError before this Buy)
```

---

## 4. Part C — SuggestionEngine / action_map mission gate

### C1 — the gap Continuity #1 left open

`ReasoningLayer._collect_suggested_actions`'s `for suggestion in suggestions:` loop (the **action_map enrichment path**, fed by `SuggestionEngine.generate_suggestions` output passed as the `suggestions=` kwarg) enriches an injected `type: "increase_payload"` entry **unconditionally** — this loop runs *before* the `if not enriched and ... high_margin` fallback that `B1-continuity-mission-intent` (#1) already gated, so whenever `simular`/`iterate` calls `ReasoningLayer.build(context, suggestions=suggestions_payload)` with a payload that includes `increase_payload` (which `SuggestionEngine` emits whenever margin > 1.8), `enriched` is non-empty before the #1 gate is ever reached — **#1's fix was structurally unreachable from the simulate/iterate paths**. Separately, `simulate.py`/`iterate.py`/`create_project.py` each also put the **raw, unfiltered** `SuggestionEngine` output straight into `result["suggestions"]`, rendered by CLI's own `"- Podrías {label}"` bullet list — a second, completely independent leak.

### C2/C4 — the fix (two consumer sites, `SuggestionEngine` itself untouched)

Per lock C4's explicit choice — "SuggestionEngine may stay physics-only if all consumers filter" — `suggestion_engine.py` was **not touched**. Two new shared helpers in `reasoning_layer.py`:

1. **`ReasoningLayer._mission_context_fields`/`_mission_intent_active_for`** — small refactor extracting the `(objective, restrictions, components)` read from `context`, now shared between the pre-existing `_mission_aware_high_margin_suggestion` (#1) and the new gate below.
2. **The action_map loop gate**: `if suggestion_type == "increase_payload" and self._mission_intent_active_for(context): continue` — skips enriching the injected entry. If nothing else in the payload got enriched, the pre-existing `if not enriched and ... high_margin` fallback (#1's own waterfall) now correctly fires with the mission-aware alternate. If a sibling suggestion (e.g. `improve_efficiency`) also enriched, `increase_payload` is simply **suppressed** — both outcomes are explicitly sanctioned by IC lock/test T9 ("waterfall/alternate instead, **or suppress**").
3. **`filter_mission_gated_suggestions(suggestions_payload, objective, restrictions, components)`** (module-level, `reasoning_layer.py`) — for the **raw** bullet list only. Chosen UX: **suppress**, not rewrite-in-place — the raw `Suggestion` schema (`type`/`reason`/`expected_effect`/`priority`) has no `label`/`action_type` fields to carry the rich #1 waterfall alternate, so duplicating that logic into a second schema was rejected as needless duplication (lock C4). The rich alternate still surfaces via `ReasoningLayer.suggested_actions` (point 2 above) — this function only prevents the *same* "Aumentar carga útil" bullet from *also* appearing, unfiltered, in the separate raw list.

Wired at all **three** call sites that build a `suggestions_payload` from `SuggestionEngine`: `src/jarvis/actions/simulate.py`, `src/jarvis/actions/iterate.py` (the physical-iterate branch only — the declarative-iterate branch always passes `suggestions=[]`, nothing to gate), `src/jarvis/actions/create_project.py`.

### C3 — neutral regression

Confirmed byte-identical: a neutral project's raw suggestions list and `ReasoningLayer.suggested_actions` both still show `increase_payload`/"Aumentar carga útil" unchanged.

### C5 — forbidden items confirmed untouched

`HIGH_MARGIN_THRESHOLD` (both `reasoning_layer.py`'s `1.5` and `suggestion_engine.py`'s own separate `1.8`) unchanged; no `ASSEMBLY_READY` touch; no LLM rewrite of suggestions.

### Empirical verification

```
dron-de-vigilancia-doméstico (real fixture, margin 3.62, cameras+radio both medium):
  raw SuggestionEngine list  → ["improve_efficiency"]           (increase_payload suppressed)
  ReasoningLayer top action  → "Mejorar eficiencia"              (increase_payload suppressed, sibling survived)

Synthetic (mission active, ONLY increase_payload injected):
  ReasoningLayer top action  → mission-aware alternate fires (waterfall, IC #1 logic reused)

Neutral 10-min-autonomía-shaped fixture (objective forced neutral, cameras/radio stripped, margin 3.62):
  raw SuggestionEngine list  → ["increase_payload", "improve_efficiency"]   (unchanged)
  ReasoningLayer top action  → "Aumentar carga útil"                        (unchanged)
```

---

## 5. Docs (lock: Shared #4)

**File:** `docs/USER_GUIDE_CRAFT_MONTAGE.md`

- §3.2: `cambiar X` family list extended to include `controladora`/`gps`; the "🟡 Trampa conocida" line documenting the FC/GPS rebind gap removed/replaced with a closed-note.
- §12.2: the three now-fixed "Limitaciones conocidas" bullets (`cambiar controladora`/`cambiar gps` don't reopen; `actualiza el fc`/`actualiza el gps` don't exist; ESC rebind omit-key leak) collapsed into two closed-notes citing this Buy.

**Noted but intentionally NOT touched** (out of this Buy's literal lock #4 scope, which named only "FC rebind / bind-esc leak"): §12.2's separate "Hélices → motores sigue n/a (Buy aparte)" line is *also* stale — it predates `B1-disk-station-reach`/`B1-propellers-motors-catalog-pair`, which already shipped real `station_reach_*`/`catalog_pair_*` evidence for both mount-only pairs. This is leftover doc debt from those two prior, already-closed Buys, not from this one — flagged here rather than opportunistically fixed, per the narrow-scope discipline this session has followed throughout.

---

## 6. Tests

### Added (`tests/test_catalog_hygiene_mission_suggestions_b1.py`, 21 tests)

| ID | Tests | Covers |
|---|---|---|
| T1 | `test_t1_esc_rebind_to_sku_without_height_drops_stale_height` | ESC omit-key drop on real SKU change |
| T2 | `test_t2_esc_rebind_preserves_mounted_on_and_pose` | `mounted_on`/`declared_box_pose` survive |
| — | `test_esc_same_sku_refresh_preserves_estimated_temporary_height` | Regression guard for the mid-implementation fix (§2) |
| T3 | `test_t3_flight_controller_rebind_to_sku_without_height_drops_stale_height` | FC omit-key drop |
| — | `test_sensor_bind_omit_key_mechanism_shares_esc_fc_helper` | Sensors family shares the same helper (live library has only one sensor SKU, so only same-SKU round-trip is exercisable against real data) |
| T4 | `test_t4_cambiar_controladora_resolves_flight_controller` | Rebind resolver, new keys |
| T5 | `test_t5_cambiar_gps_resolves_sensors` | Rebind resolver, new keys |
| — | `test_t4_t5_regression_existing_rebind_keys_unaffected` | esc/frame/bare-help unaffected |
| T6 | `test_t6_cambiar_controladora_offers_numbered_fc_catalog`, `test_t6_cambiar_gps_offers_numbered_sensor_catalog` | End-to-end IDLE dispatch → numbered offer |
| T7 | `test_t7_actualiza_el_fc_resolves_refresh_key`, `test_t7_actualiza_el_gps_resolves_refresh_key`, `test_t7_refresh_component_from_catalog_succeeds_for_flight_controller`, `test_t7_refresh_component_from_catalog_succeeds_for_sensors` | Refresh resolver + writer success path |
| T8 | `test_t8_filter_mission_gated_suggestions_suppresses_increase_payload`, `test_t8_filter_mission_gated_suggestions_neutral_returns_unchanged`, `test_t8_simulate_action_mission_active_suppresses_raw_increase_payload` | Raw-list gate, unit + end-to-end |
| T9 | `test_t9_action_map_loop_skips_injected_increase_payload_when_mission_active`, `test_t9_action_map_loop_suppresses_when_sibling_suggestion_also_present` | Both IC-sanctioned outcomes (alternate vs. suppress) |
| T10 | `test_t10_neutral_mission_regression_increase_payload_still_enriched`, `test_t10_simulate_action_raw_list_and_reasoning_both_neutral_regression` | Neutral regression, unit + end-to-end |

### T11/T12

`tests/test_continuity_mission_intent_b1.py` and `tests/test_wizard_mission_nudge_b1.py` — untouched (`git diff --stat` empty), both fully green (25 tests). Full suite:

```
python -m pytest tests/test_catalog_hygiene_mission_suggestions_b1.py -q  → 21 passed
python -m pytest -q                                                        → 3027 passed, 1 skipped
```

No UI files touched — `ui/spatial-board` vitest suite not re-run (unaffected).

---

## 7. Exact frozensets (per-family catalog-projected keys, lock A2's "report exact frozenset")

```
motor:              thrust_n, kv_rating, weight_g, power_w, stator_diameter_mm,
                     stator_height_mm, diameter_mm, shaft_diameter_mm, height_mm
battery:             battery_capacity_wh, mass_g, chemistry, cell_count,
                     length_mm, width_mm, height_mm
propeller:           diameter_in, pitch_in, mass_g, blade_count, material,
                     hub_diameter_mm, hub_thickness_mm, mass_tolerance_g, shaft_bore_mm
esc:                 current_a, mass_g, length_mm, width_mm, height_mm
flight_controller:   length_mm, width_mm, height_mm
sensors:             length_mm, width_mm, height_mm
kit_hardware:        pin_count, pitch_mm, wire_gauge_awg, color, pin_config
frame:               mass_kg, size_class_inch, material, wheelbase_mm, configuration,
                     body_length_mm, body_width_mm, max_stack_height_mm
```

## 8. Out of scope (unchanged, named debt per IC §4)

More identity rules (payload/arm/…, queue #5) · axial prop↔motor/HD-005 (parked) · plate-box/Path N (parked) · full `SuggestionEngine` redesign (only the `increase_payload` mission gate was in scope) · the stale "hélices → motores n/a" doc line (§5, flagged not fixed).

## 9. Remaining risks

None identified. The mid-implementation fix in Part A (SKU-change vs. same-SKU-refresh distinction) was caught by the existing regression suite before it could ship as a new bug — both previously-passing tests it would have broken are green again, plus a new test locks the distinction explicitly.
