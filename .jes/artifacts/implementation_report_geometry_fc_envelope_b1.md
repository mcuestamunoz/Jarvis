# Implementation Report — Flight Controller Declared Box (Pixhawk 4 only, identity-linked, no catalog) — representar only (B1)

**IC:** [implementation_contract_geometry_fc_envelope_b1.md](implementation_contract_geometry_fc_envelope_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-07
**Baseline:** package `0.3.8` · ESC B1 CLOSED suite 2327

**Architectural divergence (as locked in the IC, stated plainly):** this Buy is **not** Battery/Motor/ESC-shaped. There is no `library/fc/`, no `FcSpec`, no `bind_flight_controller_*`, and no `catalog_ref` is ever set on a flight-controller `ComponentSpec` by this change. The three declared dims are identity-linked from a static, sourced table keyed by the same canonical `model` string `extract_flight_controller_properties` already produces from free text — declared-by-recognized-identity only, never catalog-bound.

---

## Files changed

- `src/jarvis/domains/aerial.py`:
  - New `FLIGHT_CONTROLLER_DIMENSIONS: dict[str, dict[str, object]]` sitting immediately after `FLIGHT_CONTROLLER_MAP`, with exactly one entry: `"pixhawk_4"` → `length_mm=44.0`, `width_mm=84.0`, `height_mm=12.0`, plus `source_urls` (PX4 docs + Holybro product page) and a `source_note` quoting both pages' verbatim "44x84x12mm" and explicitly recording that no mount pattern is claimed and Pixhawk 4 Mini was not seeded.
  - `extract_flight_controller_properties`: after attaching `model` exactly as before, looks up `FLIGHT_CONTROLLER_DIMENSIONS.get(found_model)` and, only when an entry exists, attaches `length_mm`/`width_mm`/`height_mm` as `PropertyValue(unit="mm", confidence=<same as the model match>, source="declared")`. A model with no table entry (every other `FLIGHT_CONTROLLER_MAP` key) returns `model` only, byte-identical to before this IC. No digit is ever read from the `normalized` input string for this feature — the dims come solely from the static table, never from user text.
  - Docstring updated to state the identity-linked/no-catalog/no-mm-parsing distinction explicitly.
- `tests/test_control_component.py`:
  - `test_extract_fc_pixhawk4_declared_envelope` — the sourced 44/84/12mm triple, unit/source/confidence.
  - `test_extract_fc_pixhawk4_mini_has_no_dims` — the distinct canonical model `pixhawk_4_mini` stays dims-less (no inheritance from its sibling `pixhawk_4`).
  - `test_extract_fc_generic_pixhawk_has_no_dims` — bare "pixhawk" (no digit) stays dims-less.
  - `test_fc_completeness_unchanged_by_declared_dims` — `_flight_controller_completeness` returns an identical verdict with and without the three dim properties present (N5 lock).
  - `test_handle_component_description_fc_persists_declared_envelope` — the real end-to-end persist path (`orchestrator._handle_component_description("Pixhawk 4", session)` → `set_control_component`) writes all three dims onto `components["flight_controller"]`, and `catalog_ref` stays `None`.

**Not touched, confirmed by `git diff --stat`:** `library/**` (no `fc/` directory created), `library.py` (no FC family added), `catalog_bind.py` (no FC bind function added), Battery/Motor/ESC/Frame schemas and seeds, `ui/**`, `component_writers.py` (no change needed — `set_control_component` already writes `spec.properties` directly with no field-stripping, confirmed by reading it before touching anything), `calculation_engine.py`, the Structure PASS footnote.

## Behavior changed

- Free-text declaration of "Pixhawk 4" (or any phrase the existing keyword match resolves to canonical model `"pixhawk_4"`) now also yields `length_mm`, `width_mm`, `height_mm` alongside `model` — both through the raw extractor function and through the real orchestrator persist path (`_handle_component_description` → `set_control_component`), verified end-to-end.
- Every other recognized FC model (`pixhawk`, `pixhawk_4_mini`, `pixhawk_6`/`6c`/`6x`, `ardupilot`, `betaflight`, `naze32`, `matek`) is byte-identical to before this IC — `model` only, no dims, no regression.
- **Zero code change to `ui/spatial-board/` or `workspace/spatial_board.py`.** Verified live: a `ComponentSpec` built from `extract_flight_controller_properties("pixhawk 4")`'s output renders `model`, `length_mm: "44 mm"`, `width_mm: "84 mm"`, `height_mm: "12 mm"` as ordinary field rows through the existing generic `_fields()` projector.
- `_flight_controller_completeness` is unaffected — it only ever inspects `model`'s confidence, confirmed unchanged by direct read and by the new regression test comparing its output with and without dims present.
- `catalog_ref` remains `None` for flight-controller components under every code path — no catalog, no bind function, no SKU identity was introduced.
- **Existing saved projects** (e.g. `autonomía-de-10min`, whose `flight_controller` currently has `model` only, `catalog_ref: null`) will **not** retroactively gain dims — the dims are attached at extraction time, so a project needs its FC re-declared (e.g. typing "Pixhawk 4" again through the control-block flow) to pick up the new properties, exactly as the IC's N2 lock anticipated. This was not run against that specific live project as part of this implementation (no destructive re-declare was performed on real workspace data); the persist path is proven correct via the new integration test and the direct extractor/Board checks above instead.

## Tests

Executed: `python -m pytest -q` → **2332 passed**, 0 failed (baseline 2327 + 5 new). Ran `tests/test_control_component.py` alone first (46 passed — 41 pre-existing + 5 new) before the full run. No existing test was weakened, and none of the pre-existing Pixhawk-4 extraction tests asserted "model only" exclusivity, so none needed updating (confirmed by reading each before writing new tests, per the IC's own instruction to extend rather than weaken).

## Non-goals honored

No `library/fc/`, no `FcSpec`, no loader, no `bind_flight_controller_*`, no `catalog_ref` anywhere (confirmed via `git diff --stat` and via the new persist-path test explicitly asserting `catalog_ref is None`). No Battery/Motor/ESC/Frame schema or seed edits. No free-text mm digit parsing (the table lookup happens only after a model match; no regex against `normalized` for dimensions was added). No Pixhawk 4 Mini or any other model seeded. No `mount_pattern_mm`/30.5/stack/fit logic or CLI copy anywhere. No mass/weight field. No completeness change. No version bump.

## Remaining risk / notes for review

- As noted above, no real workspace project was re-declared as part of this implementation — the IC's own §3.5 called unit tests sufficient for review and named a Board re-declare smoke as optional/Engineer's call, not a code requirement.
- The `FLIGHT_CONTROLLER_DIMENSIONS` table's value type is `dict[str, object]` (not a typed dataclass) — deliberately minimal, matching the IC's own instruction to avoid inventing a `FcSpec`-shaped structure; if a second model is ever sourced and added, this shape already scales to more entries without further design work.
