# Implementation Report — Structure B additive enrichment B2 (`thickness_mm` arms-only)

**IC:** [implementation_contract_structure_b_thickness_arms_b2.md](implementation_contract_structure_b_thickness_arms_b2.md)
**Implementer:** Claude Code
**Date:** 2026-09-05
**Baseline:** Structure B Fase 1 + G-N1 CLOSED @ suite 2229

---

## Files changed

- `src/jarvis/knowledge/library.py` — `FrameSpec.arm_thickness_mm: float | None = None` (additive field, next to `arm_material`). `_frame_from_raw` parses `data.get("arm_thickness_mm")` the same way as `wheelbase_mm` (float-or-None, never invented).
- `library/frames/_datos.json` — added `arm_thickness_mm` to all four seed rows, each value re-verified directly against the row's own cited `source_url` (fetched live, quoted below) rather than trusted from the investigation summary alone:
  - `tbs_source_one_v5_5in`: **6mm** ("Arm Thickness: 6mm", racedayquads.com spec list).
  - `tbs_source_one_v5_1_7in_dc`: **6mm** ("Fuselage Thickness: 2.5mm bottom plate, 2mm top/middle plate, 6mm arms", progressiverc.com).
  - `iflight_xl7_v4_7in`: **5mm** ("5mm arms, 1,5mm vertical side plates", fpv24.com) — not 4mm; verified from source, not assumed.
  - `armattan_rooster_5in`: **4mm** ("Arm Thickness — 4mm", armattanquads.com).
  Each row's `source_note` extended to mention the arm thickness; no `plate_thickness_mm` (or any plate-thickness field) added anywhere, per the locked non-goal.
- `src/jarvis/core/catalog_bind.py` — `frame_part_specs_from_catalog`'s inner `_part` helper gained an optional `thickness_mm` parameter: the creation gate is now `count is None and material is None and thickness_mm is None` (was count/material only), and when set it adds a `thickness_mm` `PropertyValue` (`unit="mm"`, `source="declared"`). Only the `frame_arm` call site passes `spec.arm_thickness_mm`; `frame_plate`/`frame_cage`/`frame_standoff` call sites are unchanged (no thickness ever reaches them).
- `src/jarvis/domains/aerial.py` — `_props_from_part_clause(clause, key=None)` gained a `key` parameter and, only when `key == FRAME_ARM_KEY`, matches `_ARM_THICKNESS_MM_PATTERN` (`\d+([.,]\d+)?\s*mm\b`) scoped to that clause and emits `thickness_mm`. `extract_all_frame_part_properties` now passes the matched `key` through. Existing `count` regex (`\b(\d+)\b`) already cannot match the digits inside `"6mm"` (no trailing word boundary between digit and letter — confirmed with a quick interpreter check), so no spurious `count` is created from an arm-thickness-only phrase.
- `src/jarvis/core/project_closure.py` — `_frame_part_sublines` now also reads `thickness_mm`; the "skip if nothing to show" gate is `not count_bit and not material_bit and not thickness_bit`. Rendering: thickness alone → `" — 6mm"` (acts like the material slot); thickness alongside material → appended as `", 4mm"` after the material — matching the IC's two example shapes exactly (`└ arm — 6mm`, `└ arm ×4 — fibra de carbono, 4mm`).
- `src/jarvis/core/component_writers.py` — **no change**. `upsert_frame_part` merges an arbitrary `dict[str, PropertyValue]` and `_structure_part_completeness` only inspects `"count"`/`"material"` — both already generic enough to carry `thickness_mm` through the free-text path without modification, confirmed by reading the code before touching anything (§3.5 lock: thickness must never make completeness `"high"` by itself — this is structurally true today since the completeness function never looks at `thickness_mm`).
- `src/jarvis/core/orchestrator.py` — **no change**. Both call sites (`_apply_inferred_component_spec`, the parts-only follow-up branch) already forward whatever `extract_all_frame_part_properties` / `_props_from_part_clause` returns generically to `upsert_frame_part`.

## Tests

New/updated, all under the existing test files for this feature area (no new file):

