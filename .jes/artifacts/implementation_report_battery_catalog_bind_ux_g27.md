# Implementation Report — Battery Catalog UX + G27 Hardening (IC 2 / Project Closure arc)

**Contract:** [`implementation_contract_battery_catalog_bind_ux_g27.md`](implementation_contract_battery_catalog_bind_ux_g27.md)
**Implementer:** Claude Code
**Base:** `checkpoint-requirements-closure` (`e986a58`)
**Status:** Complete, all slices (Bat-1 … Bat-8) implemented, full suite green (**1973 passed**, +13 new), CLI probe **6/6 PASS**.

---

## 1. Bat-0 — as-is trace (verified live, not assumed)

Re-ran the investigation's bind → writer → calc → autonomy → readiness call graph against the current codebase before writing any UX code:

```text
bind_battery_from_catalog(sku)                    catalog_bind.py:78-123   [unchanged]
  → ComponentSpec{battery_capacity_wh, mass_g, chemistry, cell_count}
  ↓
set_battery_component(state, spec, capacity_wh)   component_writers.py:122-169  [unchanged]
  → current_parameters["battery_capacity_wh"]
  → current_parameters["battery_mass_kg"]           (real SKU mass_g, not the
                                                       150 Wh/kg heuristic)
  → current_parameters["battery_cell_count"]
  ↓
calculation_engine.build()                        calculation_engine.py:164-178 [unchanged]
  → autonomy_min = calculate_autonomy_min(battery_capacity_wh, motor_power_w × motors)
  ↓
engineering_readiness._energy_evidence            engineering_readiness.py:923-932 [unchanged]
  → catalog_bound = _catalog_ref_set(..., "battery")
```

**Confirmed before coding:** `grep -rn bind_battery_from_catalog src/` returned **zero** hits outside `catalog_bind.py` itself — the bind→writer→calc chain was exactly as complete and exactly as unwired to any production call site as the investigation reported. `set_battery_component` is already imported at `orchestrator.py:53` (used by an unrelated numeric-wizard path), confirming the locked apply pattern (§5) could reuse it directly with no new import surface.

This trace determined the whole rest of the implementation: **no calc/energy/readiness code needed to change at all** — only a UX entry point calling the two existing functions, plus the G27 parser fix.

---

## 2. Files changed

| File | Slice | Change |
|---|---|---|
| `src/jarvis/schemas/action_schema.py` | Bat-1 | `InteractiveSessionState.battery_suggestions: list[dict]` (additive, runtime-only). |
| `src/jarvis/core/state_manager.py` | Bat-1 | Comment note added to the persisted-fields exclusion list. |
| `src/jarvis/core/battery_catalog_assist.py` | Bat-2 | **New.** `BatterySuggestion`, `build_battery_catalog_suggestions`, `format_battery_catalog_suggestions`, `battery_spec_to_suggestion`. Re-exports `is_help_choose_phrase`/`match_suggestion_by_input` from `motor_catalog_assist` (★2, same as `propeller_catalog_assist`). |
| `src/jarvis/core/orchestrator.py` | Bat-3/4 | `_offer_component_battery_catalog`, `_apply_component_battery_catalog_pick` (locked apply path), `_try_start_assisted_battery_help` (IDLE fallback), dispatch wiring in `_handle_component_description` and the IDLE help-choose chain, cross-family suggestion-clearing symmetry on the motor/propeller offer methods. |
| `src/jarvis/core/acquisition_brief.py` | Bat-5 | Catalog-bullet gate extended `("motors", "propellers")` → `("motors", "propellers", "battery")`; stale comment ("battery... no bind path yet") corrected. |
| `src/jarvis/llm/semantic_intent_adapter.py` | Bat-6 | `_resolve_battery_capacity_wh_from_text()` (new, module-private) + a `canonical == "battery_capacity_wh"` branch inside `adapt()`. `_parse_value` itself **untouched**. |
| `tests/test_battery_catalog_bind_ux.py` | Bat-7 | New, 12 tests. |
| `scripts/cli_probe_battery_catalog_bind_ux.py` | Bat-8 | New, self-contained, 6/6 PASS. |

**`param_definition_session.py` not touched** — the contract listed it as "Bat-6 only if ingest path needs choke point." It doesn't: G27's bug lives entirely in `semantic_intent_adapter.adapt()`, which never routes through `param_definition_session`'s ingestion layer (that layer's own `is_derived` gate, from IC 1, is unrelated to this bug).

