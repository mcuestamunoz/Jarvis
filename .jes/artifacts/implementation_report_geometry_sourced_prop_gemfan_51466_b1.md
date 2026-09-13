# Implementation Report — #4e Sourced prop Gemfan Hurricane MCK 51466-3 V2 B1

Status: Done (implementation) — awaiting review + Engineer smoke
Parent: `implementation_contract_geometry_sourced_prop_gemfan_51466_b1.md`
Baseline: package `0.4.1` (unchanged) · suite `2713` → `2718` (2713 + 5 new). UI `83` (unchanged — no `ui/` file touched)

## Summary

Seeded a new Class A propeller SKU, `gemfan_hurricane_mck_51466_3_v2`,
from the Engineer's own locked §0.1 purchase-ground-truth citation
(HobbyDrone product page). Diameter is derived from the page's own stated
131.8mm (`5.189in`, rounded to 4 places) — never the bare "5 inch"
category the model-code prefix might suggest. Pitch is 3.6in taken
directly from the page — never 4.66 decoded from the model code's
trailing digits. Option A: `gf_5045x3` stays byte-stable. The 5min
workspace's `propellers` component was rebound to the new SKU, and the
review process (via an explicit AskUserQuestion gate) surfaced and fixed
one real, disclosed side effect on the "ayúdame a elegir" propeller
suggestion list.

## Files changed

- `library/helices/_datos.json` — inserted `gemfan_hurricane_mck_51466_3_
  v2` after `gf_5045x3`. Fields: `diameter_in: 5.189` (131.8/25.4,
  rounded), `pitch_in: 3.6`, `mass_g: 4.2`, `manufacturer` ("Gemfan"),
  `model`, `identity_status: "verified"`, `source_url`, `blade_count: 3`,
  `material: "PC"`, `hub_thickness_mm: 6.8`, `shaft_bore_mm: 5` (M5 bore
  — no `hub_diameter_mm`, since the page never states the hub's own
  outer diameter, per lock #6's explicit "M5 is bore, not hub OD"
  distinction), and a `source_note` disclosing the diameter/pitch
  derivation, the deliberate omission of `hub_diameter_mm`, the color/
  package-contents facts (not modeled), and the qualitative "2207-2306
  and up" motor-compatibility note (never modeled as `compatible_kv_band`
  — no numeric band was ever stated).
  - `gf_5045x3`: zero bytes changed (confirmed by T4 and by `git diff`
    showing only an insertion).
- `src/jarvis/core/propeller_catalog_assist.py` — `build_propeller_
  catalog_suggestions`'s `limit` parameter bumped from `5` to `6`.
  **Engineer-approved via an explicit AskUserQuestion gate** (see below)
  — this file was NOT in the IC's own stated file list, but adding the
  new SKU caused a real, disclosed regression this fix directly
  addresses. Docstring updated explaining the exact cause and fix.
- `workspace/autonomía-de-5min-4b63337fd4fd/state.json` — the
  `propellers` component rebound from `gf_5045x3` to `gemfan_hurricane_
  mck_51466_3_v2` via a **fresh** `bind_propeller_from_catalog(new_sku)`
  call (no `base=`), with `mounted_on`/`declared_box_pose`/`declared_fit_
  attestation` copied over explicitly afterward via `.model_copy`. See
  the "N1 — fresh bind, not a base-merge" note below for why.
- `tests/test_geometry_sourced_prop_gemfan_51466_b1.py` (new) — T1–T5,
  see below.
- `tests/test_geometry_propeller_cited_seeds_b2.py` — `test_t8_list_
  propellers_includes_new_sku_18_rows` bumped from 18 to 19 rows,
  asserting both `apc_10x6_ep` and the new SKU are present (a required
  census update, not a weaken — same discipline the IC's own §1 called
  for).
- `tests/test_geometry_propeller_envelope_b0_b1.py` — `test_t9_only_
  cited_propellers_have_mass_g`'s golden set of 3 mass-bearing SKUs
  extended to 4, adding the new SKU (same discipline).
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD ACTUAL synced (suite `2718`,
  new 🟡 LANDING entry, queue updated).
- `.jes/state/engineering_state.json` — top-level tracking fields synced;
  `engineer_ratification` left untouched.

