# Implementation Report — Wizard vigilancia / mission nudge at SYSTEM_DEFINITION (`B1-wizard-mission-nudge`)

**IC:** `implementation_contract_wizard_mission_nudge_b1.md`
**Implementer:** Claude Code
**Date:** 2026-09-16
**Checkpoint:** package `0.4.1` (unchanged) · suite **2993 passed, 1 skipped** (was 2985) · UI unaffected (no UI files touched)

---

## 1. Scope delivered

Exactly the locked scope — a suggest-only, one-line mission nudge appended to `SystemDefinitionSession.start()`'s known-architecture step-0 A/B/C message, shown iff the project's `objective`/`restrictions` text signals mission intent AND `cameras`/`radio_module` aren't already declared. No LLM, no new session mode/schema field, no Continuity/SuggestionEngine edits, no auto-added blocks, no version bump, no `workspace/` mutation (tests-only; all Buys in this cycle were verified via a real `JarvisOrchestrator(workspace_root=tmp_path)` in a temp directory, never the live `workspace/` tree).

## 2. Files changed

| File | Change |
|---|---|
| `src/jarvis/core/reasoning_layer.py` | New `mission_intent_text_signal(objective, restrictions) -> bool` — the path-(A)-only half of `mission_intent_active`, extracted so a caller can require "mission text present" without pulling in path (B)'s component-presence trigger. `mission_intent_active` now calls it internally (byte-identical truth table, confirmed by the untouched `B1-continuity-mission-intent` test suite still passing). |
| `src/jarvis/core/system_definition_session.py` | New module-level import of `mission_intent_text_signal`; new locked `_MISSION_NUDGE_LINE` constant; new `_mission_nudge_applies(project_state)` helper (text signal AND neither `cameras` nor `radio_module` already declared); `start()`'s known-architecture branch now conditionally appends the nudge line to the step-0 message. The unknown-domain branch (`arch is None`, which skips straight to step 1's free-block list — there is no A/B/C to nudge toward there) is untouched. |
| `tests/test_wizard_mission_nudge_b1.py` (new) | 8 tests, T1–T5 (see §5). |

## 3. Where the nudge is wired (lock #2) and the "definir sistema" re-entry question

`SystemDefinitionSession.start()` has exactly **one** call site in the whole codebase: `orchestrator.py`'s `_handle_interactive_request`, immediately after a successful `create_project` (`orchestrator.py:6819`). Grepped for a `"definir sistema"` intent/grammar handler — **none exists**. The only occurrence of that phrase anywhere in `src/` is as copy text inside `SystemDefinitionSession.answer()`'s escape-word response (`"Escribe 'definir sistema' cuando quieras"`), which is never actually parsed back into a call to `.start()` by any orchestrator checkpoint. This is a pre-existing gap unrelated to this Buy — reported per the IC's own request ("report whether it does"), not fixed (out of scope). Practical consequence: the nudge fires on the one real path that exists today (immediately post-`create_project`); if a future Buy ever wires a real `"definir sistema"` re-entry to call `.start()` again, the nudge will automatically apply there too with zero additional code, since the check lives inside `.start()` itself.

## 4. The nudge gate and copy

```python
_MISSION_NUDGE_LINE = (
    "Si tu misión necesita cámara o radio/enlace, elige B para añadirlos "
    "ahora (luego 'cámara' / 'radio')."
)

def _mission_nudge_applies(project_state) -> bool:
    components = project_state.design_properties.components or {}
    if any(key in components for key in ("cameras", "radio_module")):
        return False
    restrictions = (project_state.current_parameters or {}).get("restrictions")
    return mission_intent_text_signal(project_state.objective, restrictions)
```

