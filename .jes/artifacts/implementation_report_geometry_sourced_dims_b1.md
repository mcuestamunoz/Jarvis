# Implementation Report — #4 Sourced dims B1 (5min Class A seed pack)

Status: Done (implementation) — awaiting review + Engineer smoke
Parent: `implementation_contract_geometry_sourced_dims_b1.md`
Baseline: package `0.4.1` (unchanged) · suite `2697` → `2703` (2697 + 6 new) · UI `83` (unchanged — no `ui/` file touched)

## Summary

Seeded a new Class A battery SKU, `gens_ace_2200mah_3s_35c_gtech`, from
the Engineer's own locked §0.1 purchase-ground-truth citation bag
(genstattu.com product page — real pack the Engineer will order/receive).
Option A per the Engineer's 2026-09-10 decision: a brand-new catalog row,
never a mutation of the generic `lipo_3s_2200mah` entry (which stays
byte-stable — no dims, mass 180g, C 50, no manufacturer). The 5min
workspace's `battery` component was rebound to the new SKU via the
existing `bind_battery_from_catalog`/`set_battery_component` writer pair
— no new geometry pipeline — so the Board now draws 74.7×33.5×25.4mm
instead of the stale declared 80×34×22 override, and `battery_mass_kg`
recalculates to 0.143 (was 0.18).

## Files changed

