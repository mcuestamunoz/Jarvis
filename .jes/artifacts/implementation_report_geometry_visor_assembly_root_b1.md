# Implementation Report — Visor assembly root (Main Plate at world origin) B1

**IC:** [implementation_contract_geometry_visor_assembly_root_b1.md](implementation_contract_geometry_visor_assembly_root_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-09
**Baseline:** package `0.3.8` · suite 2583 (unchanged — this cycle is `ui/`-only). UI: 43 → **47** (+4)

---

## Files changed

| File | Change |
|---|---|
| `ui/spatial-board/src/scene3dLayout.ts` | `layoutSolidsFromPose` now detects an assembly root: an item with `id === "frame_plate"` (exact key, a module constant `ASSEMBLY_ROOT_ID`) AND `geometry.shape === "box"`. When present, that item is placed centered at world `(0,0,0)` (same origin `offsetMm` stations already use) instead of a row slot; a `declaredBoxPose` whose `originKey` is that active root measures its Δmm from the root's world-0 center instead of a row-slot center — still single-level, never a chain (any OTHER origin keeps today's row-slot-based placement, byte-for-byte). N1 tidy: `layoutSolidsRow`'s row is now built only from items that are neither the active root nor carrying `offsetMm` — neither ever reserves footprint space for whoever comes after them, regardless of whether a root is active this run. No other function touched (`layoutSolidsRow`, `clusterCenterPx`, `expandSolidCopies` all unchanged). |
| `ui/spatial-board/src/scene3dLayout.test.ts` | New `describe("Visor assembly root B1 (Main Plate at world origin)")` block with U10–U13. |

`src/`, `library/`, `workspace/`, `pyproject.toml` — confirmed **untouched** (`git status --short` shows no new changes beyond what already existed from earlier closed cycles this session; version still `0.3.8`). No `spatial_board.py` DTO change was needed — `solidCopyOffsetsMm`, the pose writer, and the envelope writer are all exactly as they shipped in the prior cycles.

---

## Behavior changed

- When the projected `frame_plate` node has `geometry.shape === "box"` (only possible today via the Declared Main Plate envelope B1 cycle — never invented here), the 3D visor places it centered at world `(0,0,0)` instead of a row slot. This is the exact same world origin the quad-X `offsetMm` stations already center on, so motors/propellers and the Main Plate now share one coordinate frame instead of sitting in two visually separate clusters (the "visual gap X vs stack" the parent review flagged).
- A component with `declaredBoxPose.originKey === "frame_plate"` (e.g. battery/FC/ESC posed against the plate) now measures its declared Δmm from that world-0 center when the root is active — previously it measured from `frame_plate`'s arbitrary row-slot position. Posing against any OTHER origin (e.g. ESC→FC) is completely unaffected — still exactly today's single-hop, row-slot-based placement.
- **N1 tidy** (a wart the Visor X stations review flagged): an item carrying `offsetMm` no longer reserves row-cursor footprint space for whoever is laid out after it, and the active root doesn't either — this holds regardless of whether a root is active, so a project with stations but no plate box (e.g. no envelope declared yet) also stops wasting row space on 8 disk footprints for its remaining plain-row items (FC, battery, etc.).
- `frame_plate_2` (or any other plate) never becomes root even if it happens to be a box — only the exact key `frame_plate` qualifies (verified, U13). A `frame_plate` that is present but not yet a box (no envelope declared) also never activates root behavior — falls through to today's row (verified, U13).
- `clusterCenterPx`, `expandSolidCopies`, `layoutSolidsRow`, the Python projector, and the pose/envelope writers are all byte-identical to before this cycle.

---

## Tests added / executed

New `describe` block in `scene3dLayout.test.ts`, 4/4 passing:
- **U10**: `frame_plate` box + 4 quad-X motor stations + one plain unposed item (`esc`) — plate centers at world 0 (wrapper-centered, `originZ === 0`); station 0 (FR, `+a,+a`) lands at the expected declared-mm point around that same origin; `esc`, the only remaining row item, sits at row cursor `0` — never pushed right by the 4 station footprints.
- **U11**: a `battery` posed with `originKey: "frame_plate"`, `zMm: 8` against an active plate root — its layout is the root's world-0 center plus `8mm` on the CSS Y axis (declared +Z → CSS Y, same remap as always), minus its own half-height/width, exactly as the existing pose math already computes for any other origin.
- **U12**: no `frame_plate` box present (only motor stations + an unposed FC) — stations still sit at world 0, and FC (the only row item) stays at cursor `0`, undisturbed by the station footprints. Documents the deliberate choice (per IC lock #7's unqualified wording) that the N1 tidy applies whether or not a root is active this cycle — not conditioned on root presence.
- **U13**: `frame_plate_2` (a box, wrong key) gets a plain row slot, never world-0 centering; a `frame_plate` present but shaped as a `disk` (no envelope box declared) also stays on the plain row — only the exact key **and** a declared box together activate root behavior.

`npm test` → **47 passed** (43 pre-existing + 4 new), `npm run typecheck` → clean. Full Python suite: `python -m pytest -q` → **2583 passed**, 0 failed (unchanged from baseline — confirms zero `src/` drift, as this cycle is `ui/`-only).

---

## Non-goals honored

No `spatial_board.py` change — `solidCopyOffsetsMm`, the wheelbase/quad-X math, and every Python DTO are untouched. No multi-hop pose composition (ESC→FC still measures from FC's row slot, not from any further chain — U8's existing single-hop guarantee is unaffected and still green). No `frame` root or `frame_plate_2` ever treated as assembly root (U13). No plate L×W invented, no `wheelbase_mm`→box stitching, no disk-origin pose change. No new CLI/Board copy strings — this is a pure visor placement change. No version bump.

---

## Remaining risks

- None identified specific to this change — root detection and the N1 row-exclusion are both narrowly scoped (exact key + exact shape check) and covered directly by tests, including the two "must NOT activate" negative cases (U13).
- The Engineer's live smoke (reloading the Board on `autonomía-de-5min`, confirming the visual gap between the plate and the motor/propeller X is gone or much smaller) remains a separate, manual step per IC §6 — this report only verifies the underlying layout math via unit tests, not a rendered screenshot.
- As explicitly accepted by the IC itself (§6, "ACCEPT this Buy"): ESC vs FC may still look slightly off since that relation stays single-level (measured from FC's row slot, not FC's own posed point) — this is a known, deliberately-scoped limitation, not a regression introduced here.
