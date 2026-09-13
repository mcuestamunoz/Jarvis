# Implementation Report — #4c Sourced ESC SpeedyBee BLS 60A 4-in-1 B1

Status: Done (implementation) — awaiting review + Engineer smoke
Parent: `implementation_contract_geometry_sourced_esc_speedybee_b1.md`
Baseline: package `0.4.1` (unchanged) · suite `2703` (IC's stated baseline) / actual pre-cycle `2708` (after the parallel #4b FC+GPS cycle landed) → `2713` (2708 + 5 new). UI `83` (unchanged — no `ui/` file touched)

## Summary

Seeded a new Class A ESC SKU, `speedybee_bls_60a_30x30_4in1`, from the
Engineer's own locked §0.1 purchase-ground-truth citation (SpeedyBee's
own product page — a real 4-in-1 ESC the Engineer will order/receive,
cited despite the page showing "Discontinued" on re-fetch, per the IC's
own explicit instruction to disclose rather than STOP or invent a
replacement). Option A: a brand-new catalog row, `hobbywing_xrotor_40a_6s`
stays byte-stable. The 5min workspace's `esc` component was rebound to
the new SKU via the existing `bind_esc_from_catalog`/`set_control_
component` writer pair — the SAME pair the live "ESC visor rebind B1"
IDLE flow already uses for exactly this kind of switch (`base=` merge to
preserve pose/mount) — so the Board now draws 45.6×44×8mm instead of the
stale Hobbywing 50×21.6×12 box.

## Files changed

- `library/esc/_datos.json` — inserted `speedybee_bls_60a_30x30_4in1`
  after `hobbywing_xrotor_40a_6s`. Fields: `manufacturer` ("SpeedyBee"),
  `model`, `part_number` ("SB-BLS-60A"), `identity_status: "verified"`,
  `esc_topology: "4in1"`, `channels: 4`, `continuous_current_a: 60` (the
  page's own "60A * 4" — modeled as the per-channel figure, the same
  convention `continuous_current_a` already carries for the single-channel
  Hobbywing row), `burst_current_a: 80`, `continuous_current_source:
  "manufacturer_spec"`, `voltage_min`/`voltage_max` (9.0 / 25.2) derived
  from `cells_min`/`cells_max` (3 / 6) using the EXACT SAME per-cell
  convention the Hobbywing row already encodes (3.0V/cell floor, 4.2V/cell
  ceiling — confirmed by back-computing Hobbywing's own 6.0V/25.2V from
  its 2S/6S range before writing this row, so both rows share one
  consistent, undocumented-but-inferable convention rather than two
  different ones), `mass_g: 23.5`, `source_url`, `length_mm`/`width_mm`/
  `height_mm` (45.6/44/8), and a `source_note` disclosing: the BLHeli_S
  J-H-40 firmware and current-sensor Scale=400/Offset=0 facts (noted, not
  modeled — no such schema fields exist), the 30.5×30.5mm/4mm mounting
  pattern (noted, not modeled — no `mount_pattern` field exists, per lock
  #9's explicit "do not invent" boundary), the axis-mapping confidence
  (N1 — the page states "Dimension: 45.6(L) * 44(W) *8mm(H)", an
  explicitly labeled order, mapped directly), and the Discontinued
  availability disclosure.
  - `hobbywing_xrotor_40a_6s`: zero bytes changed (confirmed by T4 and by
    `git diff` showing only an insertion).
- `workspace/autonomía-de-5min-4b63337fd4fd/state.json` — the `esc`
  component rebound from `hobbywing_xrotor_40a_6s` to `speedybee_bls_60a_
  30x30_4in1` via `bind_esc_from_catalog(new_sku, base=old_spec)` — the
  SAME call shape `orchestrator._apply_component_esc_catalog_pick` (the
  live "ESC visor rebind B1" IDLE flow) already uses to preserve
  `declared_box_pose`/`mounted_on` across a catalog switch — followed by
  `set_control_component`, the same single writer that flow uses. Two
  deliberate additions beyond that flow's own precedent:
  1. `.model_copy(update={"name": new_sku})` — the base-merge path never
     updates `.name` (confirmed by reading `bind_esc_from_catalog`'s own
     code), and the Board's `declaredName` field reads `spec.name`
     directly, so without this patch the card would still show the old
     Hobbywing identity string next to the new SpeedyBee dims. This
     mirrors the reasoning already documented in the #4 battery IC's own
     report (N1-style note there) for the identical asymmetry in
     `bind_battery_from_catalog`.
  2. `declared_fit_attestation` explicitly cleared. The live ESC spec
     carried a valid Engineer-declared fit attestation (against
     `flight_controller`, fingerprinted on the ESC's OLD 50×21.6×12mm
     geometry). This rebind path (`bind_esc_from_catalog`+`set_control_
     component`) is NOT one of the two writers
     (`set_component_declared_box_pose`/`set_component_declared_box_
     envelope`) that the Fit attestation B1 Buy hooked its automatic
     invalidation into, so nothing would have cleared it automatically.
     The Board projector's own stale-fingerprint check (recomputes and
     compares at read time) would have hidden the "verificación" field
     regardless once the geometry changed — no lying seal could ever have
     reached the screen — but leaving a now-permanently-mismatched object
     sitting in `state.json` forever contradicts that Buy's own
     "disk stays honest" preference for persist-clear over projector-only
     hiding. Clearing it here applies that established discipline to a
     write path the original Buy didn't anticipate, rather than inventing
     a new rule.
- `tests/test_geometry_sourced_esc_speedybee_b1.py` (new) — T1–T5, see
  below.