- `library/baterias/_datos.json` — inserted `gens_ace_2200mah_3s_35c_
  gtech` immediately after `lipo_3s_2200mah` (same electrical class,
  adjacent for readability). Fields: `chemistry`, `energy_wh` (24.42,
  computed 2200mAh×11.1V/1000, matching the generic row's own value),
  `mass_g` (143), `cells` (3), `nominal_voltage` (11.1), `capacity_mah`
  (2200), `c_rating` (35), `max_continuous_current_a` (77, `2.2×35`) with
  `max_continuous_current_source: "derived_from_c_rating"` (same
  convention as the CNHL/Spektrum/GNB rows), `manufacturer` ("Gens Ace"),
  `model`, `identity_status: "verified"`, `source_url`, `length_mm`/
  `width_mm`/`height_mm` (74.7/33.5/25.4), and a `source_note` disclosing:
  the Engineer purchase-ground-truth authority, the explicit distinction
  from the untouched generic row, the burst-70C fact (noted, not modeled
  — no `burst_c_rating` field exists), the G-tech balancer / Deans main
  plug facts (no dedicated schema fields for these — folded into prose,
  same as every other row's non-modeled facts), the ±20g net-weight
  tolerance, and the axis-mapping confidence (N1 — the page states
  "Dimensions: 74.7*33.5*25.4mm (LxWxH)", an explicitly labeled order,
  mapped directly).
  - `lipo_3s_2200mah` itself: zero bytes changed (confirmed by T4 and by
    `git diff` showing only an insertion, no modification to that block).
- `workspace/autonomía-de-5min-4b63337fd4fd/state.json` — the `battery`
  component rebound from `lipo_3s_2200mah` to `gens_ace_2200mah_3s_35c_
  gtech` via `bind_battery_from_catalog(new_sku, base=old_spec)` (merging
  the new catalog `properties`/`catalog_ref` onto the existing spec, so
  `mounted_on: "frame_plate_2"`, `declared_box_pose` (the Situar-placed
  pose), and `declared_fit_attestation: null` all survive unchanged —
  this is a pure identity+dims+mass change, not a pose/mount reset,
  matching how the existing envelope writer already treats a geometry
  change: it never touches pose/mount, only a stale fit attestation
  which was already `null` here) plus a manual `.model_copy(update=
  {"name": new_sku})` (the base-merge path in `bind_battery_from_catalog`
  deliberately never updates `.name` — confirmed by reading
  `orchestrator.py`'s own IDLE catalog-rebind comment explaining exactly
  why a genuine SKU switch must patch `.name` separately). Then
  `set_battery_component(state, new_spec, capacity_wh=24.42)` — the
  SAME single writer every other battery bind already goes through — to
  refresh `current_parameters["battery_mass_kg"]` (0.18 → 0.143) and
  confirm `battery_capacity_wh`/`battery_cell_count` are unchanged
  (24.42 / 3, since neither the pack's energy nor cell count differs from
  the generic placeholder it replaced). Written via the same
  `write_json`+`ProjectState.model_validate_json` pattern
  `board_pose_bridge.py`/`board_fit_attestation_bridge.py` already use for
  direct `state.json` mutation — no new persistence path.
- `tests/test_geometry_sourced_dims_b1.py` (new) — T1–T6, see below.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD ACTUAL synced (suite `2703`,
  new 🟡 LANDING entry, queue updated).
- `.jes/state/engineering_state.json` — top-level tracking fields synced;
  `engineer_ratification` left untouched.

**Not touched**: `src/jarvis/core/catalog_bind.py` (see N1 below —
this was a deliberate no-op, not an oversight), `library/frames/
_datos.json` (Rooster `plates[]` confirmed still thickness-only, T5),
`ui/spatial-board/**`, `pyproject.toml` (version still `0.4.1`), the
10min workspace (out of the IC's own scope — only 5min was named).

## N1 — `source="declared"` kept on projected mm keys (IC §0 lock #6)

The IC's own lock #6 said to *prefer* `source="catalog"` on the newly
projected Class A mm keys, but to **STOP and keep `declared`** if that
would break a locked golden test. It would: `tests/test_catalog_bind_v1.py`
asserts `bound.properties["length_mm"].source == "declared"` for
`lipo_4s_1500mah` (a pre-existing Class A battery bind), and every other
family's own bind helper (`bind_motor_from_catalog`'s stator/shaft dims,
`bind_propeller_from_catalog`'s hub dims) uses `source="declared"`
uniformly too — there is no existing `source="catalog"` value anywhere in
the codebase to introduce consistently. Per the IC's own pre-authorized
fallback, `catalog_bind.py` was left completely untouched; the new SKU's
projected dims carry `source="declared"`, identical to every sibling
family. This is a documentation note, not an open question — the IC
itself resolved this branch in advance.

## Behavior changed

- New: `default_library.get_battery("gens_ace_2200mah_3s_35c_gtech")`
  resolves to a fully-cited Class A pack; `bind_battery_from_catalog`
  projects its L×W×H/mass/energy/cells exactly like every other
  Class A battery.
- Unchanged: `lipo_3s_2200mah` (byte-stable — T4), every other seeded
  Class A battery (T6), Rooster `armattan_rooster_5in.plates[]` (T5),
  `catalog_bind.py`, `pose_envelope_screening.py`, `ASSEMBLY_READY`/
  readiness rollup (no code path there reads battery dims at all — never
  touched, never needed touching).
- 5min-workspace-only: the `battery` component's identity/dims/mass
  changed; its declared pose/mount/attestation fields did not.

## Tests

New file `tests/test_geometry_sourced_dims_b1.py` (6 tests):
- T1 `get_battery(new SKU)` → L/W/H 74.7/33.5/25.4, mass 143, C 35, cells
  3, nominal_voltage 11.1, capacity_mah 2200, manufacturer "Gens Ace",
  `identity_status == "verified"`, `source_url` contains "genstattu.com".
- T2 `bind_battery_from_catalog` projects all three mm keys and mass with
  `source == "declared"` (see N1), correct `catalog_ref`.
- T3 `_geometry_from_spec` on the bound spec → `{"shape": "box",
  "length_mm": 74.7, "width_mm": 33.5, "height_mm": 25.4}`.
- T4 `lipo_3s_2200mah` still has no L×W×H, mass 180, C 50, no
  manufacturer — byte-stable.
- T5 Rooster `armattan_rooster_5in.plates[]` entries still have no
  `length_mm`/`width_mm` — no invent.
- T6 `lipo_4s_1500mah` (CNHL) and `lipo_6s_6000mah` (GNB) dims/mass
  unchanged from their existing seeded values.

Executed:
- `python -m pytest -q tests/test_geometry_sourced_dims_b1.py` → 6
  passed.
- `python -m pytest -q` (full suite) → **2703 passed**.
- Manual smoke of the actual mutated `state.json` via a throwaway script:
  confirmed `battery.name`/`catalog_ref.sku` == new SKU, `properties`
  dims/mass/wh/cells updated, `mounted_on`/`declared_box_pose`/
  `declared_fit_attestation` all preserved verbatim, and
  `current_parameters["battery_mass_kg"] == 0.143` (was `0.18`) with
  `battery_capacity_wh`/`battery_cell_count` unchanged (24.42 / 3).
- Manual smoke of `project_spatial_nodes` on the mutated state: the
  `battery` node's `geometry` is now the 74.7×33.5×25.4 box and its
  `declaredName` shows the new SKU; the `sobres` field still fires
  ("Los sobres se solapan..." — screening, no verificado) since the pose
  numbers themselves didn't change.

## Non-goals honored

- No crawler — the citation bag was Engineer-provided; `source_url` was
  not re-fetched programmatically in this session (per the IC's own "if
  useful" wording, and since the bag was already complete and internally
  consistent).
- No Rooster/frame Main Plate L×W invented (T5).
- No `#4b` user-catalog-contribution flow.
- No Conversation Engine, no version bump (`0.4.1` unchanged).
- Generic `lipo_3s_2200mah` never mutated (T4).
- No XT60/harness box invented — untouched, out of scope.

## Remaining risks

- The `source_url` was not re-verified live in this session (network
  fetch was judged unnecessary given the Engineer's bag was complete and
  self-consistent — energy_wh derivation matched the generic row's own
  convention exactly, and the dimension quote was unambiguous/labeled).
  If the Engineer wants the page re-confirmed before smoke, that is a
  zero-code follow-up, not a re-open of this IC.
- The 5min rebind is a direct workspace mutation (not a game-state write
  through the orchestrator's own IDLE rebind flow) — chosen because the
  IC's own Files table names `state.json` directly rather than an IDLE
  bridge, and because a live orchestrator session's IDLE rebind path
  (`_apply_delta`'s energy_wh-driven switch) is designed for a DIFFERENT
  trigger (a changed `battery_capacity_wh` parameter) that doesn't apply
  here (the energy_wh is identical between the two SKUs) — reusing it
  would have required inventing a reason for the Wh to "change" that
  isn't true. The direct-mutation approach reuses the same writer
  (`set_battery_component`) and the same persistence helper
  (`write_json`) real bridges already use, so no new pipeline was
  introduced.
