# Implementation Report — Spatial Board Honest Absence (B3)

**IC:** [implementation_contract_spatial_board_honest_absence_b3.md](implementation_contract_spatial_board_honest_absence_b3.md)
**Implementer:** Claude Code
**Date:** 2026-09-05
**Baseline:** `v0.3.8` / `checkpoint-spatial-board-projector` (`f3deae0`)

---

## Files changed

- `src/jarvis/workspace/spatial_board.py`:
  - Module docstring: the old "no inventa slots ausentes" sentence (now false) replaced with an explanation of the B3 rule — a declared block's `BLOCK_TO_COMPONENTS` key absent from `components` becomes a `kind: "slot"` node; never for an undeclared block; never a `ComponentSpec`; never a BOM bucket.
  - `project_spatial_nodes`: removed the `if not components: return []` short-circuit (N2 lock) — the new guard is `if not components and not blocks: return []`. Added `expected_by_column = _expected_keys_by_column(blocks)` and a `place_slot`/`_emit` sibling to the existing `place` (per §2.3 — `place_slot` never indexes `components[key]`). The main column loop now walks `range(max(len(blocks), max(lanes, default=-1) + 1))` — every declared block's own column, not only columns that already have a real root (§2.4) — placing each column's expected keys first (real card if present, slot if absent), then falling back to the existing `_sort_roots`/orphan logic for keys not in the canonical `BLOCK_TO_COMPONENTS` list. `emitted` (already existed) prevents any key from ever being placed twice.
  - New `_expected_keys_by_column(blocks)`: first-match-deduped expected keys per column (a key owned by multiple blocks, e.g. `motors` in propulsion+energy, is listed once, at its first block) — pure function over `BLOCK_TO_COMPONENTS`, no new dependency.
- `tests/test_spatial_board_projector.py`: see Tests below.
- `docs/system_map/00_entry/ENTRY_MAP.md`: one new adapters-table row for `adapters/cli/board.py` (`jarvis board`) + `workspace/spatial_board.py`, stating it's a read-only projector, no writer/BOM/ERF/Continuity import. No new C-xxx.
- `README.md`: the "Pizarra" blurb gained one clause — slots are architecture gaps, not BOM/completeness; CLI still mutates.
- `ui/spatial-board/`: **zero changes.** `kind: "slot"` already existed in `types.ts`, already had CSS (`.sb-card--slot`, `.sb-minimap__dot--slot`) from the viewport-motor fixture phase, and `kind` is only ever used as a CSS class-name interpolation (`SpatialCard.tsx`, `Minimap.tsx`) — confirmed no type error, no frontend edit needed.

## Behavior changed

- A project with a declared `system_blocks` entry whose expected component (per `BLOCK_TO_COMPONENTS`) isn't in `design_properties.components` now emits a display-only `kind: "slot"` node for that key, rendered by the existing (previously unused) dashed-border card/minimap-dot styling.
- A project with `system_blocks == []` is byte-identical to before (no slots, real cards only) — the "no inventa para bloques no declarados" virtue is preserved, now proven by a positive test (`test_no_declared_blocks_still_invents_nothing`) instead of only a negative one.
- A project with declared blocks and **zero** components no longer returns `[]` — it returns one slot per expected key of those blocks.
- A key present in `components` under any form (root or child) is never also emitted as a slot — verified explicitly (`test_present_key_never_dual_slot_and_card`).
- Frame parts (`frame_arm`, ordinal plate siblings, etc.) are untouched — they were never in `BLOCK_TO_COMPONENTS` and still aren't reachable by the slot pass.

## Tests

All in `tests/test_spatial_board_projector.py` (extended, nothing gutted):

- `test_missing_expected_keys_of_declared_blocks_become_slots` — replaces the now-superseded `test_does_not_invent_missing_architecture_slots` (its own premise — "never invent anything" — is exactly what this IC changes, per the IC's own instruction); asserts `wheels` still absent (actuation undeclared), the six missing propulsion/energy/structure/control keys are `kind="slot"`, `motors` stays `kind="component"`.
- `test_no_declared_blocks_still_invents_nothing` — `system_blocks=[]` unaffected.
- `test_empty_components_with_declared_blocks_yields_only_slots` — N2 lock: empty `components` + 4 declared blocks → 7 deduped slots, not `[]`.
- `test_fixture_a_present_components_plus_missing_expected_slots` — the investigation report's Fixture A reconstructed as a permanent regression test (motors/battery/frame/`frame_arm`/empty-name FC present; propellers/esc/sensors missing → slots; FC stays `component` with `declaredName == ""`; `frame_arm` stays `kind="part"`).
- `test_present_key_never_dual_slot_and_card` — an `esc` `ComponentSpec` never produces a second `esc` slot.
- `test_slot_payload_shape` — exact DTO shape: `declaredName == ""`, `fields == [{"label": "estado", "value": "no declarado"}]`, no `SKU`.
- `test_projector_module_does_not_import_bom_or_readiness_or_continuity` — greps the module's own source for `build_component_bom`/`engineering_readiness`/`project_continuity`, asserts none present (module isolation, locked stance).

Executed: `python -m pytest -q` → **2310 passed**, 0 failed (baseline 2294 + net new). `cd ui/spatial-board && npm test` → **4/4 passed**, unchanged (Q1–Q11 transform math untouched, confirmed via `git status ui/` showing zero diffs).

## Non-goals honored

No `build_component_bom`/`engineering_readiness`/`project_continuity` import (grep-tested). No `BLOCK_TO_COMPONENTS`, writer, orchestrator, or `_derive_overall` change. No HTTP write route, no card-click handler. No `ui/` edit. No version bump. `spatial_layout.json` (B1), poll/`mtime` freshness (B2), `PropertyValue.source` display (B4), presentation grouping (B5), lane labels, glyphs, Continuity/ERF chrome, catalog pick from card, edges, PRODUCT_SCOPE, new C-xxx — none touched.

## Residual

**B1 (layout in the project tree, `views/spatial_layout.json` or equivalent) remains the next product Buy**, per the investigation report and this IC's own §7 — not attempted here.
