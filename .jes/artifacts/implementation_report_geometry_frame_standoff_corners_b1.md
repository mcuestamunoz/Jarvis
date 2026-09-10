# Implementation Report — Frame standoff ×4 at Main Plate corners B1

**IC:** [implementation_contract_geometry_frame_standoff_corners_b1.md](implementation_contract_geometry_frame_standoff_corners_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-10
**Baseline:** package `0.3.8` · suite 2646 → **2652** (2646 + 6 new)

---

## Files changed

| File | Change |
|---|---|
| `src/jarvis/workspace/spatial_board.py` | New `_STANDOFF_CORNER_COUNT = 4` (a separate constant from `_QUAD_X_STATION_COUNT`, kept textually distinct so a future declared `standoff_count` Buy touches only this constant/branch). New `_main_plate_corner_points(plate_geometry, standoff_geometry)` — the corner-inset formula (`hx = Lp/2 - Ls/2`, `hy = Wp/2 - Ws/2`, fail-closed on either going negative), a private helper that never touches `_quad_x_station_points`. New `_frame_standoff_corner_offsets_mm(standoff_spec, components)` — the ONE shared gate (standoff own box, literal `frame_plate` key with a box) + formula call, used by both `_solid_copies`'s new `frame_standoff` branch (decides `count == 4`) and `_solid_copy_offsets_mm`'s new `frame_standoff` branch (emits the actual points), so the two can never drift apart. |
| `tests/test_geometry_frame_standoff_corners_b1.py` | **New.** P1–P6 exactly per IC §3. |

`ui/`, `library/`, `workspace/`, `pyproject.toml` — confirmed **untouched** by this cycle (`git status --short` shows no new changes on any of them; version still `0.3.8`).

---

## Behavior changed

- When `frame_standoff` has a declared box AND the literal `frame_plate` key (Main Plate, never an ordinal sibling like `frame_plate_2`) also has a declared box with finite `length_mm`/`width_mm`, the standoff now gets a fixed `solidCopies == 4` and four corner offsets on the Main Plate footprint — inset by half the standoff's own L×W (`hx = Lp/2 - Ls/2`, `hy = Wp/2 - Ws/2`), verified against the live fixture: plate 100×100, standoff 5×5 → offsets exactly `(±47.5, ±47.5, 0)` (P1).
- Missing either box, or a plate with no L×W, yields no `solidCopies` at all (P2). A standoff whose own footprint is larger than the plate in either axis fails closed — no copies, never a negative/inverted inset (P3).
- The count is **fixed at 4** this Buy — never read from motors/`motor_count`/`quad_x`/`wheelbase_mm`, and the resulting offsets are visibly and structurally different from the quad-X families' own points even when both a `frame` with `quad_x`+`wheelbase_mm=230` and this standoff/plate pair coexist (verified, P4/P6): the standoff's offsets always have `|xMm| == |yMm| == 47.5` (plate-footprint math), never the quad-X families' `81.317...` (wheelbase math).
- Still exactly **one** `frame_standoff` `ComponentSpec`/BOM/card node (P5) — copies are visor-only, drawn via the already-existing, unchanged `expandSolidCopies` mechanism, which strips `declaredBoxPose` on any node with `solidCopies >= 2` exactly as it already did for every other family.
- Motors/propellers/frame_arm/prop_adapter's own quad-X copy behavior is completely untouched — verified directly alongside the new standoff behavior in the same fixture (P6).

---

## Tests added / executed

New: `tests/test_geometry_frame_standoff_corners_b1.py` — 6/6 passing:
- P1: standoff 5×5×25 + Main Plate 100×100×4 → `solidCopies==4`, all four `(±47.5, ±47.5)` sign combinations present, `zMm==0` on every point.
- P2: missing standoff geometry, missing plate entirely, and a plate present but without L×W — all three yield no `solidCopies`.
- P3: standoff length or width larger than the plate — fails closed, no `solidCopies`/offsets in either case.
- P4: with a `quad_x`+230mm frame and motors also present, standoff offsets are still `±47.5` (plate math), never equal to motors' `±81.317` (wheelbase math).
- P5: exactly one `frame_standoff` node in the projected list.
- P6: motors/propellers/frame_arm/prop_adapter all still get `solidCopies==4` sharing the identical quad-X points, while `frame_standoff` gets its own distinct plate-corner points in the same fixture.

Full suite: `python -m pytest -q` → **2652 passed**, 0 failed (2646 unchanged baseline confirmed before writing tests, then +6).

---

## Live verification (read-only)

Read the real `autonomía-de-5min` project (never saved back): `frame_standoff` (5×5×25) and `frame_plate` (100×100×4) both already have declared boxes from earlier cycles. The projector now emits `solidCopies==4` on `frame_standoff` with offsets exactly `(±47.5, ±47.5, 0)`, visibly distinct from `motors`' own `(±81.317, ±81.317, 0)` quad-X points, and exactly one `frame_standoff` node in the list. No `workspace/` file was mutated.

---

## Non-goals honored

No declared `standoff_count` Continuity grammar — count is hardcoded at 4 this Buy, deferred to a later, separate Buy (documented explicitly, per lock #8). No four `frame_standoff_*` BOM keys — still exactly one `ComponentSpec`. No motor/`quad_x`/wheelbase read anywhere in the new code path. No camera/VTX extra posts — only the one `frame_standoff` key this IC scopes. No mm invented — every dimension came from the already-declared specs. No `_quad_x_station_points` reuse or modification (a brand-new, separate helper was written instead, per lock #5). No `ui/` change — `expandSolidCopies` was already generic enough to require none. No Conversation Engine. No version bump.

---

## Remaining risks

- None identified specific to this change — the new gate/formula is fully self-contained in one shared helper (`_frame_standoff_corner_offsets_mm`) called identically from both `_solid_copies` and `_solid_copy_offsets_mm`, so the two can never disagree, and every fail-closed path (missing box, oversized standoff) is directly exercised by tests.
- As explicitly deferred by the IC itself (lock #8): a declared, generalist `standoff_count` (N≠4, or Engineer-typed offsets) is a separate, later Buy — this cycle only ships the fixed-4 corner case.
- The Engineer's live smoke (reloading the Board on `autonomía-de-5min`, confirming four posts sit at the plate corners rather than on the motor X) remains a separate, manual step per IC §5 — this report verifies the parse/project chain, not the rendered 3D result.
