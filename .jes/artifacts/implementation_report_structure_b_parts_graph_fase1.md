# Implementation Report — Structure B Parts Graph (Fase 1)

**Project:** Jarvis
**Date:** 2026-09-04
**Implementer:** Claude Code
**IC:** [implementation_contract_structure_b_parts_graph_fase1.md](implementation_contract_structure_b_parts_graph_fase1.md)
**Baseline:** tag `v0.3.6` · suite 2197 · Structure honesty IC landed (suite 2200 at start of this IC)

---

## Files changed

- `src/jarvis/schemas/action_schema.py` — `ComponentSpec.parent_key: str | None = None` (first intra-project parent/child precedent in this schema; additive, default `None`, every existing project deserializes unchanged).
- `src/jarvis/domains/aerial.py` — `CONFIGURATION_MAP` + `_extract_configuration` (closed vocabulary: `quad_x`/`quad_plus`/`hex`/`deadcat`/`tricopter`, word-boundary matched, never derived from `motor_count`); `_extract_wheelbase_mm` (keyword-gated — `wheelbase`/`distancia entre motores`/`motor a motor` context required, a bare `"230mm"` is never claimed); `extract_frame_properties` extended to also populate `configuration`/`wheelbase_mm` (root-only, additive — `_frame_completeness` untouched, still mass+material only); locked part-type keys `FRAME_ARM_KEY`/`FRAME_PLATE_KEY`/`FRAME_CAGE_KEY`/`FRAME_STANDOFF_KEY`; `_PART_TYPE_MAP` + `extract_frame_part_properties` (declared-phrase → locked key + `count`/`material`, `None` when unrecognized — never a stub); `_structure_part_completeness` (independent of `_frame_completeness`, never feeds Structure PASS).
- `src/jarvis/core/component_writers.py` — `upsert_frame_part(project_state, part_key, properties, *, catalog_ref=None)`: single writer for a part-type child, merges onto any existing child, always `parent_key="frame"`. Test-callable API only in this IC (no orchestrator free-text wiring) — same "identity exists, reachability is incremental" posture as `bind_frame_from_catalog` itself before its own assist IC shipped.
- `src/jarvis/core/catalog_bind.py` — `bind_frame_from_catalog` additionally projects `wheelbase_mm`/`configuration` onto the root when present on the seed row; new `frame_part_specs_from_catalog(sku) -> dict[str, ComponentSpec]` projects part-type children from `FrameSpec`'s optional per-part fields, returning `{}` when the SKU has none (every row except `armattan_rooster_5in` today).
- `src/jarvis/core/project_closure.py` — `_MEASURABLE` gains `configuration`/`wheelbase_mm`/`count` (same "declared label, not a physics quantity" routing as `material`/`model`); `build_component_bom` now skips any spec with `parent_key is not None` in **both** iteration loops (Cursor review N1) — never a top-level peer, orphans (parent missing) included; `format_bom_lines` gained `_frame_part_sublines` (display-only, locked render order `frame_arm → frame_plate → frame_cage → frame_standoff`, `└ {label} ×{count} — {material}`), called after the `frame` line in all three non-missing buckets.
- `src/jarvis/knowledge/library.py` — `FrameSpec` gained 9 optional fields (`wheelbase_mm`, `configuration`, `arm_count`, `arm_material`, `plate_count`, `plate_material`, `cage_material`, `standoff_count`, `standoff_material`), all default `None`; loader parses them when present, omits otherwise (never invents).
- `library/frames/_datos.json` — enriched all four existing rows with `wheelbase_mm`/`configuration` (every figure confirmed by re-fetching each row's own cited `source_url` specifically for this IC — see §"Seed sourcing" below); `armattan_rooster_5in` additionally gained `arm_material`/`plate_material`/`cage_material`/`standoff_material` (all four sourced from the manufacturer's own page, already cited). No counts were added anywhere — no source page enumerates arm/plate/standoff counts, so none were invented.
- `src/jarvis/core/orchestrator.py` — `_apply_component_frame_catalog_pick` (Catalog Foundation IC-3's existing method) now also calls `frame_part_specs_from_catalog` + `upsert_frame_part` after writing the root — the one production call site for the parts graph in Fase 1. A pick with no part fields (every row except Armattan) upserts nothing; behavior for those picks is unchanged.
- `tests/test_frame_parts_graph_v1.py` (new), `tests/test_frame_catalog_bind_ux.py` (2 new tests) — see below.

No edits to `_structure_evidence`, `_derive_subsystem_verdict`, `_derive_overall` (`engineering_readiness.py` — zero diff, confirmed via `git diff --stat`), `_frame_completeness`, `classify_component`, `BLOCK_TO_COMPONENTS` (confirmed `["structure"]` still maps to `["frame"]` only), or `project_continuity.py` (zero new diff this IC).

## Seed sourcing (wheelbase + Armattan part materials)

All four figures were re-verified by fetching each row's own cited `source_url` specifically for this IC (not reused from an earlier aggregated search):

| SKU | `wheelbase_mm` | Confirmed on |
|---|---|---|
| `tbs_source_one_v5_5in` | 226 | racedayquads.com: *"Wheelbase: 226mm"* |
| `tbs_source_one_v5_1_7in_dc` | 320 | progressiverc.com: *"320mm motor-to-motor"* |
| `iflight_xl7_v4_7in` | 285 | fpv24.com: *"Wheelbase: 285mm"* |
| `armattan_rooster_5in` | 230 | armattanquads.com (manufacturer): *"230mm @ 5in"* |

`configuration` mapped from each page's own stated shape name: TBS 5″ "wide-stance, X configuration" → `quad_x`; TBS 7″ DC "deadcat (DC) configuration" → `deadcat` (exact vocabulary match); iFlight "True-X configuration" → `quad_x`; Armattan "Compressed-X" → `quad_x` (X-family mapping, noted in `source_note`).

Armattan's `arm_material`/`plate_material`/`cage_material`/`standoff_material` were already fully confirmed during Catalog Foundation IC-1's own sourcing: *"carbon fiber main plate/arms with titanium cage and aluminum standoffs"* — mapped to the exact canonical `library/materiales/_datos.json` keys (`fibra de carbono`/`titanio`/`aluminio`).

No `arm_count`/`plate_count`/`standoff_count` was set for any row — no source page states a part count (Compressed-X/quad-X implies 4 arms conventionally, but the page never states it numerically, so it was left unset rather than inferred from the configuration name).

## Behavior changed

- `ComponentSpec` can now express `parent_key`, enabling sibling components in `design_properties.components` to represent declared parts of an assembly.
- Free text can declare `configuration`/`wheelbase_mm` on a frame, and part-type phrases (`"4 brazos fibra de carbono"`) are extractable via `extract_frame_part_properties` — but this extractor is **not yet wired into the live orchestrator free-text wizard** (scoping decision, below).
- Picking a catalog frame with seeded part data (currently only `armattan_rooster_5in`) now also creates `frame_arm`/`frame_plate`/`frame_cage`/`frame_standoff` children with `parent_key="frame"`, each carrying its declared material.
- BOM shows these children as display-only sub-lines under the `frame` line (`└ arm — fibra de carbono`, etc.) — **never** as top-level peer entries, verified by direct test and by the CLI walk in the appendix.
- **Confirmed unchanged, by regression test:** `Structure` subsystem's ERF verdict and all four evidence bits are byte-identical whether or not part children are declared (`test_structure_pass_and_evidence_unchanged_with_vs_without_children`).

## Scoping decision: free-text part wiring deferred

The IC's §2.4 asked to "wire through the existing frame/component apply path with the smallest change." Tracing the live dispatch (`_handle_component_description`'s `expected_keys`/`BLOCK_TO_COMPONENTS` gating), the smallest-change path that avoids inventing new routing is to keep part declaration reachable only through the **catalog bind** apply path (already fully wired, §above) and as a **direct, tested API** (`extract_frame_part_properties` + `upsert_frame_part`) — mirroring exactly how `bind_frame_from_catalog` itself was "test-callable only" before its own IC-3 assist UX shipped. Wiring free-text part declarations into the live interactive wizard would require deciding how a single user message splits between root frame properties and child part properties, and how `frame_arm` (never in any `BLOCK_TO_COMPONENTS` list) is even reached in the `expected_keys`-gated dispatch loop — a real routing decision the IC did not fully specify. Named here as residual, not silently dropped.

