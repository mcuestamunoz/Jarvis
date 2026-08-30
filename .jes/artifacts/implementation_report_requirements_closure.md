# Implementation Report — Requirements Closure (IC 1 / Project Closure arc)

**Contract:** [`implementation_contract_requirements_closure.md`](implementation_contract_requirements_closure.md)
**Implementer:** Claude Code
**Base:** `v0.3.0` / `checkpoint-propeller-catalog-bind` (`2efe1c2`)
**Status:** Complete, all 6 slices (Req-1 … Req-6) implemented, full suite green (**1960 passed**, +13 new), CLI probe **5/5 PASS**.

---

## 1. Files changed

| File | Slice | Change |
|---|---|---|
| `src/jarvis/schemas/state_schema.py` | Req-1 | New `restrictions_explicitly_none()` + closed token list `_EXPLICIT_NONE_RESTRICTIONS`. `_parse_constraints` **left untouched** — see §3 deviation. |
| `src/jarvis/core/engineering_readiness.py` | Req-2 | New `_requirements_declared()`; `_requirements_evidence.defined` now calls it instead of the bare `bool(parsed_constraints)`. |
| `src/jarvis/core/param_definition_session.py` | Req-3, Req-4 | New `extract_restrictions_update()` + `ParamDefinitionSession.try_update_restrictions()` (G26 write path). New `is_derived` gate at the top of `apply_and_recalculate()` (defense-in-depth). |
| `src/jarvis/core/orchestrator.py` | Req-3 | One intercept calling `try_update_restrictions()`, placed immediately before the existing `try_ingest()` call. |
| `tests/test_requirements_closure.py` | Req-5 | New, 13 tests. |
| `scripts/cli_probe_requirements_closure.py` | Req-6 | New, self-contained probe, 5/5 PASS. |

