# Implementation Report — #4b Sourced FC + GPS envelopes B1

Status: Done (implementation) — awaiting review + Engineer smoke
Parent: `implementation_contract_geometry_sourced_fc_gps_b1.md`
Baseline: package `0.4.1` (unchanged) · suite `2703` → `2708` (2703 + 5 new) · UI `83` (unchanged — no `ui/` file touched)

## Summary

Seeded two new identity-linked declared boxes from the Engineer's own
locked §0.1 purchase-ground-truth citation bags, using the SAME pattern
`FLIGHT_CONTROLLER_DIMENSIONS`/`pixhawk_4` already established (Geometry
axis, Minimum Geometric KNOW, FC B1): a free-text identity match attaches
a sourced L×W×H, never a catalog family, never a bind function, never a
`catalog_ref`. SpeedyBee F405 V4 (flight controller, 41.6×39.4×7.8mm) was
added to the existing `FLIGHT_CONTROLLER_MAP`/`FLIGHT_CONTROLLER_
DIMENSIONS`. Holybro M10 (GPS, 50×50×14.4mm) required a NEW `GPS_
DIMENSIONS` table (mirroring the FC one) since no GPS dims mechanism
existed yet, attached inside `extract_sensor_properties` exactly where
`gps_model` is already resolved.

## Files changed

- `src/jarvis/domains/aerial.py`:
  - `FLIGHT_CONTROLLER_MAP`: added three aliases (longest-first per the
    existing convention) — `"speedybee f405 v4"`, `"speedybee f405"`,
    `"f405 v4"` → `"speedybee_f405_v4"`. No bare `"f405"` or `"betaflight"`
    alias added or touched — those still resolve exactly as before
    (`"betaflight"` stays dims-less; a lone `"f405"` matches nothing at
    all, confirmed by T2).
  - `FLIGHT_CONTROLLER_DIMENSIONS`: added `"speedybee_f405_v4"` entry
    (41.6/39.4/7.8mm, GetFPV `source_url`, `source_note` disclosing the
    labeled L/W/H axis order (N1) and the separately-noted 10.5g weight /
    30.5×30.5mm mounting-hole pattern — neither modeled, both explicitly
    called out as NOT the component's own box).
  - `GPS_MAP`: added two aliases — `"holybro m10 gps"`, `"holybro m10"` →
    `"holybro_m10"`, both longer than the existing bare `"m10"` → so a
    message naming Holybro always resolves to the new canonical identity;
    a bare `"m10"` is untouched — still resolves to `"ublox_m10"`.
  - New `GPS_DIMENSIONS: dict[str, dict[str, object]]` (module-level,
    right after `GPS_MAP`, same shape/docstring style as `FLIGHT_
    CONTROLLER_DIMENSIONS`) — one entry, `"holybro_m10"` (50/50/14.4mm,
    HobbyDrone `source_url`, `source_note` disclosing the unlabeled-order
    verbatim mapping (N2a), the 32g weight (not modeled), and the
    separate 25×25×4mm antenna submodule (explicitly never folded into
    this box)).
  - `extract_sensor_properties`: after `gps_model` is resolved, looks up
    `GPS_DIMENSIONS.get(found_model)` and attaches `length_mm`/`width_mm`/
    `height_mm` with the same `confidence`/`source="declared"` as the
    `gps_model` property itself — mirrors `extract_flight_controller_
    properties`'s own dims-attach block line for line. Every other GPS
    model (`ublox_m8n`/`ublox_m9n`/`ublox_m10`/`here3`/`here3_plus`/
    `here_plus`/`here2`/`generic_gps`) has no entry in `GPS_DIMENSIONS`,
    so none of them are affected (T4, and the existing `test_control_
    component.py` GPS tests all still pass unchanged).
- `tests/test_geometry_sourced_fc_gps_b1.py` (new) — T1–T5, see below.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD ACTUAL synced (suite `2708`,
  new 🟡 LANDING entry, queue updated).
- `.jes/state/engineering_state.json` — top-level tracking fields synced;
  `engineer_ratification` left untouched.

**Not touched**: `library/**` (no `library/fc/`, no `library/sensors/` —
confirmed by `git status --short -- library/` showing nothing for this
cycle), `ui/spatial-board/**`, the battery family (`#4`'s own SKU/state
untouched here), `pyproject.toml` (version still `0.4.1`), the 5min
workspace (see the note below — this is deliberate, not an oversight).

## Note — 5min live re-declare left to Engineer smoke

The IC's own lock #8 describes the INTENDED live outcome ("stale FC
44×84×12 · sensors 40×40×12" should become the new sourced boxes after a
re-declare), and §5/§7 explicitly frame that re-declare as an ENGINEER
smoke action ("Engineer → smoke (re-declare FC + GPS)"), unlike the prior
#4 battery IC, whose own §4 Files table explicitly named `workspace/
autonomía-de-5min.../state.json` as something for the implementer to
rebind directly. This IC's §4 Files table names only `aerial.py` and the
new test file — no workspace path. Consistent with that distinction, the
5min workspace was left untouched this cycle; the Engineer's own smoke
pass will exercise the actual free-text re-declare path
(`extract_flight_controller_properties`/`extract_sensor_properties` via
the live orchestrator), which is also a more faithful smoke test of the
IDLE extraction path itself than a scripted state mutation would be.

## Behavior changed

- New: `extract_flight_controller_properties("speedybee f405 v4")` (and
  the two shorter aliases) now returns `model="speedybee_f405_v4"` plus
  41.6/39.4/7.8mm dims.
- New: `extract_sensor_properties("holybro m10")` (and `"holybro m10
  gps"`) now returns `gps_model="holybro_m10"` plus 50/50/14.4mm dims.