## Tests added/updated

- `tests/test_frame_parts_graph_v1.py` (new, 21 tests): schema round-trip, configuration/wheelbase extraction (including "never from motor_count", "bare mm not claimed"), part-phrase extraction (all four types + unrecognized→None), BOM N1 (children never peers, sub-line rendering, orphan parent_key no-crash), Structure PASS/evidence regression with vs. without children, catalog bind projection (wheelbase/configuration on root, all four Armattan children, TBS row → no children), `upsert_frame_part` writer.
- `tests/test_frame_catalog_bind_ux.py` (2 new): end-to-end pick → children upserted with correct `parent_key`, never top-level BOM peers; TBS pick → no children created.

## Tests executed

- Targeted: `pytest tests/test_frame_parts_graph_v1.py tests/test_frame_catalog_bind_ux.py tests/test_catalog_foundation_v1.py tests/test_catalog_bind_v1.py -q` → 100 passed.
- Full suite: `pytest -q` → **2223 passed** (2200 baseline + 23 new tests), zero failures, zero skipped, zero weakened.
- **CLI walk:** `ayúdame a elegir` → pick Armattan Rooster → `estado` shows `✓ frame: armattan_rooster_5in [armattan_rooster_5in] qty=1 (high)` followed by four `└` sub-lines (arm/plate/cage/standoff with materials), and the readiness block shows `Structure UNVERIFIABLE` (sim never ran in the minimal fixture) with **no** `frame_arm`/etc. lines anywhere in `ENGINEERING READINESS` or `TOP GAPS` — confirms the graph is genuinely invisible to verdict/gap logic.

## Residual (Fase 2, explicitly out per the IC)

- `hardware` nodes, per-instance part nodes (e.g. `arm_front_left`), `mounts_on`/spatial edges, sum-of-parts mass, `arm_count`↔`motor_count` or `configuration`↔part-graph cross-checks — none implemented, none proposed.
- Free-text part-declaration wiring into the live interactive wizard (see scoping decision above) — the extractor exists and is tested; live-chat reachability is not yet built.
- Seed enrichment for `arm_count`/`plate_count`/`standoff_count` — no source states them; left unset for all rows.
