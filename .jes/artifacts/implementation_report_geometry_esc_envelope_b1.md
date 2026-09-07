# Implementation Report — ESC Declared Envelope (box, reusing Battery vocabulary) — representar only (B1)

**IC:** [implementation_contract_geometry_esc_envelope_b1.md](implementation_contract_geometry_esc_envelope_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-07
**Baseline:** package `0.3.8` · Motor B1 CLOSED suite 2323

---

## Files changed

- `src/jarvis/knowledge/library.py`:
  - `EscSpec` gains three optional fields: `length_mm`, `width_mm`, `height_mm` (all `float | None = None`, additive, no required-field change) — same names as `BatterySpec`, no ESC-only vocabulary.
  - `_esc_from_raw` parses each from JSON when present, omits (`None`) when absent — same convention as every other optional ESC field.
- `library/esc/_datos.json` (1 row total, confirmed) — updated `hobbywing_xrotor_40a_6s`:
  - `length_mm=50.0`, `width_mm=21.6`, `height_mm=12.0` — the size stated for `part_number: "30901001"` (International/Asian Version B, no output wires), which the row already declared before this IC. The other physical variant on the same source page (Version A, part `30901013`, 42.0×21.6×12.0mm) was **not** seeded — different part number, not this row.
  - `source_url` normalized (N3) from `https://a.hobbywing.com/en/products/xrotor-40a122` (fails TLS validation, confirmed) to the working mirror `https://www.hobbywing.com/en/products/xrotor-40a122` — same product, same path.
  - `mass_g` left at `26` unchanged (N2) — the page states 15g for this exact part number, a real discrepancy flagged in `source_note` as pre-existing debt, not resolved here.
  - `source_note` extended with the verbatim size quote, the part-number disambiguation rationale, the excluded Version A dims, the URL normalization, and the mass discrepancy flag.
- `src/jarvis/core/catalog_bind.py` — `bind_esc_from_catalog`:
  - Projects `length_mm`/`width_mm`/`height_mm` as `PropertyValue(unit="mm", confidence=0.9, source="declared")` when present on the `EscSpec` — mirrors `bind_battery_from_catalog`'s exact pattern, no signature change (this bind was already SKU-first/`library`-parameterized).
  - Existing `current_a`/`mass_g` projection untouched.
  - Docstring updated to state plainly that no ESC catalog-pick wizard exists in Continuity/orchestrator (still true, per N4 — confirmed no such call site exists anywhere in the tree) and that the function remains test-callable/script-callable only.
- `tests/test_catalog_foundation_v1.py` — 4 new tests: the seeded row's exact envelope values (with the part-number disambiguation spelled out in the docstring), a `mass_g` regression confirming it's untouched, a `source_url` regression confirming the mirror normalization, and a bind-level test confirming the three new keys plus unaffected `current_a`/`mass_g`.

## Behavior changed

- `EscSpec` for `hobbywing_xrotor_40a_6s` now carries a declared box envelope (this is the catalog's only ESC row, so there is no "other rows unchanged" case to report — trivially true).
- `bind_esc_from_catalog("hobbywing_xrotor_40a_6s")` now includes the three geometry keys in its returned `ComponentSpec.properties`, alongside the pre-existing `current_a`/`mass_g`.
- **Zero code change to `ui/spatial-board/` or `workspace/spatial_board.py`.** Verified live: a `ComponentSpec` bound via `bind_esc_from_catalog` renders `length_mm: "50 mm"`, `width_mm: "21.6 mm"`, `height_mm: "12 mm"` as ordinary field rows through the existing generic `_fields()` projector, alongside `current_a`/`mass_g`/SKU — no Board change needed.
- No change to ESC completeness computation, `calculation_engine.py`, or `electrical_compatibility.py` (confirmed via `git diff --stat` showing zero lines changed in either) — none of these read the three new field names, which are brand-new and previously unused anywhere in the tree.
- No stack/fit/mount-pattern field, sentence, or CLI copy added anywhere (N5).
- No ESC catalog-pick UX built (N4) — `bind_esc_from_catalog` remains unreachable from any production orchestrator flow, exactly as before this IC.
- Structure PASS footnote and `ASSEMBLY_READY` untouched.

## Tests

Executed: `python -m pytest -q` → **2327 passed**, 0 failed (baseline 2323 + 4 new). Ran the catalog-specific files first (`test_catalog_foundation_v1.py` + `test_catalog_bind_v1.py`, 92 passed) before the full run. No existing test was weakened or removed.

## Non-goals honored

No Battery/Motor/Frame/FC geometry touched (confirmed via `git diff --stat`: zero changes to any of those schemas). No `mass_g` value change (still 26, regression-tested). No Continuity/orchestrator ESC catalog-pick wizard built. No fit/stack/mount-pattern logic or CLI copy anywhere. No free-text ESC-mm extractor added to `aerial.py` (confirmed zero diff). No version bump.

## Smoke (optional, §3.6)

Ran the live-projector smoke described in the IC: a `ComponentSpec` bound via `bind_esc_from_catalog("hobbywing_xrotor_40a_6s")`, placed into a minimal project state, renders all five properties (`current_a`, `mass_g`, `length_mm`, `width_mm`, `height_mm`) plus `SKU` on its Board card — confirming the "no `ui/` change required" claim end-to-end. (Note for anyone re-running this smoke: a `system_blocks` list that includes `"propulsion"` will also render `motors`/`propellers` B3 slot cards alongside the ESC card if those aren't also declared — expected honest-absence behavior from the earlier Spatial Board IC, not a regression here; look up the `esc` card by its `id`, not by list position.)

## Remaining risk / notes for review

- The `mass_g=26` vs. page-stated `15g` discrepancy for this exact part number remains unresolved, as locked (N2) — flagged in `source_note` for whoever picks it up next.
- `bind_esc_from_catalog` still has no live user-reachable entry point (N4, as locked) — this Buy's dims are correct and tested but not visible to a real project until/unless a separate ESC catalog-pick UX is built in a future, different IC.