- Unchanged: every other FC/GPS identity and every existing test in
  `test_control_component.py` (51 passed together with the new file, run
  in the same invocation) — `pixhawk_4`'s own 44/84/12mm, generic
  `"pixhawk"`/`"betaflight"`/`ardupilot`/`naze32`/`matek` (dims-less),
  `ublox_m8n`/`m9n`/`m10`/`here3`/`here3_plus`/`here_plus`/`here2`/
  `generic_gps` (dims-less), `_flight_controller_completeness`/`_sensor_
  completeness` (neither reads `GPS_DIMENSIONS`/the new FC entry at all
  — dims never gate completeness, confirmed by inspection, no new test
  needed since the completeness evaluators are untouched code).

## Tests

New file `tests/test_geometry_sourced_fc_gps_b1.py` (5 tests):
- T1 `"speedybee f405 v4"` (and the two shorter aliases) →
  `model="speedybee_f405_v4"`, 41.6/39.4/7.8mm, `source="declared"`.
- T2 `pixhawk_4` regression (44/84/12mm) still holds; bare
  `"betaflight"` stays dims-less; bare `"f405"` matches nothing at all
  (`extract_flight_controller_properties("f405") == {}`).
- T3 `"holybro m10"` / `"holybro m10 gps"` → `gps_model="holybro_m10"`,
  50/50/14.4mm.
- T4 bare `"m10"` → `gps_model="ublox_m10"`, no L/W/H keys at all.
- T5 `_geometry_from_spec` on a `ComponentSpec` carrying each of the two
  new dims triples → correct box geometry for both.

Executed:
- `python -m pytest -q tests/test_geometry_sourced_fc_gps_b1.py tests/
  test_control_component.py` → 51 passed (5 new + 46 existing FC/GPS/
  sensor-completeness regressions, run together to directly confirm zero
  interference).
- `python -m pytest -q` (full suite) → **2708 passed**.
- Manual smoke via a throwaway script (shown above) confirming the exact
  extractor outputs for all four cited phrasings plus the two negative
  cases (bare `"f405"`, bare `"m10"`).

## Non-goals honored

- No `library/fc/` or `library/sensors/` created — the identity-linked
  free-text pattern was extended, never replaced with a catalog family.
- No `catalog_ref`/bind function for either FC or GPS.
- No Pixhawk table rewrite — `pixhawk_4`'s own entry is byte-unchanged.
- No dims on bare `ublox_m10` — the antenna's 25×25×4mm footprint is
  disclosed in `source_note` prose only, never modeled as a schema field
  or folded into the module's own box.
- No battery re-seed, no Rooster L×W, no version bump, no `ui/` change.

## Remaining risks

- None specific to this Buy. The `GPS_DIMENSIONS` table is a new
  module-level dict, but it follows `FLIGHT_CONTROLLER_DIMENSIONS`'s own
  established shape byte-for-byte (same key set: `length_mm`/`width_mm`/
  `height_mm`/`source_urls`/`source_note`), so no new pattern was
  introduced for a future reviewer to learn.
