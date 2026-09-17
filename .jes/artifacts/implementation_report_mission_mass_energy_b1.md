# Implementation Report — Mission mass → AUW + Continuity ladder (`B1-mission-mass-energy`)

**IC:** `implementation_contract_mission_mass_energy_b1.md`
**Implementer:** Claude Code
**Date:** 2026-09-17
**Checkpoint:** package `0.4.1` (unchanged) · suite **3058 passed, 1 skipped** (was 3044) · UI unaffected

---

## 1. Scope delivered

Declared (never invented) `mass_g` on `cameras`/`radio_module` mirrors into a new `mission_payload_mass_kg` parameter, which enters `total_mass` additively (**P1** — never displaces `payload_kg`), with a plain-language double-count warning when both are nonzero. Continuity's mission-aware waterfall now asks for mass before falling back to the soft "Revisar margen..." line. No catalog seeds, no `power_w`→energy coupling, no VTX, no version bump, no `workspace/` mutation (tests-only; the live-vigilancia smoke in §6 was fully in-memory, `save_state` never called).

## 2. Files changed

| File | Change |
|---|---|
| `src/jarvis/domains/aerial.py` | Extracted `CAMERA_KEYWORDS`/`RADIO_KEYWORDS` as named module-level tuples (previously inline in the `ComponentRule(...)` calls) so the new mass-declare grammar can reuse the exact same vocabulary — no second, possibly-diverging keyword list. `ComponentRule` definitions updated to reference the named tuples (byte-identical values). |
| `src/jarvis/core/mission_mass_declare_assist.py` (new) | Pure IDLE grammar parser — `parse_mission_mass_declare(user_input)`, mirrors `estimated_temporary_esc_assist.py`'s structure. |
| `src/jarvis/core/component_writers.py` | New `set_mission_component_mass(project_state, component_key, mass_g)` — the single writer for `mass_g` on `cameras`/`radio_module` and the `mission_payload_mass_kg` mirror. Fail-closed: raises on an unknown key or an undeclared target (never auto-creates identity). |
| `src/jarvis/core/system_architecture_catalog.py` | `COMPONENT_MIRRORED_PARAMS` gained `"mission_payload_mass_kg"`. |
| `src/jarvis/core/calculation_engine.py` | `total_mass` sum extended with `mission_payload_mass_kg` (reads `parameters.get(...) or 0.0`, same pattern as `battery_mass_kg`/`motor_mass_kg`). |
| `src/jarvis/core/orchestrator.py` | New `_try_handle_mission_mass_declare` bridge, wired into the IDLE dispatch chain right after the ESC provisional-height bridge. |
| `src/jarvis/core/reasoning_layer.py` | `_mission_aware_high_margin_suggestion` extended with two new waterfall steps (declare camera mass / declare radio mass) before the soft-margin fallback; new `_mission_mass_double_count_insight` wired into `_build_insights`. |
| `docs/USER_GUIDE_CRAFT_MONTAGE.md` | New "Declarar masa de misión" subsection (lock #12). |
| `tests/test_mission_mass_energy_b1.py` (new) | 14 tests, T1–T11 (see §7). |
| `tests/test_continuity_mission_intent_b1.py` | Two pre-existing tests updated to add `mass_g` to their fixtures (their own intent — "identity resolved reaches soft margin" — now additionally requires mass declared; see §5). |

## 3. Design choices (report per lock's own "report choice" instructions)

- **Mirror key name**: `mission_payload_mass_kg` (the IC's own "working" suggestion, kept as final — no better name emerged).
- **`power_w`**: not parsed, not stored, no energy coupling (lock #4 default — "mass-only, no energy coupling"). Not even ignored-but-stored: the grammar (§7a/7b) only recognizes mass (`g`/`gramos`), so a `power_w` value in the same phrase is simply never matched by this grammar at all.
- **P1 vs P2**: **P1 (additive + warn)**, per the IC's own default. `payload_kg` is never read, zeroed, or displaced by any code this Buy touched.
- **Grammar language**: ES primary + EN aliases, via the shared `CAMERA_KEYWORDS`/`RADIO_KEYWORDS` tuples (already ES+EN from `B1-mission-payload-identity`).

## 4. Lock #9c/9d — documented gaps, not oversights

**9c (mount reminder)**: `mount_standard_assist.py`'s own `_STACK_SUBJECTS` tuple (`esc`/`flight_controller`/`battery`/`sensors`) is explicitly locked by that module's own docstring — *"never widened without a new ★"*. `cameras`/`radio_module` are not in it. Reusing that module's mechanism for these two keys would require widening its own locked scope, which this IC does not grant (and which would violate that module's own gate, not just skip a nice-to-have). Per this IC's own instruction ("reuse mount assist — do not invent a second mount system"), the honest resolution is to **skip** 9c rather than either violate the other module's lock or build a second, parallel mount system. Documented inline in `reasoning_layer.py`.

**9d (autonomy-target reminder)**: needs a deterministic autonomy-target read. `ReasoningLayer`'s `context` dict only carries raw `current_parameters["restrictions"]` text — never the derived `parsed_constraints["autonomy_min"]` (computed by `ProjectState`'s own model validator, not exposed to this module). Re-deriving that regex a second time here would be exactly the kind of keyword-list duplication `B1-catalog-hygiene-mission-suggestions` (this session's own prior IC) explicitly avoided elsewhere. Per lock #9d's own explicit permission — *"wire only if a deterministic restriction/param path already exists; else document gap and keep ladder stop at 9c + soft margin"* — this is skipped too.

**Net effect**: the waterfall is `camera identity → radio identity → camera mass → radio mass → soft margin`. Both skipped steps are named, explained, and out of scope rather than silently absent.

## 5. Two pre-existing tests updated (intentional, not weakened)

`tests/test_continuity_mission_intent_b1.py::test_t5_both_medium_plus_softens_to_margin_review_5d` and `::test_t7_continuity_vigilancia_shaped_closed_design_never_shows_increase_payload` both had fixtures with `cameras`/`radio_module` at medium+ completeness but **no `mass_g`** — before this Buy, that combination reached the soft-margin fallback directly (5d). Now it correctly reaches the new "declare mass" step first (this Buy's entire purpose). Both tests' own stated intent — "identity resolved reaches soft margin" — is preserved by adding `mass_g` to their fixtures, rather than changing what they assert.

## 6. Empirical verification

```
Writer:
  set_mission_component_mass(state, "cameras", 28.0)  → mass_g=28.0, mirror=0.028 kg
  + radio 3.0                                          → mirror=0.031 kg
  clear camera mass                                    → mirror drops to 0.003 kg

CalculationEngine.build:
  baseline (no mission mass)         → total_mass_kg = X
  + mission_payload_mass_kg=0.028    → total_mass_kg = X + 0.028 exactly

Grammar:
  "cámara RunCam"      → NONE (correctly falls through to identity-declare — see bug below)
  "cámara 28 g"        → SET, cameras, 28.0
  "radio 3 g"          → SET, radio_module, 3.0
  "cuánto pesa la cámara" → INCOMPLETE (asks for the number)
  "reductor"           → NONE

Continuity ladder (live dron-de-vigilancia-doméstico, in-memory, never saved):
  Step 1 (no mass declared)     → "Declara masa de cámara (g)"
  Step 2 (camera mass declared) → "Declara masa de radio (g)"
  Step 3 (both masses declared) → "Revisar margen vs carga de misión"
  Insights at step 2: [..., "payload_kg (1.0 kg) y masa de misión declarada (0.028 kg,
    cámara/radio) están sumando ambos al AUW — si ya incluías esos gramos en
    payload_kg, redúcelo para no contar dos veces.", ...]
  mission_payload_mass_kg after both declares: 0.031
```

## 7. Bug caught and fixed during implementation

**First draft was too eager**: `parse_mission_mass_declare` initially returned `INCOMPLETE` for ANY phrase containing a camera/radio keyword with no number — including a pure identity declare like `"cámara RunCam"`. Live-tested against the orchestrator before writing formal tests, this silently intercepted identity declares with a confusing "indica la masa..." prompt instead of registering the identity. Fixed by requiring an explicit mass/weight word (`masa`/`peso`/`pesa`/`mass`/`weight`) before returning `INCOMPLETE` — a bare subject mention with neither a number nor a mass word now correctly returns `NONE` and falls through to the identity-declare grammar untouched. Locked by `test_t7_parser_never_intercepts_bare_identity_phrase`.

## 8. Tests

### Added (`tests/test_mission_mass_energy_b1.py`, 14 tests)

| ID | Tests | Covers |
|---|---|---|
| T1 | `test_t1_camera_mass_mirrors_and_raises_total_mass` | Writer mirror + calc engine sum |
| T2 | `test_t2_radio_mass_adds_both_sum` | Both masses sum correctly |
| T3 | `test_t3_clearing_mass_drops_mirror_and_regresses_total` | Clear path |
| T4 | `test_t4_double_count_warning_present_when_both_nonzero`, `test_t4_double_count_warning_absent_when_either_zero` | P1 warn insight |
| T5 | `test_t5_grammar_sets_mass_with_declared_source`, `test_t5_grammar_radio_mass_also_works` | End-to-end IDLE grammar |
| T6 | `test_t6_grammar_refuses_when_target_absent_no_stub` | Honest refuse, no auto-create |
| T7 | `test_t7_identity_only_declare_never_sets_mass`, `test_t7_parser_never_intercepts_bare_identity_phrase` | Never-invent guarantee + the bug fix regression |
| T8 | `test_t8_continuity_top_suggestion_is_declare_camera_mass_when_missing` | Ladder step d |
| T9 | `test_t9_next_hole_is_declare_radio_mass_after_camera_mass_set` | Ladder step e |
| T10 | `test_t10_neutral_project_increase_payload_still_available` | Regression |
| T11 | `test_t11_mission_intent_both_masses_set_soft_margin_never_increase_payload` | Full ladder end state |

### Updated (pre-existing, intent-preserving)

`tests/test_continuity_mission_intent_b1.py` — 2 tests (§5).

### Executed

```
python -m pytest tests/test_mission_mass_energy_b1.py -q          → 14 passed
python -m pytest tests/test_continuity_mission_intent_b1.py -q    → 17 passed
python -m pytest -q                                                 → 3058 passed, 1 skipped
```

No UI files touched — `ui/spatial-board` vitest suite not re-run (unaffected).

## 9. Out of scope (unchanged, named debt per IC §4)

`power_w`→autonomy/draw coupling (follow-on Buy) · `library/cameras` cited bags (needs Engineer cite rows) · VTX identity (parked) · P2/P3 `payload_kg` displace (only if P1 smoke hurts) · plate-box/Path N/HD-* (parked) · `payload_bay`/`arm` mass (not this Buy) · lock #9c/9d (documented gaps, §4).

## 10. Remaining risks

None identified. The one bug found (§7) was caught via direct empirical testing against the real orchestrator before any formal test was written, and is now locked by a dedicated regression test. `payload_kg` was never read/written/zeroed by any new code — verified by grepping every new function for `payload_kg` (none found outside the pre-existing insight/warn read).
