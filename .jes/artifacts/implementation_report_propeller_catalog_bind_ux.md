# Implementation Report — Propeller Catalog Bind UX

**Contract:** [`implementation_contract_propeller_catalog_bind_ux.md`](implementation_contract_propeller_catalog_bind_ux.md)
**Checkpoint base:** `checkpoint-phase2-p2-1` (`e82b8a1`)
**Status:** Implemented — Prop-1 through Prop-7 complete. 8 new tests + 1 updated regression test + CLI probe (6/6), full suite green (**1947 passed**, up from 1939 baseline). **Not committed.**

---

## 1. Files changed

| File | What |
|---|---|
| `src/jarvis/schemas/action_schema.py` | **Prop-1.** `InteractiveSessionState.propeller_suggestions: list[dict] = Field(default_factory=list)` — additive, symmetric with `motor_suggestions`. |
| `src/jarvis/core/state_manager.py` | Comment-only update: `propeller_suggestions` documented as runtime-only (same tier as `motor_suggestions`), not added to `_PERSISTED_SESSION_FIELDS`. |
| `src/jarvis/core/propeller_catalog_assist.py` | **Prop-2 (new module).** `PropellerSuggestion` TypedDict, `propeller_spec_to_suggestion`, `build_propeller_catalog_suggestions` (★1: `match_motor_propeller` filter, `[]` when no motor bound), `format_propeller_catalog_suggestions`. Re-exports `is_help_choose_phrase`/`match_suggestion_by_input` **imported from** (not copied from) `motor_catalog_assist.py` — ★2. |
| `src/jarvis/core/orchestrator.py` | **Prop-3/4/5.** New module-level `_is_stub_or_absent`/`_wants_catalog_help` predicates (★4). `_handle_component_description`'s catalog dispatch block replaced with the priority-gated motors/propellers chain (★4). New `_offer_component_propeller_catalog`/`_apply_component_propeller_catalog_pick` methods (mirror the motor ones; ★5 re-call of `set_motor_component` inside apply). `_offer_component_motor_catalog` now also clears `propeller_suggestions` when offering a fresh motor list. New `_try_start_assisted_propeller_help` (★6 B), wired as the FN-005 IDLE fallback when the motor assist returns `None`. |
| `src/jarvis/core/acquisition_brief.py` | **Prop-6.** Catalog bullet gate widened from `key == "motors"` to `key in ("motors", "propellers")`; comment updated. |
| `tests/test_g21_g22_catalog_bind_ux.py` | **Required update, not a weakening** — see §2/§6. |
| `tests/test_propeller_catalog_bind_ux.py` | **Prop-7.** New — 8 tests. |
| `scripts/cli_probe_propeller_catalog_bind_ux.py` | **Prop-7.** New — CLI probe, 6/6 PASS, real wizard turns only (no `bind_propeller_from_catalog` state patch). |

No changes to `catalog_bind.py`, `component_writers.py`, `library.py`/`resolve_operating_point`, `design_explorer.py`, `motor_catalog_assist.py` (only imported from, never edited), `project_continuity.py`, `engineering_readiness.py`. Confirmed via `git diff --stat -- src/ library/ tests/ scripts/`: exactly the files above.

---

## 2. Behavior changed (and explicitly what did not)

**Changed:**
- Propellers can now be acquired via a live numbered catalog picker, both inside the composite `propulsion` component wizard and as an IDLE re-bind for a freeform-declared, unbound propeller.
- A catalog-bound motor's operating-point resolution now correctly upgrades from `fallback_operating_point` to `exact_operating_point` the moment a compatible propeller is catalog-bound — no battery/voltage step required for the ★6 dataset (confirmed, §7 below).
- `_handle_component_description`'s catalog dispatch is no longer gated on bare `"motors" in expected_keys` — it now checks live incompleteness (`_wants_catalog_help`). This closes a real, previously-latent starvation bug: in the composite `["motors","propellers","esc"]` wizard, `expected_keys` never shrinks, so a propeller help-choose block placed after the old unconditional motors check would never have been reachable once motors was bound. Confirmed exactly via the fix.
- **One existing test's assertion changed** (`tests/test_g21_g22_catalog_bind_ux.py::test_g21_idle_help_choose_noop_when_catalog_ref_set`) — see §6 for the explicit rationale; this is a required update for legitimate new behavior, not a weakened guard.