- `tests/test_geometry_esc_visor_rebind_b1.py` — one pre-existing test,
  `test_p3_library_hobbywing_box_and_single_row`, asserted `list_escs()`
  returns exactly `[hobbywing_xrotor_40a_6s]` — a "single catalog row"
  golden that this Buy's second Class A row necessarily breaks. Renamed
  to `test_p3_library_hobbywing_box_present` and the final assertion
  changed from equality-to-a-singleton-list to `_HOBBYWING in names` —
  this is a genuine catalog-size regression caused by the IC's own intent
  (adding a second row), not a weakening: Hobbywing's own dims are still
  asserted unchanged in the same test, and every OTHER test in that file
  (the resolver-phrase parametrize, the pick-by-name-then-index flows,
  the composite-propulsion guard) needed zero changes because none of
  them assumed a single-row catalog — only this one static list-equality
  check did. Module docstring's "1-row Hobbywing catalog" phrase updated
  to match. 11/11 tests in that file still pass.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD ACTUAL synced (suite `2713`,
  new 🟡 LANDING entry, queue updated).
- `.jes/state/engineering_state.json` — top-level tracking fields synced;
  `engineer_ratification` left untouched.

**Not touched**: `library/fc/`, `library/sensors/`, `library/frames/`
(Rooster `plates[]` confirmed still thickness-only, T5), the battery
family (GenS Ace confirmed unchanged, T5), `ui/spatial-board/**`,
`pyproject.toml` (version still `0.4.1`), no `mount_pattern` schema field
invented anywhere.

## Behavior changed

- New: `default_library.get_esc("speedybee_bls_60a_30x30_4in1")` resolves
  to a fully-cited Class A 4-in-1 ESC; `bind_esc_from_catalog` projects
  its L×W×H/mass/`current_a` exactly like the existing Class A ESC does.
- Unchanged: `hobbywing_xrotor_40a_6s` (byte-stable — T4), Rooster
  `armattan_rooster_5in.plates[]`, the GenS Ace battery SKU (T5),
  `catalog_bind.py` (zero diff — the existing `bind_esc_from_catalog`
  already handled everything this Buy needed).
- 5min-workspace-only: the `esc` component's identity/dims/mass/current
  changed; its declared pose/mount survived; its now-stale fit
  attestation was cleared (see above).
- `test_geometry_esc_visor_rebind_b1.py`'s catalog-size assumption
  updated (see above) — every other assertion in that file, and every
  other test in the full suite, is unaffected.

## Tests

New file `tests/test_geometry_sourced_esc_speedybee_b1.py` (5 tests):
- T1 `get_esc(new SKU)` → L/W/H 45.6/44/8, mass 23.5, continuous 60A,
  burst 80A, channels 4, topology "4in1", cells 3–6, manufacturer
  "SpeedyBee", `identity_status == "verified"`, `source_url` contains
  "speedybee.com".
- T2 `bind_esc_from_catalog` projects L×W×H + mass + `current_a` (60.0)
  with `source == "declared"`, correct `catalog_ref`.
- T3 `_geometry_from_spec` on the bound spec → `{"shape": "box",
  "length_mm": 45.6, "width_mm": 44.0, "height_mm": 8.0}`.
- T4 `hobbywing_xrotor_40a_6s` unchanged — topology/channels/current/
  dims/mass all still their original values.
- T5 Rooster `plates[]` still thickness-only; GenS Ace battery SKU
  unchanged — confirming this Buy touched nothing outside the ESC family.

Executed:
- `python -m pytest -q tests/test_geometry_sourced_esc_speedybee_b1.py`
  → 5 passed.
- `python -m pytest -q tests/test_geometry_esc_visor_rebind_b1.py` → 11
  passed (was 10 passed + 1 failed before the P3 fix).
- `python -m pytest -q` (full suite) → **2713 passed**.
- Manual smoke of the mutated `state.json` via a throwaway script:
  confirmed `esc.name`/`catalog_ref.sku` == new SKU, `properties`
  dims/mass/current updated, `mounted_on`/`declared_box_pose` preserved
  verbatim, `declared_fit_attestation` now `None` (was a valid seal
  against the old geometry), and `project_spatial_nodes` emits the
  45.6×44×8 box with `declaredName == "speedybee_bls_60a_30x30_4in1"`
  and no stale `verificación` field in the projected `fields`.

## Non-goals honored

- `hobbywing_xrotor_40a_6s` never rewritten (T4).
- No `mount_pattern` schema field invented for the 30.5×30.5mm/4mm hole
  pattern — disclosed in `source_note` prose only.
- No stack-height invented.
- No version bump (`0.4.1` unchanged).
- FC+GPS (#4b) and battery (#4) families untouched by this cycle.

## Remaining risks

- The `continuous_current_a` field models the page's own per-channel
  figure (60A) directly, matching how `continuous_current_a` already
  behaves for a single-channel ESC — there is no separate
  "per-board-total" field in `EscSpec`, so a future 4-in-1-aware
  calculation (e.g. total board current draw = 60A × 4 channels) would
  need to multiply by `channels` itself; this Buy did not add such a
  calculation (out of scope — Structure/electrical compatibility logic is
  untouched) but the raw numbers needed for it are all present on the
  row (`continuous_current_a=60`, `channels=4`).
- The voltage_min/voltage_max per-cell convention (3.0V/4.2V) was
  reverse-engineered from the existing Hobbywing row rather than being
  independently documented anywhere in the codebase — if that convention
  is ever formalized (e.g. a shared helper), this row already conforms to
  it, so no follow-up edit would be needed.
