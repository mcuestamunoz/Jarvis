# Implementation Report — Battery declared envelope (L×W×H) — representar only (B1)

**IC:** [implementation_contract_geometry_battery_envelope_b1.md](implementation_contract_geometry_battery_envelope_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-06
**Baseline:** tag `v0.3.8` · Structure CLOSED suite 2294 · Board B3 suite 2310

---

## Files changed

- `src/jarvis/knowledge/library.py` — `BatterySpec` gains three optional fields: `length_mm`, `width_mm`, `height_mm` (all `float | None = None`, additive, no required-field change). `_battery_from_raw` parses each from JSON when present (`float(...)`), omits (`None`) when absent — same convention as every other optional battery field.
- `library/baterias/_datos.json` — seeded exactly the three `identity_status: verified` rows the IC locked, with the exact values locked in §0.4:
  - `lipo_4s_1500mah`: 37 / 35 / 75 mm (CNHL page's unlabeled `"37X35X75mm"` — verbatim print order, N2a)
  - `lipo_4s_5000mah`: 138.5 / 47.7 / 40.7 mm (Spektrum page's labeled Length/Width/Height, N1)
  - `lipo_6s_6000mah`: 141 / 64 / 41 mm (Rotorama page's unlabeled `"Dimensions: 141x64x41mm"` — verbatim print order, N2a)
  Each row's `source_note` extended with the exact quoted dimension string and which mapping rule (N1 labeled vs N2a verbatim-order) applied. All seven other battery rows (including `lipo_4s_10000mah`) are untouched — no `source_url` for dims, so nothing was added.
- `src/jarvis/core/catalog_bind.py` — `bind_battery_from_catalog`:
  - Projects `length_mm`/`width_mm`/`height_mm` as `PropertyValue(unit="mm", confidence=0.9, source="declared")` when the corresponding `BatterySpec` field is not `None` — mirrors the exact `wheelbase_mm`/`arm_thickness_mm` projection pattern already shipped for Structure.
  - **N6 docstring fix**: removed the stale "No CLI/UX entry point calls this yet" claim (confirmed false during the investigation — `orchestrator._apply_component_battery_catalog_pick` and a second call site are live, production call paths) and replaced it with an accurate one-paragraph description.
- `tests/test_catalog_foundation_v1.py` — 4 new loader tests: the three sourced rows' exact mm triples (including the N1-vs-N2a distinction, called out explicitly in each test's docstring), plus one confirming an unsourced row's dims stay `None`.
- `tests/test_catalog_bind_v1.py` — 2 new bind tests: a sourced row's `ComponentSpec.properties` carries all three keys with `unit="mm"`/`source="declared"`, and an unsourced row's properties contain none of the three keys at all (not even as `None`-valued entries).

## Behavior changed

- `BatterySpec` for the three seeded rows now carries a declared box envelope; all other rows unchanged (`None`).
- `bind_battery_from_catalog` for those three SKUs now includes `length_mm`/`width_mm`/`height_mm` in the returned `ComponentSpec.properties`; for every other SKU, behavior is byte-identical to before this IC.
- **Zero code change to `ui/spatial-board/` or `workspace/spatial_board.py`.** Verified live (not just asserted): `project_spatial_nodes` on a battery `ComponentSpec` bound via `bind_battery_from_catalog("lipo_4s_1500mah")` already renders `length_mm: "37 mm"`, `width_mm: "35 mm"`, `height_mm: "75 mm"` as ordinary field rows — `_fields()`'s existing generic `spec.properties.items()` iteration picks them up with no changes, exactly as the investigation predicted.
- No change to battery `completeness` computation, `calculation_engine.py`, hover/sag energy paths, Structure PASS footnote, or `ASSEMBLY_READY` — none of these read `length_mm`/`width_mm`/`height_mm` (confirmed by reading each; none touched, none reference battery geometry).

## Tests

Executed: `python -m pytest -q` → **2316 passed**, 0 failed (baseline 2310 + 6 new). No existing test was weakened or removed. Ran the specific battery/catalog files first (`test_catalog_foundation_v1.py` + `test_catalog_bind_v1.py`, 81 passed) before the full run.

## Non-goals honored

No Motor/ESC/Frame envelope fields. No `diameter_mm`/`envelope_shape`/bounding volume/glyph. No fit/clearance/"cabe" logic anywhere. No free-text L×W×H extractor added to `aerial.py`. No dims invented for any unsourced row. Structure PASS footnote, `ASSEMBLY_READY`, and `calculation_engine.py` untouched — confirmed via `git diff --stat` showing only the 5 files listed above. No version bump.

## Remaining risk / notes for review

- The N6 docstring fix is scoped to the one paragraph the IC named — no other `catalog_bind.py` docstrings were audited or touched for similar staleness in this IC (out of scope here).
- `lipo_4s_10000mah` (and the other six unsourced rows) remain undimensioned — expected, matches "never invent" discipline; a future sourcing pass could add more rows to this same pattern without any further schema change.
