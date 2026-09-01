# Implementation Report — Motor OP Voltage Coherence

**Contract:** [`implementation_contract_motor_op_voltage_coherence.md`](implementation_contract_motor_op_voltage_coherence.md)
**Implementer:** Claude Code
**Base:** `v0.3.3` / `checkpoint-validation-case-regression-gate` (`ceb44b4`)
**Status:** Complete, all slices (MOP-1 … MOP-7) implemented. Full suite **2036 passed, 0 failed, 0 skipped**. New probe **6/6 PASS**. All named regression probes green except one **pre-existing, unrelated** failure (§6).

---

## 1. Slices delivered

| Slice | File(s) | Change |
|---|---|---|
| MOP-1 | `src/jarvis/knowledge/library.py` | `resolve_operating_point`'s `voltage_matches` now requires `voltage_v is not None` — an unknown query voltage can no longer auto-match an exact row. Docstring updated. |
| MOP-2 | `src/jarvis/core/component_writers.py` | `propulsion_resolution` JSON gains `voltage_validated`/`resolved_at_voltage_v`. New shared `_resolve_battery_voltage_v()` helper (used by both `set_motor_component` and the new gate — replaces the duplicated inline derivation). `set_battery_component`'s tail conditionally re-calls `set_motor_component` when the stored resolution was never voltage-validated, or was validated at a voltage now incompatible with the new pack. |
| MOP-3 | `src/jarvis/core/design_explorer.py` | `explore()`'s `base_params` (baseline + params-only grid) now reads live `project_state.current_parameters` directly, not a re-normalized copy. `normalized_state` is still computed and still used, unchanged, as the substrate for catalog/component-delta candidates. |
| MOP-4 | `src/jarvis/core/orchestrator.py` | `_handle_explore`'s message appends one honest line when the live `propulsion_resolution.voltage_validated == false`. |
| MOP-5 | `tests/test_dse_motor_op_dual_truth.py`, `tests/test_phase2_lookup_operating_point.py`, `tests/test_propeller_catalog_bind_ux.py`, `tests/test_requirements_closure.py` | CASE A/B flipped to PASS; sanity precondition test repurposed (its old premise can no longer occur); 2 new ★4 sibling tests; MOP-1 resolver test + bridge test; 3 pre-existing tests/probe adjusted where they were accidentally relying on `voltage_v=None` auto-matching (see §4). |
| MOP-6 | `scripts/cli_probe_dse_motor_op_dual_truth.py` (new) | Deterministic 6-step probe mirroring the field walk end-to-end. |
| MOP-7 | this report | — |

**`src/` touch set — exactly as the contract's §4 table predicted:**

```text
src/jarvis/knowledge/library.py      |  30 +++++++---
src/jarvis/core/component_writers.py | 109 ++++++++++++++++++++++++++++-------
src/jarvis/core/design_explorer.py   |  19 ++++--
src/jarvis/core/orchestrator.py      |  15 +++++
```

No file outside this set was touched under `src/`. `design_explorer._score_candidate`, G24 viable selection, `_finalize_viable_list`, H5/ESC catalog, FN-R routing, and `invalidate_diverged_catalog_refs` are all byte-identical.

---

## 2. §2 locked semantics — verification notes

### 2.1 Resolver voltage gate (§2.1, MOP-1)

Live-verified against the contract's own table:

```text
voltage_v=None,  hq_5045_bn bound        -> fallback_operating_point (was exact — the bug)
voltage_v=16.0,  hq_5045_bn bound        -> exact_operating_point @ 432W (existing validated combo, unchanged)
voltage_v=22.2,  hq_5045_bn bound        -> fallback_operating_point @ 10.042N, power_w=None (unchanged)
```

Only the exact-match branch's voltage gate changed. Fallback-branch voltage handling, `_OP_VOLTAGE_EPSILON_V`, max-thrust selection among multiple exact rows, and propeller SKU matching are all untouched — confirmed by the unchanged behavior of every pre-existing test that supplies an explicit `voltage_v`.

### 2.2 Voltage provenance (§2.2)

`propulsion_resolution` now always carries `voltage_validated` (bool) and `resolved_at_voltage_v` (float|null) for every catalog-bound motor resolution (exact/fallback/legacy alike — the JSON block is written whenever `resolved_op is not None`, unconditionally of resolution type). Both fields are plain JSON scalars inside the existing JSON-string value — no nested-dict hashability regression (unchanged discipline from the original P2-2 note in the same file).

