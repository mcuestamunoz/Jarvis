# Implementation Report — #4g Sourced frame GEPRC GEP-Racer B1 (P1 partial)

Status: Done (implementation) — awaiting review + Engineer smoke
Parent: `implementation_contract_geometry_sourced_frame_gep_racer_b1.md`
Baseline: package `0.4.1` (unchanged) · suite `2730` (post external #4d landing) → `2735` (2730 + 5 new). UI `83` (unchanged — no `ui/` file touched)

## Summary

Seeded a new Class A frame SKU, `geprc_gep_racer_5in`, from the
Engineer's own locked §0.1 purchase-ground-truth citation (a GEPRC
product page, corroborated by the parts listing). Option A: a brand-new
catalog row; `armattan_rooster_5in` stays byte-stable. This is a **P1
partial** seed per the IC's own explicit gate: root facts (wheelbase,
body footprint, mass, configuration) and curated part *thicknesses*/
*standoff height* are seeded, but plate/arm L×W and standoff Ø/section
are deliberately left UNKNOWN — the Engineer's own 2026-09-11 photo
review locked that 175×173mm is the airframe's OUTER envelope (never a
plate box), 208mm is the diagonal wheelbase, and "M3×6×24mm" is a
thread-length callout, never an outer diameter. The 5min workspace's
`frame` component was rebound to the new SKU, and its `frame_*` children
were rebuilt from scratch (clearing stale Rooster-era declared L×W and
the Rooster-only `frame_cage`, which GEP-Racer's own citation never
states).

## Files changed

- `library/frames/_datos.json` — inserted `geprc_gep_racer_5in` after
  `armattan_rooster_5in`. Fields: `manufacturer` ("GEPRC"), `model`
  ("GEP-RACER Frame"), `mass_g` (78), `size_class_inch` (5),
  `wheelbase_mm` (208), `configuration` ("quad_x" — page never says
  "deadcat"), `arm_thickness_mm` (5.0), `arm_material` ("fibra de
  carbono (T700)" — this catalog's own English→Spanish material
  convention, T700 grade preserved parenthetically), `plates` (three
  `PlateSeed` entries — "Top plate"/"Aluminum plate"/"Bottom plate", each
  `thickness_mm: 2.0`, no `material` field on any — the bag explicitly
  states "(thickness only)"; "Aluminum" lives only in that plate's own
  label, never asserted as a schema-level material fact beyond the
  label itself), `body_length_mm`/`body_width_mm` (175/173 — root-only,
  same iFlight XL7 "Body dimensions" precedent this IC's own Parents
  section names), `standoffs` (one `StandoffSeed`, `height_mm: 24,
  count: 4` — never a diameter/section, since none is stated), no root
  `material` (the citation never states an overall airframe material
  distinct from the arm-specific T700 carbon fact), `identity_status:
  "verified"`, `source_url`, and a `source_note` disclosing every honesty
  boundary from the IC's own lock table: the 208mm-is-wheelbase /
  175×173mm-is-outer-envelope-not-plate-L×W distinction, the "never copy
  175×173 onto any frame_plate\*" instruction, the "M3×6×24 is a
  thread-length callout, not Ø" instruction, the mount-hole facts (noted,
  no schema field), and a pointer to this IC's own §0.1 CAD-search
  sibling (`implementation_contract_geometry_gep_racer_part_cad_b1.md`,
  closed B0) for why per-part L×W/standoff Ø remain absent.
  - `armattan_rooster_5in`: zero bytes changed (confirmed by T3 and by
    `git diff` showing only an insertion).
