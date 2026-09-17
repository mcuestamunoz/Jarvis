# Implementation Report — Disk-station radial reach (`B1-disk-station-reach`)

**IC:** `implementation_contract_disk_station_reach_b1.md`
**Implementer:** Claude Code
**Date:** 2026-09-15
**Checkpoint:** package `0.4.1` (unchanged) · suite **2968 passed, 1 skipped** (was 2945) · UI unaffected (no UI files touched)

---

## 1. Scope delivered

Exactly the locked scope — a new, narrowly-named `station_reach_*` screening for `motors ↔ frame_arm` only, reusing the Visor's own already-shipped radial math, with an optional human seal gated on `station_reach_ok` and its own fingerprint. `propellers ↔ motors` untouched (still `n_a_disk`). `pose_envelope_screening.screen_posed_envelope` untouched. No proxy box, no Path N, no invented mm, no version bump, no `workspace/` mutation (tests-only, default per lock #11 — no ★ Path D requested; live projects were read and exercised in-memory for verification, never saved).

## 2. Files changed

| File | Change |
|---|---|
| `src/jarvis/core/station_reach_screening.py` (new) | `StationReachScreening`, `screen_station_reach(child, origin_key, components)`, `format_station_reach()`. Imports `_quad_x_wheelbase_mm`/`_quad_x_station_points` from `workspace.spatial_board` — the exact same functions the Visor uses to place the arm box, never a second copy. |
| `src/jarvis/core/component_writers.py` | Added `compute_station_reach_fingerprint(frame, origin, child)`. Branched `set_component_declared_fit_attestation`: `component_key == "motors"` routes to the new station-reach gate/fingerprint instead of box overlap (the box branch is now structurally unreachable for `motors`, since motors is never a box). Added `_clear_motors_station_reach_attestation` helper, called from `upsert_frame_part` (when `part_key == "frame_arm"`) and `merge_frame_root_declared_properties` (any write to `frame.configuration`/`wheelbase_mm`). Added an unconditional `_cleared_fit_attestation(updated_spec)` call to `set_component_mounted_on` (a component's own `mounted_on` is a fingerprint input for its own station-reach attestation; a no-op for the box family, whose fingerprint never reads `mounted_on`). |
| `src/jarvis/core/fit_relations_assist.py` | `_mount_only_relation_row` now special-cases `child == "motors" and origin == "frame_arm"` to call new `_motors_frame_arm_reach_row` (screens via `screen_station_reach`, re-verifies any stored attestation via new `_motor_reach_attestation_is_valid`, maps to row statuses `station_reach_ok`/`station_reach_over`/`station_reach_insufficient`/`station_reach_estimated`/`attested`). `propellers ↔ motors` is unchanged — still always `n_a_disk`. `ready_count` now also counts `station_reach_ok` rows; the checklist marker for `station_reach_ok` is `→` (same as `screen_overlap`). Docstrings updated throughout to describe the new evidence class. |
| `src/jarvis/core/orchestrator.py` | `_try_handle_fit_attestation`'s bare-phrase (no named subject) SET eligibility scan now also includes `motors` when `screen_station_reach(spec, "frame_arm", components).status == "station_reach_ok"` — otherwise a bare `"declaro verificado"` would silently exclude the one component whose evidence class the box-overlap scan structurally cannot see. Named-subject resolution (`"motor"`/`"motores"` → `"motors"`) already worked unchanged via the existing `mounted_on_declare_assist` subject table — no changes needed there. |
| `tests/test_disk_station_reach_b1.py` (new) | 23 tests, T1–T8 (see §5). |
| `tests/test_geometry_fit_relations_checklist_b1.py` | Two pre-existing tests updated: `test_r5_motors_propellers_are_n_a_disk_with_mount_warning` → renamed `test_r5_propellers_stays_n_a_disk_motors_now_station_reach` (motors is now `station_reach_insufficient` in that fixture — no `frame.wheelbase_mm`/`configuration` declared — `propellers` unchanged, still `n_a_disk`); `test_r5_mount_warning_absent_once_mounted` — assertion updated from `n_a_disk` to `station_reach_insufficient` (same fixture, same missing-wheelbase reason; the `mount_warning is None` assertion this test actually guards is unchanged). |

## 3. Behavior changed

- `fit_relations_assist`'s `motors ↔ frame_arm` row is no longer hardcoded `n_a_disk` — it now reports a real, honestly-named engineering screening: `station_reach_ok` (ready to attest), `station_reach_over` (arm longer than the wheelbase-derived station radius, never silently shrunk), `station_reach_insufficient` (missing `quad_x`/`wheelbase_mm`/arm `length_mm`/`motors.mounted_on == "frame_arm"`), or `station_reach_estimated` (either fact is `estimated_temporary` — fails closed for attest).
- An Engineer can now `declaro verificado el motor` (or a bare `declaro verificado` when motors is the only eligible item) when `motors` is `station_reach_ok`. The seal is a new fingerprint over `(wheelbase_mm, arm length_mm, arm length_mm source, frame configuration, motors.mounted_on)` — never the box `compute_fit_attestation_fingerprint`. It clears automatically when the arm's `length_mm` changes, when the frame's `configuration`/`wheelbase_mm` changes, or when motors' own `mounted_on` changes.
- `propellers ↔ motors` is completely unchanged — still unconditionally `n_a_disk`, same reason string.
- `pose_envelope_screening.screen_posed_envelope` is completely unchanged — motors/propellers still resolve to `no_pose`/`child_not_box` there, exactly as before this Buy (T6).
- The box family's own attestation path (`flight_controller`/`esc`/`battery`/`sensors`) is unaffected — verified explicitly (T7) that a box-family seal still uses `compute_fit_attestation_fingerprint` and the box-overlap gate, untouched by the new `motors`-only branch.

## 4. Empirical verification (before writing tests)

Ran live against real `ComponentSpec` fixtures and the two real projects with full cited facts (`10-min-autonomía`, `dron-de-vigilancia-doméstico`, both `motors`: Ø28.5mm/H33.1mm, `frame_arm`: 80×20×5mm, `frame`: `quad_x`/225mm wheelbase, `motors.mounted_on == "frame_arm"`):

```
screen_station_reach (synthetic, L=80 <= R≈159.1)        → station_reach_ok
screen_station_reach (synthetic, L=300 > R≈159.1)        → station_reach_over
screen_station_reach (no mounted_on)                     → station_reach_insufficient
screen_station_reach (arm length_mm estimated_temporary) → station_reach_estimated

set_component_declared_fit_attestation(ps, "motors", True)  → OK, fingerprint '225.0|80.0|declared|quad_x|frame_arm'
upsert_frame_part(..., "frame_arm", {length_mm: 95})         → motors attestation cleared (None)
set_component_mounted_on(..., "motors", None)                → motors attestation cleared (None)
set_component_declared_fit_attestation(ps, "esc", True)       → still raises via the UNCHANGED box path (estimated_dims on this project's plate)
```

Full `fit_relations_assist` checklist on `10-min-autonomía` before/after attest:
```
before: "→ motors → frame_arm: El brazo declarado alcanza el radio de estación del quad-X — alcance de estación, no verificado. — escribe "declaro verificado el motor""
after:  "✓ motors → frame_arm: verificado por el Engineer — no es una comprobación geométrica de Jarvis"
```

IDLE bridge smoke (`orchestrator._try_handle_fit_attestation`, no persistence): `"declaro verificado el motor"` and bare `"declaro verificado"` both correctly attest `motors` when it's the only `station_reach_ok` candidate.

Live projects §3 smoke reproduced exactly (both real projects, in-memory only, never saved): `motors` row `station_reach_ok` → attest succeeds → arm `length_mm` forced to 999mm → attestation clears → row becomes `station_reach_over`.

## 5. Tests

### Added (`tests/test_disk_station_reach_b1.py`, 23 tests)

| ID | Tests | Covers |
|---|---|---|
| T1 | `test_t1_reach_ok_when_arm_length_within_station_radius` | L ≤ R → `station_reach_ok` |
| T2 | `test_t2_reach_over_when_arm_longer_than_station_radius_never_shrunk` | L > R → `station_reach_over` |
| T3 | `test_t3_missing_wheelbase_is_insufficient`, `test_t3_missing_arm_length_is_insufficient`, `test_t3_not_quad_x_is_insufficient`, `test_t3_missing_mount_is_insufficient_never_inferred`, `test_t3_missing_frame_arm_key_is_insufficient` | Every missing-input path → `station_reach_insufficient` |
| T4 | `test_t4_estimated_temporary_arm_length_is_estimated_status`, `test_t4_estimated_temporary_wheelbase_is_estimated_status`, `test_t4_attest_set_raises_on_estimated_arm`, `test_t4_attest_set_raises_on_insufficient` | `estimated_temporary` → `station_reach_estimated`; attest SET raises on both estimated and insufficient |
| T5 | `test_t5_motors_frame_arm_uses_reach_status_propellers_still_n_a_disk`, `test_t5_motors_attested_row_after_valid_seal` | `assess_fit_relations` wiring; `propellers` untouched |
| T6 | `test_t6_screen_posed_envelope_unchanged_child_not_box_for_motors` | `screen_posed_envelope` unchanged for a cylinder motor |
| T7 | `test_t7_attest_ok_only_on_station_reach_ok`, `test_t7_station_reach_fingerprint_differs_from_box_fingerprint`, `test_t7_attestation_clears_when_arm_length_changes`, `test_t7_attestation_clears_when_mounted_on_changes`, `test_t7_box_family_attestation_still_uses_box_fingerprint_unaffected` | Attest gate, fingerprint distinctness, clear-on-change (arm length, mounted_on), box family isolation |
| T8 | `test_t8_copy_never_claims_aabb_or_bare_verified`, `test_t8_relaciones_idle_shows_reach_row_never_writes`, `test_t8_idle_declaro_verificado_motor_attests`, `test_t8_idle_bare_declaro_verificado_finds_motors_when_only_eligible` | Copy honesty; IDLE `relaciones` read-only; IDLE `declaro verificado` (named + bare) attest path |

### Updated (`tests/test_geometry_fit_relations_checklist_b1.py`)

- `test_r5_motors_propellers_are_n_a_disk_with_mount_warning` → renamed `test_r5_propellers_stays_n_a_disk_motors_now_station_reach`; `motors` assertion changed from `n_a_disk` to `station_reach_insufficient` (fixture has no `frame.wheelbase_mm`); `na_count` changed from `2` to `1`.
- `test_r5_mount_warning_absent_once_mounted` — `row.status` assertion changed from `n_a_disk` to `station_reach_insufficient`; the `mount_warning is None` assertion (what the test actually names/guards) is unchanged.

### Executed

```
python -m pytest tests/test_disk_station_reach_b1.py -q               → 23 passed
python -m pytest tests/test_geometry_fit_relations_checklist_b1.py -q → 15 passed
python -m pytest -q                                                    → 2968 passed, 1 skipped
```

No UI files touched — `ui/spatial-board` vitest suite not re-run (unaffected by this Buy, per lock/T9 preference for "no UI this cycle").

## 6. Design notes / judgment calls

- **Fingerprint field order** (locked by test T7): `(wheelbase_mm, arm length_mm, arm length_mm source, frame configuration, child.mounted_on)`, joined the same plain-string way as `compute_fit_attestation_fingerprint` — not a cryptographic hash, an equality check against a later recomputation.
- **Attestation-clearing strategy**: always-clear on write (never diff-based), mirroring every existing attestation-clearing hook in `component_writers.py` (e.g. the pose writer's own "always-clear... never compares old vs new" precedent). Applied at three sites: `upsert_frame_part` (frame_arm), `merge_frame_root_declared_properties` (frame wheelbase/configuration), `set_component_mounted_on` (the component's own mounted_on) — plus the pre-existing read-time re-verification in `fit_relations_assist._motor_reach_attestation_is_valid` (mirrors `_attestation_is_valid` for the box family) as a second, independent guarantee.
- **Writer branching, not a second writer function**: `set_component_declared_fit_attestation` remains the single writer for `declared_fit_attestation` (per lock #9's own wording, "the writer path branches") — `component_key == "motors"` is the only branch point; every other key is byte-identical to the pre-existing box-overlap path.
- **Bare-phrase IDLE eligibility (judgment call, not explicitly required by the IC text)**: extended the no-named-subject SET scan to include `motors` via its own evidence class. Without this, a bare `"declaro verificado"` would report "ningún par tiene screening en solape" even when `motors` was the only actually-ready item — a functional/honesty gap, since the box-overlap scan can structurally never see a disk component. This is additive only (adds one more `or` clause to the existing comprehension) and does not change behavior for any box-family key.
- **Noun for the attest-phrase suggestion**: used `"el motor"` (singular), matching this codebase's existing convention of singular nouns for plural component keys (e.g. `"sensors"` → `"el sensor"` in `craft_montage_stack_assist._SUBJECT_NOUNS`).

## 7. Out of scope (unchanged, named debt per IC §4)

`propellers ↔ motors` reach/axial (needs its own evidence class) · margin band/tolerance on L vs R (separate ★) · Path N (HOLD) · plate-box/stack AABB attest (parallel bag track) · Visor Situar drag for multi-copy motors · `ASSEMBLY_READY` coupling.

## 8. Remaining risks

None identified. The one latent risk flagged in the parent investigation (`compute_fit_attestation_fingerprint` would `KeyError` if ever called on a non-box geometry) was not exercised or worsened by this Buy — the new `motors` branch never calls that function, and no other code path was changed that could route a disk/cylinder geometry into it.