**Explicitly unchanged (verified, not merely assumed):**
- `resolve_operating_point`'s match rules, the ★6 seed data, `v1_max_thrust` selection policy — zero lines touched anywhere in `library.py` (confirmed by `git diff --stat` — the file doesn't appear in the changed list).
- G21's motor catalog UX: `test_g21_component_wizard_help_choose_shows_numbered_catalog`, `test_g21_component_wizard_pick_sets_catalog_ref` — pass unchanged; probe step 6 spot-checks it live end-to-end.
- G22's single strict authority — `motor_catalog_assist.build_motor_catalog_suggestions` untouched.
- Freeform propeller declaration (`hélices 5x4.5`) still never sets `catalog_ref` and still never produces a false `exact_operating_point` (`test_freeform_propeller_never_produces_false_exact_op`).
- `set_motor_component`'s hashability contract (P2-1 lesson) — the ★5 re-call goes through the exact same code path, no new risk.
- BOM (Impl D), ERF-2 electrical facts, Continuity ranking formulas, G24/G26/G27 — zero lines touched.

---

## 3. ★1–★7 compliance

| ★ | Compliance |
|---|---|
| ★1 (suggestion authority = `match_motor_propeller`, no SKU hardcode) | Implemented exactly — `build_propeller_catalog_suggestions` contains no motor-SKU-specific branching anywhere; verified by the probe surfacing `gemfan_5030`/`gemfan_6040` alongside the P2-1 pair (ordinary diameter-tolerance matches, not special-cased). |
| ★2 (new module, import not duplicate) | `propeller_catalog_assist.py` imports `is_help_choose_phrase`/`match_suggestion_by_input` from `motor_catalog_assist` — `git diff` confirms `motor_catalog_assist.py` itself has zero changes. |
| ★3 (`propeller_suggestions` field, additive) | Implemented; existing sessions without it default to `[]` (Pydantic default), confirmed by the full suite passing unchanged for every pre-existing session-state test. |
| ★4 (predicate gating — mandatory, non-negotiable) | Implemented **exactly** per the IC's locked predicates: `_is_stub_or_absent`/`_wants_catalog_help` as specified, dispatch order motors-first, propellers only reachable when motors' own conditions don't consume the turn. `test_motors_help_choose_wins_when_both_incomplete` proves motors still wins when both want help; the CLI probe's step 3 proves propellers becomes reachable once motors is bound. |
| ★5 (explicit re-call, no new helper) | `_apply_component_propeller_catalog_pick` calls `set_motor_component` a second time with the existing motor spec — no `refresh_propulsion_resolution` or any other new function was created. Confirmed by `git diff --stat` (`component_writers.py` absent from the changed-files list). |
| ★6 (scope A+B) | Both implemented: Prop-3 (component wizard) + Prop-5 (IDLE re-bind, `_try_start_assisted_propeller_help`). |
| ★7 (no battery step needed) | Confirmed end-to-end by the CLI probe and by `test_propeller_pick_sets_catalog_ref_and_reresolves_exact_op` — neither declares a battery or `battery_cell_count`, and both reach `exact_operating_point`/9.7086 N from the propeller bind alone. |

**Additional locks — all honored:** `bind_propeller_from_catalog`/`set_propeller_component` reused, no parallel binder (confirmed: `catalog_bind.py`/no new bind function in `component_writers.py`); `resolve_operating_point` untouched; G24/G26/G27/ESC/battery-catalog/version-bump untouched; G21 motor help-choose/IDLE re-bind unbroken (probe step 6 + full suite); `propulsion_resolution` stays a JSON string (no change to that mechanism, only a second caller of the same writer).

---

## 4. Tests added + commands run + results

`tests/test_propeller_catalog_bind_ux.py` — 8 tests (IC §9.1 items 1-7, item 7 split into two: pure-function empty-list check + wizard-level honest-message check):

1. `test_propeller_component_wizard_help_choose_after_motors_bound` — composite wizard, motors bound → propeller list (not motors), `motor_suggestions` cleared.
2. `test_propeller_pick_sets_catalog_ref_and_reresolves_exact_op` — pick → `catalog_ref` set, `propulsion_resolution` parses to `exact_operating_point`/`v1_max_thrust`, thrust = 9.7086 N, no battery declared anywhere in the test.
3. `test_propeller_idle_help_choose_when_freeform_unbound` — freeform-declared propeller, IDLE help-choose → picker opens, singleton `["propellers"]`.
4. `test_propeller_idle_help_choose_noop_when_catalog_ref_set` — bound propeller → IDLE help-choose → no re-open.
5. `test_motors_help_choose_wins_when_both_incomplete` — both incomplete → motor list, `propeller_suggestions` stays `[]`.
6. `test_freeform_propeller_never_produces_false_exact_op` — freeform declare after a motor bind → `propulsion_resolution` stays exactly `fallback_operating_point` (unchanged), `catalog_ref` stays `None`.
7. `test_no_motor_bound_yields_empty_suggestions_not_full_dump` — pure `build_propeller_catalog_suggestions(None)` → `[]`.
8. `test_propeller_component_wizard_help_choose_before_motors_bound_is_honest` — singleton `["propellers"]` wizard, no motor bound → honest "bind a motor first" message, not a full catalog dump.