**Not touched** (confirmed via `git diff`, matches §5's "must not change" list exactly): `library.py`, `resolve_operating_point`, `component_writers`'s propulsion OP bridge, `catalog_bind.py`, `project_closure._bom_sku_resolved`, battery/propeller catalog assist, G27 parser, G24 DSE, `docs/ENGINEERING_READINESS_VISION.md`, `pyproject.toml` version.

---

## 2. Behavior changed

- **New:** a project whose `restrictions` is an explicit, closed-list "no constraint" statement (`"no"`, `"ninguna"`, `"ninguno"`, `"ningun"`, `"none"`, `"n/a"`, `"na"`, `"sin restricciones"`, `"sin restriccion"`, `"no restrictions"`, `"without restrictions"` — case/whitespace-insensitive) now satisfies `requirements.defined`. No numeric key is ever fabricated in `parsed_constraints` for this case (verified: `parsed_constraints == {}` in every explicit-none test).
- **New:** a mid-session utterance containing `restricci*`/`restriction*` now writes `current_parameters["restrictions"]` directly and re-derives `parsed_constraints` (via `ProjectState.model_copy`'s existing FN-010 override) — this previously had no writer at all.
- **New:** any attempt to write a `PARAMETER_REQUIREMENTS[...].is_derived == True` key (e.g. `"autonomia"`, `"empuje"`) through `param_definition_session.apply_and_recalculate` is now rejected with the registry's own `derived_message`, instead of being silently persisted as a loose `current_parameters` key.
- **Unchanged:** all physics, calculation, simulation, catalog, BOM, and P2-1/propulsion-OP-resolution behavior — confirmed by the full test suite (1947 pre-existing tests pass byte-identical) and the dedicated smoke test (`test_p2_propulsion_resolution_unchanged`).
- **Live headline result:** re-running `build_engineering_readiness` against the two investigation fixtures (`workspace/1-324107ef7006`, `workspace/crear-un-dron-de-autonomia-con-payload-1kg-184eac8b7789`) after this change:
  - `1-324107ef7006`: `overall` flips **`NOT_ASSEMBLY_READY` → `ASSEMBLY_READY`** (8/9 → 9/9 PASS, 0 gaps).
  - `crear-un-dron-de-autonomia-con-payload-1kg-184eac8b7789`: `requirements` flips **`INCOMPLETE` → `PASS`**; `overall` stays `NOT_ASSEMBLY_READY` (6 pre-existing BOM/architecture gaps, all out of this IC's scope — expected, matches §10's S0→S1/S1→S2 independence).

---

## 3. Deliberate deviation from the contract — disclosed, not silent

**§2.2's "recommended" objective-fallback interaction was NOT implemented.**

The contract's §2.2 prose recommends: *"explicit-none on restrictions means no autonomy requirement from objective either, since the user declared no restrictions at project level."* This is **not** one of the ★-locked decisions (★1–★9) — it's implementer guidance embedded in §2.2's prose.

Before implementing it, I checked existing test coverage and found it **directly conflicts** with two existing, already-passing tests in `tests/test_u5_constraint_validation.py`, both of which are explicitly named as encoding the FN-010 acceptance criterion:

- `test_parse_constraints_falls_back_to_objective_when_restrictions_absent` — asserts that `restrictions="ninguno"` + an objective containing `"autonomía de 40min"` **does** populate `parsed_constraints.autonomy_min == 40.0`.
- `test_project_creation_derives_autonomy_from_objective_fallback` — docstring literally says *"FN-010 criterio de aceptación"* — full orchestrator integration test asserting the same, through `create_project` + disk reload.

Implementing §2.2's suggested suppression would have required weakening or deleting these two tests to make the suite pass — forbidden by CLAUDE.md ("Weakening or deleting tests only to make the suite pass") and by the contract's own §7 acceptance criterion ("No weakened tests without disclosure").

**Decision:** left `_parse_constraints` (`state_schema.py:20-54`) completely unmodified. `restrictions_explicitly_none()` is a pure additive helper, not wired into constraint parsing at all — it is consumed only by `_requirements_declared()`.

**Impact of not implementing it:** none on this IC's own gate. Every scenario the contract's §1.2/§1.9 examples and the two investigation fixtures exercise has an `objective` with no numeric autonomy/weight pattern, so the untouched FN-010 fallback never fires in those cases — `_requirements_declared()`'s explicit-none branch is what does the work. The only behavioral difference from the contract's stated preference is the edge case where `restrictions` is explicit-none **and** `objective` independently names an achievable numeric target — in that edge case, the existing (tested, locked) FN-010 behavior now provides an actual, honest numeric constraint via the objective fallback, which is arguably *more* informative than suppressing it, not less.

---

## 4. Tests added (13, `tests/test_requirements_closure.py`)

| Test | Covers |
|---|---|
| `test_restrictions_explicitly_none_recognizes_closed_list` | Req-1 closed list, case/whitespace-insensitive |
| `test_restrictions_explicitly_none_false_for_absent_or_ambiguous` | Req-1 negative cases (§2.2 "must return False for") |
| `test_requirements_pass_when_restrictions_explicitly_no` | Req-5 #1 |
| `test_requirements_incomplete_when_restrictions_absent` | Req-5 #2 |
| `test_requirements_incomplete_when_restrictions_unparseable` | Req-5 #3 (§2.3) |
| `test_fixture2_shape_assembly_ready_after_req1_req2` | Req-5 #4 — headline gate |
| `test_gap_requirements_unmet_autonomy_when_target_exceeds_sim` | Req-5 #7 — honest gap, negative arm |
| `test_requirements_pass_with_achievable_stated_constraint` | positive arm of the above (not explicitly listed but needed to prove the gap logic isn't one-sided) |
| `test_g26_restrictions_update_sets_parsed_constraints` | Req-5 #5 |
| `test_g26_explicit_none_restatement_flips_requirements` | mid-session explicit-none restatement (write path + ★3(b) combined) |
| `test_g26_derived_autonomia_rejected` | Req-5 #6 |
| `test_extract_restrictions_update_ignores_unrelated_turns` | routing guard — confirms the keyword-gated intercept doesn't fire on unrelated numeric turns |
| `test_p2_propulsion_resolution_unchanged` | Req-5 #8 |

**Zero weakened tests.** No existing test file was modified.

---

## 5. Tests executed

```text
pytest tests/test_requirements_closure.py -v   → 13 passed
pytest tests/ (full suite)                     → 1960 passed (1947 pre-existing + 13 new)
python scripts/cli_probe_requirements_closure.py → 5/5 PASS
```

Targeted regression sweep before the full run (all green): `test_u5_constraint_validation.py`, `test_engineering_readiness_aggregator.py`, `test_engineering_readiness_cli.py`, `test_engineering_readiness_gaps.py`, `test_engineering_readiness_subsystems.py`, `test_engineering_readiness_continuity.py`, `test_engineering_readiness_erf2_gaps.py`, `test_engineering_readiness_erf2_subsystems.py`, `test_d4_param_gatekeeper.py`.

---

## 6. Scope decisions disclosed

1. **§3 deviation** — §2.2's objective-fallback suppression not implemented; see §3 above.
2. **Bare-phrase explicit-none mid-session, without a "restricci*" keyword** (e.g. a lone `"ninguna"` typed in response to an unrelated prompt) is **not** intercepted by `try_update_restrictions` — the routing guard requires the literal keyword to appear in the utterance, exactly as scoped in the contract's own §3.1 note ("Out of scope for G26 fix... a bare 'ninguna'/'no' with no restrictions keyword"). ★3(b)'s explicit-none semantics still apply to whatever value is already on record (typically set at project creation).
3. **No `HistoryEntry`/`record_action` call** in `try_update_restrictions` — mirrors the existing, precedented `orchestrator._apply_catalog_motor_pick` pattern (direct `save_state`, no recalculation). Deliberate: `record_action` **replaces** `latest_results` wholesale, which would have wiped the project's existing `simulation`/`calculations` and regressed every other subsystem's evidence — a constraint restatement alone must never do that.

---

## 7. Remaining risks

- `extract_restrictions_update`'s payload regex (`_RESTRICTIONS_PAYLOAD_RE`) is a general-purpose connector-stripper (`es|son|a|:`); an unusual phrasing outside the contract's three example shapes could extract an odd payload string. Low risk in practice — `_parse_constraints` only reacts to two specific regexes (autonomy/weight), so a malformed payload simply fails to parse into `parsed_constraints` and correctly falls into the §2.3 INCOMPLETE (not silently wrong) path.
- CLI probe and new tests build a synthetic "Fixture-2-shaped" `ProjectState` rather than depending on the untracked `workspace/` directory (deliberate — see §6 rationale in the original investigation about not depending on scratch state). The synthetic fixture was validated to reproduce the exact same subsystem verdicts as the real fixture before being used.

---

## 8. Gate check (contract §7)

| Criterion | Result |
|---|---|
| Fixture-2-shaped project reaches `ASSEMBLY READY` with `restrictions="no"`, zero new gaps | **PASS** — live-verified against the real fixture and the synthetic test fixture |
| Explicit-none doesn't add fake `parsed_constraints` entries | **PASS** — `parsed_constraints == {}` asserted |
| G26 write path persists `restrictions` + re-derives `parsed_constraints`; derived write rejected | **PASS** |
| Unachievable numeric constraint surfaces `GAP-REQUIREMENTS-UNMET` honestly | **PASS** |
| Full suite green; probe 5/5 | **PASS** — 1960/1960, 5/5 |
| P2-1/propulsion paths untouched | **PASS** — confirmed by `git diff` (zero touch) + smoke test |
| No weakened tests without disclosure | **PASS** — zero existing tests modified; one scope deviation disclosed (§3) |

**Ready for Cursor review.**
