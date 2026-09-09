# Implementation Report — Motor visor copies from the project's `motor_count` B1

**IC:** [implementation_contract_geometry_motor_count_instances_b1.md](implementation_contract_geometry_motor_count_instances_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-09
**Baseline:** package `0.3.8` · Python suite 2466 · UI suite 34 passed · HEAD `3d4e647`

---

## Files changed

- `src/jarvis/workspace/spatial_board.py` — **§3.1**: new module-level `_solid_copies(spec) -> int | None`. Omits (`None`) unless **all** of: `spec.suggested_key == "motors"`; `_geometry_from_spec(spec)` is not `None` (a real solid already exists); and `spec.properties["motor_count"].value` is present, a finite number, a whole number (`float(raw).is_integer()`), and `2 <= int(raw) <= 16`. Never reads `configuration`, never `current_parameters`, never defaults to `4` — confirmed by construction (the function's only inputs are `spec.suggested_key`, `_geometry_from_spec(spec)`, and `spec.properties.get("motor_count")`; nothing else is read). `place()` now computes `_solid_copies(spec)` and passes it to `_emit(...)` as `solid_copies=...`; `_emit`'s signature gained that keyword and sets `node["solidCopies"] = solid_copies` only when not `None` — the same conditional-key pattern already used for `geometry`/`mounted_on`/`declared_box_pose`, no new pattern invented.
- `ui/spatial-board/src/types.ts` — `SpatialNode.solidCopies?: number` added, documented as motors-only, geometry-gated, never-a-default.
- `ui/spatial-board/src/scene3dLayout.ts` — **§3.3**: new `ExpandedSolid` type and `expandSolidCopies(nodes)`. For a node with `solidCopies >= 2`, emits N entries `{layoutId: "<id>#<i>", selectId: "<id>", geometry, declaredBoxPose: undefined}` (pose deliberately stripped — composing it onto N copies would stack them at one point). Otherwise emits one passthrough entry `{layoutId: id, selectId: id, geometry, declaredBoxPose}`. Preserves input order (iterates nodes in order, expands each in place).
- `ui/spatial-board/src/Scene3D.tsx` — calls `expandSolidCopies(...)` on the geometry-bearing `solids` list **before** `layoutSolidsFromPose`/`clusterCenterPx`, both of which now consume `layoutId` as their `id` (never the raw node id — three `id: "motors"` entries would collide, as the IC required). The render loop now maps over `expanded` instead of `solids`: `<Solid3D key={e.layoutId} id={e.selectId} ... />` — `Solid3D` itself needed **no** changes, since its existing `id` prop already drives both `data-node-id` and `onSelect(id)`, and passing `selectId` there gives exactly the locked behavior (all copies of a click-selected motor highlight together; clicking any copy selects the one `motors` card). Docstring updated to name the new expand-before-layout step.
- `tests/test_geometry_motor_count_instances_b1.py` (**new**) — P1–P7 per the IC's own table, using a synthetic disk-shaped `motors` fixture (not the live SunnySky binding, which has no `diameter_mm`) plus an untouched `propellers` disk to prove the gate doesn't leak to other keys.
- `ui/spatial-board/src/scene3dLayout.test.ts` — new `describe("expandSolidCopies", ...)` block, U1–U4 per the IC's own table.

## Behavior changed

- `project_spatial_nodes` output now includes `solidCopies` on the `motors` node when its own `motor_count` property is a whole number in `[2, 16]` **and** it already has `geometry` — omitted in every other case (missing, `1`, `0`, non-integer, out of range, or no geometry). No other node (propellers, FC, ESC, frame, parts, slots) can ever carry this key — the gate checks `suggested_key == "motors"` directly, not a general geometry+count heuristic.
- The CSS 3D visor now draws N copies of a `motors` solid when `solidCopies` is present, laid out as N additional row occupants (via the existing, unchanged `layoutSolidsFromPose`) — still **one** `motors` card, **one** `mountedOn` edge, **one** BOM node; clicking any copy calls `onSelect("motors")` and all copies share the same `selected` highlight (same `selectId`).
- A copied motor's `declaredBoxPose` (if it ever had one) is stripped for the copies — verified by U3 — so this Buy cannot silently stack N copies at one declared point; an *uncopied* motor (N=1 or omitted) keeps its existing one-hop pose path unchanged (verified: the `else` branch of `expandSolidCopies` passes `declaredBoxPose` through untouched).
- Live demo (`autonomía-de-10min`) confirmed unchanged and matching the IC's own required outcome: **1** `motors` node, `geometry` absent (SunnySky R2305 has no `diameter_mm`), `solidCopies` absent — i.e. still **zero** motor solids in the 3D pane. This was checked via a read-only Python snippet against the live `state.json` (never a test, never a mutation) — the file is byte-identical (`git status --short -- workspace/` empty).

## Tests

- `python -m pytest -q` → **2473 passed**, 0 failed (baseline 2466 + 7 new, all in `tests/test_geometry_motor_count_instances_b1.py`). Ran the new file alone first (7 passed), then the full suite.
- `cd ui/spatial-board && npm test -- --run` → **38 passed** across 5 files (baseline 34 + 4 new `expandSolidCopies` cases in `scene3dLayout.test.ts`, now 17 tests total in that file). All 5 test files green.
- `npm run typecheck` → clean (`tsc --noEmit`, no errors).
- `npm run build` → clean production build (47 modules, no errors/warnings).
- Live census re-verified directly against `workspace/autonomía-de-10min-9ada1a1b0cca/state.json` via `project_spatial_nodes_from_path` (read-only): 1 `motors` node, no `geometry`, no `solidCopies` — the ACCEPT outcome the IC's own §6 smoke table requires. Not asserted as an automated test (per §1, live smoke is Engineer's after this report), only checked by hand to confirm before writing this report.

## Non-goals honored

- No default of 4 anywhere — confirmed by reading `_solid_copies`'s own source: the only numeric literal is the `[2, 16]` bound, never a substituted count.
- `configuration`/`quad_x` never read by `_solid_copies` — confirmed both by the function's source (it only touches `spec.properties.get("motor_count")`) and by test P5 (a frame with `configuration=quad_x` present alongside `motor_count=3` still yields `solidCopies == 3`, not 4).
- `current_parameters.motor_count` never read — `_solid_copies` takes a `ComponentSpec`, which has no `current_parameters` field at all; the read is structurally confined to `spec.properties`.
- No wheelbase/quad-X placement — copies use the existing, unchanged row-slot layout (`layoutSolidsFromPose` via `expandSolidCopies`'s expansion), never `wheelbase_mm`, never 4-station corners.
- No SKU/catalog Ø seeded to make the demo "prettier" — the live smoke correctly still shows zero motor solids, and this was left as-is per the IC's own explicit ACCEPT criterion.
- No propeller instancing — `expandSolidCopies`/`_solid_copies` only ever act on a node whose `suggested_key == "motors"`; the propellers fixture in every Python test carries no `solidCopies` key in any scenario (explicitly asserted in P1).
- No new `ComponentSpec`/card/BOM node — `place()` still emits exactly one node per component key; `solidCopies` is purely a rendering-count hint consumed only by the 3D visor's `expandSolidCopies`.
- `Solid3D.tsx` untouched — the IC's own §5 file table flagged this as "only if needed"; it wasn't, since `id`/`onSelect`/`data-node-id` already do the right thing when the parent passes `selectId` as `id`.
- No version bump (`pyproject.toml` still `0.3.8`); fit stub still QUEUED (not touched); `component_writers.py`, `declared_box_pose_declare_assist.py`, `orchestrator.py`, `boardSelection.ts`, `package.json` all byte-identical to before this cycle (confirmed via `git diff --stat`, empty for all).
- No test weakened — the new Python and TS files are entirely additive; no existing test's assertions changed.

## Remaining risks / notes for review

- `expandSolidCopies` currently has no explicit test for a *mix* of a copied node and an already-posed *other* node in the same list beyond U4's finite-midpoint check — U4 does cover an FC (unposed) + motors (2 copies) list end-to-end through `layoutSolidsFromPose`/`clusterCenterPx` without error, but a dedicated "posed non-motor solid alongside copied motors" arithmetic assertion was judged out of this IC's own locked scope (§3.4 only requires copies to be unposed row occupants; it does not ask for a new composed-scene worked example).
- The live demo's `motors` component still has zero geometry, so this Buy is verified end-to-end only against synthetic fixtures for the "N copies actually render" path — exactly the outcome §6's own smoke table calls ACCEPT, not a gap to close here.
