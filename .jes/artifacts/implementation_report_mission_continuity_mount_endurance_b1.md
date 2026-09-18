# Implementation Report — Mission Continuity: mount + endurance (`B1-mission-continuity-mount-endurance`)

**IC:** `implementation_contract_mission_continuity_mount_endurance_b1.md`
**Implementer:** Claude Code
**Date:** 2026-09-18
**Checkpoint:** package `0.4.1` (unchanged) · suite **3077 passed, 1 skipped** (was 3068) · UI unaffected

---

## 1. Scope delivered

After mission identity + mass are done, Continuity's mission-aware high-margin waterfall (`ReasoningLayer._mission_aware_high_margin_suggestion`) now asks for **mount** (cámara/radio → airframe) and **autonomía objetivo (min)** before the soft margin line — reusing the existing `mount_standard_assist` checklist and the existing `_parse_constraints`/`parsed_constraints` authority, never a second mount system or a duplicated autonomy regex. No poses/mm, no plate-box, no `power_w`→energy, no VTX, no firmware, no Conversation Engine/LLM, no version bump, no `workspace/` mutation (tests-only; the live-vigilancia smoke in §6 was fully in-memory — `save_state` never called).

## 2. Files changed

| File | Change |
|---|---|
| `src/jarvis/core/mounted_on_declare_assist.py` | `_SUBJECT_PATTERNS` widened with `cameras`/`radio_module`, reusing `aerial.py`'s own `CAMERA_KEYWORDS`/`RADIO_KEYWORDS` tuples via a new small helper (`_keyword_tuple_to_pattern`) — no second, possibly-diverging noun list. |
| `src/jarvis/core/mount_standard_assist.py` | `_STACK_SUBJECTS` widened with `("cameras", "cámara", "montada")` / `("radio_module", "radio", "montado")` — this Buy IS the "new ★" that tuple's own module docstring required to widen it. Module docstring's locked in-scope graph updated to name the addition. |
| `src/jarvis/schemas/state_schema.py` | New public `derive_parsed_constraints(current_parameters, objective=None)` — thin wrapper over the existing private `_parse_constraints`, for callers holding a LOCAL, not-yet-persisted `current_parameters` dict. |
| `src/jarvis/core/orchestrator.py` | `_build_analyze_context` gained `"parsed_constraints": project_state.parsed_constraints` (both the `None`-project and main-return branches). |
| `src/jarvis/actions/simulate.py` | `ReasoningLayer.build(...)` context gained `"parsed_constraints": project_state.parsed_constraints`. |
| `src/jarvis/actions/iterate.py` | Both `reasoning_layer.build(...)` call sites (physical + declarative) gained `"parsed_constraints": derive_parsed_constraints(updated_parameters, project_state.objective)` — the LOCAL `updated_parameters` dict may have just changed `restrictions` mid-turn, so `project_state.parsed_constraints` alone would be stale there. |
| `src/jarvis/core/reasoning_layer.py` | New `_mission_mount_suggestion(components)` helper (reconstructs `ComponentSpec` objects from the context's serialized dicts, calls `mount_standard_assist.build_mount_standard_checklist`, returns the first `cameras`/`radio_module` row — camera before radio, ambiguous plate never guessed). `_mission_aware_high_margin_suggestion` extended with the mount check and an autonomy-target check (`"autonomy_min" not in context.get("parsed_constraints")`) right before the soft-margin fallback. Docstring rewritten to describe the full 8-step waterfall and name which plumbing closed B1-mission-mass-energy's own documented 9c/9d gaps. |
| `docs/USER_GUIDE_CRAFT_MONTAGE.md` | New "Montar cámara/radio + autonomía objetivo" subsection (lock #11) — mount phrases + how to set autonomía via `restricciones:`, linked from the mass section. |
| `tests/test_mission_continuity_mount_endurance_b1.py` (new) | 9 tests, T1–T9 (T10 = full suite, §7). |
| `tests/test_continuity_mission_intent_b1.py` | `_context()` helper gained an optional `parsed_constraints` param; two pre-existing tests (`test_t5_...`, `test_t7_...`) updated to pass `parsed_constraints={"autonomy_min": 8.0}` (§5). |
| `tests/test_mission_mass_energy_b1.py` | `test_t11_...` updated to set `context["parsed_constraints"] = {"autonomy_min": 8.0}` (§5). |

## 3. Design choices / lock reporting

- **Lock #7 (autonomy read path)**: `orchestrator._build_analyze_context` and `simulate.py` read the already-computed `project_state.parsed_constraints` directly — zero recomputation, since neither mutates `current_parameters` before building context. `iterate.py`'s two sites use the new public `state_schema.derive_parsed_constraints` wrapper instead, because their `updated_parameters` is a local dict that may have just changed `restrictions` mid-turn (G26 mid-session restriction-write capability) and would otherwise read a stale `project_state.parsed_constraints`. Both paths call the SAME private `_parse_constraints`/`_AUTONOMY_CONSTRAINT_RE` — no second regex anywhere (verified statically in T8, §7).
- **Lock #4/#5/#6 (mount reuse)**: `_mission_mount_suggestion` calls `mount_standard_assist.build_mount_standard_checklist` — the exact same function `montajes estándar` renders — rather than re-implementing plate-target resolution or ambiguity detection. The `ReasoningLayer` context carries serialized component dicts (`.model_dump()`), so each is reconstructed into a `ComponentSpec` object before the call (the checklist function's own contract), rather than duplicating its `_plate_target` logic inline.
- **Priority order**: camera before radio (`mission_rows[0]`), mirroring `_STACK_SUBJECTS`'s own declared order — matches lock #5's "prefer ONE suggestion (first hole: camera before radio)".
- **Ambiguous plate**: never resolved automatically. Continuity's suggestion text points at `montajes estándar` (lock #6) instead of guessing a target.

## 4. Empirical verification (before formal tests)

```
Parse: "cámara montada en la placa" (1 plate)  -> SET, cameras, frame_plate
Parse: "radio montado en el frame"             -> SET, radio_module, frame
Checklist: unmounted camera+radio, 1 plate     -> both rows "suggested", target=frame_plate

Ladder (synthetic context):
  mounts missing            -> "Monta la cámara en la placa/frame"      declare_mission_mount
  camera mounted, radio not -> "Monta el radio en la placa/frame"       declare_mission_mount
  both mounted, no autonomy -> "Declara autonomía objetivo (min)"       declare_autonomy_target
  autonomy present          -> "Revisar margen vs carga de misión"      mission_margin_review
  ambiguous plate (2+)      -> "Elige placa para el montaje de misión (montajes estándar)"
```

### Live smoke — `dron-de-vigilancia-doméstico` (in-memory, `save_state` never called)

The real project has **three** declared plates (`frame_plate`, `frame_plate_2`, `frame_plate_3`) — an unplanned but useful live exercise of the ambiguous-plate path (lock #6):

```
estado (baseline, masses already declared, no mounts) ->
  "Elige placa para el montaje de misión (montajes estándar)" | declare_mission_mount
  reason: "Hay varias placas declaradas — Jarvis no adivina cuál para la cámara;
           usa 'montajes estándar' para elegir."

parse_mounted_on_declare("cámara montada en la placa", <3 plates>) ->
  AMBIGUOUS_TARGET, candidates=(frame_plate/"Top plate", frame_plate_2/"Middle plate",
  frame_plate_3/"Bottom plate")

set_component_mounted_on(state, "cameras", "frame_plate")   -> mounted_on=frame_plate
set_component_mounted_on(state, "radio_module", "frame_plate") -> mounted_on=frame_plate
estado (mounts resolved, no autonomy_min) ->
  "Declara autonomía objetivo (min)" | declare_autonomy_target

restrictions <- "vuelo mínimo 8 min"  -> parsed_constraints = {"autonomy_min": 8.0}
estado (mounts + autonomy present) -> "Revisar margen vs carga de misión" | mission_margin_review
```

No fake "validated flight" was ever emitted — the soft margin line is the SAME pre-existing `mission_margin_review` copy, and `simulate.py`'s existing `autonomy_threshold = project_state.parsed_constraints.get("autonomy_min")` plumbing (unchanged this Buy) still drives the honest computed-vs-target WARN/FAIL path.

## 5. Two pre-existing tests updated (intentional, not weakened)

`tests/test_continuity_mission_intent_b1.py::test_t5_both_medium_plus_softens_to_margin_review_5d` and `::test_t7_continuity_vigilancia_shaped_closed_design_never_shows_increase_payload`, plus `tests/test_mission_mass_energy_b1.py::test_t11_mission_intent_both_masses_set_soft_margin_never_increase_payload`: all three fixtures had `cameras`/`radio_module` at medium+ completeness with `mass_g` already set (satisfying the PRE-this-IC waterfall's terminal condition) but declared no frame/plate component and no `parsed_constraints`. None of the three declare a frame/plate component at all, so the new mount step correctly finds nothing to suggest a target for and falls through untouched; each now supplies `parsed_constraints={"autonomy_min": 8.0}` so the new autonomy-target step also clears, reaching the same soft-margin assertion each test originally intended. No assertion was changed — only fixtures gained the one field the longer ladder now requires, exactly mirroring how `B1-mission-mass-energy` resolved the identical class of breakage one cycle earlier.

## 6. Tests

### Added (`tests/test_mission_continuity_mount_endurance_b1.py`, 9 tests)

| ID | Test | Covers |
|---|---|---|
| T1 | `test_t1_parse_camera_mount_phrase_set` | Camera mount phrase parses to SET |
| T2 | `test_t2_parse_radio_mount_phrase_set` | Radio mount phrase parses to SET |
| T3 | `test_t3_montajes_estandar_includes_camera_row_when_unmounted_present` | Checklist row for cámara |
| T4 | `test_t4_masses_set_camera_unmounted_top_suggestion_is_mount_camera` | Ladder: mount-camera step |
| T5 | `test_t5_mounts_done_no_autonomy_min_declare_autonomy_target` | Ladder: autonomy-target step |
| T6 | `test_t6_mounts_and_autonomy_present_soft_margin_never_increase_payload` | Ladder terminal state |
| T7 | `test_t7_neutral_high_margin_project_increase_payload_still_available` | Regression (no mission intent) |
| T8 | `test_t8_reasoning_layer_never_introduces_second_autonomy_regex` | Static + behavioral: no duplicated regex |
| T9 | `test_t9_ambiguous_multi_plate_never_invents_a_plate_key` | Ambiguous plate: parse, checklist, and Continuity all refuse to guess |

T10 (full pytest green, `0.4.1`) — see §7.

### Updated (pre-existing, intent-preserving)

`tests/test_continuity_mission_intent_b1.py` — 2 tests; `tests/test_mission_mass_energy_b1.py` — 1 test (§5).

### Executed

```
python -m pytest tests/test_mission_continuity_mount_endurance_b1.py -q   -> 9 passed
python -m pytest tests/test_continuity_mission_intent_b1.py -q            -> 17 passed
python -m pytest tests/test_mission_mass_energy_b1.py -q                  -> 14 passed
python -m pytest -q                                                       -> 3077 passed, 1 skipped
```

Package version unchanged (`pyproject.toml` still `0.4.1`). No UI files touched — `ui/spatial-board` vitest suite not re-run (unaffected). No `workspace/` write occurred anywhere in this cycle, including the live smoke in §4.

## 7. Out of scope (unchanged, named debt per IC §4)

`power_w`→energy coupling (M3, next cola) · VTX identity (M4, opt) · pose Δmm/plate L×W invention (physical, out of Continuity's remit) · firmware/Fase C (after M7) · auto-bind mounts on identity declare (not this Buy — mounts stay a declared, never inferred, relation).

## 8. Remaining risks

None identified. The ambiguous-plate branch was exercised against the real `dron-de-vigilancia-doméstico` project (which happens to carry three declared plates) rather than only a synthetic fixture, confirming lock #6 end-to-end on live data. `mounted_on_declare_assist`'s existing Spanish-only mount-verb gate (`"montad[ao]s? en"`) means an English phrase like `"camera mounted on the frame"` still returns `NONE` — a pre-existing limitation of that module, not a regression and not in this IC's scope to fix.
