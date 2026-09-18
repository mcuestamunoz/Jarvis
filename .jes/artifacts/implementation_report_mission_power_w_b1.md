# Implementation Report — Mission `power_w` → energy / autonomía (`B1-mission-power-w`)

**IC:** [implementation_contract_mission_power_w_b1.md](implementation_contract_mission_power_w_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-18
**Baseline:** package `0.4.1` (unchanged, no version bump) · suite **3122 passed, 1 skipped** (≥3100 checkpoint met) · UI unaffected (no UI files touched)

---

## Summary

Declared `power_w` on `cameras`/`radio_module` now flows end to end: grammar → writer → mirror → both `calculation_engine` autonomy paths → Continuity ladder hole. No watts are ever invented from a model string, brand, or the RunCam Phoenix 2 citation's `200mA@5V` note — that stays a plain-text citation until the user declares a real number (or a future catalog row adds an explicit `power_w` field, which this Buy deliberately did not add).

## Grammar (`src/jarvis/core/mission_power_declare_assist.py`, new)

`parse_mission_power_declare(user_input)` mirrors `mission_mass_declare_assist.py`'s exact shape (`SET`/`INCOMPLETE`/`NONE` result, same dataclass pattern). Reuses (does not duplicate) `resolve_mission_mass_subject` for camera/radio subject resolution — same `CAMERA_KEYWORDS`/`RADIO_KEYWORDS` vocabulary the identity rules and the mass grammar already use, so the three grammars can never drift apart on "what counts as a camera/radio phrase." Gate: subject + a number followed by `w`/`vatio(s)` (e.g. `cámara 1 W`, `radio 0.5 vatios`). A bare subject with a power *word* (`potencia`/`watt(s)`/`vatio(s)`) but no number → `INCOMPLETE` (asks for the number, never guesses). A bare identity phrase (`cámara RunCam`) → `NONE`, falls through to the identity-declare grammar untouched (verified by the `test_never_invent_watts_from_identity_alone` regression test, mirroring the mass Buy's own T7).

## Writer (`src/jarvis/core/component_writers.py`)

`set_mission_component_power(project_state, component_key, power_w)` — byte-for-byte structural mirror of `set_mission_component_mass`: fail-closed if the component isn't already declared (`ValueError`, lock #7-equivalent), `power_w=None` clears the field, the mirror `current_parameters["mission_accessory_power_w"]` is always recomputed as the full SUM across both mission keys from scratch (never an incremental add/subtract). Declaring power alone never touches `completeness` (lock #9) — the function only ever writes `properties`/the mirror, same as the mass writer.

## Mirrored param (`src/jarvis/core/system_architecture_catalog.py`)

`mission_accessory_power_w` added to `COMPONENT_MIRRORED_PARAMS`, next to `mission_payload_mass_kg`. No bridging branch added in `param_definition_session.py` — same as the mass param, a direct write via `apply_and_recalculate` is simply filtered out (never applied, never errors), verified by T9.

## Energy seam (`src/jarvis/core/calculation_engine.py`)

`mission_accessory_power_w` is read once (`round(float(parameters.get("mission_accessory_power_w") or 0.0), 4)`, same pattern as `mission_payload_mass_kg`) and added into **both** autonomy paths as a flat, non-multiplied term:

- Hover path: `hover["motor_hover_power_w"] * motors + mission_accessory_power_w`
- Non-hover (bench-rating) path: `effective_power_w * motors + mission_accessory_power_w`

Accessory power is never multiplied by motor count — it's one shared accessory load, not a per-motor draw (lock #6). Zero/absent reproduces the exact pre-Buy autonomy formula (T6: `absent.autonomy_min == pytest.approx(explicit_zero.autonomy_min)`, plus a byte-identical formula check against the pre-Buy `Wh / (motor_power_w × motors) × 60` expression). T5 confirms accessory power strictly lowers autonomy for an otherwise-identical state.

## Orchestrator wiring (`src/jarvis/core/orchestrator.py`)

