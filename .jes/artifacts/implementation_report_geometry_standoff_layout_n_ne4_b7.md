# Implementation Report — Standoff visor layout N≠4 (B7 / 6·8 perimeter)

Status: Done (implementation) — awaiting review + Engineer smoke
Parent: `implementation_contract_geometry_standoff_layout_n_ne4_b7.md`
Baseline: package `0.4.1` (unchanged) · suite `2686` → `2697` (2686 + 10 new + 1 net from an updated parametrize) · UI `83` (unchanged — no `ui/` file touched)

## Summary

Widened `frame_standoff`'s projector layout from corners-only (N=4) to
also place N=6 and N=8 posts on the Main Plate perimeter, per the locked
§0.1 formula: 4 corners always (unchanged from B4-min), plus 2 midpoints
of the longer plate-edge pair for N=6, plus all 4 edge midpoints for N=8.
Any other in-range `count` (2, 3, 5, 7, 9..16), a missing/non-numeric
`count`, a non-box standoff/plate, or a standoff footprint larger than the
plate still omits both `solidCopies`/`solidCopyOffsetsMm` — B7 only widens
the ACCEPTED set, never the fail-closed fallback for a rejected one. Still
exactly one `frame_standoff` BOM node.

## Files changed

- `src/jarvis/workspace/spatial_board.py`:
  - `_STANDOFF_LAYOUT_COUNTS = (4, 6, 8)` added alongside the existing
    `_STANDOFF_CORNER_COUNT = 4`.
  - `_frame_standoff_corner_offsets_mm` renamed to `_frame_standoff_
    layout_offsets_mm` — the ONE gate+formula function `_solid_copies`
    and `_solid_copy_offsets_mm` both call, so the two can never drift
    apart. Count gate widened from `count != 4` to `count not in
    _STANDOFF_LAYOUT_COUNTS`. N=4 still returns `_main_plate_corner_
    points`'s own 4 points UNCHANGED (same function, same call, same
    formula — byte-identical, confirmed by P1's regression test). N=6/8
    append `_standoff_perimeter_midpoints_mm`'s additive points.
  - New `_standoff_perimeter_midpoints_mm(plate_geometry,
    standoff_geometry, count)` — recomputes the same `hx`/`hy` inset
    formula `_main_plate_corner_points` already uses (duplicated
    deliberately rather than shared, so that already-tested function's
    corner-only contract never changes shape) and returns the locked
    midpoint set for `count in {6, 8}`; any other count returns `None`
    (never reached in practice, since the caller only passes 6/8).
  - `_solid_copies`'s `frame_standoff` branch: now returns
    `len(offsets)` from `_frame_standoff_layout_offsets_mm` rather than a
    hardcoded `_STANDOFF_CORNER_COUNT` — this makes the copies↔offsets
    lockstep (§0 lock #8) structural rather than merely consistent: the
    emitted `solidCopies` is always, by construction, the exact length of
    the offsets list that would be emitted.
  - `_solid_copy_offsets_mm`'s `frame_standoff` branch: gate widened from
    `solid_copies != _STANDOFF_CORNER_COUNT` to `solid_copies not in
    _STANDOFF_LAYOUT_COUNTS`.
  - Comments updated wherever they said "only N=4 / omit otherwise" to
    reflect the widened `{4, 6, 8}` set.
- `tests/test_geometry_standoff_count_gate_b4.py` — `test_p3_count_not_4_
  yields_no_copies` (parametrized `[3, 6]`) renamed to `test_p3_count_
  not_in_layout_set_yields_no_copies` and reparametrized to `[3, 5, 7]` —
  `count=6` is no longer a "no copies" case (that assertion moved to the
  new B7 test file's own P4). Module docstring's P3 bullet updated to
  match. No other test in this file changed — P1/P2/P4-P8 (N=4 corner
  regression, absent-count honesty, missing-geometry/oversized fail-
  closed, quad-X divergence, single-node, motor-family regressions) are
  untouched.
- `tests/test_geometry_standoff_layout_n_ne4_b7.py` (new) — P1–P10, see
  below.
- `docs/IMPLEMENTATION_TASKS.md` — PRIORIDAD ACTUAL synced (suite `2697`,
  new 🟡 LANDING entry, queue updated).
- `.jes/state/engineering_state.json` — top-level tracking fields synced;
  `engineer_ratification` left untouched.

**Not touched**, confirmed via `git diff --stat`: `src/jarvis/domains/
aerial.py`, `src/jarvis/core/orchestrator.py` (this cycle's own diff is
zero — the file's cumulative diff in the working tree is entirely from
the two prior, still-uncommitted cycles), `ui/spatial-board/**`,
`library/**`, `pyproject.toml` (version still `0.4.1`), no `workspace/`
mutation.

## Behavior changed

- New: `frame_standoff.properties["count"] == 6` or `== 8` (with a
  declared box standoff and a declared box `frame_plate`) now emits
  `solidCopies`/`solidCopyOffsetsMm` — perimeter points, never a row.
- Unchanged: `count == 4` behavior is byte-identical to B4-min (same
  function call, same formula, regression-tested at P1). Every other
  in-range `count` (2, 3, 5, 7, 9..16), missing, or non-numeric still
  omits both keys entirely — same fail-closed honesty B4-min established,
  now also covering 5 and 7 explicitly (P3 in both the updated gate suite
  and the new B7 suite).
- Unchanged: motors/propellers/frame_arm/prop_adapter quad-X copy/offset
  logic — zero lines touched in those branches; regression-tested (P9 in
  the new file, and the existing gate suite's own P8).
- Unchanged: `_main_plate_corner_points`'s own signature and body — not a
  single line inside it changed.

## Tests

New file `tests/test_geometry_standoff_layout_n_ne4_b7.py` (10 tests):
- P1 `count=4` → same 4 corner points as B4-min, `zMm == 0` on all.
- P2 `count` absent → no copies.
- P3 `count=3` → no copies.
- P4 `count=6` + 100×100 plate / 5×5 standoff → `solidCopies == 6`; point
  set = 4 corners ∪ `{(0, ±47.5)}`.
- P5 `count=8` + same fixture → `solidCopies == 8`; corners ∪ all 4 edge
  mids.
- P6 `count=6` + plate 120×80 (`Lp > Wp`) → long-edge mids on `±hy`
  (`hx=57.5, hy=37.5`).
- P7 `count=6` + plate 80×120 (`Wp > Lp`) → long-edge mids on `±hx`
  (`hx=37.5, hy=57.5`).
- P8 fail-closed: oversized standoff (200mm vs 100mm plate) → no copies;
  missing `frame_plate` → no copies.
- P9 exactly one `frame_standoff` node; motors/propellers/frame_arm/
  prop_adapter quad-X copies (4, with wheelbase 230) unaffected by a
  sibling `count=6` standoff.
- P10 standoff offsets (`count=8`, 8 points) still differ from motors'
  quad-X station offsets (4 points) even with `wheelbase_mm=230` present
  on a sibling `frame` spec.

Updated `tests/test_geometry_standoff_count_gate_b4.py`:
- `test_p3_count_not_4_yields_no_copies([3, 6])` →
  `test_p3_count_not_in_layout_set_yields_no_copies([3, 5, 7])` — the only
  change in this file; P1/P2/P4-P8 untouched, none weakened.

Executed:
- `python -m pytest -q tests/test_geometry_standoff_layout_n_ne4_b7.py` →
  10 passed.
- `python -m pytest -q tests/test_geometry_standoff_count_gate_b4.py` →
  10 passed (was 9 before the parametrize edit; net +1 from adding a
  third rejected-N case).
- `python -m pytest -q` (full suite) → **2697 passed**.

## Non-goals honored

- No Continuity per-post offset declare grammar.
- No row fallback for arbitrary N (propeller pattern) — Option A (the
  IC's own default) was implemented, not Option B.
- No N=5/7/9+ perimeter heuristic — only `{4, 6, 8}` accepted, matching
  the IC's own locked table exactly.
- No Rooster/catalog `standoff_count` seed invented.
- No `ui/` change, no IDLE/`aerial.py` change, no version bump.
- The tie-break for `Lp == Wp` (the 100×100 fixture) resolves toward the
  `y`-edge branch, exactly as locked in §0.1/§3.

## Remaining risks

- None specific to this Buy. The deliberate duplication of the `hx`/`hy`
  inset formula between `_main_plate_corner_points` and
  `_standoff_perimeter_midpoints_mm` (rather than a shared helper) means
  a future change to that formula (e.g. a different inset convention)
  would need to update both call sites — documented in both functions'
  own docstrings, pointing at each other.