**Design note on the suppression condition** (not spelled out verbatim in the IC's lock #3 sentence, resolved via the IC's own required test T3): lock #3 says to skip the nudge when `mission_intent_active` is true *only because* `cameras`/`radio_module` already exist — trivially satisfied by using the text-only signal as the sole trigger. But T3 additionally requires suppressing the nudge when the objective **is** mission-like **and** `cameras` is **already** declared — i.e. "already handled, stop nudging" takes priority over "text still says vigilancia." Implemented `_mission_nudge_applies` to check already-declared presence **first** (either `cameras` **or** `radio_module** alone is enough to suppress — the user has engaged with mission payload, no more "escribe B" spam needed for either), and only fall through to the text check when neither exists yet. Verified empirically against both a live `dron-de-vigilancia-doméstico`-shaped fixture (T3 — nudge suppressed) and a fresh vigilancia project with no components yet (T1 — nudge shown).

## 5. Empirical verification (before writing tests)

Real `JarvisOrchestrator(workspace_root=tmp_path)` in a temp directory (never the live `workspace/`):

```
objective="dron de vigilancia doméstico" → step-0 message includes:
  "Si tu misión necesita cámara o radio/enlace, elige B para añadirlos ahora (luego 'cámara' / 'radio')."

objective="dron de prueba" → message unchanged from pre-Buy shape, no nudge line.

objective="dron de vigilancia doméstico" + cameras already declared (medium) → no nudge line.
objective="dron de vigilancia doméstico" + radio_module already declared (low) → no nudge line.

objective="dron de vigilancia doméstico" → answer("a") → components =
  {motors, propellers, esc, battery, frame, flight_controller, sensors}
  — no "cameras", no "radio_module" (nudge never auto-adds anything).

objective="dron de vigilancia doméstico" → answer("b") → answer("cámara") → answer("listo")
  → "cameras" present (identity rules from B1-mission-payload-identity fire unchanged).
```

Full suite run after the change (before adding the new test file) showed **0 regressions** — every pre-existing `SystemDefinitionSession` test (including the ones asserting the exact literal step-0 message text for neutral objectives) still passed unmodified, confirming the nudge is purely additive for the mission-signal case.

## 6. Tests

### Added (`tests/test_wizard_mission_nudge_b1.py`, 8 tests)

| ID | Tests | Covers |
|---|---|---|
| T1 | `test_t1_vigilancia_objective_shows_nudge`, `test_t1_camera_english_objective_shows_nudge` | Mission-text objective (Spanish + English) shows the nudge |
| T2 | `test_t2_neutral_objective_excludes_nudge` | Neutral objective — nudge absent; full message asserted byte-for-byte against the pre-Buy shape |
| T3 | `test_t3_cameras_already_declared_suppresses_nudge_despite_mission_objective`, `test_t3_radio_module_already_declared_suppresses_nudge` | Already-declared `cameras`/`radio_module` suppresses the nudge even with a mission-like objective |
| T4 | `test_t4_restrictions_alone_carry_mission_keyword_shows_nudge` | `restrictions`-only signal (objective neutral) still shows the nudge |
| T5 | `test_t5_option_a_after_nudge_still_applies_base_architecture_only`, `test_t5_option_b_after_nudge_can_still_add_camera_identity_rules_unaffected` | **A** after the nudge stubs the base 7 components only (no auto camera/radio); **B** → `cámara` still resolves via the unaffected `B1-mission-payload-identity` rules |

### Executed

```
python -m pytest tests/test_wizard_mission_nudge_b1.py -q  → 8 passed
python -m pytest -q                                         → 2993 passed, 1 skipped
```

No UI files touched — `ui/spatial-board` vitest suite not re-run (unaffected by this Buy).

## 7. Out of scope (unchanged, named debt per IC §4)

`SuggestionEngine`'s `increase_payload` on `simular` (queue #4) · `propellers ↔ motors` evidence (queue #3) · more identity rules (queue #5) · `library/cameras` physics bags (parked) · plate-box/HD-* (parked physical).

## 8. Remaining risks

None identified. The refactor to `reasoning_layer.mission_intent_active` (splitting out `mission_intent_text_signal`) preserves its exact prior truth table — confirmed by the full `B1-continuity-mission-intent` test suite (`tests/test_continuity_mission_intent_b1.py`) still passing unmodified. The pre-existing "definir sistema" copy-without-a-handler gap (§3) is documented but not fixed, per the IC's own scope boundary.
