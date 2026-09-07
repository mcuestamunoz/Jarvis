# Implementation Report — ESC Mass Hygiene B1 (`hobbywing_xrotor_40a_6s` 26→15)

**IC:** [implementation_contract_catalog_esc_mass_hygiene_b1.md](implementation_contract_catalog_esc_mass_hygiene_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-07
**Baseline:** package `0.3.8` · suite 2344

---

## Files changed

- `library/esc/_datos.json` — `hobbywing_xrotor_40a_6s`:
  - `mass_g`: **26 → 15**. `part_number` (`30901001`), `length_mm`/`width_mm`/`height_mm` (50.0/21.6/12.0), `source_url`, electrical ratings, topology, and channels are all **byte-identical** to before this IC — confirmed by diff (only the `mass_g` value and `source_note` text changed).
  - `source_note` rewritten to: (1) drop the bare "26g" figure from the identity-summary sentence, (2) state the page's own "15g" figure explicitly for PN `30901001` alongside the already-cited "50.0x21.6x12.0mm" quote, (3) name Version A's weight (18.5g) alongside its already-noted different size/PN, (4) explicitly record that the prior `26` matched neither real weight value, was not an average or unit-conversion artifact of either, and has no cited primary source — undocumented/unknown, per the investigation's own §D finding — rather than silently dropping the number with no trace. The "flagged as pre-existing data-quality debt, not resolved in this IC" framing from the prior ESC Geometry B1 IC is retired, since this IC is the resolution.
- `tests/test_catalog_foundation_v1.py`:
  - `_assert_esc_hobbywing` (shared helper) — `mass_g` assertion updated to `pytest.approx(15.0)`.
  - `test_esc_mass_unchanged_by_geometry_addition` → **renamed** `test_esc_mass_coherent_with_version_b_envelope`, docstring rewritten to state the mass now matches the same PN the dims are sourced from, and the assertion body extended to also check `length_mm`/`width_mm`/`height_mm` alongside the corrected `mass_g` — so the test now actively proves "one coherent variant," not merely "value happens to be X."
  - `test_bind_esc_from_catalog_projects_continuous_current` — trailing `mass_g` assertion updated to `15.0`.
  - `test_bind_esc_from_catalog_projects_declared_envelope` — trailing `mass_g` assertion (on its own line, `pytest.approx(26.0)` → `pytest.approx(15.0)`) and the comment above it updated to no longer imply the value is an untouched pre-existing debt.

## Behavior changed

- `ComponentLibrary.get_esc("hobbywing_xrotor_40a_6s").mass_g` now returns `15.0` instead of `26.0` — confirmed live: `mass_g= 15.0 | part_number= 30901001 | dims= 50.0 21.6 12.0`.
- `bind_esc_from_catalog("hobbywing_xrotor_40a_6s")`'s `properties["mass_g"]` now projects `15.0` — no logic change was needed in `bind_esc_from_catalog` itself (it already projects `spec.mass_g` verbatim); only the seed value changed.
- No other ESC row is affected (the catalog has exactly one ESC row, confirmed unchanged this session). No Battery/Motor/Frame/FC seed, `EscSpec` schema, `aerial.py`, or `ui/**` file was touched — confirmed via `git diff --stat` showing zero changes to any of those paths.
- The Board glyph payload is unaffected: `_geometry_from_spec` (Board glyphs B1) never reads `mass_g` — it was already, and remains, independent of this correction. `mass_g` continues to appear only as a text `fields` entry on the card, now showing the corrected value for any freshly-bound ESC.

**N4 honesty note (as required by the IC):** this correction only changes what the **catalog seed** returns going forward. Any already-saved project whose `flight_controller`/`esc` component previously bound `hobbywing_xrotor_40a_6s` and persisted `mass_g: 26` into its own `ComponentSpec.properties` **keeps that stale 26g value on disk and on its Board card** until that component is re-bound (the same re-declare/rebind requirement named by the prior Geometry B1 ICs for their own seed corrections/additions — catalog seed changes were never designed to retroactively rewrite already-persisted project state). This is expected, not a bug, and no workspace project was touched or migrated by this IC, per its own explicit non-goal.

## Tests

Executed: `python -m pytest -q` → **2344 passed**, 0 failed (same count as baseline — this IC retargets existing assertions rather than adding new test cases, per its own "retarget, don't delete coverage" instruction; no coverage was removed, one test's assertion surface was strengthened). Ran `tests/test_catalog_foundation_v1.py` alone first (60 passed) before the full run.

Grep verification after edits: zero remaining `26`/`26.0` associated with this ESC's mass in either the seed or the test file — the only remaining `26` in the tree is the historical figure named explicitly, in prose, inside the rewritten `source_note` ("mass_g corrected from a prior 26g...") — intentional documentation of the correction, not a live value.

## Non-goals honored

No PN, dims, electrical ratings, topology, or channel count changed (confirmed identical via diff). No Version A second SKU added. No `ui/**`, `workspace/spatial_board.py`, motor/battery/FC/sensor seed, `aerial.py`, Continuity/orchestrator, or `calculation_engine.py` file touched (confirmed via `git diff --stat`: only the two files listed above changed). No Continuity ESC picker, pose, fit, or CAD introduced. No version bump. No workspace project auto-migrated.

## Remaining risk / notes for review

- As noted in the N4 honesty section above, any live project bound to this SKU before this IC will display a now-stale `26g` until rebound — this is the same, already-established behavior pattern this axis's prior ICs (e.g. Motor B1's arm sibling correction) have relied on, not a new risk this IC introduces.
- The 26g figure's origin remains genuinely unknown, as the investigation itself concluded — this report does not claim to have solved that mystery, only to have replaced the undocumented number with the one the manufacturer's own page states for this exact part number.