### 2.3 Conditional battery-bind re-resolution (§2.3)

**Locus chosen: hook inside `set_battery_component`'s tail** (the contract's first-listed option), not duplicated per call site. Rationale:

- `set_battery_component` is the single canonical writer for the battery component (file's own "MIRRORED PARAM CONTRACT" doctrine) — hooking here covers every production call site uniformly: the battery catalog pick (`_apply_component_battery_catalog_pick`), freeform battery description (`param_definition_session.py`, `orchestrator.py:2203`), and DSE apply/iterate (`actions/iterate.py`) — without duplicating the gate logic four times.
- **Disclosed redundancy, not a bug:** when reached via `apply_components_delta`'s own `_APPLY_ORDER` loop (used for explore's baseline/candidate normalization), the loop *already* unconditionally re-derives the motors component right after "battery" on every call, regardless of this hook. The hook's own re-resolve in that path is therefore superseded immediately by the loop's own subsequent `set_motor_component` call — harmless (same end state, one extra cheap resolver lookup), never incorrect. Verified: no test or probe exercising `apply_components_delta` regressed or slowed measurably (full suite: 2036 tests in 2.5s).

**Gate logic** (`needs_revalidation`, default `True`, flipped to `False` only when *proven* safe):

```text
stored resolution present AND voltage_validated == true AND
  |resolved_at_voltage_v - new_pack_voltage| <= _OP_VOLTAGE_EPSILON_V
    -> no-op (P2-2/IC2 lock preserved)
otherwise (never validated, or validated-but-now-incompatible, or no stored resolution at all)
    -> re-call set_motor_component with the existing motors spec
```

Live-verified both branches (§5, ★4 sibling tests) using **real catalog data only** — no synthetic voltage tuning:

- Never-validated → real 6S/22.2V bind: re-triggers, `voltage_validated` flips False→True, `resolved_at_voltage_v` flips None→22.2.
- Already-validated + compatible (OP-3, `sunnysky_r2205_2500`+`gf_5045x3`@14.8V, two different real 4S/14.8V catalog SKUs bound in sequence): `propulsion_resolution` stays **byte-identical** across the second bind — the P2-2/IC2 regression contract is not reopened.

### 2.4 DSE explore/apply coherence (§2.4, MOP-3)

`base_params` in `explore()` now equals `dict(project_state.current_parameters or {})` for both the baseline calc and the params-only grid. `normalized_state` (still `apply_components_delta(project_state, {})`) is retained, unchanged, solely as the substrate for catalog-motor and component-delta candidates (§2.4 rule 2 — unchanged as instructed). `_handle_apply_exploration`'s params-only branch was **already** merging onto live `current_parameters` directly (confirmed unchanged, no edit needed there) — the investigation's own finding that apply's mechanism was never the buggy half is what MOP-3 is scoped around.

### 2.5 MOP-4 (optional, included)

One-line honest note appended to `_handle_explore`'s message when `voltage_validated == false` in live state: *"Línea base usa estimación — voltaje de batería pendiente de validación."* Read-only, parses the existing `propulsion_resolution` JSON — no new subsystem, no new context key.

### 2.6 P2-2 preserved semantics

`motor_power_w` (catalog rating) is never overwritten by any code path touched in this IC — confirmed by every OP-electrical test/probe still asserting `motor_power_w=400.0`/`592.0` unchanged alongside the resolved (or absent) `motor_op_power_w`.

---

## 3. Live verification — field-walk numbers, before/after

```text
BEFORE (v0.3.3, the bug):
  motor+prop bound, no battery  -> LOCKS exact_operating_point @ 432W (voltage_v=None bug)
  battery bound (6S/22.2V)      -> stale 432W survives (P2-2/IC2 never re-calls motor writer)
  live calc autonomy            = 7.7083 min
  explore baseline autonomy     = 8.325 min   (DISAGREES with live calc)
  explore's top candidate promise = 12.8077 min
  post-apply actual autonomy    = 7.7083 min  (DOES NOT deliver the promise)

AFTER (this IC):
  motor+prop bound, no battery  -> honest fallback_operating_point, no motor_op_* (MOP-1)
  battery bound (6S/22.2V)      -> MOP-2 revalidates honestly at 22.2V, still fallback
  live calc autonomy            = 8.325 min
  explore baseline autonomy     = 8.325 min   (AGREES — MOP-3)
  explore's top candidate promise = 12.8077 min
  post-apply actual autonomy    = 12.8077 min (DELIVERS the promise)
```

