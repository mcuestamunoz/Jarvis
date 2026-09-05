# Implementation Report — Structure B Frame Assembly Physical Model B2 (plate multiplicity)

**IC:** [implementation_contract_structure_b_frame_assembly_physical_model.md](implementation_contract_structure_b_frame_assembly_physical_model.md)
**Implementer:** Claude Code
**Date:** 2026-09-05
**Baseline:** Parts Graph Fase 1 + G-N1 @ 2229 · arms `thickness_mm` B2 @ 2286 · suite 2286

---

## Files changed

- `src/jarvis/knowledge/library.py`:
  - New `PlateSeed` frozen dataclass: `label: str | None`, `thickness_mm: float | None`, `material: str | None` — verbatim-from-source display label, never a closed role vocabulary (investigation report §B7).
  - `FrameSpec.plates: list[PlateSeed] | None = None` (additive; existing `plate_count`/`plate_material` scalars kept as the legacy fallback, per N2).
  - `ComponentLibrary._frame_from_raw` now calls a new `ComponentLibrary._parse_plates(name, data.get("plates"))` staticmethod that parses the JSON list into `PlateSeed` entries, returns `None` when absent, and **raises `ValueError`** (not silent truncation) when the list has more than `_MAX_PLATES = 8` entries or isn't a list — this is the N7 bound enforced at load time.
- `library/frames/_datos.json` — curated `plates` list added to all four seed rows, exactly the entries locked in IC §3.2, each re-verified against the row's own `source_url` this session (not just copied from the IC text):
  - `tbs_source_one_v5_5in`: Top 2mm, Middle 2mm, Bottom 2.5mm
  - `tbs_source_one_v5_1_7in_dc`: Top/Middle 2mm, Bottom 2.5mm
  - `iflight_xl7_v4_7in`: "upper and lower plate" 2mm, "vertical side plates" 1.5mm
  - `armattan_rooster_5in`: Main Plate 4mm (material `fibra de carbono`), Top (LiPo) plate 2mm, Small front (top) plate 1.5mm, Small rear (top) plate 1.5mm
  - Every `source_note` updated to state the plate list is curated from the page's own spec list, not the full Included kit.
- `src/jarvis/domains/aerial.py`:
  - New `FRAME_PLATE_MAX_SIBLINGS = 8` constant, `frame_plate_key(index)` (0 → `"frame_plate"`, 1 → `"frame_plate_2"`, ... 7 → `"frame_plate_8"`) and `is_frame_plate_key(key)` helpers, placed next to the existing `FRAME_*_KEY` constants — the single source of truth both `catalog_bind.py` and `project_closure.py` now import, so the N7 bound is defined once.
