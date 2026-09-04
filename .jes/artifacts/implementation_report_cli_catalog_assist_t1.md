# Implementation Report — CLI catalog-assist T1 (misfit re-offer)

**IC:** `implementation_contract_cli_catalog_assist_t1.md` (★1–★5 locked)
**Status:** Implemented, full suite green, ready for Cursor review.

---

## 1. Files changed

| File | Change |
|---|---|
| `src/jarvis/core/engineering_readiness.py` | New `bound_motor_sku_is_underspec(project_state) -> bool` (§2.1) — reuses `resolve_motor_catalog_surface`, checks `gap_evidence_fact.startswith("bound_sku_underspec:")`, no reimplementation of `_motor_covers_requirements`. `_motor_catalog_gaps` now varies the `Gap.title` by `gap_evidence_fact` prefix (§2.5); `gap_type="GAP-MOTOR-CATALOG-UNRESOLVED"` unchanged. |
| `src/jarvis/core/orchestrator.py` | `_try_start_assisted_motor_help` (§2.2): the old `catalog_bound_motor_covers_power_w → return None` dead-end now branches on `bound_motor_sku_is_underspec` — `False` keeps the G21 fall-through (`return None`), `True` opens the COMPONENT motor catalog via the same `_offer_component_motor_catalog` bridge the freeform re-bind branch already used. `_handle_component_description` (§2.3): `motors_want_help` now ORs in `bound_motor_sku_is_underspec(gate_project_state)` alongside `_wants_catalog_help`; propeller/battery gates untouched. |
| `src/jarvis/core/project_continuity.py` | `build_project_continuity` (§2.4): rank 2 (sim warning/fail) stays first and its generic copy stays the default; when `_underspec_live` (from `readiness.motor_catalog_gap_fact` when `readiness` is passed, else a text match on the existing underspec sentence), the copy instead names up to 5 G22 candidates with the locked disclaimer, or the honest empty-search sentence. `next_useful_why` reuses `motor_catalog_gap` — no invented PASS/CERRADO claim. |
| `src/jarvis/core/project_closure.py` | New `catalog_bound_motor_lacks_nameplate_watts(design_properties) -> bool` (§2.6) — dual-mode (dict/object) like its neighbor, but checks the *actual* library `max_watts` for the bound SKU, not identity alone. `catalog_bound_motor_covers_power_w` itself is byte-unchanged. |
| `src/jarvis/core/reasoning_layer.py` | `_catalog_bound_motor_lacks_watts` now calls `catalog_bound_motor_lacks_nameplate_watts` instead of the identity-only predicate — the "no declara vatios" CTA/insight only fires when the bound SKU's library `max_watts` is actually `None`. |
| `tests/test_g21_g22_catalog_bind_ux.py` | New `test_g21_idle_help_choose_reopens_motor_list_when_bound_sku_underspec` (walk-fixture-shaped: `sunnysky_r2305_2500`+`gf_5045x3`+`lipo_6s_10000mah`, real orchestrator, sim fail, reproduces the stuck loop and confirms the fix). Existing `test_g21_idle_help_choose_noop_when_catalog_ref_set` unchanged and still green. |
| `tests/test_project_continuity.py` | New `test_continuity_sim_fail_underspec_names_candidates` and `test_continuity_sim_fail_without_underspec_unchanged`. |
| `tests/test_engineering_readiness_gaps.py` | Added title assertions to the three existing per-shape tests (`test_gap_motor_catalog_unresolved_trigger`, `..._bound_sku_underspec`, `..._bound_sku_missing_from_library`) — `gap_type` assertions untouched, `evidence[0].fact` assertions untouched. |
| `tests/test_energy_params.py` | New `test_reasoning_missing_energy_catalog_bound_motor_with_watts_no_cta` (r2305, has watts, must not see the CTA). Existing emax no-watts test unchanged. |
| `tests/test_cli_catalog_assist_t1.py` | **New.** 4 tests: IDLE underspec opens COMPONENT motor catalog; IDLE covering-SKU falls through (G21 intact); composite-wizard COMPONENT gate reopens on underspec; composite-wizard COMPONENT gate does not reopen when covering. |
| `scripts/cli_probe_cli_catalog_assist_t1.py` | **New**, optional. Confirms all 4 scenarios end-to-end against the real orchestrator. |
| `docs/IMPLEMENTATION_TASKS.md`, `.jes/state/engineering_state.json` | Synced (this change). |

No file outside this list was touched. `catalog_bound_motor_covers_power_w`, `derive_prop_energy_block_closure`, N1's discharge-copy gate, `_derive_overall`, `find_motors_for_requirements`, and G24-B `_score_candidate` were not modified.

## 2. Behavior changed

