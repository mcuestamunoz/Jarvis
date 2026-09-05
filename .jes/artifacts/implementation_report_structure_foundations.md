# Implementation Report — Structure Foundations (claim copy)

**Project:** Jarvis
**Date:** 2026-09-04
**Implementer:** Claude Code
**IC:** [implementation_contract_structure_foundations.md](implementation_contract_structure_foundations.md)
**Baseline:** tag `v0.3.6` + claim hygiene + control parity in tree · suite closed at 2164

---

## Files changed

- `src/jarvis/core/project_closure.py` — `_bom_completeness_tail` extended: for `key == "frame"` with a `project_state` argument provided, reads the existing `frame_class_compatibility_state(project_state)` (Structure A's own predicate, not re-derived) and appends `" — compatibilidad de clase nivel A pendiente"` (missing) or `" — clase incompatible nivel A"` (incompatible); `not_required`/`class_compatible` keep the plain tail. `format_bom_lines` gained an optional `project_state=None` parameter, threaded through to the helper — omitting it (existing callers) keeps prior byte-identical output.
- `src/jarvis/core/orchestrator.py` — `format_bom_lines(bom)` call in `build_startup_context` now passes `project_state` (already in scope).
- `src/jarvis/workspace/render_views.py` — `render_sistema`'s `format_bom_lines(bom)` call now passes `state` (already in scope).
- `src/jarvis/core/project_continuity.py` — new `_frame_class_gap_live(readiness)` predicate (reads `readiness.gaps` for `GAP-FRAME-SIZE-MISSING`/`GAP-FRAME-PROP-SIZE`, never re-derives the LEVEL A screening) and one new situation branch, inserted after the existing autonomy/`margin_claim_weak` guards and before the plain `sim_status=="pass"` fallback: `elif sim_status == "pass" and _frame_class_gap_live(readiness): situation = _FRAME_CLASS_GAP_SITUATION`.
- `tests/test_project_closure_v1.py`, `tests/test_project_continuity.py` — new tests (below).

No edits to `_frame_completeness`, `classify_component`, `component_presence_tier`, `frame_class_compatibility_state`, `frame_size_blocks_structure_complete`, any `GAP-FRAME-*` gap type/severity/blocks, `_structure_evidence`, `_derive_subsystem_verdict`, `_derive_overall`, `CatalogRef`, or `library/`.

## Behavior changed

- **BOM:** a `frame` entry in the `defined` bucket now shows `(high — compatibilidad de clase nivel A pendiente)` when the propeller diameter is known and no `size_class_inch` is declared, or `(high — clase incompatible nivel A)` when a class is declared but too small for the bound propeller. When class is compatible, not required (no propeller declared yet), or when `project_state` is omitted, the tail stays plain `(completeness)` — byte-identical to before.
- **Continuity situation:** PASS + a live `GAP-FRAME-SIZE-MISSING`/`GAP-FRAME-PROP-SIZE` on `readiness` now reads *"Comprobación de empuje: PASS. Compatibilidad de clase (nivel A) pendiente."* instead of *"Diseño validado en simulación (PASS)..."* — even when `architecture_progress` is `None` (the gate reads the Gap Registry directly). PASS with no frame-class gap (or `readiness` omitted) is unchanged.
- **Not changed:** architecture `n/n` counters (already correctly gated, per the investigation), `frame_next_missing_step`/`_question` copy, ERF subsystem verdicts, gap severities/blocks, `ASSEMBLY_READY` eligibility, `_frame_completeness` bucket assignment (a frame with a live class gap still lands in the `defined` BOM bucket — only its displayed tail changed).

## Tests added/updated

- `test_project_closure_v1.py`: `test_bom_frame_class_missing_gets_pending_suffix`, `test_bom_frame_class_incompatible_gets_incompatible_suffix`, `test_bom_frame_class_compatible_stays_plain`, `test_bom_frame_suffix_absent_without_project_state` (backward-compat guard; motors line unaffected, verified in the flight-controller-suffix test already in this file).
- `test_project_continuity.py`: `test_situation_frame_class_gap_never_says_diseno_validado`, `test_situation_frame_prop_size_gap_uses_same_locked_sentence`, `test_situation_diseno_validado_unchanged_when_readiness_has_no_frame_gap`.

## Tests executed

- Targeted: `pytest tests/test_project_closure_v1.py tests/test_project_continuity.py -q` → 35 passed.
- Full suite: `pytest -q` → **2171 passed** (2164 baseline + 7 new tests), zero failures, zero skipped, zero weakened.

## Residual risks / documented debt

- **N1 (per investigation review):** the main `estado` path was already architecture/ERF-honest for frame-class gaps (`Arquitectura n/n` and the readiness block's `Structure` verdict already correctly showed `INCOMPLETE`/non-4/4). This IC closes the two remaining surfaces (BOM tail, Continuity situation) that still overstated it — no other rendering path was found to disagree.
- **Frame catalog and declared layout params remain named options**, not pursued (per investigation §E) — a frame catalog would need a `CatalogRef.family` schema change (`"frame"` is not a valid value today) and a new `library/frames/` catalog; layout params (wheelbase/arm/clearance) have no consumer today and risk brushing the forbidden tip-clearance-physics line. Both stay options for a later, separately Engineer-named thread.
- The broader "PASS + any live gap" Continuity situation pattern (of which frame-class and margin are two named instances) is not audited generally in this IC — only the frame-class instance was closed, per the investigation's explicit scope narrowing (not reopening claim hygiene as a workstream).