- `src/jarvis/core/catalog_bind.py` — `frame_part_specs_from_catalog`:
  - `_part` helper gained a `label` parameter (emits a `label` `PropertyValue`, `unit=None`, `source="declared"`) and the creation gate now includes `label is not None`.
  - **N2 precedence:** when `spec.plates` is non-empty, the legacy `_part(FRAME_PLATE_KEY, "plate", spec.plate_count, spec.plate_material)` call is **not** made at all — plates are projected exclusively from `spec.plates`, one `_part(frame_plate_key(i), ...)` call per curated entry (index 0 → `frame_plate`, index ≥1 → ordinal sibling). When `spec.plates` is `None`/empty, the single legacy call remains, byte-identical to before this IC.
  - **N3:** each curated entry becomes its own `_part` call regardless of whether its `thickness_mm` matches another entry's (TBS's two 2mm entries — Top, Middle — become two distinct dict keys, never merged/deduped by value).
  - **N6 preserved verbatim:** every `_part`-created `ComponentSpec.completeness` stays hardcoded `"high"`, unchanged from before this IC (arm/cage/standoff and now plate siblings alike) — a comment now names this as known debt vs. `_structure_part_completeness` inline, per the IC's explicit instruction not to "fix" it incidentally.
  - A defensive `>FRAME_PLATE_MAX_SIBLINGS` `ValueError` also guards the projection call itself (belt-and-suspenders — the loader's own bound already makes this unreachable through the normal `ComponentLibrary` load path, but a test constructs a `FrameSpec` directly to exercise it — see T1's loader-level test, this is not that; no test exercises the catalog_bind-level guard since it's unreachable via the public loader).
- `src/jarvis/core/project_closure.py` — `_frame_part_sublines`:
  - Iteration order is now `"frame_arm"`, then every `frame_plate*` ordinal key from `frame_plate_key(0..7)` in order, then `"frame_cage"`, `"frame_standoff"` — replacing the old fixed 4-tuple (`_FRAME_PART_ORDER` removed, confirmed unreferenced elsewhere via `grep`).
  - When a part's `label` property is present, the display slot that `material` would otherwise fill renders the label instead (`" — {label}"`, thickness appended as `", {thickness}"` when present) — `material` is still stored on the `ComponentSpec` for provenance but not separately echoed once a label exists, matching the IC's own example lines exactly (verified: `└ arm — 6mm`, `└ plate — Top, 2mm`, `└ plate — Middle, 2mm`, `└ plate — Bottom, 2.5mm` reproduced live, see Tests below).
  - `label_word` is `"plate"` for any `is_frame_plate_key(key)` match — arm/cage/standoff keep their existing single-key labels unchanged.
- `src/jarvis/core/component_writers.py` — **no change.** `clear_frame_part_children` already removes by `parent_key == "frame"` scan (not the four locked keys directly, per its own docstring) — confirmed this already generically clears any number of ordinal plate siblings with zero code change; `upsert_frame_part` already merges an arbitrary properties dict, so `label`/multiple plate keys pass through unmodified.
- `src/jarvis/core/orchestrator.py` — **no change.** The one production call site (`for part_key, part_spec in frame_part_specs_from_catalog(...).items(): upsert_frame_part(...)`) already iterates the returned dict generically; ordinal plate keys are handled with zero code change.

## Tests

New/updated across the existing test files for this feature area (no new file), organized by IC §4 ID:

- **T1** — `tests/test_catalog_foundation_v1.py`: `test_frame_loader_parses_curated_plates` (TBS 5in → 3 `PlateSeed` entries, labels/thicknesses match §3.2), `test_frame_loader_plates_omitted_when_absent` (synthetic row, `plates is None`), `test_frame_loader_plates_over_max_rejected` (9-entry synthetic row → `ValueError` at load time, not truncation).
- **T2** — `tests/test_frame_parts_graph_v1.py`: `test_frame_part_specs_from_catalog_tbs_5in_arm_and_three_plates_no_cage_standoff` (replaces the now-stale `..._tbs_row_has_arm_thickness_only` — TBS 5in now also sources 3 plates, the IC's own named regression target vs. the arms-B2 IC).
- **T3** — same file: `test_frame_part_specs_from_catalog_armattan_has_arm_four_plates_cage_standoff` (replaces the stale `..._has_all_four_parts` — Armattan now has 7 part children, not 4).
- **T4 (N2)** — same file: `test_n2_plates_present_ignores_legacy_scalar_material_and_count` — a synthetic seed row sets both `plate_material`/`plate_count` scalars **and** a `plates` list; asserts projection reads only from `plates` (exactly one `frame_plate` key, no fifth/conflicting path, scalar value never leaks in).
- **T5 (N3)** — same file: `test_plate_multiplicity_never_merges_equal_thickness_siblings` — TBS 5in's Top/Middle (both 2mm) stay two distinct dict entries.
- **T6** — same file: `test_bom_renders_distinct_labeled_plate_lines_in_ordinal_order` — asserts the exact three BOM lines for TBS 5in, byte-for-byte matching the IC's example format.
- **T7 (twin)** — same file: `test_structure_pass_and_evidence_unchanged_with_vs_without_plate_siblings` — `_frame_completeness`/`_structure_evidence`/ERF Structure verdict identical with vs. without Armattan's 4 plate siblings present.
- **T8** — `tests/test_idle_frame_rebind_b2.py`: `test_rebind_to_tbs_clears_stale_armattan_children` updated (Armattan's "before" set is now 7 `frame_*` keys, not 4; "after" rebind-to-TBS set is `frame_arm`+3 ordinal plates, not just `frame_arm`; explicit assertion that `frame_plate_2`'s label is TBS's `"Middle"`, not a stale Armattan `"Top (LiPo) plate"`).
- **T9 (N4 — free-text stays OUT)** — `tests/test_frame_parts_freetext_gn1.py`: `test_freetext_multiple_plate_clauses_never_gain_ordinal_siblings` — a message naming two plates by different words (`"placa superior 2mm, placa inferior 2.5mm"`) still produces at most the single locked `frame_plate` key, never `frame_plate_2`, and never a `thickness_mm` on it (arms-only B2 lock re-confirmed).
- Helper coverage: `test_frame_plate_key_helpers_locked_bound` — `frame_plate_key`/`is_frame_plate_key`/`FRAME_PLATE_MAX_SIBLINGS` behave exactly per the N7 lock (8 max, no `frame_plate_top`-style key ever recognized).

**Regression fixes (pre-existing tests whose premise — "TBS/iFlight rows have no plate data" — this IC's own T2 explicitly names as changing):**
- `tests/test_frame_catalog_bind_ux.py::test_frame_pick_tbs_row_creates_only_arm_thickness_child` → renamed `..._creates_arm_thickness_and_curated_plates_no_cage_standoff`, now asserts the 3 TBS plate siblings by label alongside the unchanged arm-thickness-only assertions and the still-correct cage/standoff absence.

No assertion was weakened in any of the above — each now asserts *more* (the new, honest multi-plate state) than before, never less.

Executed: `python -m pytest -q` → **2294 passed**, 0 failed (baseline 2286 + net new/renamed regression fixtures).

## Behavior changed

- Four catalog seed rows now carry a curated `plates` list.
- `frame_part_specs_from_catalog` for all four SKUs now projects multiple `frame_plate*` ordinal siblings instead of at most one — TBS rows and iFlight (previously zero or one plate child) now show 2–4 plate children each, all display-only, all `parent_key="frame"`.
- BOM renders one `└ plate` line per plate sibling, in ordinal order, with the curated `label` in the display slot `material` previously used (material still stored, not separately echoed once a label exists).
- IDLE catalog rebind (`clear_frame_part_children`) now clears more `frame_plate_*` siblings than before on a re-pick — required zero code change since it already scans by `parent_key`, but the *number* of children it clears/creates per SKU changed, exercised explicitly by the updated T8.
- No change to: `mass_kg`/Σ mass (M0), `_structure_evidence`, `_frame_completeness`, `_structure_part_completeness`'s own rule, the `completeness="high"` catalog-projection hardcode (N6, deliberately preserved), ASSEMBLY_READY, Structure PASS gating/footnote, free-text extraction (still single-plate-key only, N4), node *type* set (`structure_part` only — no new type introduced), version.

## Non-goals honored

No closed role taxonomy (labels are verbatim strings, never matched/compared), no free-text multi-plate parsing, no auto-ingest of full "Included" kit lists (only the curated entries named in IC §3.2), no per-part `mass_kg`, no dims, no hardware, no Σ thickness/Σ mass, no cage/standoff multiplicity, no MEASURE/CAD/FEA, no PASS footnote wording change, no completeness-hardcode "fix," no version bump — confirmed by `git diff --stat` (only the four files listed above plus tests touched) and by the T7 twin passing.

## Remaining risks / notes for review

- The catalog-bind-level `>FRAME_PLATE_MAX_SIBLINGS` guard in `frame_part_specs_from_catalog` is currently unreachable through the public `ComponentLibrary` loading path (the loader's own `_parse_plates` bound already prevents any loaded `FrameSpec` from exceeding 8 entries) — it exists purely as defense-in-depth for a `FrameSpec` constructed directly (e.g. in a future test), and is untested for that reason (testing it would require bypassing the loader). Flagging so this isn't mistaken for a gap in T1's coverage — T1 covers the loader bound, which is the one path production code actually goes through.
- N6's completeness inconsistency (catalog path hardcodes `"high"`; the free-text/`upsert_frame_part` path recomputes via `_structure_part_completeness`, which would grade a label+thickness-only plate `"low"`) is unchanged, pre-existing since the arms-B2 IC, and explicitly named as debt not to fix here — worth a reader's awareness that a catalog-picked plate's *persisted* completeness (after `upsert_frame_part` runs in the orchestrator's pick flow) will actually be `"low"` for most of the new plate siblings (label+thickness only, no material/count), even though `frame_part_specs_from_catalog`'s own returned object says `"high"` — this divergence was already true for TBS's arm-thickness-only child before this IC and is not a new risk this IC introduces.
