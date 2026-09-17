# Implementation Report — SYSTEM_DEFINITION B routing vs global intercept (`B1-system-definition-b-routing`)

**IC:** `implementation_contract_system_definition_b_routing_b1.md`
**Implementer:** Claude Code
**Date:** 2026-09-17
**Checkpoint:** package `0.4.1` (unchanged) · suite **3068 passed, 1 skipped** (was 3058) · UI unaffected

---

## 1. Scope delivered

Exactly the locked scope — while `OrchestratorMode.SYSTEM_DEFINITION` is active, block-collection now owns the turn until `listo`/escape: the global component intercept no longer steals a block name that happens to also be a `ComponentRule` keyword, and a meta "add more blocks" phrase no longer gets appended as a junk custom block. No changes to `ComponentRule`s/extractors/completeness ladders, no removal of free-text custom blocks, no Continuity rewrite, no version bump, no `workspace/` mutation (tests-only).

## 2. Root cause (confirmed exactly as the IC's parent review described)

`_interceptable_component_specs` (`orchestrator.py`) already excluded `CREATE_PROJECT_INTERACTIVE`, `DEFINE_MISSING_PARAMETERS`, and `ITERATE_INTERACTIVE` — but **not** `SYSTEM_DEFINITION`. The "Global component intercept" block in `_handle_user_text_inner` runs *before* the `SYSTEM_DEFINITION` mode dispatch (line ~1617), so when a user typed a block name that also matches a real `ComponentRule` (`"payload"` → `payload_bay`, `"manipulador"` → `arm`, etc. — all four added by the immediately-prior `B1-extended-identity-rules`), it got intercepted into `_handle_component_description` and never reached `SystemDefinitionSession.answer()` at all. Separately, `_handle_custom_blocks`'s free-text fallback honestly registered any unrecognized phrase (including a meta phrase like `"añadir bloques"`) as a junk custom block with no component expansion.

## 3. Files changed

| File | Change |
|---|---|
| `src/jarvis/core/orchestrator.py` | `_interceptable_component_specs` gained a fourth mode exclusion: `if session.mode == OrchestratorMode.SYSTEM_DEFINITION: return []`. `_should_intercept_component`'s own docstring updated to document all four exclusions (previously only listed two). |
| `src/jarvis/core/system_definition_session.py` | New `_META_ADD_MORE_PHRASES` frozenset (exact tuple in §4); `_handle_custom_blocks` checks it (after `_DONE_WORDS`, before `normalize_block_alias`) and returns a no-op reprompt instead of appending to `custom_blocks`. |
| `tests/test_system_definition_b_routing_b1.py` (new) | 10 tests, T1–T7 (see §6). |

## 4. Exact meta-phrase tuple (lock #4)

```python
_META_ADD_MORE_PHRASES = frozenset({
    "añadir bloques", "anadir bloques", "añadir bloque", "anadir bloque",
    "add blocks", "add block",
    "más bloques", "mas bloques",
    "otro bloque", "otra vez",
})
```

Matched against `user_input.strip().lower()` — the same normalization `_handle_custom_blocks` already uses for `_DONE_WORDS` and block-alias lookup (no new normalization scheme introduced). Added `"anadir bloque"` (singular, no accent) alongside the IC's own literal list for symmetry with `"añadir bloque"` — harmless, same spirit.

## 5. Lock #5 and #7 — confirmed unaffected / no action needed

- **Lock #5 (step 0 unchanged)**: `_OPTION_B`'s own substring match on `"añadir"` was not touched — verified live that `"añadir bloques"` at **step 0** still correctly enters mode B (unchanged from before this Buy). The new `_META_ADD_MORE_PHRASES` check only exists inside `_handle_custom_blocks` (step 1), never step 0's `_handle_choice`.
- **Lock #7 (Continuity footer)**: no separate suppression was needed — once lock #2's intercept-gate fix removes the mid-B component save entirely, there is no `status=ok` mid-B path left to produce a misleading Continuity-adjacent footer. No new subsystem invented, per the lock's own instruction.

## 6. Empirical verification

```
Fresh project -> SYSTEM_DEFINITION step 0 -> "b" -> step 1:
  "payload"      -> "Bloque 'payload' añadido..."       (was: "Estoy definiendo payload_bay...")
  "manipulador"  -> "Bloque 'manipulation' añadido..."
  "ruedas"       -> "Bloque 'actuation' añadido..."
  "gearbox"      -> "Bloque 'transmission' añadido..."
  "añadir bloques" -> "¿Qué bloque quieres añadir? (uno a uno, 'listo' para terminar)"
                      custom_blocks unchanged (still [])
  "payload" (right after the meta phrase) -> still "añadido" correctly

After "listo": components = {motors, propellers, esc, battery, frame,
  flight_controller, sensors, payload_bay, arm, wheels, gearbox} — all 11.

IDLE regression (session finished via Option A):
  "bahía de carga" -> status=ok, action=component_description_saved, payload_bay saved
  "cámara RunCam"  -> status=ok, cameras saved
```

Full suite run after each of the two fixes (intercept gate, then meta-phrase check) showed **0 regressions** at every step.

## 7. Tests

### Added (`tests/test_system_definition_b_routing_b1.py`, 10 tests)

| ID | Tests | Covers |
|---|---|---|
| T1 | `test_t1_payload_via_orchestrator_routes_to_block_not_component` | Root-cause fix, exact IC wording ("añadido", not "Estoy definiendo") |
| T2 | `test_t2_manipulador_via_orchestrator_routes_to_block` | Same for manipulator |
| T3 | `test_t3_ruedas_via_orchestrator_routes_to_actuation_block` | Alias path |
| T4 | `test_t4_gearbox_via_orchestrator_routes_to_transmission_block` | Alias path |
| T5 | `test_t5_meta_add_more_phrase_is_noop`, `test_t5_meta_phrases_english_and_variants_all_noop`, `test_t5_payload_still_works_right_after_meta_phrase` | Meta-phrase no-op, ES+EN variants, no side-effect on the next real block name |
| T6 | `test_t6_all_four_stubs_present_after_listo` | End-to-end stub creation |
| T7 | `test_t7_idle_freetext_identity_regression_unaffected`, `test_t7_idle_camera_identity_regression_unaffected` | IDLE global intercept still works post-session |

### Executed

```
python -m pytest tests/test_system_definition_b_routing_b1.py -q  → 10 passed
python -m pytest -q                                                 → 3068 passed, 1 skipped
```

No UI files touched — `ui/spatial-board` vitest suite not re-run (unaffected).

## 8. Out of scope (unchanged, named debt per IC §4)

Continuity copy while `system_defined=False` (residual UX, not this Buy) · auto-opening a component wizard after `listo` for the new stubs (optional follow-on, not requested) · `B1-mission-mass-energy` (separate, already implemented in a prior cycle this session) · identity keyword/`frame_arm` changes (untouched).

## 9. Remaining risks

None identified. The fix is a single added mode-exclusion (mirroring three pre-existing ones) plus a single frozenset membership check — both minimal, both directly traced to the exact root cause described in the IC's own parent review, and both verified live before and after formal tests were written.
