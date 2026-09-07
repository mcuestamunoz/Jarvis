# Implementation Report — Motor Declared Envelope (stator + overall diameter + shaft) — representar only (B1)

**IC:** [implementation_contract_geometry_motor_envelope_b1.md](implementation_contract_geometry_motor_envelope_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-06
**Baseline:** package `0.3.8` · Geometry Battery B1 CLOSED suite 2316

---

## Files changed

- `src/jarvis/knowledge/library.py`:
  - `MotorSpec` gains four optional fields: `stator_diameter_mm`, `stator_height_mm`, `diameter_mm`, `shaft_diameter_mm` (all `float | None = None`, additive, no required-field change). Docstring comment explicitly names why overall axial height/length is *not* among them (§C of the investigation — EMAX's shaft-inclusive "Motor Height" vs SunnySky's body-only "Body Length" don't measure the same thing).
  - `_motor_from_raw` parses each from JSON when present, omits (`None`) when absent — same convention as every other optional motor field.
- `library/motores/_datos.json` (22 rows total, confirmed) — seeded exactly the two `identity_status: verified` rows the IC locked:
  - `emax_rs2205s_2300`: `stator_diameter_mm=22`, `stator_height_mm=5`, `diameter_mm=27.9`, `shaft_diameter_mm=3`
  - `sunnysky_r2205_2500`: `stator_diameter_mm=22`, `stator_height_mm=5`, `diameter_mm=27.4` (no `shaft_diameter_mm` — not stated on its page)
  Each row's `source_note` extended with the exact quoted spec labels (including the manufacturer's own diameter label — "Motor Diameter" vs "Rotor Diameter" — both mapped to the single `diameter_mm` property key, per N3) and an explicit note of which overall-length figure was seen and deliberately *not* seeded, and why. The unsourced sibling `emax_rs2205_2300` (no trailing "s" — a distinct SKU, thrust 8N vs the sourced row's ~10N) and all other 19 motor rows are untouched.
- `src/jarvis/core/catalog_bind.py` — `bind_motor_from_catalog`:
  - Gained an optional `library: ComponentLibrary | None = None` keyword parameter, mirroring Battery/Propeller/ESC's existing binds.
  - After building the existing suggestion-derived `projected` dict, looks up `lib.get_motor(sku)` in a `try`/`except (KeyError, ValueError)` — a miss (N4: unknown/unsourced SKU) leaves `projected` exactly as it was, no crash, no invented dims. On a hit, projects each of the four fields present on the `MotorSpec` as `PropertyValue(unit="mm", confidence=0.9, source="declared")`.
  - `MotorSuggestion` (`motor_catalog_assist.py`) was **not** touched, as locked — confirmed zero diff on that file.
- `tests/test_catalog_foundation_v1.py` — 3 new loader tests: both sourced rows' exact envelope values (including the labeled-vs-verbatim distinction called out in each docstring), plus one confirming the unsourced sibling SKU never inherits its sourced sibling's dims.
- `tests/test_catalog_bind_v1.py` — 4 new bind tests: sourced-row happy path (all 4 keys), SunnySky's asymmetric coverage (shaft key absent entirely, not `None`-valued), the unsourced sibling SKU (no geometry keys at all), and the N4 unknown-SKU case (suggestion-only properties still project correctly, no crash, no geometry keys).

## Behavior changed

- `MotorSpec` for the two seeded rows now carries a declared cylinder envelope; every other row unchanged (`None`).
- `bind_motor_from_catalog` for those two SKUs now includes the geometry keys in the returned `ComponentSpec.properties`; for every other SKU — including a lookup miss — behavior is byte-identical to before this IC.
- **Zero code change to `ui/spatial-board/`, `workspace/spatial_board.py`, or `motor_catalog_assist.py`.** Verified live: a `ComponentSpec` bound via `bind_motor_from_catalog` for `emax_rs2205s_2300` already renders `stator_diameter_mm: "22 mm"`, `stator_height_mm: "5 mm"`, `diameter_mm: "27.9 mm"`, `shaft_diameter_mm: "3 mm"` as ordinary field rows through the existing generic `_fields()` projector — no Board change needed, exactly as the investigation predicted.
- No change to motor completeness computation, `calculation_engine.py`, thrust/energy resolution, Structure PASS footnote, or `ASSEMBLY_READY` — none of these read the four new fields (confirmed by reading each; none reference motor geometry, and the fields are brand-new names unused anywhere else in the tree before this IC).
- No overall axial height/length field exists anywhere in this slice, as locked (N5).

## Tests

Executed: `python -m pytest -q` → **2323 passed**, 0 failed (baseline 2316 + 7 new). Ran the catalog-specific files first (`test_catalog_foundation_v1.py` + `test_catalog_bind_v1.py`, 88 passed) before the full run. No existing test was weakened or removed.

## Non-goals honored

No Battery/ESC/Frame geometry touched. No `envelope_shape`/glyph/preview. No fit/clearance/arm-mount/"cabe" logic anywhere. No free-text motor-mm extractor added to `aerial.py`. No dims invented for any of the 20 unsourced motor rows (including the unsourced sibling `emax_rs2205_2300`, explicitly tested). `MotorSuggestion` TypedDict and `motor_catalog_assist.py` untouched — confirmed via `git diff --stat` showing zero lines changed there. Structure PASS footnote, `ASSEMBLY_READY`, and `calculation_engine.py` untouched — confirmed via `git diff --stat` showing only the 5 files listed above. No version bump.

## Smoke (optional, §3.7)

Ran the live-projector smoke described in the IC (not a unit test, a direct `project_spatial_nodes` call against a motor `ComponentSpec` bound via `bind_motor_from_catalog("emax_rs2205s_2300")`): the Board card correctly rendered all four new fields as text rows with their `mm` units, alongside the existing `thrust_n`/`kv_rating`/`weight_g`/SKU fields, confirming the "no `ui/` change required" claim end-to-end rather than only at the unit-bind level.

## Remaining risk / notes for review

- `emax_rs2205_2300` (the project's currently-bound live SKU, per the IC's own header) still has no geometry — expected (N2); a rebind to `emax_rs2205s_2300` or `sunnysky_r2205_2500` would be needed to see dims on a real project's Board, exactly as the IC's smoke note anticipated.
- The `except (KeyError, ValueError)` around `lib.get_motor(sku)` is defensive for `ValueError` (not currently raised by `get_motor`, which only raises `KeyError`) — kept for symmetry with how other loader call sites in this codebase guard lookups; harmless, no observed effect on any test.
