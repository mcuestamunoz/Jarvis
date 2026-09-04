# Implementation Report — Structure A N1 hotfix (override mirror from merged props)

**IC:** [implementation_contract_structure_a_n1_hotfix.md](implementation_contract_structure_a_n1_hotfix.md)
**Parent IC:** [implementation_contract_structure_a.md](implementation_contract_structure_a.md)
**Implementer:** Claude Code
**Date:** 2026-09-03

## Files changed

- `src/jarvis/core/component_writers.py` — `set_frame_material`'s `structure_mass_override_kg` mirror now reads from the **merged** `props.get("mass_kg")` instead of the `mass_kg` **argument**. A partial update (e.g. size or material only, `mass_kg=None`) that leaves an existing mass declaration in the merged component no longer deletes the override; the override is only popped when the merged frame genuinely has no `mass_kg`.
- `tests/test_frame_component.py` — two new regression tests: `test_set_frame_material_size_only_preserves_existing_mass_override` (size-only update on a 0.65 kg frame) and `test_set_frame_material_material_only_preserves_existing_mass_override` (material-only update on a 0.45 kg frame). Both confirm the override survives.
- `tests/test_structure_a.py` — `test_walk_pvc_5_pulgadas_preserves_existing_mass_override`: the literal reproduced walk (fresh 0.65 kg frame, iterate `"pvc 5 pulgadas"`) through the real wizard end to end — override stays 0.65, `size_class_inch` is written, and `CalculationEngine().build(...)`'s `total_mass_kg` is asserted identical before/after (the dual-truth symptom the IC named — component says 0.65 kg, physics silently switching to the structure-mass-factor fallback — is what this locks against).

## Behavior changed

Exactly as the IC's table specifies:
- `set_frame_material(state, 0.2, "pvc")` (explicit mass) — unchanged.
- `set_frame_material(state, None, "pvc", 5.0)` on a state with an existing `mass_kg=0.65` — override now stays `0.65` instead of being deleted.
- `set_frame_material(state, None, None)` on a state with no `mass_kg` at all — unchanged (still pops).
- `apply_components_delta`'s frame re-derive (`component_writers.py:539-544`) — verified unchanged: it always extracts `mass_kg` from `spec.properties` (the delta's own spec, or the pre-existing component re-applied for baseline normalization) and passes that explicit, non-`None` value into `set_frame_material` whenever the component has mass — so the merged `props["mass_kg"]` and the old argument-based value are identical there. No behavior change at that call site, confirmed by reading it and by the full suite staying green with zero new failures.

## Tests

- Added 3 tests (2 in `tests/test_frame_component.py`, 1 in `tests/test_structure_a.py`) — all pass.
- Executed: full suite — `python -m pytest -q` → **2143 passed**, 0 failed (baseline 2140 + 3 new).
- Re-ran `tests/test_frame_component.py` + `tests/test_structure_a.py` together (38 tests) before the full run — all green, including every pre-existing test in both files (`test_set_frame_material_mass_only_no_material_key`, the size-class/misfit/compatible tests from the parent IC, etc.) — confirming the fix didn't regress any explicit-mass path.

## Non-goals honored

No gap, Continuity, `_block_progress_status`, `_derive_overall`, `extract_frame_properties`, iterate-session, or orchestrator code touched — verified: this turn's edits were confined to exactly the three files in §5 (`component_writers.py`, `tests/test_frame_component.py`, `tests/test_structure_a.py`). No mass, density, or class invented — the fix only changes *which already-computed value* the mirror reads from (arg vs. merged dict); it introduces no new data source.

## Remaining risks

None identified. The fix is a single conditional's source change, the affected code path is narrow (one function, one block), and every caller shape named in the IC's table (explicit mass, size-only, material-only, no-mass, `apply_components_delta` re-derive) has a passing regression test.
