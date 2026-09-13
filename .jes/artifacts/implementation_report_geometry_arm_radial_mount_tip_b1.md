# Implementation Report — Arm radial Visor + Mount tip/parse align B1

**Buy ids:** `B1-arm-radial-visor` + `B1-mount-tip-parse-align`
**IC:** [implementation_contract_geometry_arm_radial_mount_tip_b1.md](implementation_contract_geometry_arm_radial_mount_tip_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-13
**Baseline:** package `0.4.1` · suite 2844 → **2858** (14 new Python tests) · UI 99 → **103** (4 new TS tests)

---

## Part A — mount tip/parse align

### A2/A3 — checklist tip + trigger (`mount_standard_assist.py`)

- Ambiguous-plate rows now carry an `example_phrase` built from the same `(key, noun, participle)` table the "suggested" branch already uses (`f"{noun} {participle} en <clave>"`), and `format_mount_standard_checklist` renders that instead of the bare `f"'{subject} montado en <clave>'"`. A raw key like `flight_controller`/`sensors` never silently fails `_resolve_subject`'s noun-only table again, because the tip itself never surfaces the raw key.
- Trigger regex widened from `montajes\s+estandar` to `montajes?\s+estandar` — one-character change, singular "montaje estándar" now resolves identically to the plural.

### A3 (parse) — exact-key subject fallback (`mounted_on_declare_assist.py`)

- `parse_mounted_on_declare`'s SET path: `subject = _resolve_subject(subject_segment) or _exact_key_match(subject_segment, components)`. Locked to the **SET** path only, per the IC's own arrow notation (`"... SET"`) — the CLEAR path is untouched and still noun-only (confirmed by `test_a4_clear_path_unchanged_noun_only`).
- `_resolve_subject`/`resolve_component_subject_noun` (the public wrapper reused by `declared_envelope_declare_assist.py`, `declared_box_pose_declare_assist.py`, `estimated_temporary_plate_assist.py`, and two orchestrator call sites) were **not** touched — widening that shared noun-only function would have silently changed behavior for four unrelated callers outside this Buy's scope. The exact-key fallback lives only inside `parse_mounted_on_declare` itself.

## Part B — arm radial Visor (L-aware)

### `_frame_arm_radial_offsets_mm` (new, `spatial_board.py`)

Implements IC §0.1 exactly: for each of the four quad-X stations (`_quad_x_station_points`, unchanged), `R = hypot(station.x, station.y)`, `û = station/R`. If the arm's own declared `length_mm` (L) fits the gap (`L <= R`), the center is pulled back from the station by `L/2` along `û` so the box's **distal** end lands exactly on the station. If `L > R`, the geometry is never rescaled — the center sits at `û * (R/2)` instead, so the box may honestly overhang the station or fall short of the origin. Each point also carries `yawDeg = atan2(station.y, station.x)` in degrees. Returns `None` (never partial) when the arm has no box geometry, `length_mm` isn't a positive number, or the shared wheelbase gate fails.

`_solid_copy_offsets_mm` now branches `frame_arm` to this new helper; `motors`/`propellers`/`prop_adapter` are **byte-identical** to before — still `_quad_x_station_points(wheelbase_mm)` directly, confirmed by `test_b1_motors_propellers_prop_adapter_keep_raw_station_points`.

### Frontend — `yawDeg` threading (`ui/spatial-board/src`)

- `types.ts`: `SpatialNode.solidCopyOffsetsMm` points gained an optional `yawDeg`.
- `scene3dLayout.ts`: `SolidLayout`, `PoseItem.offsetMm`, and `ExpandedSolid.offsetMm` all gained the same optional `yawDeg`; `layoutSolidsFromPose`'s `item.offsetMm` branch threads `item.offsetMm.yawDeg` straight through (undefined for motors/propellers/prop_adapter, since their DTO never carries it). `expandSolidCopies` needed no code change — it already assigns the whole `offsets[i]` object, so `yawDeg` flows through the existing assignment once the type allowed it.
- `Solid3D.tsx`: new `yawDeg` prop, applied only on the box branch as `rotateY(${-yawDeg}deg)`, composed as `translate3d(...) rotateY(...)` (rotate about the box's own local center first, then move to world position — never rotating about the world origin). The `-yawDeg` sign is derived from the CSS `rotateY(a)` matrix (`x' = cos(a)x + sin(a)z`, `z' = -sin(a)x + cos(a)z`) against this codebase's own documented axis remap (declared +X → CSS X, declared +Y → CSS Z/depth): solving for the angle that sends local `(1,0,0)` to world `(cos(yawDeg), 0, sin(yawDeg))` gives `a = -yawDeg`. Verified algebraically (see code comment) against the concrete station-0 case (yawDeg=45° → both X and Z should be positive) but **not visually rendered** — this is the one part of the change I could not confirm in a browser; Engineer's own §3.B smoke ("arms diagonal toward motors... not boxes under motor disks") is the actual verification for this sign.

## Files changed

- `src/jarvis/core/mount_standard_assist.py` — ambiguous tip uses noun+participle; singular trigger.
- `src/jarvis/core/mounted_on_declare_assist.py` — exact-key subject fallback on the SET path only.
- `src/jarvis/workspace/spatial_board.py` — new `_frame_arm_radial_offsets_mm`; `_solid_copy_offsets_mm` branches `frame_arm` to it; `import math` added.
- `ui/spatial-board/src/types.ts`, `scene3dLayout.ts`, `Solid3D.tsx`, `Scene3D.tsx` — `yawDeg` threaded end to end.
- `tests/test_geometry_arm_radial_mount_tip_b1.py` (new) — 14 tests, A1–A4 + B1–B5 + no-writer-touch.
- `ui/spatial-board/src/scene3dLayout.test.ts` — 4 new tests (U25–U28) covering yaw threading through `layoutSolidsFromPose`/`expandSolidCopies`.

### Pre-existing tests updated for the now-superseded "arm == raw station" assumption

Three existing test files asserted `frame_arm`'s offsets were **identical** to motors' raw station points — the exact behavior this IC's own Engineer lock explicitly supersedes ("use declared arm L... not fixed station/2"; the old behavior here was actually the even-simpler "no placement logic at all", not even a station/2 midpoint). Each assertion was updated to instead assert the arm differs from the raw station and matches the new L-aware formula (fixture numbers unchanged: arm L=80mm, wheelbase=230mm in all three, so the same expected values apply everywhere):

- `tests/test_geometry_frame_arm_visor_x_b1.py::test_p3_...` — renamed to `test_p3_projector_arm_stations_are_l_aware_not_raw_motor_stations`, docstring updated, assertion flipped from `==` to `!=` plus explicit expected L-aware values.
- `tests/test_geometry_prop_adapter_visor_x_b1.py::test_p5_...` — arm asserted separately from the shared motors/propellers/prop_adapter equality block.
- `tests/test_geometry_standoff_count_gate_b4.py::test_p8_...` and `tests/test_geometry_frame_standoff_corners_b1.py::test_p6_...` — same split; arm asserted `!=` the shared quad-X offsets plus its own `yawDeg`.

No test was weakened — each now asserts the correct, IC-locked behavior instead of the superseded one, with the same or greater precision (exact expected numeric values, not just an equality/inequality check).

## Tests

Executed: `python -m pytest -q` → **2858 passed, 1 skipped** (0 failed). `cd ui/spatial-board && npx vitest run` → **103 passed** (was 99). `npx tsc --noEmit` → clean.

Coverage against IC §2:

| ID | Covered by |
|---|---|
| A1–A4 | `test_a1_exact_key_subject_parses_as_set`, `test_a2_ambiguous_tip_uses_noun_not_bare_key`, `test_a3_singular_montaje_trigger_matches_plural`, `test_a4_noun_based_phrases_still_parse_non_regression`, `test_a4_clear_path_unchanged_noun_only` |
| B1 | `test_b1_motors_propellers_prop_adapter_keep_raw_station_points` |
| B2 | `test_b2_l_less_equal_r_distal_end_at_station` |
| B3 | `test_b3_l_greater_than_r_centers_on_half_gap_l_unchanged` |
| B4 | `test_b4_yaw_matches_atan2_station` |
| B5 | `test_b5_missing_length_mm_omits_offsets`, `test_b5_no_wheelbase_omits_offsets_and_copies`, `test_b5_motor_count_not_four_omits_offsets_and_copies`, `test_b5_negative_or_zero_length_omits_offsets` |
| B6 | `scene3dLayout.test.ts` U25–U28 (yawDeg threads from DTO through `layoutSolidsFromPose`/`expandSolidCopies`); `Solid3D.tsx`'s `rotateY` application is code-reviewable but not DOM-rendered (no rendering test harness exists in this repo today) — Engineer visual smoke is the actual confirmation |
| T | Full suite green above; `pyproject.toml` still `0.4.1` |

## Reproducibility check against both live projects (read-only)

Loaded both live `state.json` files directly into `ProjectState`, no orchestrator mutation, nothing saved:

- **`10-min-autonomía`**: `frame_arm` has a real declared box; `solidCopies: 4`, offsets show the box centered ~72.5mm from origin per station with `yawDeg` in `{45, -45, -135, 135}` — its distal end (`center + L/2` along the radial direction) lands exactly on the motor station at ~112.5mm, confirming the "distal at station" formula end-to-end against real project data, not just the synthetic fixture.
- **`autonomía-de-5min`**: no `frame_arm` declared at all — `solidCopies`/`solidCopyOffsetsMm` both absent, exactly the pre-existing "not declared → nothing to draw" honesty (unrelated to this Buy).

## Non-goals honored

No arm L invented from wheelbase/body (only ever reads the arm's own `length_mm`). No geometry rescaling (`L > R` never shrinks L). No new `mounted_on`/`declared_box_pose` writer for `frame_arm` (confirmed by `test_no_new_frame_arm_pose_or_mount_writer_call` — the spec object is byte-identical before/after projection). Motors/propellers/prop_adapter stations untouched (`test_b1_...`). No four separate BOM arm keys (still one `frame_arm` `ComponentSpec`). No version bump (`pyproject.toml` still `0.4.1`). No `workspace/` mutation (confirmed via `git status --short -- workspace/`, empty).

## Remaining risks / notes for review

- **The `Solid3D.tsx` `rotateY(-yawDeg)` sign is algebraically derived, not visually confirmed** — I do not have a browser in this environment to render the CSS 3D scene. I verified the matrix algebra against the codebase's own documented axis remap and a concrete station case, and left a full derivation as a code comment, but Engineer's §3.B smoke ("arms diagonal toward motors... not boxes under motor disks") is the real check. If the sign is flipped, the fix is a single character (`-yawDeg` → `yawDeg`) in `Solid3D.tsx`.
- The `_exact_key_match` subject fallback in `parse_mounted_on_declare` is generic (any declared key, not just the four stack-subject keys) — mirroring `_resolve_target`'s own already-generic exact-key-first discipline. A literal `"frame_arm montado en frame_plate"` would now resolve `frame_arm` as a SUBJECT, which is outside `mount_standard_assist.py`'s own checklist scope (frame_arm is a TARGET-only noun there) but not explicitly forbidden by this IC for the raw grammar layer — flagging for Cursor to confirm this generality is intended, since the IC's own examples only named `flight_controller`/`sensors`.
- Four existing test files' assertions were changed from `==` to `!=` (arm vs. raw station) because the IC explicitly supersedes that old behavior — flagged prominently above and in each touched file's own comments so a future reader never mistakes this for an unexplained flip.