- `workspace/autonomía-de-5min-4b63337fd4fd/state.json` — the `frame`
  component and every `frame_*` child rebound/rebuilt from
  `armattan_rooster_5in` to `geprc_gep_racer_5in`:
  1. `clear_frame_part_children(state)` — the EXISTING IDLE-frame-rebind
     (B2) writer, called here for exactly the scenario its own docstring
     names ("re-picking Armattan → TBS" — now Armattan → GEPRC): removed
     `frame_arm`, `frame_cage`, `frame_plate` through `frame_plate_6`,
     and `frame_standoff` in one pass, so no stale Rooster-era part (or
     an orphaned `frame_cage` GEP-Racer's own citation never states)
     survives next to a root that no longer names it.
  2. A **fresh** `bind_frame_from_catalog("geprc_gep_racer_5in")` (no
     `base=`) built the new root properties — deliberately NOT a `base=`
     merge onto the old Rooster spec, because Rooster's own root
     `material` ("fibra de carbono") and `max_stack_height_mm` (22.0)
     have no GEP-Racer equivalent in this citation and would otherwise
     leak onto the new spec, the exact class of bug the #4e propeller
     rebind already surfaced. `mounted_on`/`declared_box_pose`/
     `declared_fit_attestation` (all `None` on the live Rooster root
     already) copied over explicitly regardless, for consistency with
     every other `#4*` rebind's own discipline.
  3. `current_parameters["structure_mass_override_kg"]` refreshed
     125g→78g (`0.125`→`0.078`) — mirroring the two-place write
     `set_frame_material` itself performs, since that narrower writer
     (mass/material/size_class-only) doesn't cover the Structure B
     root fields (`wheelbase_mm`/`configuration`/`body_*`) this Buy also
     needed, so the frame root was assembled directly rather than routed
     through it.
  4. `frame_part_specs_from_catalog("geprc_gep_racer_5in")`'s five
     entries (`frame_arm`, `frame_plate`, `frame_plate_2`,
     `frame_plate_3`, `frame_standoff`) each `upsert_frame_part`-ed fresh
     onto the now-cleared component set — none carries `length_mm`/
     `width_mm`, matching the P1 lock exactly. Confirmed via
     `project_spatial_nodes`: every one of these five nodes now has
     `geometry: None` (no box) — honest, since L×W is genuinely unknown,
     rather than the stale Rooster boxes the Board drew before this Buy.
- `tests/test_geometry_sourced_frame_gep_racer_b1.py` (new) — T1–T5, see
  below.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD ACTUAL synced (suite `2735`,
  new 🟡 LANDING entry, queue updated).
- `.jes/state/engineering_state.json` — top-level tracking fields synced;
  `engineer_ratification` left untouched.

**Not touched**: `PlateSeed`/`StandoffSeed` schema (both already had
exactly the fields this Buy needed — no L×W on either, confirmed by
inspection before writing a single line), `catalog_bind.py`/
`component_writers.py` (both already provided everything needed —
`bind_frame_from_catalog`, `frame_part_specs_from_catalog`,
`clear_frame_part_children`, `upsert_frame_part` — zero diff from this
cycle's own work; an unrelated external fix to the `base=`-merge
`.name`/`suggested_key` staleness in `bind_motor/battery/propeller/esc_
from_catalog` landed in parallel and is visible in `git diff` but was not
made by this cycle and did not need touching for this Buy since a fresh
bind was used throughout), `ui/spatial-board/**`, `pyproject.toml`
(version still `0.4.1`).

## Behavior changed

- New: `default_library.get_frame("geprc_gep_racer_5in")` resolves to a
  fully-cited Class A frame; `bind_frame_from_catalog`/`frame_part_specs_
  from_catalog` project its root/part facts exactly like the existing
  iFlight XL7 row does.
- Unchanged: `armattan_rooster_5in` (byte-stable — T3), `PlateSeed`/
  `StandoffSeed` (no schema change), `catalog_bind.py`/
  `component_writers.py` writer logic (zero diff from this cycle).
- 5min-workspace-only: the `frame` component's identity/root-facts
  changed; every `frame_*` child was rebuilt (Rooster's six plates + arm
  + cage + standoff replaced by GEP-Racer's three plates + arm +
  standoff — no cage); no child carries an invented L×W/Ø; the Board no
  longer draws any frame-part box on this project (honest, since none of
  the new SKU's parts have a sourced L×W yet).

## Tests

New file `tests/test_geometry_sourced_frame_gep_racer_b1.py` (5 tests):
- T1 `get_frame(new SKU)` → wheelbase 208, body 175×173, mass 78, size
  class 5in, configuration "quad_x", arm thickness 5.0, exactly three
  plates (labels "Top plate"/"Aluminum plate"/"Bottom plate", each
  2.0mm thick), exactly one standoff (height 24, count 4), manufacturer
  "GEPRC", `identity_status == "verified"`, `source_url` contains
  "geprc.com".
- T2 `bind_frame_from_catalog` projects `wheelbase_mm`/`configuration`/
  `body_length_mm`/`body_width_mm`/`mass_kg`; `frame_part_specs_from_
  catalog` produces exactly the five expected child keys, and NONE of
  them carries `length_mm`/`width_mm` in their properties (the direct
  proof of the P1 honesty gate at the projection layer, independent of
  the workspace rebind's own manual verification).
- T3 `armattan_rooster_5in` unchanged — wheelbase 230, mass 125,
  `body_length_mm`/`body_width_mm` still `None`, material still "fibra
  de carbono".
- T4 confirms `PlateSeed` genuinely has no `length_mm`/`width_mm`
  attributes at all (via `hasattr`) — the schema-level guarantee behind
  T2's property-level check.
- T5 confirms `StandoffSeed` has no `diameter_mm`/`length_mm`/`width_mm`
  attributes, and the projected `frame_standoff` child's properties never
  carry any of those keys either.

Executed:
- `python -m pytest -q tests/test_geometry_sourced_frame_gep_racer_b1.py`
  → 5 passed.
- `python -m pytest -q` (full suite) → **2735 passed**.
- Manual smoke of the mutated `state.json` via a throwaway script:
  confirmed `frame.name`/`catalog_ref.sku` == new SKU, root properties
  match the citation bag exactly (no stale Rooster `material`/
  `max_stack_height_mm`), all six old `frame_*` children replaced by
  exactly five new ones (no `frame_cage`), none carrying `length_mm`/
  `width_mm`, and `current_parameters["structure_mass_override_kg"]`
  correctly refreshed to `0.078`.
- Manual smoke of `project_spatial_nodes` on the mutated state: `frame`,
  `frame_arm`, `frame_plate`, `frame_plate_2`, `frame_plate_3`, and
  `frame_standoff` all report `geometry: None` — no invented boxes.

## Non-goals honored

- `armattan_rooster_5in` never rewritten (T3).
- No plate/arm L×W invented from the 175×173mm outer-envelope figure
  (T2/T4) — the Engineer's own explicit "never copy 175×173 onto plates"
  lock honored at both the catalog-seed layer and the workspace-rebind
  layer.
- No standoff Ø/section invented from "M3×6×24" (T5) — read correctly as
  a thread-length callout, not an outer diameter.
- No `PlateSeed`/`StandoffSeed` schema field added.
- No mount-hole schema invented — noted in `source_note` prose only.
- No version bump (`0.4.1` unchanged).
- The #4g-A CAD sibling IC (closed B0, no authentic file found) was not
  reopened or second-guessed by this Buy — its own investigation report
  is cited in this row's `source_note` as the reason per-part boxes stay
  absent for now.

## Remaining risks

- None specific to this Buy's own diff. The frame root's write path
  (fresh `bind_frame_from_catalog` + a direct `current_parameters` mirror
  + `upsert_frame_part` for children) is slightly more manual than the
  single-writer pattern battery/ESC/propeller rebinds use, because no
  generic "set the whole frame root" writer exists — `set_frame_
  material` is deliberately narrow (mass/material/size_class only) and
  the Structure B root fields (`wheelbase_mm`/`configuration`/`body_*`)
  have no writer of their own beyond `bind_frame_from_catalog`'s own
  base-merge return value. This is pre-existing architecture, not
  something this Buy needed to change — noted here only so a future
  frame rebind knows the same manual assembly is still the right pattern
  until/unless a dedicated frame-root writer is ever introduced.