```
python -m pytest tests/test_propeller_catalog_bind_ux.py -v
# 8 passed

python -m pytest tests/test_g21_g22_catalog_bind_ux.py tests/test_phase2_lookup_operating_point.py -v
# all passed (named regression suites, 1 assertion updated with explicit rationale — see §6)

python -m pytest -q
# 1947 passed
```

1939 baseline (post-`checkpoint-phase2-p2-1`) + 8 new = 1947.

---

## 5. CLI probe result

`scripts/cli_probe_propeller_catalog_bind_ux.py` — **6/6 PASS**, real wizard turns only, no state-patch shortcuts:

1. `definir propulsion` → `ayúdame a elegir` → `emax_rs2205s_2300` listed as candidate `#5` → picked by number → bound.
2. `estado` → `fallback_operating_point · 10.042 N`.
3. `ayúdame a elegir` (propellers now the live gap) → real numbered list: `gemfan_5030, gemfan_6040, gf_5045x3, hq_5045_bn` — includes `hq_5045_bn`.
4. Pick `4` → `propellers.catalog_ref.sku == "hq_5045_bn"`.
5. `estado` → `exact_operating_point · 9.7086 N` — reached with **zero** battery/voltage step, confirming ★7.
6. Fresh second project: `definir propulsion` → `ayúdame a elegir` still returns the full motor candidate list — G21 unbroken.

---

## 6. Test change disclosure (required — CLAUDE.md "zero weakened tests")

`tests/test_g21_g22_catalog_bind_ux.py::test_g21_idle_help_choose_noop_when_catalog_ref_set` had its assertion changed. This is disclosed explicitly, not silently folded into the diff:

- **Original assertion:** `result.get("action") != "component_description_prompt"` — written when the *only* possible source of that action, in this fixture (bound motor, no propellers component at all), was a false motor re-bind.
- **Why it broke:** this fixture's project has motors bound and propellers as a genuine stub (absent). That is now the fixture's exact use case for the new, intended Prop-5 behavior: propellers legitimately wants catalog help, and the IDLE fallback correctly offers the propeller picker. The old assertion was testing an implementation detail (no `component_description_prompt` action at all) rather than the actual regression it was meant to guard (no false *motor* re-bind).
- **What changed:** the test now asserts directly and only the real regression guard — `pending_missing_params` must never become `["motors"]` again — and additionally asserts that *if* a picker opens, it's legitimately the propeller one (`pending_missing_params == ["propellers"]`), never a stray motor prompt.
- **Net effect:** the test is *stricter* about the thing it actually guards (motor re-bind), not weaker — it just no longer forbids a different, intended feature it was never designed to reason about.

No other test assertions were loosened, removed, or had their scope narrowed.

---

## 7. Remaining risks / deferred

1. **Battery/ESC catalog pick UX** — still out of scope (C3), as locked. `_wants_catalog_help`/`_try_start_assisted_propeller_help` pattern is now proven twice (motors, propellers) and would generalize cleanly to battery if that's ever prioritized — not built here.
2. **`_wants_catalog_help`/`_is_stub_or_absent` are currently duplicated as module-level functions in `orchestrator.py`** rather than shared with `component_writers.py`'s own `still_missing` completeness check (which uses a slightly different, narrower predicate — no `catalog_ref` check). Both are correct for their own purpose (dispatch gating vs. wizard-advancement), but a future cleanup could examine whether they should converge. Not done here — out of this IC's minimal-change scope.
3. **ESC** is still fully out of scope — `propulsion` block's third component key (`esc`) has no catalog concept at all (confirmed in the P2-1/Phase-2 investigations: no `ESCSpec` class exists). The probe's step 4 shows the wizard naturally advancing to "Describe el ESC" next, unaffected by this work.
4. **G26/G27** — untouched, as scoped; still independent debt.
