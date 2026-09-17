# Implementation Report — Propellers↔motors catalog-pair evidence (`B1-propellers-motors-catalog-pair`)

**IC:** `implementation_contract_propellers_motors_catalog_pair_b1.md`
**Implementer:** Claude Code
**Date:** 2026-09-16
**Checkpoint:** package `0.4.1` (unchanged) · suite **3006 passed, 1 skipped** (was 2993) · UI unaffected (no UI files touched)

---

## 1. Scope delivered

Exactly the locked scope — `propellers ↔ motors` now gets a real, narrowly-named catalog-pairing screening (`catalog_pair_ok`/`catalog_pair_mismatch`/`catalog_pair_unverifiable`) instead of an unconditional `n_a_disk`, reusing the exact same authority ERF's `prop_motor` compatibility check already uses. `motors ↔ frame_arm` untouched. No axial/shaft/hub geometry invented, no `pose_envelope_screening` change, no human attest path for this evidence class (lock #8), no ERF/`ASSEMBLY_READY` change, no version bump, no `workspace/` mutation (tests-only; live-project verification below was in-memory `ProjectState.model_validate(json.load(...))` reads, never `save_state`).

## 2. Files changed

| File | Change |
|---|---|
| `src/jarvis/core/electrical_compatibility.py` | Extracted the components-only core of `_prop_motor` into a new public `prop_motor_pairing_outcome(components: dict) -> CheckOutcome`. `_prop_motor(project_state)` now just calls `prop_motor_pairing_outcome(_components(project_state))` — byte-identical behavior (verified: full ERF test suite, 37 tests, still green unmodified). This is the "shared helper" lock #3 asked for — `fit_relations_assist.py` and ERF now call the literal same function, structurally unable to drift apart. |
| `src/jarvis/core/fit_relations_assist.py` | New `_CATALOG_PAIR_STATUS_MAP` (`compatible→catalog_pair_ok`, `mismatch→catalog_pair_mismatch`, `unverifiable→catalog_pair_unverifiable`), new `_format_catalog_pair(status)` (locked copy, see §4), new `_propellers_motors_catalog_pair_row(...)`. `_mount_only_relation_row` now special-cases `child=="propellers" and origin=="motors"` (alongside the pre-existing `motors`/`frame_arm` special-case) to call the new row builder. `ready_count`'s formula is untouched — `catalog_pair_*` never counts as "ready to attest" (lock #8, no attest path). Checklist marker: `catalog_pair_ok` gets its own `≈` symbol, distinct from the reach/box family's `→` "ready" arrow. Docstrings updated throughout (module header, `_MOUNT_ONLY_RELATIONS` comment, `FitRelationRow.status` enumeration, `assess_fit_relations`, `format_fit_relations_checklist`) to describe the new evidence class and note that `n_a_disk` is now a reserved-but-unused status (no live pair hits it any more). |
| `tests/test_propellers_motors_catalog_pair_b1.py` (new) | 13 tests, T1–T7 (see §5). |
| `tests/test_disk_station_reach_b1.py`, `tests/test_geometry_fit_relations_checklist_b1.py` | Two pre-existing tests updated (status-name only): both had an unbound `propellers` fixture that used to read `n_a_disk` and now correctly reads `catalog_pair_unverifiable` (neither component has a `catalog_ref` in either fixture — this is the intended new behavior, not a weakened test). `na_count` assertions updated `1 → 0` to match. |

## 3. Module choice (lock #1 — "report choice")

Did **not** create a new module for this Buy. The actual evidence-class *authority* (`match_motor_propeller` catalog membership check) already lived in `library.py`/`electrical_compatibility.py`; the only new code needed on top of it is a status-name mapping and a copy formatter — a few lines, not a "screening" with its own geometry math like `station_reach_screening.py` had. Put `prop_motor_pairing_outcome` in `electrical_compatibility.py` (next to its sibling `_prop_motor`, sharing the same `CheckOutcome` vocabulary) and the row-building/copy logic directly in `fit_relations_assist.py` (next to `_motors_frame_arm_reach_row`, same pattern). This keeps the shared authority in one place and avoids a near-empty module.

## 4. The locked copy (lock #6)

```
catalog_pair_ok:           "Motor y hélice tienen emparejamiento de catálogo compatible
                            (ids o pulgadas compatibles) — no confirma dimensiones
                            mecánicas ni el rendimiento real de ese combo."

catalog_pair_mismatch:     "Motor y hélice están en catálogo pero el emparejamiento no es
                            compatible (ni ids ni pulgadas coinciden) — no confirma
                            dimensiones mecánicas."

catalog_pair_unverifiable: "Jarvis no verifica emparejamiento de catálogo; falta SKU/
                            familia de motor y/o hélice, o no están en catálogo."
```