`_try_handle_mission_power_declare` — same structure as `_try_handle_mission_mass_declare`, wired immediately after it in the IDLE routing chain (deterministic-parse family, no LLM). Returns `None` for any phrase without a recognized camera/radio subject so it never steals other declares; `INCOMPLETE` asks for a number; missing identity → honest refuse (`'cámara' aún no declarado — declara primero la cámara.`, matching the mass writer's own message shape).

## Continuity ladder (`src/jarvis/core/reasoning_layer.py`)

New `_mission_power_suggestion(components)` — camera before radio (lock #10's "prefer one suggestion"), same waterfall discipline as `_mission_mount_suggestion`. Wired into `_mission_aware_high_margin_suggestion` **after** the autonomy-target step and **before** the final margin-review fallback, per the IC's own default (§0.2): "After M2 autonomy-target step, before soft margin." Returns `None` (falls through to margin review) once both mission components carry `power_w`.

**Regression note:** this insertion moved the ladder's terminal state one step further, so four pre-existing tests across three files that previously reached "Revisar margen vs carga de misión" without declaring `power_w` needed their fixtures updated to include it (same kind of update the mount+endurance Buy made to this exact terminal-state test when *it* extended the ladder — documented precedent, not new debt):
- `tests/test_mission_mass_energy_b1.py::test_t11_mission_intent_both_masses_set_soft_margin_never_increase_payload`
- `tests/test_continuity_mission_intent_b1.py::test_t5_both_medium_plus_softens_to_margin_review_5d`
- `tests/test_continuity_mission_intent_b1.py::test_t7_continuity_vigilancia_shaped_closed_design_never_shows_increase_payload_regression`
- `tests/test_mission_continuity_mount_endurance_b1.py` (`_mission_components()` shared fixture — one edit covers all four call sites in that file, including `test_t6_mounts_and_autonomy_present_soft_margin_never_increase_payload`)

No test assertion was weakened — each now declares `power_w` explicitly (an honest, positive input) to keep reaching the same terminal state it always tested for.

## USER_GUIDE_CRAFT_MONTAGE.md

New §3.4 "Declarar potencia de misión" documents `cámara 1 W` / `radio 0.5 W`, states the autonomy-lowers-not-raises honesty, and explicitly calls out that the Phoenix 2 citation's mA note is never auto-converted. Added to the cheatsheet's mission block. §3.3's closing line updated to mention the new ladder hole.

## Tests — `tests/test_mission_power_w_b1.py` (new, 14 tests, all green)

T1–T10 per IC §2 (T7 split into three focused tests: CTA when missing, next-hole-is-radio, both-declared-reaches-margin-review — same granularity precedent as the mass Buy's own T8/T9 split), plus one extra regression (`test_never_invent_watts_from_identity_alone`) confirming both the grammar-level and catalog-bind-level "never invent" boundaries. Full suite: 3122 passed, 1 skipped.

## Forbidden items — confirmed NOT done

No mA→W invention (Phoenix 2's `200mA@5V`/`85mA@12V` stays citation-only in `source_note`; `bind_camera_from_catalog` still projects no `power_w` — verified directly in the extra regression test). No Conversation Engine, no LLM, no version bump. No folding accessory into `motor_power_w` or overwriting any OP resolution — `mission_accessory_power_w` is a wholly separate additive term, added once per autonomy computation, never touching `motor_op_power_w`/`resolve_operating_point`/`resolve_operating_point_at_thrust`. No workspace mutation — default tests-only, per lock #13.

## Remaining risks / named debt

- **Engineer smoke (§3 of the IC) not run by this implementer** — per the IC's own handoff (`Engineer → smoke §3 on vigilancia`) and lock #13 ("Live: default tests-only"), the live `dron-de-vigilancia-doméstico` workspace smoke (declare `cámara 1 W`, confirm `calcular`/`simular` autonomy drops from the ~0.7 min baseline) is left for the Engineer to run and ACCEPT/waive.
- Catalog `power_w` (lock #4 — projecting a future JSON row's explicit `power_w` the same way `mass_g` is projected) is intentionally not implemented; the Phoenix 2 seed row still carries no `power_w` field, so `bind_camera_from_catalog` has nothing to project. A future Buy adding that field to a seed row would need `_CAMERA_CATALOG_PROJECTED_KEYS` extended and the same same-SKU-refresh-preserves-a-manual-declare discipline the mass fix (post-review, `B1-library-cameras-seed`) already established for `mass_g` — worth carrying forward rather than re-discovering.
- Auto mA→W conversion, VTX, and additional mission keys beyond `cameras`/`radio_module` remain explicitly out of scope (IC §4).
