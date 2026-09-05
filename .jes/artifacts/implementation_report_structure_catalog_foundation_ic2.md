# Implementation Report — Structure Catalog Foundation IC-2 (bind + BOM + diverge)

**Project:** Jarvis
**Date:** 2026-09-04
**Implementer:** Claude Code
**IC:** [implementation_contract_structure_catalog_foundation_ic2.md](implementation_contract_structure_catalog_foundation_ic2.md)
**Baseline:** IC-1 landed · suite closed at 2177

---

## Files changed

- `src/jarvis/core/catalog_bind.py` — new `bind_frame_from_catalog(sku, *, library=None, base=None) -> ComponentSpec`, mirroring `bind_esc_from_catalog`/`bind_battery_from_catalog`, but computing `completeness`/`missing_fields` via `_frame_completeness` over the projected props (not a hardcoded `"high"`) so the two IC-1 seed rows with no stated `material` (TBS) honestly project as `"medium"`, not a fabricated `"high"`. New `_DIVERGED_FRAME_NAME` constant. New frame branch in `invalidate_diverged_catalog_refs`: clears `catalog_ref` (and renames) when the bound SKU no longer exists in the library, when the component's own `mass_kg`/`size_class_inch` no longer match the live `FrameSpec`, or when `structure_mass_override_kg` diverges from the component's own `mass_kg`.
- `src/jarvis/core/component_writers.py` — `set_frame_material` gained keyword-only `catalog_ref=None`/`component_name=None`. Every existing positional call site is unaffected (defaults preserve today's exact behavior: a fresh `ComponentSpec` is always built, so a free-text call after a bind silently clears the prior ref — verified, not just assumed, in `test_set_frame_material_free_text_after_bind_clears_ref`).
- `src/jarvis/core/project_closure.py` — `_bom_sku_resolved` gained a `"frame"` branch (`default_library.has_frame(sku)`), one line, same shape as the existing motor/battery/propeller/esc branches.
- `tests/test_catalog_bind_v1.py` — new tests (below), reusing the file's existing `_closed_project` fixture.

No edits to `engineering_readiness.py` (evidence builders, gap types, `_derive_subsystem_verdict`, `_derive_overall`), `acquisition_brief.py`, `orchestrator.py` (beyond what claim hygiene already landed — zero new touches this IC), `library/frames/_datos.json` (read-only, seed unchanged), `frame_class_compatibility_state`, or any Continuity/CLI claim-copy string.

## Behavior changed

- `bind_frame_from_catalog(sku)` now exists as a deterministic, test-callable API — no production caller (no CLI, no orchestrator, no assist), exactly matching ESC's/battery's/propeller's own current posture.
- `set_frame_material(..., catalog_ref=..., component_name=...)` can now persist a bound SKU's identity into `components["frame"]`; the mass mirror into `structure_mass_override_kg` goes through the same single path as free text — no second mass rule was added (unlike motor's 2A: frame mass counts identically whether bound or free-text, confirmed in the IC-1/investigation finding and unchanged here).
- BOM: a bound, live frame SKU now resolves `sku_resolved=True` (via `_bom_identity_suffix`, already generic), rendering `[sku]` the same way motor/battery/propeller/esc already do. A bound SKU later removed from the library resolves `False` (frankenstein-safe).
- `invalidate_diverged_catalog_refs` now also reconciles frame: SKU-vanished, mass-diverged, class-diverged, or params-mirror-diverged all clear `catalog_ref` and rename to `"frame (parámetros divergentes)"` — properties themselves are left untouched (no fallback needed, since free-text physics already treats any declared mass/class the same way regardless of provenance).
- Confirmed unchanged: Structure A's LEVEL A class screening runs identically over a catalog-bound frame's projected `size_class_inch` as it does over a free-text one — `test_bound_frame_still_runs_level_a_class_screening` binds `armattan_rooster_5in` (5″) against a 10″ propeller and confirms `GAP-FRAME-PROP-SIZE` fires and `structure` reads `INCOMPLETE`, with zero new gap-builder code.
- `catalog_bound` for frame remains outside the `_derive_subsystem_verdict` PASS conjunction — unchanged, unproposed.

## Tests added/updated

`tests/test_catalog_bind_v1.py`: `test_bind_frame_from_catalog_projects_mass_and_class`, `test_bind_frame_from_catalog_material_absent_is_honest_not_invented`, `test_bind_frame_from_catalog_unknown_sku_raises`, `test_bind_frame_from_catalog_applies_into_project_state`, `test_set_frame_material_free_text_after_bind_clears_ref`, `test_bom_sku_resolved_frame_true_for_live_sku_false_for_missing`, `test_invalidate_diverged_catalog_refs_frame_mass_diverges`, `test_invalidate_diverged_catalog_refs_frame_class_diverges`, `test_invalidate_diverged_catalog_refs_frame_no_op_when_unchanged`, `test_invalidate_diverged_catalog_refs_frame_sku_removed_from_library`, `test_bound_frame_still_runs_level_a_class_screening`.

## Tests executed

- Targeted: `pytest tests/test_catalog_bind_v1.py -q` → 25 passed.
- Full suite: `pytest -q` → **2188 passed** (2177 baseline + 11 new tests), zero failures, zero skipped, zero weakened.

## Residual (per §7 of the IC)

- **IC-3** (assist/`ayúdame a elegir` for frame) remains **not authorized** — no code toward it was written.
- Propeller/ESC divergence-clearing parity remains out of this IC (still only motor/battery/frame covered; propeller and ESC divergence-clearing are pre-existing gaps, unrelated to this thread, not touched).
- Layout params / CAD / FEA remain out, unaffected.
- No assist/pick UX exists yet for frame — binding is reachable only via direct API calls (tests), the same posture ESC has had for months with zero production regressions.