**Caught by this Buy's own T6 test, fixed before shipping**: a first draft of the `catalog_pair_ok`/`catalog_pair_mismatch` copy said *"no verifica eje, hub, ni el empuje exacto del combo"* — technically an honest disclaimer, but it used the literal forbidden words `"eje"`/`"hub"` even inside a negation clause, violating lock #6's word-level ban. Rephrased to *"no confirma dimensiones mecánicas ni el rendimiento real de ese combo"* — same honest meaning, zero forbidden tokens (verified by the test asserting `("cabe", "alcance", "hub", "eje", "clearance", "combo exacto de empuje", "VERIFIED")` are all absent from the propellers row's own text).

## 5. Empirical verification (before writing tests)

Live projects, read in-memory only (`ProjectState.model_validate(json.load(...))`, never saved):

```
10-min-autonomía:              motor=iflight_xing_e_pro_2207_2450, prop=gemfan_hurricane_mck_51466_3_v2
dron-de-vigilancia-doméstico:  same pair
autonomía-de-5min:             motor=emax_rs2205s_2300, prop=gemfan_hurricane_mck_51466_3_v2

→ all three: propellers row = catalog_pair_ok, exact copy above.
```

Synthetic cases:
```
unbound motor+prop (no catalog_ref)              → catalog_pair_unverifiable
bound motor + wrong-family propeller ref         → catalog_pair_unverifiable
bound motor (5" band) + apc_10x6_ep (10" prop)   → catalog_pair_mismatch
bound motor (5" band) + gemfan_..._51466 (5.1")  → catalog_pair_ok
motors↔frame_arm row (unaffected)                → station_reach_ok, in every case above
screen_posed_envelope(propellers, ...)           → no_pose (disk geometry, unchanged)
```

Full suite run after wiring the row (before adding the new test file): **2 pre-existing failures**, both from unbound-propeller fixtures that used to assert `n_a_disk` — confirms the change is real and correctly propagates; both updated (§2).

## 6. Tests

### Added (`tests/test_propellers_motors_catalog_pair_b1.py`, 13 tests)

| ID | Tests | Covers |
|---|---|---|
| T1 | `test_t1_both_bound_compatible_is_catalog_pair_ok` | Compatible pair → `catalog_pair_ok` |
| T2 | `test_t2_both_bound_incompatible_is_catalog_pair_mismatch` | Incompatible pair (10" prop on 5"-band motor) → `catalog_pair_mismatch` |
| T3 | `test_t3_unbound_motor_is_catalog_pair_unverifiable`, `test_t3_unbound_propeller_is_catalog_pair_unverifiable`, `test_t3_wrong_family_is_catalog_pair_unverifiable`, `test_t3_neither_present_is_catalog_pair_unverifiable_never_silent_n_a_disk` | Every unverifiable path — never silently `n_a_disk` |
| T4 | `test_t4_motors_frame_arm_still_uses_station_reach_unaffected` | `motors`↔`frame_arm` regression guard |
| T5 | `test_t5_screen_posed_envelope_unchanged_for_propellers` | `screen_posed_envelope` unchanged (still `no_pose`/disk geometry) |
| T6 | `test_t6_copy_asserts_catalog_pair_honesty_and_forbidden_tokens` | Copy honesty across all three statuses — caught and fixed the `hub`/`eje` leak (§4) |
| T7 | `test_t7_row_outcome_matches_erf_prop_motor_check_ok/mismatch/unverifiable`, `test_t7_no_human_attest_path_for_catalog_pair` | Row outcome pinned against `evaluate_electrical_compatibility(...).prop_motor` for all three outcomes; confirms no attest path exists (`status != "attested"`, `suggest is None`) |

### Updated (pre-existing, status-name only)

- `tests/test_disk_station_reach_b1.py::test_t5_motors_frame_arm_uses_reach_status_propellers_still_n_a_disk` → renamed `test_t5_motors_frame_arm_uses_reach_status_propellers_uses_catalog_pair`; `propellers` assertion `n_a_disk → catalog_pair_unverifiable`; `na_count` `1 → 0`.
- `tests/test_geometry_fit_relations_checklist_b1.py::test_r5_propellers_stays_n_a_disk_motors_now_station_reach` → renamed `test_r5_propellers_uses_catalog_pair_motors_uses_station_reach`; same status/`na_count` update.

### Executed

```
python -m pytest tests/test_propellers_motors_catalog_pair_b1.py -q                                → 13 passed
python -m pytest tests/test_disk_station_reach_b1.py tests/test_geometry_fit_relations_checklist_b1.py -q → 38 passed
python -m pytest -q                                                                                 → 3006 passed, 1 skipped
```

No UI files touched — `ui/spatial-board` vitest suite not re-run (unaffected by this Buy).

## 7. Design notes / judgment calls

- **Mount independence (lock #4)**: `_propellers_motors_catalog_pair_row` never reads `propellers.mounted_on` — the catalog-pair status depends only on both components' `catalog_ref`s. `mount_warning` remains its own, separately-computed annotation via the pre-existing `_mount_warning(...)` call in `_mount_only_relation_row`, unchanged for this pair. Verified: a propeller with no `mounted_on` declared still gets a full `catalog_pair_ok`/`mismatch`/`unverifiable` status alongside its independent mount warning.
- **`n_a_disk` retained as a reserved status** (lock #5's "optional" carve-out): the generic fallback branch in `_mount_only_relation_row` is now unreachable for both current pairs in `_MOUNT_ONLY_RELATIONS`, but was left in place rather than deleted — it's the correct honest behavior for any future third mount-only pair added without an evidence class, and removing it would be an unrelated, unjustified structural change per this Buy's own narrow scope.
- **Checklist marker for `catalog_pair_ok`**: chosen as `≈` (distinct from `→` "ready to attest") specifically because lock #8 forbids inventing an attest path — reusing `→` would visually imply "you can now `declaro verificado` this," which is false for this evidence class.

## 8. Out of scope (unchanged, named debt per IC §4)

Axial/shaft/hub clearance geometry (needs an Engineer bag — parked) · HD-005 exact OP XING-E+51466+4S (lab/estimate ★) · `SuggestionEngine`'s `increase_payload` on `simular` (queue #4) · hygiene bind-esc/FC-GPS (#4) · more identity rules (#5) · plate-box/Path N (parked).

## 9. Remaining risks

None identified. The `electrical_compatibility.py` refactor (`_prop_motor` → thin wrapper over the new public function) preserves its exact prior public behavior, confirmed by the full ERF/electrical-compatibility test suite (37 tests) passing unmodified both before and after this Buy's own new tests were added.
