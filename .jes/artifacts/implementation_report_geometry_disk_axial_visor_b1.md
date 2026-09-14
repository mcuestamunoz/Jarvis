# Implementation Report — Disk axial Visor from cited dims B1 (`B1-disk-axial-visor`)

**IC:** [implementation_contract_geometry_disk_axial_visor_b1.md](implementation_contract_geometry_disk_axial_visor_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-14
**Baseline:** package `0.4.1` · suite 2873 → **2892** (19 new Python tests) · UI 103 → **105** (2 new UI tests)

---

## ★ confirmation — prior no-cylinder lock lifted for this Buy

Per IC §0 lock #2, the Engineer's ★ on this IC explicitly lifts the "never a cylinder" claim `_geometry_from_spec` carried since Motor height cited B1 and Propeller B0/B1 — **only** for the narrow case both a diameter path and one of the two named, cited axial properties (Motor `height_mm`, Propeller `hub_thickness_mm`) already exist on the same spec. The module's own docstring has been rewritten to state this supersession explicitly (see below) rather than silently dropping the old claim.

## Exact mapping table (IC §4)

| Family | Diameter path | Axial property read | Cylinder `height_mm` = | Never read |
|---|---|---|---|---|
| Motor | `diameter_mm` | `properties.height_mm` | the `height_mm` value, verbatim | `stator_height_mm`, `stator_diameter_mm` |
| Propeller | `diameter_mm` or `diameter_in` (×25.4, unchanged conversion) | `properties.hub_thickness_mm` (only read when `height_mm` is absent — Motor's own key takes priority if a spec somehow had both) | the `hub_thickness_mm` value, verbatim | `hub_diameter_mm` (a different, non-axial fact) |
| Any | full `length_mm`+`width_mm`+`height_mm` | — | — (box wins unconditionally, unchanged priority) | — |

## `_geometry_from_spec` (`spatial_board.py`) — priority now 4-deep

1. Full L×W×H → `box` (byte-identical to before).
2. Diameter path + axial fact (`height_mm` else `hub_thickness_mm`) → `cylinder` `{diameter_mm, height_mm}`.
3. Diameter path alone → `disk` `{diameter_mm}` (byte-identical to before).
4. Neither → `None`.

The function's own docstring was rewritten to document this priority and to explicitly narrow (not remove) its prior "never stitches two different physical references together" claim: `stator_height_mm` is still categorically excluded, forever, even when a diameter and no `height_mm` are both present — confirmed by a dedicated regression (`test_c3_stator_height_mm_alone_never_creates_geometry`) that a stator-only spec still gets no geometry at all.

## UI — `types.ts` / `scene3dScale.ts` / `Solid3D.tsx`

- `SpatialGeometry` gained `{ shape: "cylinder"; diameter_mm: number; height_mm: number }`.
- `solidExtentPx`: cylinder → `{x: diameter, y: diameter, z: height_mm}` (z now > 0, unlike disk's permanent 0).
- `solidWrapperPx`: cylinder reuses the box's own `{width: extent.x, height: extent.z}` formula (it also stands with its axial extent along the screen-vertical axis), not the disk's square wrapper.
- `Solid3D.tsx`: new cylinder branch — two circular caps reusing the **exact same** `sb-solid__disk-face` CSS class a flat disk already uses (a cap literally *is* a disk face, so zero new cap styling was needed) plus 16 flat rectangular side "slats" arranged in a ring (`rotateY(angle) translateZ(radius)`, the standard CSS 3D carousel/cylinder composition), reusing the existing `sb-solid__face` style for each slat — so the existing selected/hit-through/needs-origin modifier CSS rules (which already target `.sb-solid__face, .sb-solid__disk-face`) apply to the cylinder automatically, with only one new CSS rule added (`.sb-solid--cylinder .sb-solid__cylinder-body { position: relative; transform-style: preserve-3d; }`, mirroring the box's own `.sb-solid__cuboid` rule). 16 segments is a cheap, visually-round-enough count for a small visor solid — not a manufacturing-precision claim, and documented as such in the code comment.
- Each side slat's own width (a ring chord, much narrower than the wrapper) required an explicit `left` re-centering offset before the ring transform — the box's front/back faces never needed this because their width already equals the wrapper's own width; this is called out in a code comment so a future reader doesn't mistake it for dead code.
- **2D card glyph**: left unchanged (still whatever the existing disk/box glyph rendering does) per the IC's own explicit "may stay disk silhouette... do not block on glyph polish" allowance — not touched this Buy.

## Regressions flipped (IC §1.3, "T7-class")

Six existing tests asserted the now-explicitly-superseded "diameter + axial fact → still disk" claim. Each was updated to assert `cylinder` with the correct `height_mm`, with a comment naming this Buy as the reason for the flip (never a silent behavior change):

- `tests/test_geometry_motor_height_cited_b1.py::test_t7_...` — renamed to `test_t7_geometry_is_cylinder_when_diameter_and_height_mm_both_cited`.
- `tests/test_geometry_propeller_envelope_b0_b1.py::test_t7_...` — renamed to `test_t7_geometry_is_cylinder_when_diameter_and_hub_thickness_both_cited`.
- `tests/test_geometry_sourced_prop_gemfan_51466_b1.py::test_t3_...` — renamed to `test_t3_projector_emits_cylinder_diameter_131_8mm_hub_6_8mm`.
- `tests/test_geometry_sourced_motor_xing_e_pro_b1.py::test_t3_...` — renamed to `test_t3_bind_projects_cylinder_28_5_by_33_1` (this is the exact live 10-min motor SKU).
- `tests/test_geometry_motor_visor_rebind_b1.py::test_p1_...` — motors geometry assertion updated (propellers in that fixture has no `hub_thickness_mm`, so it correctly stays disk, untouched).
- `tests/test_geometry_motor_visor_rebind_b1.py::test_p5_...` — renamed from "...never_a_cylinder" to `test_p5_height_mm_is_a_card_field_and_now_the_cylinder_axial_extent`.

I found all six by (1) grepping every test file for "cylinder"/"never a cylinder" mentions, (2) a broader crude scan for any fixture where a diameter key and `height_mm`/`hub_thickness_mm` co-occur textually near each other, then manually confirming each candidate actually feeds a real `diameter`+axial combination into `_geometry_from_spec` before touching it — several near-hits (`test_geometry_disk_from_diameter_mm`, `test_geometry_box_wins_over_diameter_when_both_present`, `test_geometry_propeller_cited_seeds_b2.py`'s own hub-diameter-only fixtures, `test_geometry_assembly_fit_cabe_b1.py`'s disk-child screening test) were confirmed to genuinely lack the trigger combination (only `stator_height_mm`, or only `hub_diameter_mm`, or diameter-only) and were left untouched — full suite run after the projector change confirmed exactly these 6 failures and no others, matching my manual audit precisely.

## Census — live-bound catalog SKUs: cylinder vs. disk (no new seeds)

No catalog JSON file was edited this Buy (`library/motores/_datos.json`, `library/helices/_datos.json` confirmed unmodified via `git status`, asserted by `test_no_new_catalog_seeds_added_this_buy`). Consuming only what's already cited:

| SKU | Family | Cites | Result |
|---|---|---|---|
| `iflight_xing_e_pro_2207_2450` (live 10-min motor) | Motor | Ø28.5, `height_mm` 33.1 | **cylinder** |
| `emax_rs2205s_2300` | Motor | Ø27.9, `height_mm` 31.7 | **cylinder** |
| `sunnysky_r2205_2500` | Motor | Ø only, no `height_mm` | disk (unchanged) |
| `gemfan_hurricane_mck_51466_3_v2` (live 10-min/5-min prop) | Propeller | Ø(diameter_in), `hub_thickness_mm` 6.8 | **cylinder** |
| `gf_5045x3` | Propeller | Ø, `hub_thickness_mm` 9.5 | **cylinder** |
| `dal_7040` | Propeller | Ø, `hub_thickness_mm` 7.0 | **cylinder** |
| `apc_10x6_ep` | Propeller | Ø, `hub_thickness_mm` 9.9 (plus `hub_diameter_mm`, never read as axial) | **cylinder** |
| `hq_5045_bn` | Propeller | Ø only, no hub bag cited | disk (unchanged) |

## Screening/attest — confirmed unchanged (IC §0 lock #8)

`screen_posed_envelope` needed **zero code changes**: its existing `child_geometry.get("shape") != "box"` gate already rejects `"cylinder"` the same way it always rejected `"disk"` — confirmed directly (`test_c7_screening_refuses_cylinder_child_as_not_box`, plus a new symmetric check that a cylinder is equally refused as a pose **origin**, `test_c7_screening_refuses_cylinder_as_pose_origin_too`, mirroring the disk-origin gate `set_component_declared_box_pose` already had). `fit_relations_assist.py` needed **zero code changes** either — its `n_a_disk` status for motors/propellers is keyed off the relation being disk-only-by-design (motors→frame_arm, propellers→motors), not off the projector's own shape string, so it reports the exact same honest `n_a_disk` line before and after this Buy (confirmed against both live projects below).

## Files changed

- **`src/jarvis/workspace/spatial_board.py`** — `_geometry_from_spec` extended with the cylinder branch + rewritten docstring.
- **`ui/spatial-board/src/types.ts`** — `SpatialGeometry` cylinder variant.
- **`ui/spatial-board/src/scene3dScale.ts`** — `solidExtentPx`/`solidWrapperPx` cylinder branches.
- **`ui/spatial-board/src/Solid3D.tsx`** — cylinder rendering branch (caps + 16 side slats).
- **`ui/spatial-board/src/spatial-board.css`** — one new rule (`.sb-solid--cylinder .sb-solid__cylinder-body`).
- **`ui/spatial-board/src/scene3dScale.test.ts`** — 2 new tests (C8-equivalent: extent/wrapper).
- **`tests/test_geometry_disk_axial_visor_b1.py`** (new) — 19 tests: C1–C7 plus the SKU census and the no-new-seeds check.
- Six pre-existing test files updated for the flipped regression (listed above).

No writer touched. No new catalog data. No version bump.

## Tests

Executed: `python -m pytest -q` → **2892 passed, 1 skipped** (0 failed). `cd ui/spatial-board && npx vitest run` → **105 passed** (was 103). `npx tsc --noEmit` → clean.

Coverage against IC §2:

| ID | Covered by |
|---|---|
| C1 | `test_c1_motor_diameter_and_height_mm_yields_cylinder` |
| C2 | `test_c2_motor_diameter_only_still_disk` |
| C3 | `test_c3_stator_height_mm_never_used_as_cylinder_height`, `test_c3_stator_height_mm_alone_never_creates_geometry` |
| C4 | `test_c4_propeller_diameter_in_and_hub_thickness_yields_cylinder` |
| C5 | `test_c5_propeller_diameter_only_no_hub_thickness_stays_disk`, `test_c5_hub_thickness_alone_without_diameter_yields_no_geometry` |
| C6 | `test_c6_box_wins_over_diameter_and_axial_when_full_lwh_present` |
| C7 | `test_c7_screening_refuses_cylinder_child_as_not_box`, `test_c7_screening_refuses_cylinder_as_pose_origin_too` |
| C8 | `scene3dScale.test.ts`: cylinder `solidExtentPx` (`z > 0`) and `solidWrapperPx` |
| C9 | **Not covered by an automated render test** — this repo's vitest config runs in `environment: "node"` with no DOM/React-render harness (`@testing-library`/`jsdom` are not installed, and no existing test in this codebase renders a component). Adding one would be a disproportionate new dependency for a single visor detail; the cylinder branch is code-reviewable directly and Engineer's own §3 smoke (steps 1–2, visible axial depth) is the actual verification, same limitation already flagged and accepted in the prior arm-radial-visor cycle's report for `Solid3D`'s `rotateY`. |
| T | Full suite green above; `pyproject.toml` still `0.4.1` |

## Reproducibility check against both live projects (read-only — no `workspace/` write)

Loaded both live `state.json` files directly into `ProjectState`, no orchestrator mutation, nothing saved:

- **`10-min-autonomía`**: `motors` geometry now `{shape: cylinder, diameter_mm: 28.5, height_mm: 33.1}`; `propellers` geometry now `{shape: cylinder, diameter_mm: ~131.8, height_mm: 6.8}`. `relaciones` checklist unchanged in substance — motors/propellers still report `n_a_disk` verbatim.
- **`autonomía-de-5min`**: `motors` geometry now `{shape: cylinder, diameter_mm: 27.9, height_mm: 31.7}` (this project is bound to `emax_rs2205s_2300`, not the XING-E Pro); `propellers` same Gemfan Hurricane cylinder as 10-min. Same `n_a_disk` fit-relations result confirmed.
- Silhouette checklist (`assess_silhouette`) re-verified unaffected on 10-min — it never reads motors/propellers geometry at all (only the four boxed stack subjects), so its output is byte-identical before/after this Buy.

## Non-goals honored

No invented mm (every cylinder dimension traces to a `PropertyValue` already on the spec). No photo pixel-scale, no mass/KV estimate. `stator_height_mm` never read as body H (explicit regression). No prop blade-volume invention — copy and code comments explicitly label the propeller axial extent as hub/center thickness only. No box stitched from a diameter. Screening/attest untouched (confirmed, zero code changes needed there). Multi-copy motors/props/prop_adapter still not Situar-draggable (this Buy touched no drag-eligibility code at all — `isDraggableSolid`/`boardPoseDrag.ts` untouched). No new catalog seeds. No version bump. No `workspace/` mutation.

## Remaining risks / notes for review

- The cylinder's lateral surface is a 16-segment flat-panel approximation (a real, honest, but faceted cylinder), not a true curved surface — CSS has no native curved 3D primitive, so this is the same class of approximation as the box's own six-flat-face presentation, just with more faces. If Engineer's visual smoke finds 16 segments too coarse or unnecessarily fine, the segment count is a single named constant (`_CYLINDER_SIDE_SEGMENTS` in `Solid3D.tsx`) to tune.
- C9 (component-render test) is not automated — see the table note above. This is a pre-existing repo-wide gap (no rendering harness at all), not something newly introduced by this Buy.
- 2D card glyph was left as-is (still whatever it already showed for a disk-shaped spec) per the IC's own explicit non-blocking allowance — a future Buy could add a distinct cylinder glyph cue if desired.