- **Bug fix (the stuck loop):** on a project where motor, propeller, and battery are all catalog-bound but the bound motor SKU has drifted underspec (no longer covers current thrust — the exact walk-fixture shape), IDLE `"ayúdame a elegir"` previously returned `None` from both short-circuits and dead-ended into a bare `estado`/`project_status` reprint, twice in a row for the same phrase. It now opens the existing numbered G22 motor list (or the honest empty-search sentence) via the same `_offer_component_motor_catalog` bridge already used for the freeform-motor re-bind case.
- **Continuity:** `estado` after a sim fail with underspec now names the G22 candidates (or the honest empty search) in `next_useful_step`, with an explicit "Elegir no garantiza sim PASS" disclaimer — never claims PASS or bloque CERRADO. Sim-fail without underspec is byte-unchanged.
- **GAP title:** `GAP-MOTOR-CATALOG-UNRESOLVED`'s `gap_type` ID is unchanged; its `title` now reads `"Bound motor SKU no longer covers thrust"` for `bound_sku_underspec:*` and `"Bound motor SKU missing from catalog"` for `bound_sku_missing:*`; the pre-existing `"Motor SKU unresolved"` title is unchanged for the plain empty-search/unbound case.
- **Watts CTA:** "este motor de catálogo no declara vatios" now only fires when the bound SKU's real library `max_watts` is `None` (e.g. `emax_rs2205s_2300`). A SKU that does declare watts (e.g. `sunnysky_r2305_2500`, 220W) now falls through to the normal `"Declarar motor_power_w"` CTA instead.
- **Unchanged:** `catalog_bound_motor_covers_power_w` (still identity-only, still gates architecture-progress/energy-nag suppression exactly as before), `_derive_overall`/`ASSEMBLY_READY`, `derive_prop_energy_block_closure`, N1's discharge-copy predicate, `find_motors_for_requirements`'s sort/filter logic, G24-B `_score_candidate`. No filter relaxation of any kind was introduced — every candidate shown is exactly what the existing `build_motor_catalog_suggestions`/`resolve_motor_catalog_surface` authorities already compute.

## 3. Tests

**New/updated, all passing:**

```
tests/test_g21_g22_catalog_bind_ux.py           10 passed  (+1 new, existing G21 noop guard unchanged)
tests/test_project_continuity.py                 9 passed  (+2 new)
tests/test_engineering_readiness_gaps.py         20 passed (title asserts added to 3 existing tests)
tests/test_energy_params.py                      40 passed (+1 new)
tests/test_cli_catalog_assist_t1.py               4 passed (new file)
```

**Optional probe:** `python scripts/cli_probe_cli_catalog_assist_t1.py` — confirms, against the real orchestrator: (1) underspec bound motor → numbered list on both consecutive turns (no stuck loop) and the new `estado` "Siguiente paso" line; (2) covering bound motor → noop (G21 intact); (3) r2305 (220W) → no "no declara vatios"; (4) emax (no watts) → still shows it. Output matches all pytest assertions.

**Full suite:**

```
python -m pytest -q   → 2103 passed (2095 baseline + 8 new tests), zero regressions
```

## 4. Acceptance checklist (§6 of the IC)

- ✅ Underspec + IDLE `ayúdame a elegir` → numbered G22 list (walk fixture reproduced verbatim in `test_g21_idle_help_choose_reopens_motor_list_when_bound_sku_underspec`; same phrase asserted twice, not a stuck loop).
- ✅ Bound motor that still covers → G21: no motor picker (`test_g21_idle_help_choose_noop_when_catalog_ref_set` unchanged and green; new `test_idle_covering_bound_sku_falls_through` / `test_component_gate_covering_bound_sku_does_not_reopen_motor_list` add direct coverage).
- ✅ Continuity sim-fail + underspec → step names candidates / help-choose; no PASS/CERRADO claim (`test_continuity_sim_fail_underspec_names_candidates` asserts the disclaimer text and absence of "CERRADO").
- ✅ GAP type ID unchanged; underspec title changed (`test_engineering_readiness_gaps.py`, 3 shapes).
- ✅ emax no-W CTA unchanged; r2305 does not say "no declara vatios" (`test_energy_params.py`).
- ✅ `catalog_bound_motor_covers_power_w` still identity-only — byte-unchanged, confirmed via `git diff` on `project_closure.py` (only an addition, no edit to the existing function).
- ✅ Block Closure rollup / `_derive_overall` / G22 search function unmodified — not present in the changed-files list; full suite (which includes `tests/test_block_closure_prop_energy.py`) stayed green.
- ✅ Suite green: 2103 passed.

## 5. Risks / notes for Cursor

- `bound_motor_sku_is_underspec` re-derives `physical_requirements` via `derive_physical_requirements` and re-calls `resolve_motor_catalog_surface` each time it's invoked (once in the IDLE gate, once — via `readiness` — in the COMPONENT gate through `gate_project_state`, and again inside `build_engineering_readiness` for `ctx["readiness"]`). This is the same "recompute vs pass-through" tradeoff the Block Closure IC hit with the G9-A single-catalog-resolve regression guard (`test_startup_context_invokes_catalog_resolver_once`) — confirmed the full suite (which includes that guard) is still green, so no double-resolve regression was introduced here, but a future IC touching this same neighborhood should be aware `bound_motor_sku_is_underspec` is a fresh, independent resolve, not reusing an already-computed `readiness` when called from the two orchestrator gates (no `readiness` object is available at that point in either call site — this is deliberate per the IC's own scope, not an oversight).
- `motor_catalog_gap_fact`-vs-text-match branch in `project_continuity.py`: when `readiness` is omitted (existing direct-caller/unit-test convention), underspec detection falls back to a substring match on `motor_catalog_gap`'s Spanish sentence ("ya no cubre el hueco de diseño") rather than re-deriving the fact — exactly as the IC specifies, but it does mean this string is now a second de facto contract surface (the sentence text in `resolve_motor_catalog_surface` and the substring check in `project_continuity.py` must stay in sync). Flagging for visibility, not proposing a change — the IC explicitly chose this shape to avoid a second resolve on the `estado` path.

**Cursor reviews against `implementation_contract_cli_catalog_assist_t1.md`.**