- `tests/test_catalog_foundation_v1.py`: `test_frame_loader_parses_arm_thickness_mm` (T1a), `test_frame_loader_arm_thickness_mm_omitted_when_absent` (T1b, synthetic minimal seed row).
- `tests/test_frame_parts_graph_v1.py`:
  - `test_frame_part_specs_from_catalog_tbs_row_has_arm_thickness_only` (T2, replaces the now-stale `..._tbs_row_has_no_parts` — TBS now sources arm thickness, the IC's own named regression target).
  - `test_frame_part_specs_from_catalog_armattan_has_all_four_parts` extended with a `thickness_mm≈4.0` assertion (T3).
  - `test_frame_part_specs_from_catalog_no_seed_row_puts_thickness_on_plate` (T7, all four seed SKUs).
  - `test_bom_thickness_only_arm_still_renders_subline`, `test_bom_thickness_and_material_and_count_all_render` (T5, both IC example shapes verbatim).
  - `test_structure_pass_and_evidence_unchanged_with_vs_without_arm_thickness` (T6 twin).
- `tests/test_frame_parts_freetext_gn1.py`: `test_extract_arm_clause_thickness_mm`, `test_wheelbase_mm_alone_never_becomes_arm_thickness`, `test_plate_clause_with_mm_never_extracts_thickness`, `test_arm_clause_thickness_and_material_together` (T4).

**Regression fixes (pre-existing tests whose premise "TBS rows have zero part fields" the IC explicitly flagged as changing):**
- `tests/test_frame_catalog_bind_ux.py::test_frame_pick_tbs_row_creates_no_part_children` → renamed `..._creates_only_arm_thickness_child`, now asserts `frame_plate`/`cage`/`standoff` absent, `frame_arm` present with `thickness_mm≈6.0` and no `material`/`count`.
- `tests/test_idle_frame_rebind_b2.py::test_rebind_to_tbs_clears_stale_armattan_children` → updated to assert only `frame_arm` remains after rebinding Armattan→TBS (was `[]`), and that it carries TBS's own fresh `thickness_mm=6.0` with **no** stale Armattan `material` — proving `clear_frame_part_children` + fresh catalog projection, not a merge of old data.

No assertion was weakened in either fix — both now assert *more* (the new honest state) than before, not less.

Executed: `python -m pytest -q` → **2286 passed**, 0 failed (baseline 2229 + 4 renamed/extended pre-existing regression fixtures + remainder new).

## Behavior changed

- Four catalog seed rows now carry a sourced `arm_thickness_mm`.
- `frame_part_specs_from_catalog` for `tbs_source_one_v5_5in` and `tbs_source_one_v5_1_7in_dc` now returns a `frame_arm` child (thickness only) where it previously returned `{}` for those rows — display/enrichment only, no material/count fabricated, `frame_plate` still absent for both (no plate thickness in this IC).
- `iflight_xl7_v4_7in`'s `frame_arm` (previously absent since it had no material/count either) now exists with `thickness_mm=5.0` only.
- `armattan_rooster_5in`'s existing `frame_arm` gains `thickness_mm=4.0` alongside its existing material.
- BOM sub-lines under `frame` can now show a thickness suffix, and a part with *only* thickness (no material/count) now renders a line where it previously would have been skipped.
- Free-text arm clauses containing an mm value (e.g. `"brazos 6mm"`) now populate `frame_arm.properties["thickness_mm"]`; non-arm clauses (plate, bare wheelbase) are unaffected — verified explicitly.
- No change to: `mass_kg`/Σ mass, `_structure_evidence`, `_frame_completeness`, `_structure_part_completeness`'s `"high"` rule, ASSEMBLY_READY, Structure PASS gating, IDLE rebind clearing, node types/`parent_key`, version.

## Non-goals honored

No per-part mass, arm length, plate/cage/standoff thickness, Σ mass, density-from-thickness, geometry, new node types, PASS widening, ASSEMBLY_READY change, or version bump — confirmed by `git diff --stat` (only the five files listed above plus tests touched) and by T7/T6 passing.

## Remaining risks / notes for review

- `iflight_xl7_v4_7in`'s cited page states **5mm** arm thickness, not 4mm — the IC's own decision table only pre-verified "TBS 6mm, Armattan 4mm" and left iFlight/TBS-7in for direct verification from their cited pages; I fetched both live pages before writing the seed value rather than guessing. Worth a quick sanity glance since it wasn't a value named in the IC text itself.
- The two pre-existing tests whose premise changed (`test_frame_catalog_bind_ux.py`, `test_idle_frame_rebind_b2.py`) were not listed in the IC's own "Files (expected)" table (only `tests/…` generically) — flagging explicitly since they weren't part of the T1–T7 list but were necessary for full-suite green without weakening any assertion.
