# Implementation Report — Extended identity rules (`B1-extended-identity-rules`)

**IC:** `implementation_contract_extended_identity_rules_b1.md`
**Implementer:** Claude Code
**Date:** 2026-09-17
**Checkpoint:** package `0.4.1` (unchanged) · suite **3044 passed, 1 skipped** (was 3028) · UI unaffected

---

## 1. Scope delivered

Four new identity-only `ComponentRule`s (`payload_bay`, `arm`, `wheels`, `gearbox`) added to `aerial_registry`, unlocking the last four gated SYSTEM_DEFINITION blocks (`payload`, `manipulation`, `actuation`, `transmission`). No catalog seeds, no mirrored mass, no kinematics/drivetrain physics, no change to `frame_arm`/Structure B, no version bump, no `workspace/` mutation (tests-only; the one live-project check in §6 was read-only, never saved).

## 2. Files changed

| File | Change |
|---|---|
| `src/jarvis/domains/aerial.py` | Four new extractor/completeness pairs (`extract_payload_bay_properties`/`_payload_bay_completeness`, `extract_arm_properties`/`_arm_completeness`, `extract_gearbox_properties`/`_gearbox_completeness`, `extract_aerial_wheels_properties`/`_aerial_wheels_completeness`) + four new `ComponentRule`s appended to `aerial_registry` (now 13 rules, was 9). |
| `src/jarvis/core/system_architecture_catalog.py` | `BLOCK_ALIASES` gained `"ruedas"`/`"wheels"` → `"actuation"` and `"gearbox"`/`"caja de cambios"`/`"reductor"` → `"transmission"` (found missing during implementation — see §4). Step-1 example copy: `'batería', 'frame', 'cámara'` → `'batería', 'frame', 'cámara', 'payload'` (lock #9). |
| `docs/USER_GUIDE_CRAFT_MONTAGE.md` | §3.1 trap line ("Bloques que aún no se pueden añadir... no hay regla") replaced with a closed-note (lock #10). |
| `tests/test_extended_identity_rules_b1.py` (new) | 16 tests, T1–T7, T9 (see §7). |
| `tests/test_aerial_domain.py`, `tests/test_control_component.py` | Registry-size assertions bumped 9 → 13. |
| `tests/test_system_definition_session.py` | Two obsolete "still gated"/"still refused" tests flipped to accept-path (see §5); `test_step1_prompt_examples_are_all_resolvable` updated for the new `'payload'` example. |
| `tests/test_ground_domain.py` | One obsolete "aerial never matches `rueda`" assertion updated to reflect the intentional new shared keyword (see §5); one new test added confirming the two domains' `wheels` rules stay semantically distinct (identity-only vs. torque physics) despite sharing the keyword surface. |

## 3. The four rules (exact keywords, lock #8)

| Key | `component_type` | Keywords | Model source |
|---|---|---|---|
| `payload_bay` | `payload` | `payload`, `bahia`, `bahía`, `carga util`, `carga útil` | Descriptor map (`gopro`→`gopro_bay`, `termica`/`cámara térmica`→`thermal_payload_bay`) else generic `generic_payload_bay` whenever any keyword is present |
| `arm` | `manipulation` | `manipulador`, `brazo robot`, `robotic arm`, `brazo manipulador` — **deliberately no bare `brazo`/`arm`** (lock #5) | `robotic_arm` whenever any keyword is present |
| `wheels` | `rolling_passive` | `rueda`, `wheels`, `neumático`, `neumatico`, `tyre`, `tire` — **bare singular `wheel` excluded** (see §4) | `wheel_count` (shared `ground.extract_wheel_properties`) or `wheel_type` (`omni`/`mecanum`/`estándar`) |
| `gearbox` | `transmission` | `gearbox`, `caja de cambios`, `reductor` | A cited ratio (`\d+:\d+`) stored verbatim as `model` (e.g. `"gearbox_5_1"`) — bare trigger alone stays `low` |

## 4. Two bugs caught by the existing regression suite during implementation

**Bug 1 — `wheel` vs `wheelbase` substring collision.** My first draft included bare `"wheel"` in the `wheels` rule's keywords, per lock #8's literal "wheel(s)" wording. `ComponentRule.matches()` is a plain substring check, and `"wheel"` is a substring of `"wheelbase"` — a term free-text frame declares already use (e.g. `"quad-x wheelbase 230mm"`). This broke `test_merge_configuration_wheelbase_on_freetext_apply` (the phrase stopped reaching the `frame` rule at all). Fixed by dropping bare `"wheel"` and keeping only `"wheels"` (plural — not a substring of `"wheelbase"`), `"rueda"`, and the other non-colliding tokens. Documented inline in `aerial.py`, same discipline as the earlier `"rx"` exclusion precedent from `B1-mission-payload-identity`.

**Bug 2 — missing `BLOCK_ALIASES` entries.** Adding the `ComponentRule`s alone made `block_components_are_resolvable("actuation")`/`("transmission")` return `True`, but a live SYSTEM_DEFINITION smoke (§6) showed typing `"ruedas"`/`"gearbox"` at step 1 fell through to the unexpanded free-text path ("bloque 'ruedas' registrado como bloque custom, sin componentes predefinidos") instead of resolving to the `actuation`/`transmission` block — `BLOCK_ALIASES` had no entry mapping those Spanish/English phrases to the canonical block names (unlike `manipulation`, which already had `"manipulador"`/`"brazo"`/`"arm"` aliased). Fixed by adding the four missing aliases. Without this, the ComponentRules would have been technically resolvable but practically unreachable via natural block selection — caught by proactively smoke-testing the full SYSTEM_DEFINITION flow before writing formal tests, not by the pre-existing suite.

## 5. Two pre-existing tests updated (intentional behavior change, not weakened)

- `tests/test_system_definition_session.py::test_t1_dead_blocks_are_not_resolvable` → renamed `test_t1_previously_dead_blocks_now_resolvable_b1_extended_identity_rules`; assertion flipped from `False` to `True` for all four blocks (this IC's entire purpose).
- `tests/test_system_definition_session.py::test_t4_mode_b_payload_still_refused_no_stub` → renamed `test_t6_mode_b_payload_accepted_b1_extended_identity_rules`; assertion flipped from refuse to accept, confirms `payload_bay` stub created.
- `tests/test_ground_domain.py::test_aerial_registry_does_not_match_ground_specific_keywords` → the `rueda`/`wheels` assertion was `is None`; now confirms it matches the new **aerial** `wheels` rule specifically (`rule.suggested_key == "wheels"`), documented as an intentional, narrow exception to the "domains never share keywords" rule this test otherwise still enforces for actuator-physics keywords (`par`/`torque`/`traccion`, unchanged `None`).

## 6. Empirical verification

```
block_components_are_resolvable: payload=True, manipulation=True, actuation=True, transmission=True

infer_component('payload GoPro bay')   → payload_bay / payload / medium / model=gopro_bay
infer_component('bahía de carga')      → payload_bay / payload / medium / model=generic_payload_bay
infer_component('brazo manipulador')   → arm / manipulation / medium / model=robotic_arm
infer_component('robotic arm 6 DOF')   → arm / manipulation / medium / model=robotic_arm (DOF never structured)
infer_component('gearbox 5:1')         → gearbox / transmission / medium / model=gearbox_5_1
infer_component('reductor')            → gearbox / transmission / low
infer_component('4 ruedas')            → wheels / rolling_passive / medium / wheel_count=4
infer_component('wheels omni')         → wheels / rolling_passive / medium / wheel_type=omni
infer_component('rueda')               → wheels / rolling_passive / low

Frame-arm non-collision (T7):
infer_component('4 brazos carbono')       → frame (unchanged)
infer_component('brazo carbono 300mm')    → frame (unchanged)
aerial_registry.match('wheelbase 230mm')  → None (no false match after Bug 1 fix)

Full SYSTEM_DEFINITION smoke (fresh temp project, mode B):
  'payload'          → "Bloque 'payload' añadido"
  'manipulador'      → "Bloque 'manipulation' añadido"
  'ruedas'           → "Bloque 'actuation' añadido"        (after Bug 2 fix; was a bare custom-block registration before)
  'gearbox'          → "Bloque 'transmission' añadido"     (after Bug 2 fix)
  → after 'listo': components = {..., payload_bay, arm, wheels, gearbox} all present, all base components (motors/propellers/esc/battery/frame/flight_controller/sensors) unaffected

Live project (10-min-autonomía, read-only, never saved):
  "bahía de carga" → orchestrator IDLE free-text declare → "Payload bay registrado."
```

## 7. Tests

### Added (`tests/test_extended_identity_rules_b1.py`, 16 tests)

| ID | Tests | Covers |
|---|---|---|
| T1 | `test_t1_all_four_previously_gated_blocks_now_resolvable` | Gate unlock for all four blocks |
| T2 | `test_t2_payload_bay_generic_phrase_reaches_medium`, `test_t2_payload_bay_gopro_descriptor_reaches_medium_with_specific_model`, `test_t2_payload_bay_bare_via_forced_key_stays_low` | payload_bay ladder |
| T3 | `test_t3_manipulator_phrase_reaches_medium`, `test_t3_manipulator_never_touches_frame_arm_key` | arm identity + non-collision with `frame_arm` key |
| T4 | `test_t4_wheels_count_phrase_reaches_medium`, `test_t4_wheels_type_phrase_reaches_medium_without_count`, `test_t4_wheels_bare_stays_low` | wheels ladder (count and type paths) |
| T5 | `test_t5_gearbox_ratio_reaches_medium`, `test_t5_gearbox_bare_stays_low` | gearbox ladder |
| T6 | `test_t6_system_definition_b_payload_and_manipulador_accept_with_stubs`, `test_t6_system_definition_b_wheels_and_gearbox_accept_with_stubs` | End-to-end SYSTEM_DEFINITION accept + stub creation, all four keys |
| T7 | `test_t7_frame_arm_freetext_declare_not_stolen_by_manipulator_rule`, `test_t7_wheelbase_freetext_not_stolen_by_wheels_rule` | Both collision regressions this Buy found and fixed |
| T9 | `test_t9_completeness_ladder_never_reaches_high_without_catalog` | Ceiling check across all four families |

### Updated (pre-existing files)

- `tests/test_aerial_domain.py`, `tests/test_control_component.py` — registry size 9 → 13.
- `tests/test_system_definition_session.py` — two tests flipped (§5), one updated for new example copy.
- `tests/test_ground_domain.py` — one assertion updated, one new cross-domain distinction test added (§5).

### Executed

```
python -m pytest tests/test_extended_identity_rules_b1.py -q  → 16 passed
python -m pytest -q                                            → 3044 passed, 1 skipped
```

T8 (cameras/radio identity regression) confirmed via the full suite — `test_system_definition_session.py`'s camera/mission-payload-identity tests all still pass unmodified.

No UI files touched — `ui/spatial-board` vitest suite not re-run (unaffected).

## 8. Out of scope (unchanged, named debt per IC §4)

`library/cameras`/payload/arm physics bags (parked) · mirrored mass into energy (later ★) · lidar key (still named debt from the original perception narrowing) · plate-box/Path N/HD-* (parked) · ground wizard param redesign (orthogonal, untouched — `ground_registry`'s own `wheels`/`wheel_actuators` rules are byte-identical to before this Buy).

## 9. Remaining risks

None identified. Both issues found during implementation (§4) were caught before formal tests were written, via direct empirical verification against the actual registry/orchestrator, and are now locked by regression tests (T7's `test_t7_wheelbase_freetext_not_stolen_by_wheels_rule`, and T6's full SYSTEM_DEFINITION accept-path tests which exercise the `BLOCK_ALIASES` fix end-to-end).