Reproduced via `scripts/cli_probe_dse_motor_op_dual_truth.py` (6/6 PASS) and `tests/test_dse_motor_op_dual_truth.py::test_case_a_explore_baseline_agrees_with_live_calc` / `::test_case_b_apply_delivers_explore_promise`.

---

## 4. Existing tests/probes adjusted (MOP-1 fallout — explicitly authorized)

Three pre-existing assertions relied on the old `voltage_v=None` auto-match bug (motor/propeller bound with no battery, asserting `exact_operating_point`). Per the contract's own MOP-1 clause ("adjust only if assertion was accidentally relying on None-matches-all"), each was updated to assert the new, honest `fallback_operating_point` result — the *behavior each test actually exists to verify* (re-resolution firing, resolution pathway reachable) is unaffected; only the resulting `resolution_type`/thrust values changed, which is exactly this IC's intended fix:

| File | Test/step | Change |
|---|---|---|
| `tests/test_propeller_catalog_bind_ux.py` | `test_propeller_pick_sets_catalog_ref_and_reresolves_exact_op` → renamed `..._reresolves_op` | Asserts `fallback_operating_point`/10.042N/`voltage_validated=False` instead of `exact_operating_point`/9.7086N. |
| `tests/test_requirements_closure.py` | `test_p2_propulsion_resolution_unchanged` | Docstring + assertion updated to `fallback_operating_point`; smoke test's actual purpose (requirements IC doesn't touch the OP resolver) is unaffected. |
| `scripts/cli_probe_propeller_catalog_bind_ux.py` | Step 5 | Docstring + assertion updated to `fallback_operating_point`/10.042N. |

No assertion that supplies an explicit, known `voltage_v` was touched — every one of those (the large majority of `test_phase2_lookup_operating_point.py`, both P2-2/Validation-Case probes) passed unmodified.

---

## 5. Tests added

`tests/test_dse_motor_op_dual_truth.py` — fully rewritten per MOP-5:

- `test_motor_bound_before_battery_resolves_honestly_not_stale_exact` (sanity precondition, repurposed — the old premise, a surviving stale lock-in, can no longer occur, so this now documents the fixed state instead)
- `test_case_a_explore_baseline_agrees_with_live_calc` (was CASE A failing → now **PASSES**)
- `test_case_b_apply_delivers_explore_promise` (was CASE B failing → now **PASSES**)
- `test_motor_op_revalidated_on_battery_bind_when_voltage_was_unknown` (★4 sibling #1)
- `test_motor_op_unchanged_on_compatible_battery_bind_when_voltage_validated` (★4 sibling #2 — P2-2/IC2 lock, verified with real ★6 data, no synthetic tuning)

CASE C (battery-viable→fail cliff) was **not** re-added — ★3 ratified it is not a gate, and it never reproduced pre-fix either; nothing regresses by its absence.

`tests/test_phase2_lookup_operating_point.py` — 2 new tests:

- `test_unknown_voltage_never_matches_exact_row` (MOP-1 resolver contract)
- `test_bridge_motor_bind_before_battery_does_not_set_motor_op_power_w_from_exact_row` (bridge-level: motor+propeller bound with no battery at all never carries `motor_op_*`)

**Zero weakened tests.** Every changed assertion (§4) moved from asserting buggy behavior to asserting correct behavior — none had its check loosened or removed. `test_battery_pick_does_not_regress_already_resolved_propulsion_op` (`tests/test_battery_catalog_bind_ux.py`) was **not edited at all** and still passes.

---

## 6. Tests/probes executed

```text
pytest tests/ (full suite)                                    -> 2036 passed, 0 failed, 0 skipped
pytest tests/test_dse_motor_op_dual_truth.py -v                -> 5 passed
pytest tests/test_phase2_lookup_operating_point.py -v          -> 27 passed
pytest tests/test_battery_catalog_bind_ux.py -v                -> 13 passed (incl. test_battery_pick_does_not_regress..., unedited)
pytest tests/test_propeller_catalog_bind_ux.py -v               -> 8 passed
pytest tests/test_g5_dse_iterate_dual_truth.py -v               -> 5 passed (regression anchor)

python scripts/cli_probe_dse_motor_op_dual_truth.py             -> 6/6 PASS (new)
python scripts/cli_probe_p2_2_operating_point_bridge.py         -> 6/6 PASS
python scripts/cli_probe_validation_case_op_dataset.py          -> 6/6 PASS
python scripts/cli_probe_propeller_catalog_bind_ux.py           -> 6/6 PASS (adjusted, §4)
python scripts/cli_probe_phase2_lookup_op.py                    -> 5/5 PASS
python scripts/cli_probe_battery_catalog_bind_ux.py             -> 6/6 PASS
python scripts/cli_probe_g24_apply_by_index.py                  -> 6/6 PASS
python scripts/cli_probe_g24_viable_selection_honest_cta.py     -> 6/6 PASS
python scripts/cli_probe_frankenstein_name_clear.py             -> 5/5 PASS
python scripts/cli_probe_closure_policy_propeller_sku.py        -> 4/4 PASS (+ optional step 5)
python scripts/cli_probe_requirements_closure.py                -> 5/5 PASS

git diff --stat -- src/                                          -> exactly the 4 predicted files (§1)
```

**One pre-existing, unrelated failure disclosed:** `scripts/cli_probe_impl_d_sku_bom.py` fails on an `assert frankenstein.catalog_ref is None` (step 3, G5 frankenstein-name scenario) with **zero relation to voltage/OP resolution** — confirmed by running the identical probe on a clean `git stash` of this IC's changes (baseline `main`, before any edit in this session): it fails identically, same assertion, same line. Not caused, touched, or masked by this IC; not in scope to fix here (out of scope per contract §5 — no H5/G24-B/FN-R work). Flagged for Engineer as a separate, pre-existing issue.

---

## 7. Scope decisions disclosed

1. **MOP-4 (optional) implemented, not skipped** — the honest-line addition was small, low-risk, and directly requested by the ratified ★2; included rather than timeboxed out.
2. **Battery-bind hook locus: `set_battery_component`'s tail**, not `_apply_component_battery_catalog_pick`. Chosen over the alternative because it covers all four production call sites (catalog pick, freeform description ×2, DSE iterate) through the single canonical writer, matching this codebase's own "single point of write" doctrine, at the cost of one disclosed-harmless redundant resolver call inside `apply_components_delta`'s own loop (§2.3).
3. **`_resolve_battery_voltage_v` extracted as a shared helper** in `component_writers.py` — used by both `set_motor_component` (pre-existing derivation, now delegated) and the new revalidation gate. This is a "shared helper" tier refactor (CLAUDE.md's preferred order #2), justified by the concrete second call site this IC introduces — no behavior change to the original derivation logic, confirmed by every OP-electrical test passing unmodified.
4. **Three pre-existing tests/probe adjusted** (§4) — explicitly authorized by the contract's own MOP-1 wording; each change moves an assertion from bug-dependent to bug-fixed behavior, disclosed individually above.
5. **CASE C not re-added** — ★3 ratified it is optional/non-gating; it never reproduced even pre-fix, so its absence changes nothing about coverage of the actual, now-fixed defect.

---

## 8. Gate check (contract §6)

| Criterion | Result |
|---|---|
| Full suite green, zero intentional failing repro tests | **PASS** — 2036/2036, 0 failed, 0 skipped |
| CASE A + B in `test_dse_motor_op_dual_truth.py` pass | **PASS** |
| ★4 sibling tests pass; `test_battery_pick_does_not_regress...` passes unchanged | **PASS** — unedited, still green |
| P2-2 probe 6/6; Validation Case probe 6/6 | **PASS** |
| New probe 6/6 | **PASS** |
| Field-walk numbers: explore baseline = live calc; apply delivers explore promise | **PASS** — 8.325=8.325, 12.8077=12.8077 |
| `motor_power_w` never overwritten by OP; P2-2 Option A intact | **PASS** |
| Report documents battery-bind hook choice and probe ordering caveat | **PASS** — §2.3, §6 |

**Ready for Cursor review.**

---

## 9. Queue after IC

```text
IC PASS + probe 6/6 + suite green
  ↓
Engineer: checkpoint (e.g. checkpoint-motor-op-voltage-coherence)
  ↓
Version v0.3.4 (recommended)
  ↓
Separately flagged: scripts/cli_probe_impl_d_sku_bom.py pre-existing failure (§6) — unrelated to this IC, needs its own triage
  ↓
Deferred unchanged: H5 · G24-B · battery/ESC curation · FN-R routing arc
```

No tag created, no push, no version bump — left for Engineer.