**Not touched** (confirmed via `git diff --stat`, matches §10's "must not change" list exactly): `resolve_operating_point`, P2-1 seeds, `propeller_catalog_assist.py`/`motor_catalog_assist.py` (imported from, never edited), `_requirements_declared`/`state_schema.py` (IC 1), `project_closure._bom_sku_resolved`, G24 DSE, ESC catalog, `pyproject.toml` version, `library/baterias/_datos.json`.

---

## 3. Behavior changed

- **New:** the component wizard (`MISSING_COMPONENT_DEFINITION`/energy block) now offers a live, numbered battery catalog pick — "ayúdame a elegir" lists all 10 seed batteries (`list_batteries()`, Option A — see §5 scope note), a numeric pick calls `bind_battery_from_catalog` + `set_battery_component`, exactly as the contract's locked apply path specifies.
- **New:** IDLE "ayúdame a elegir" now falls through motor → propeller → battery (in that order), offering the battery picker once motor and propeller both have nothing left to offer.
- **New:** `semantic_intent_adapter.adapt()` resolves `"LiPo 6S 10000mAh"`-shaped text to **222.0 Wh** (matching the `lipo_6s_10000mah` seed exactly, via the deterministic `mAh/1000 × cells × 3.7V` formula — the same nominal-cell-voltage convention already used elsewhere in this codebase, e.g. `electrical_compatibility._nominal_pack_voltage_v`) instead of silently reading "6" as 6.0 Wh.
- **New:** when a cell-count marker (`"6S"`) is present but no capacity (mAh) can be found, the adapter suppresses the value entirely (`value=None`) rather than falling back to the naive digit grab — the iterate wizard then re-asks instead of persisting a wrong number.
- **Unchanged:** `_parse_value`'s behavior for every non-`battery_capacity_wh` variable (verified: `test_g27_generic_parse_value_unchanged_for_non_battery_variables` — `motor_power_w` with a `"6S 400W"`-shaped input still returns `"6"`, byte-identical to pre-fix behavior).
- **Unchanged:** P2-1 propulsion OP resolution, propeller-bind UX, motor-bind UX, IC 1's requirements semantics — confirmed by the full pre-existing suite passing unmodified (1960/1960) plus targeted regression runs.
- **Live headline result** (CLI probe, real `handle_user_text` turns): architecture A → motor bound (`sunnysky_r2305_2500`) → propeller bound (`gemfan_5030`) → ESC declared → energy block auto-opens → battery pick (`lipo_6s_10000mah`) → `battery_capacity_wh=222.0`, `battery_mass_kg` from real SKU mass, `battery_cell_count=6` → `calcular` → `autonomy_min=15.1364` (coherent, not a 6 Wh collapse) → `estado` shows `[lipo_6s_10000mah]` resolved.

---

## 4. Scope decisions disclosed

1. **Bat-2 Option B (energy-floor filter) not implemented.** The contract labels it "Optional enhancement," Option A "Acceptable default." I implemented Option A only (`list_batteries()` capped) — the ambiguity of what an *empty* filtered result should honestly fall back to (silently broaden to the full list? show a filtered-empty message?) isn't resolved unambiguously by the contract, and Option A alone already satisfies every locked acceptance criterion (§9 probe steps 2–4 all pass against the plain catalog list). Documented in `battery_catalog_assist.py`'s own module docstring.
2. **`limit=10` for battery suggestions, not `limit=5` (motors/propellers' default).** The contract's own §3 Option A table says "capped at N (**10 entries** — honest full v1 catalog)" — the full seed is exactly 10 batteries, so `limit=10` shows the entire catalog unfiltered, matching that literal wording. Motors/propellers use `limit=5` because their suggestions are already design-space-filtered (thrust/KV/compatibility); batteries have no such filter in Option A, so a lower cap would arbitrarily hide seed entries (confirmed necessary: `lipo_6s_10000mah` is 8th alphabetically — a `limit=5` default would have hidden it from the picker, failing the contract's own probe step 2 pass criterion).
3. **No new refresh helper after a battery-only pick — verified empirically, and the right call for a stronger reason than the contract's own "unlikely" framing suggested.** I initially assumed (incorrectly) that this was safe because `set_motor_component` "reads the battery fresh each call." I tested that assumption directly against `library.resolve_operating_point`'s actual matching rule (`library.py:604-621`) before writing this section, and it's more subtle:

   - `voltage_matches` is `True` whenever the caller passes `voltage_v=None` — i.e. **exact-match resolution already ignores voltage entirely when no battery is bound yet**, so the propeller-bind's existing `★5` re-call (`orchestrator.py`'s `_apply_component_propeller_catalog_pick`) already achieves `exact_operating_point` with no battery involved, for any motor/propeller pair whose library row matches on `propeller_sku` alone.
   - I then tested what re-calling `set_motor_component` *would* do once a real battery voltage becomes available. Using the `emax_rs2205s_2300` + `hq_5045_bn` pair (the one with real exact-operating-point rows, both authored at `voltage_v=16.0`) and binding `lipo_4s_5000mah` (4S ≈ 14.8V nominal — outside the exact rows' epsilon window): re-invoking `set_motor_component` after the battery bind **downgrades** the resolution from `exact_operating_point` (9.7086 N) to `fallback_operating_point` (10.042 N) — because the real voltage no longer matches the curated exact rows within tolerance.
   - **Conclusion: re-calling `set_motor_component` after a battery-only pick would be an active regression risk**, not a missed refresh — it would let an energy-domain action (picking a battery) silently downgrade an already-resolved, more-precise propulsion evidence value, with the user never having touched propulsion. Not calling it (as implemented) leaves the motor's `propulsion_resolution` exactly as good as it already was at propeller-bind time — correct, and never worse. This is a stronger justification than the contract's own "(unlikely)" phrasing assumed, and is now grounded in an actual before/after trace rather than an assumption.
4. **G27 formula-only, no library SKU cross-match.** The contract's "acceptable outcomes" list explicitly allows "deterministic Wh from mAh × nominal voltage / standard LiPo formula" as sufficient, without requiring a SKU match. Implemented the formula only — simpler, no floating-point/tolerance-matching risk, and it produces the exact seed value (222.0 Wh) for the regression anchor's own numbers by construction (10000mAh × 6S × 3.7V / 1000 = 222.0).

---

## 5. Tests added (13, `tests/test_battery_catalog_bind_ux.py`)

| Test | Covers |
|---|---|
| `test_battery_help_choose_lists_catalog_including_seed_sku` | Bat-7 #1 |
| `test_battery_pick_binds_catalog_ref_and_real_energy_mass_cells` | Bat-7 #2 |
| `test_battery_pick_does_not_regress_already_resolved_propulsion_op` | Regression lock for §4 point 3's finding |
| `test_autonomy_min_reflects_real_sku_wh_after_calcular` | Bat-7 #3 |
| `test_idle_help_choose_offers_battery_once_propulsion_bound` | Bat-7 #4 |
| `test_idle_battery_help_noop_when_already_catalog_bound` | Bat-7 #5 |
| `test_motor_help_choose_wins_over_battery_when_both_incomplete` | Bat-7 #6 |
| `test_g27_6s_10000mah_never_yields_6wh` (parametrized ×3) | Bat-7 #7 |
| `test_g27_bare_cell_count_without_capacity_is_refused_not_guessed` | Bat-7 #7 negative arm |
| `test_g27_post_bind_adapter_is_stateless_never_touches_catalog_ref` | Bat-7 #8 |
| `test_g27_generic_parse_value_unchanged_for_non_battery_variables` | ★5 regression guard |

**Note on Bat-7 #8 (post-bind):** `semantic_intent_adapter.adapt()` is a pure function over the LLM output dict — it has no `project_state` parameter and therefore structurally cannot read or clear a `catalog_ref`. The test proves this invariant directly (adapt a G27 phrase against a project with a bound battery; assert the on-disk `catalog_ref` and `current_parameters` are byte-identical before/after, since `adapt()` never wrote anything) rather than driving a full stub-LLM through the iterate wizard's confirm/apply step — that later step is an existing, unrelated wizard-flow mechanism already covered by the iterate test suite, and isn't part of what G27 touches.

**Zero weakened tests.** No existing test file was modified.

---

## 6. Tests executed

```text
pytest tests/test_battery_catalog_bind_ux.py -v         → 13 passed
pytest tests/test_catalog_bind_v1.py
       tests/test_phase2_lookup_operating_point.py
       tests/test_requirements_closure.py
       tests/test_propeller_catalog_bind_ux.py
       tests/test_g21_g22_catalog_bind_ux.py
       tests/test_semantic_intent_adapter.py
       tests/test_impl_d_sku_bom.py                      → 107 passed
pytest tests/ (full suite)                                → 1973 passed (1960 pre-existing + 13 new)
python scripts/cli_probe_battery_catalog_bind_ux.py       → 6/6 PASS
```

---

## 7. Gate check (contract §12)

| Criterion | Result |
|---|---|
| Bat-0 trace documented with file:line | **PASS** — §1 above |
| Live pick → bind → `set_battery_component` → real Wh/mass/cells on disk | **PASS** |
| Probe 6/6; new tests green; full suite green | **PASS** |
| G27 scenario never produces 6.0 Wh for 6S 10000mAh class input | **PASS** |
| Motor/propeller/propulsion IC 1 regressions intact | **PASS** — targeted + full suite |
| No weakened tests without disclosure | **PASS** — zero existing tests modified; four scope decisions disclosed (§4) |
| No hardcoded SKU list in orchestrator | **PASS** — orchestrator only calls `battery_catalog_assist`, which only calls `ComponentLibrary.list_batteries()` |
| No parallel `bind_battery_*` helper | **PASS** — reuses `catalog_bind.bind_battery_from_catalog` verbatim |
| `_parse_value` not changed globally | **PASS** — untouched; new branch gated on `canonical == "battery_capacity_wh"` only |
| No fake PASS via invented battery rows or silent 6 Wh | **PASS** |

**Ready for Cursor review.**
