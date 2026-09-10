# Implementation Report — Propeller visor copies from motors spec `motor_count` B1

**IC:** [implementation_contract_geometry_propeller_visor_copies_b1.md](implementation_contract_geometry_propeller_visor_copies_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-09
**Baseline:** package `0.3.8` · suite 2540 → **2550** (2540 + 10 new)

---

## Files changed

| File | Change |
|---|---|
| `src/jarvis/workspace/spatial_board.py` | `place()` call site now passes `components` into `_solid_copies`. `_solid_copies(spec)` (single-branch, motors-only) replaced by `_solid_copies(spec, components)` (two-branch: `motors` unchanged; new `propellers` branch cross-reads sibling `motors` spec's own `motor_count`). Extracted shared `_parse_solid_copies_count(raw_value)` helper (float/is_integer/`[2,16]` gate) to avoid duplicating that check between the two branches — private, not a new public API. |
| `tests/test_geometry_motor_count_instances_b1.py` | Amended exactly `test_p1_motor_count_3_with_disk_geometry_yields_solid_copies_3` per the IC's own instruction: now also asserts `propellers.solidCopies == 3`. P2–P7 untouched. |
| `tests/test_geometry_propeller_visor_copies_b1.py` | **New.** P1–P10 exactly per IC §4. |
| `ui/spatial-board/src/scene3dLayout.ts` | Comment-only. `expandSolidCopies`'s docstring reworded from motors-specific to key-agnostic, and a paragraph added stating propellers relies on the same no-special-case behavior. No code line changed. |
| `ui/spatial-board/src/scene3dLayout.test.ts` | Added `U5`: proves a `propellers` node with `solidCopies:3` expands identically to `motors` (same `layoutId` scheme, `selectId`, stripped pose), with no `id`-based special-case anywhere in the function. |

`_bom_quantity` (`project_closure.py`) — confirmed **zero diff** (`git diff -- src/jarvis/core/project_closure.py | grep _bom_quantity` → no output). No `library/`, no `workspace/` mutation, no `pyproject.toml` change (`version = "0.3.8"` unchanged).

---

## Behavior changed

- `propellers` nodes now get `solidCopies: N` in the spatial-board projection, under the exact same gate motors already has: own geometry present (`_geometry_from_spec`) AND a whole-number `motor_count` in `[2, 16]` — but the count is **cross-read** from the sibling `motors` `ComponentSpec`'s own `motor_count` property (never `current_parameters`, never a default of 4, never `configuration=quad_x`). This mirrors the "1 propeller per motor" convention `_bom_quantity` already ships on the BOM surface, applied to the visor surface.
- `motors`' own branch is byte-identical to before this Buy (own `motor_count`, own geometry) — confirmed via the unchanged P2–P7 assertions in `test_geometry_motor_count_instances_b1.py` staying green with no edits.
- Still exactly one `propellers` `ComponentSpec`/BOM/card node — copies are visor-only, generated presentation rows sharing one `selectId`, per the pre-existing `expandSolidCopies` mechanism (unchanged, confirmed key-agnostic by direct source read — no code edit needed there).
- Pose stays stripped on every copy — `expandSolidCopies` already did this for any node, motors or otherwise.
- No changes to `_bom_quantity`, the pose writer, disk-origin gating, frame geometry, or any catalog data.

---

## Live census (read-only, post-change)

| Project | motors geometry | motors solidCopies | propellers geometry | propellers solidCopies | propellers node count |
|---|---|---|---|---|---|
| `autonomía-de-5min` | `None` (no Ø on `emax_rs2205_2300`) | `None` | disk Ø127mm | **4** | 1 |
| `autonomía-de-10min` | `None` | `None` | disk Ø127mm | **3** | 1 |

Matches the prior investigation's prediction exactly. No `workspace/` file was mutated (read via `project_spatial_nodes_from_path`, no writes).

---

## Tests added / executed

- New: `tests/test_geometry_propeller_visor_copies_b1.py` — P1 through P10, all passing (10/10), covering: no-motor-Ø case, both-disks case, propeller-without-diameter case, no-motor_count case, declared 4 honored, `configuration=quad_x` non-override, `motor_count=1` excluded, non-integer `motor_count` excluded, `current_parameters` must not win over the spec value, and no-`motors`-component-at-all case.
- Amended: `tests/test_geometry_motor_count_instances_b1.py::test_p1_motor_count_3_with_disk_geometry_yields_solid_copies_3` — required amendment per IC, not a weaken; P2–P7 untouched and still green.
- `ui/spatial-board`: `npm test` → 39 passed (18 in `scene3dLayout.test.ts`, +1 for `U5`). `npm run typecheck` → clean, no errors.
- Full Python suite: `python -m pytest -q` → **2550 passed**, 0 failed.

---

## Non-goals honored

No version bump (`pyproject.toml` still `0.3.8`). No catalog Ø seeded. No `workspace/` mutation. No change to `_bom_quantity`, the disk-origin pose gate, frame geometry, or `KIT_TO_COMPONENTS`/kit registries. No new public API (`_parse_solid_copies_count` is private/underscore-prefixed). `scene3dLayout.ts` received comment-only edits — no behavior change, no `id === "motors"`/`id === "propellers"` special-case introduced anywhere.

---

## Remaining risks

- None identified specific to this change. The propellers branch is a pure read of an already-existing, already-tested field (`motors.motor_count`) with the same validation gate motors already uses — no new failure surface beyond what P1–P10 cover.
- As before (unchanged by this Buy): motor solids remain invisible on both live projects because the bound SKU (`emax_rs2205_2300`) has no `diameter_mm` — a separate, pre-existing gap this Buy does not touch or need to touch.
- Distinct per-copy "stations" (N offsets in millimetres) remains unbuilt — copies still render as a flat visor row, as explicitly scoped out by the parent investigation (`B1-stations` parked for a future ★).