**Not touched**: `library/motores/` (`#4d` stays parked, untouched),
`library/esc/`, `library/baterias/` (both untouched by this cycle),
`ui/spatial-board/**`, `pyproject.toml` (version still `0.4.1`).

## N1 — fresh bind, not a base-merge (a real bug I found and fixed before landing)

The prior three `#4*` rebinds (battery, FC/GPS text-only, ESC) all used
`bind_*_from_catalog(new_sku, base=old_spec)` to preserve `mounted_on`/
`declared_box_pose` across a SKU switch, because in every one of those
cases the old and new catalog rows projected the exact same SET of
optional property keys (e.g. both ESCs had `length_mm`/`width_mm`/
`height_mm`/`mass_g`/`current_a`). For propellers this assumption broke:
`gf_5045x3` has `hub_diameter_mm=5.0` (an old, since-superseded reading
of that row's own hub bore as a "diameter"), but the new Hurricane MCK
citation correctly has NO `hub_diameter_mm` (M5 is a bore, not a stated
outer hub OD — lock #6's own explicit distinction). A `base=` merge
(`{**old.properties, **new_projected}`) would have left that stale
`hub_diameter_mm=5.0` sitting on the NEW spec, since the new SKU's own
`projected` dict never sets that key to overwrite it — exactly the kind
of leaked, uncited claim this whole sourced-geometry initiative exists to
prevent. Caught this via a manual inspection of the mutated `state.json`
before calling the rebind "done"; fixed by binding fresh (`bind_
propeller_from_catalog(new_sku)`, no `base=`) and then copying
`mounted_on`/`declared_box_pose`/`declared_fit_attestation` — which live
on `ComponentSpec` directly, never inside `.properties` — onto the fresh
spec afterward. The 5min propeller had no pose set and no attestation
(`mounted_on: "motors"` only), so this particular rebind's real-world
impact was limited to the leaked field, but the fix generalizes correctly
regardless.

## N2 — Engineer-approved suggestion-limit bump (surfaced via AskUserQuestion)

Adding the new SKU made it the 6th propeller compatible with
`emax_rs2205s_2300` (`match_motor_propeller`'s ±1.0" tolerance rule).
`build_propeller_catalog_suggestions` caps its "ayúdame a elegir" list at
a fixed `limit` and sorts by `list_propellers()`'s own alphabetical
order — the new SKU (`gemfan_hurricane_mck_51466_3_v2`) sorts before
`hq_5045_bn`, pushing it out of the default top-5 window. This mattered
beyond a stale test assertion: `hq_5045_bn` is tied by exact name to real
seeded `operating_points` (measured thrust/RPM/voltage) on that motor's
own catalog row, so the live wizard would have stopped offering a
physically-measured propeller for its own motor. This was outside the
IC's own stated scope (`propeller_catalog_assist.py` wasn't in its Files
table), so I presented three options via `AskUserQuestion` rather than
picking unilaterally: (a) bump the limit 5→6, (b) leave it capped and
update the tests to accept `hq_5045_bn`'s reduced reachability, or (c)
rename the new SKU to sort after `hq_5045_bn` alphabetically (at the cost
of breaking the sibling Gemfan-row naming convention). **The Engineer
chose (a)** — the limit was bumped by exactly the delta this Buy
introduced, with the reasoning documented in the function's own
docstring. Three pre-existing tests in `tests/test_propeller_catalog_bind_
ux.py` (`test_propeller_component_wizard_help_choose_after_motors_bound`,
`test_propeller_pick_sets_catalog_ref_and_reresolves_op`, `test_propeller_
idle_help_choose_noop_when_catalog_ref_set`) needed no edits at all once
the limit was bumped — they went back to green on their own, confirming
the limit bump was the correct, minimal fix rather than a test-side
workaround.

## Behavior changed

- New: `default_library.get_propeller("gemfan_hurricane_mck_51466_3_v2")`
  resolves to a fully-cited Class A prop; `bind_propeller_from_catalog`
  projects its bag exactly like every other cited propeller does.
- `build_propeller_catalog_suggestions`'s default `limit` is now 6
  (Engineer-approved), so the "ayúdame a elegir" propeller wizard can show
  one more compatible candidate than before for any motor with 6+
  matches — a strict widening, never a narrowing.
- Unchanged: `gf_5045x3` (byte-stable — T4), every other seeded
  propeller, `catalog_bind.py` (zero diff — `bind_propeller_from_catalog`
  already handled everything this Buy needed).
- 5min-workspace-only: the `propellers` component's identity/dims/mass/
  hub-bag changed; `mounted_on` survived; no stale `hub_diameter_mm`
  leaked onto the new spec (N1).

## Tests

New file `tests/test_geometry_sourced_prop_gemfan_51466_b1.py` (5 tests):
- T1 `get_propeller(new SKU)` → diameter_in≈5.189, pitch 3.6, mass 4.2,
  blades 3, hub_thickness 6.8, shaft_bore 5, `hub_diameter_mm is None`,
  material "PC", manufacturer "Gemfan", `identity_status == "verified"`,
  `source_url` contains "hobbydrone.cz".
- T2 `bind_propeller_from_catalog` projects the full bag with
  `source == "declared"`; `hub_diameter_mm` absent from projected
  properties (confirms the bind itself never invents it, independent of
  the rebind-script fix in N1).
- T3 `_geometry_from_spec` on the bound spec → `{"shape": "disk",
  "diameter_mm": ≈131.8}`.
- T4 `gf_5045x3` unchanged — diameter/pitch/mass/hub bag/material all
  still their original values.
- T5 Pitch is exactly 3.6, explicitly asserted `!= 4.66`.

Updated tests (both genuine census/regression fixes, not weakenings):
- `tests/test_geometry_propeller_cited_seeds_b2.py::test_t8_...` — 18→19
  rows, both `apc_10x6_ep` and the new SKU asserted present.
- `tests/test_geometry_propeller_envelope_b0_b1.py::test_t9_...` — the
  mass-bearing SKU set extended by one.

Executed:
- `python -m pytest -q tests/test_geometry_sourced_prop_gemfan_51466_b1.py
  tests/test_geometry_propeller_cited_seeds_b2.py` → 13 passed.
- `python -m pytest -q tests/test_propeller_catalog_bind_ux.py tests/
  test_geometry_propeller_envelope_b0_b1.py` → 17 passed (confirms the
  limit-bump fix with zero test-file edits needed there).
- `python -m pytest -q` (full suite) → **2718 passed**.
- Manual smoke of the mutated `state.json`: confirmed `propellers.name`/
  `catalog_ref.sku` == new SKU, properties match the citation bag exactly
  (no stale `hub_diameter_mm`), `mounted_on == "motors"` preserved, and
  `project_spatial_nodes` emits a disk (`diameter_mm ≈ 131.8006`) with
  `solidCopies == 4` (unaffected — motor-count-driven, independent of
  which propeller SKU is bound).

## Non-goals honored

- `gf_5045x3` never rewritten (T4).
- Pitch never decoded from the model code's digits (T5) — taken directly
  from the page's own explicit "Pitch: 3.6inch" statement.
- No hub cylinder / no invented `hub_diameter_mm`.
- No numeric `compatible_kv_band` invented from the qualitative
  "2207-2306 and up" note.
- No version bump (`0.4.1` unchanged).
- Motor (`#4d`, parked)/ESC (`#4c`)/battery (`#4`)/FC+GPS (`#4b`)
  families untouched by this cycle.

## Remaining risks

- The `propeller_catalog_assist.py` limit bump (5→6) is scoped exactly to
  the delta this Buy introduced. A future sourced-propeller Buy that adds
  a 7th compatible candidate for the same motor (or any motor) could
  reproduce the identical class of issue — this is a structural property
  of a fixed-size, alphabetically-ordered suggestion window growing
  against an ever-growing catalog, not something this fix "solves"
  permanently. Worth an Engineer note for future `#4*` prop/motor Buys.
- `diameter_in = 5.189` is a rounded derived value (131.8mm/25.4), not a
  value the page states directly in inches — round-tripping back to mm
  yields 131.8006mm rather than the page's exact 131.8mm. This is a
  ~0.0006mm (6-micron) discrepancy, disclosed in `source_note`, and
  matches the IC's own "≈5.189"/"≈131.8" wording — not treated as a
  precision concern.
