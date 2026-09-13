# Implementation Report — #4f Sourced battery Tattu 2300mAh 4S 75C XT60 B1

Status: Done (implementation) — awaiting review + Engineer smoke
Parent: `implementation_contract_geometry_sourced_battery_tattu_2300_4s_b1.md`
Baseline: package `0.4.1` (unchanged) · suite `2718` → `2723` (2718 + 5 new). UI `83` (unchanged — no `ui/` file touched)

## Summary

Seeded a new Class A 4S battery SKU, `tattu_2300mah_4s_75c_xt60`, from
the Engineer's own locked §0.1 purchase-ground-truth citation (an RCDrone
product page — the Engineer determined the 5min project's prior 3S GenS
Ace pack, Deans plug, is likely not craft-compatible, and moved the
project to this 4S XT60 pack instead). Option A: a brand-new catalog
row; `gens_ace_2200mah_3s_35c_gtech` is NOT deleted or mutated — it stays
in the catalog, byte-stable, for other projects. The 5min workspace's
`battery` component was rebound to the new SKU.

## Files changed

- `library/baterias/_datos.json` — inserted `tattu_2300mah_4s_75c_xt60`
  immediately before `lipo_4s_1500mah` (start of the 4S family, matching
  this row's own electrical class). Fields: `chemistry`, `energy_wh`
  (34.04, computed 2300mAh×14.8V/1000 — same convention every other
  battery row uses), `mass_g` (270), `cells` (4), `nominal_voltage`
  (14.8), `capacity_mah` (2300), `c_rating` (75), `max_continuous_
  current_a` (172.5, `2.3×75`) with `max_continuous_current_source:
  "derived_from_c_rating"` (same convention as GenS Ace/CNHL/Spektrum/
  GNB), `manufacturer` ("Tattu"), `model`, `part_number`
  ("SRC-TAA23004S75X6", the path-hinted SKU code), `identity_status:
  "verified"`, `source_url` (UTM query param stripped from the pasted
  URL, per the IC's own instruction), `length_mm`/`width_mm`/`height_mm`
  (105/35/29), and a `source_note` disclosing: the craft-compatibility
  authority for this rebind, the explicit "GenS Ace not deleted"
  statement, the XT60/JST-XHR-5P connector facts (noted, not modeled —
  no connector schema field exists), the disclosed L±5/W±2/H±2mm and
  ±20g tolerances, the axis-mapping confidence (N1 — page states "Size
  (L x W x H): 105 x 35 x 29 mm", a labeled order, mapped directly), and
  the sold-out ("Agotado") availability disclosure (Engineer still cites
  it as the real purchase identity regardless — same disclosed-not-
  blocking precedent the #4c ESC "Discontinued" note established).
  - `gens_ace_2200mah_3s_35c_gtech` and every `lipo_4s_*` row: zero bytes
    changed (confirmed by T4/T5 and by `git diff` showing only an
    insertion).
- `workspace/autonomía-de-5min-4b63337fd4fd/state.json` — the `battery`
  component rebound from `gens_ace_2200mah_3s_35c_gtech` to
  `tattu_2300mah_4s_75c_xt60` via a **fresh** `bind_battery_from_catalog
  (new_sku)` call (no `base=`), with `.name`/`mounted_on`/`declared_box_
  pose`/`declared_fit_attestation` copied over explicitly afterward via
  `.model_copy` — the same discipline the #4e propeller rebind
  established, applied here even though (unlike that case) the old and
  new battery rows happen to project the exact same property-key set
  (both have `cells` and all three dims), so there was no actual leak
  risk this time — the fresh-bind pattern is simply the now-standard,
  strictly-safer default regardless of whether a given pair of rows is
  symmetric. Followed by `set_battery_component(state, new_spec,
  capacity_wh=34.04)` — the same single writer every prior battery bind
  in this session used — refreshing `current_parameters["battery_mass_
  kg"]` (0.18→0.27, going through the GenS Ace value from the #4 cycle)
  and `battery_cell_count` (3→4); `battery_capacity_wh` moved 24.42→34.04
  correctly.
- `tests/test_geometry_sourced_battery_tattu_2300_4s_b1.py` (new) —
  T1–T5, see below.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD ACTUAL synced (suite `2723`,
  new 🟡 LANDING entry, queue updated).
- `.jes/state/engineering_state.json` — top-level tracking fields synced;
  `engineer_ratification` left untouched.

**Not touched**: `library/motores/` (`#4d` stays parked), `library/esc/`,
`library/helices/` (both untouched by this cycle), `library/frames/`
(Rooster untouched), `ui/spatial-board/**`, `pyproject.toml` (version
still `0.4.1`), no census-list test needed updating this time (no test
in the suite asserts a fixed total battery count, unlike the propeller
family's own `list_propellers()` golden count).

## Behavior changed

- New: `default_library.get_battery("tattu_2300mah_4s_75c_xt60")`
  resolves to a fully-cited Class A 4S pack; `bind_battery_from_catalog`
  projects its L×W×H/mass/energy/cells exactly like every other Class A
  battery does.
- Unchanged: `gens_ace_2200mah_3s_35c_gtech` (byte-stable — T4, and it
  remains fully usable for any other project — this Buy never removes a
  catalog row, only re-points which one the 5min project binds to),
  every `lipo_4s_*` row (T5), `catalog_bind.py` (zero diff — the existing
  `bind_battery_from_catalog` already handled everything this Buy
  needed).
- 5min-workspace-only: the `battery` component's identity/dims/mass/
  cells/energy changed; its declared pose/mount survived unchanged.

## Tests

New file `tests/test_geometry_sourced_battery_tattu_2300_4s_b1.py` (5
tests):
- T1 `get_battery(new SKU)` → L/W/H 105/35/29, mass 270, C 75, cells 4,
  nominal_voltage 14.8, capacity_mah 2300, energy_wh 34.04,
  max_continuous_current_a 172.5, manufacturer "Tattu",
  `identity_status == "verified"`, `source_url` contains "rcdrone.top".
- T2 `bind_battery_from_catalog` projects L×W×H/mass/`battery_capacity_
  wh`/`chemistry`/`cell_count` all with `source == "declared"`, correct
  `catalog_ref`.
- T3 `_geometry_from_spec` on the bound spec → `{"shape": "box",
  "length_mm": 105.0, "width_mm": 35.0, "height_mm": 29.0}`.
- T4 `gens_ace_2200mah_3s_35c_gtech` unchanged — dims/mass/C/cells all
  still their original #4-cycle values.
- T5 `lipo_4s_1500mah` (CNHL), `lipo_4s_5000mah` (Spektrum), and
  `lipo_4s_10000mah` (uncited placeholder, dims still `None`) all
  unchanged — confirming this Buy touched nothing else in the 4S family.

Executed:
- `python -m pytest -q tests/test_geometry_sourced_battery_tattu_2300_4s_
  b1.py` → 5 passed.
- `python -m pytest -q` (full suite) → **2723 passed** both before and
  after the 5min workspace rebind (the rebind touches no test-covered
  file).
- Manual smoke of the mutated `state.json` via a throwaway script:
  confirmed `battery.name`/`catalog_ref.sku` == new SKU, `properties`
  dims/mass/energy/cells updated, `mounted_on`/`declared_box_pose`
  preserved verbatim, `declared_fit_attestation` still `None` (nothing to
  clear — it was already absent, unlike the #4c ESC rebind's case), and
  `current_parameters` refreshed correctly (`battery_capacity_wh:
  34.04`, `battery_cell_count: 4`, `battery_mass_kg: 0.27`).
- Manual smoke of `project_spatial_nodes` on the mutated state: the
  `battery` node's `geometry` is now the 105×35×29 box,
  `declaredName == "tattu_2300mah_4s_75c_xt60"`, and `sobres` still
  reports the same overlap screening text (pose numbers unchanged by
  this Buy).

## Non-goals honored

- `gens_ace_2200mah_3s_35c_gtech` never deleted or mutated (T4) — it
  remains a fully valid catalog row.
- Every `lipo_4s_*` row untouched (T5).
- No XT60/JST-XHR-5P connector schema invented — disclosed in
  `source_note` prose only.
- No version bump (`0.4.1` unchanged).
- Motor (`#4d`, parked)/ESC (`#4c`)/FC+GPS (`#4b`)/propeller (`#4e`)
  families untouched by this cycle.

## Remaining risks

- None specific to this Buy. Unlike the #4e propeller rebind, no
  optional-property asymmetry existed between the old (GenS Ace) and new
  (Tattu) battery rows — both project the exact same property-key set —
  so the fresh-bind discipline was applied as a matter of consistent
  practice rather than to fix an active leak.
