# Implementation Report — Visor X stations from cited wheelbase B1

**IC:** [implementation_contract_geometry_visor_x_stations_b1.md](implementation_contract_geometry_visor_x_stations_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-09
**Baseline:** package `0.3.8` · suite 2555 → **2562** (2555 + 7 new Python), UI 39 → **43** (+4)

---

## Files changed

| File | Change |
|---|---|
| `src/jarvis/workspace/spatial_board.py` | New additive DTO `solidCopyOffsetsMm` on `motors`/`propellers` nodes. Added `_quad_x_wheelbase_mm` (the one shared frame-fact gate: `frame.configuration == "quad_x"` exactly + finite positive `frame.wheelbase_mm`), `_quad_x_station_points` (the `a = W/(2√2)` formula, 4 points FR/FL/RL/RR, Z=0), and `_solid_copy_offsets_mm` (gates on `solid_copies == 4` exactly + the frame facts, independent per spec's own geometry — already enforced upstream by `_solid_copies` itself). `place()`/`_emit` wired to pass the already-computed `solid_copies` count through (never recomputed) so the two DTO counts can never drift apart. |
| `ui/spatial-board/src/types.ts` | Added optional `solidCopyOffsetsMm?: {xMm,yMm,zMm}[]` to `SpatialNode`. |
| `ui/spatial-board/src/scene3dLayout.ts` | `ExpandedSolid` gained `offsetMm?`. `expandSolidCopies` now reads `solidCopyOffsetsMm` off the node; when its length matches `solidCopies` exactly, each copy `i` gets `offsetMm: offsets[i]` instead of a row slot — a length mismatch or absence falls back to the existing row behavior unchanged. `layoutSolidsFromPose` gained an `offsetMm` branch: when present, position is computed directly from the declared mm offset (same axis remap as pose: +X→`originX`, +Z→`originY`, +Y→`originZ`), bypassing the row-slot/origin-lookup path entirely; the underlying row-slot computation for OTHER items is untouched, so pose-based placement of unrelated solids (FC, battery, …) is unaffected. |
| `ui/spatial-board/src/Scene3D.tsx` | Threaded `solidCopyOffsetsMm` into `expandSolidCopies`'s input and `offsetMm` into `layoutSolidsFromPose`'s input — the two call sites that already existed, no new logic. |
| `tests/test_geometry_visor_x_stations_b1.py` | **New.** P1–P7 exactly per IC §4. |
| `ui/spatial-board/src/scene3dLayout.test.ts` | Added U6–U9 (continuing the existing `expandSolidCopies` describe block's numbering past the pre-existing U1–U5) covering the IC's U1–U3 behaviors plus one extra (length-mismatch fallback). |

`set_component_declared_box_pose` (writer), `library/`, `workspace/`, `pyproject.toml` — confirmed **untouched** (`git status --short` empty for all three; version still `0.3.8`).

---

## Behavior changed

- `motors` and `propellers` nodes now carry an additive `solidCopyOffsetsMm` (4 points) **iff**: that spec's own `solidCopies` (unchanged mechanism) is exactly `4`, AND the sibling `frame` spec declares `configuration == "quad_x"` (exact string) AND a finite positive `wheelbase_mm`. Any other count, or either frame fact missing/wrong, omits the key — the visor keeps today's plain row.
- Points: `a = wheelbase_mm / (2·√2)`; indices 0–3 = `(+a,+a,0)`, `(+a,-a,0)`, `(-a,-a,0)`, `(-a,+a,0)` (FR/FL/RL/RR) in the declared frame (L→+X, W→+Y, H→+Z). Opposite-pair distance (index 0 vs 2) is exactly `wheelbase_mm` — verified both in the Python unit tests and by direct computation.
- `motors` and `propellers` emit the **same** 4 points when both gates hold independently — a mute-Ø motors spec still omits its own `solidCopies`/offsets (its own geometry gate, unchanged), while propellers can still station on the identical points as long as its own `_solid_copies` is 4.
- Visor: `expandSolidCopies` places each of the 4 copies at its offset (bypassing the row slot) instead of the row layout, via the same declared-mm→CSS axis remap already used for `declaredBoxPose`. `declaredBoxPose` stays stripped on every copy regardless (unchanged). Any other node (FC, battery, unposed/uncopied solids) is completely unaffected — row-slot computation for those items is untouched.
- No change to `_bom_quantity`, the pose writer, disk-origin gating, `_solid_copies` itself (still exactly as shipped), or any catalog data.

---

## Tests added / executed

**Python** — `tests/test_geometry_visor_x_stations_b1.py`, 7/7 passing:
- P1: count 4 + `quad_x` + wheelbase 230 → motors `solidCopies==4` + 4 offsets, opposite-pair distance ≈230mm, propellers same 4 offsets, still one node each.
- P2: count 3 → `solidCopies==3`, no offsets anywhere even with `quad_x`+230.
- P3: missing `wheelbase_mm` → no offsets (never invents 230).
- P4: missing `configuration` → no offsets.
- P5: `configuration="hex"` → no offsets.
- P6: mute motors (no Ø) + count 4 + frame gate holds → motors no geometry/no offsets; propellers still stations on the same points.
- P7: no `motor_count` + `quad_x`+230 → no `solidCopies`/no offsets anywhere (`quad_x` does not win).

**UI** — `scene3dLayout.test.ts`, 43/43 passing (+4 new: U6 stations bypass the row and are not monotonically increasing; U7 `solidCopies:4` without offsets still lays out as today's row; U8 a length-mismatched `solidCopyOffsetsMm` falls back to the plain row; U9 `declaredBoxPose` stays stripped on copies even when offsets are present). `npm run typecheck` → clean.

**Full Python suite**: `python -m pytest -q` → **2562 passed**, 0 failed.

---

## Live census (read-only, post-change)

| Project | frame facts | motors `solidCopies`/offsets | propellers `solidCopies`/offsets |
|---|---|---|---|
| `autonomía-de-5min` | no `wheelbase_mm`/`configuration` yet (pre-vintage data) | `None` / `None` | `4` / `None` |
| `autonomía-de-10min` | `wheelbase_mm=230`, `configuration=quad_x` | `None` / `None` | `3` / `None` |

Both live projects correctly stay in **row** form today: 5min's frame lacks the cited facts entirely, and 10min's motor count is 3 (never coerced to 4). Neither case invents a wheelbase or forces stationing — this matches the IC's own "10min-shaped count 3 never stations" and "missing wheelbase never 230" locks. No `workspace/` file was mutated (read-only via `project_spatial_nodes_from_path`). The Engineer's live smoke (declaring `wheelbase_mm`/`configuration` on 5min's frame, then rebinding to `emax_rs2205s_2300`) is out of scope for this report per IC §6 — that remains a manual step recorded separately.

---

## Non-goals honored

No frame box/Rooster L×W invented. No `motor_count` coercion to 4. No `current_parameters` read for N. No writer change (`set_component_declared_box_pose` untouched). No `emax_rs2205_2300` Ø seeded. No per-copy `DeclaredBoxPose` array — offsets are a separate, purely additive DTO, never composed with pose. No cylinder. No Z stacking on `height_mm`. No version bump. No `"cabe"`/`"ensamblado"`/`"verificado"` in any new string.

---

## Remaining risks

- None identified specific to this change — the offsets gate reuses the exact same `solid_copies` value `_solid_copies` already computed (never recomputed independently), so the two DTO keys cannot drift apart by construction.
- As already accepted/unchanged by prior cycles: motor solids remain invisible on both live projects until the S-SKU rebind is applied (separate, already-shipped mechanism); 5min needs its frame updated with `wheelbase_mm`/`configuration` before stationing can ever activate there (an existing `actualiza la frame` flow, untouched by this Buy).
- Distinct hexacopter/other-N station layouts remain unbuilt (explicitly out of scope — `configuration != "quad_x"` or `N != 4` always falls back to the row, by design).
