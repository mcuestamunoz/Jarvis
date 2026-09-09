# Implementation Review — Scene3D-from-pose B1

**Date:** 2026-09-09  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_geometry_scene3d_from_pose_b1.md](implementation_contract_geometry_scene3d_from_pose_b1.md)  
**Report:** [implementation_report_geometry_scene3d_from_pose_b1.md](implementation_report_geometry_scene3d_from_pose_b1.md)  
**Buy:** Engineer ★ **B1** — additive DTO + CSS place, single-level

## Verdict

**PASS WITH NOTES**

IC locks held. Projector DTO and visor placement share one omit gate. Axis remap and center-to-center formula match the locked arithmetic. No chain composition (Cursor independently confirmed U8). Fit stub still QUEUED. Closable. Engineer Board smoke **ACCEPT**.

---

## Checklist

| Criterion | Result |
|---|---|
| `_declared_box_pose_dto` shared by `_fields` and `_emit` | **Pass** |
| DTO omit: missing / not-box origin; keys only for set axes | **Pass** — P1/P3/P4/P6 + Cursor P4 shapeless live |
| `_fields` no longer uses looser `origin_key in components` | **Pass** |
| `SpatialNode.declaredBoxPose?` | **Pass** |
| `solidWrapperPx` box L×H / disk diameter×diameter | **Pass** — IC U1/U2 |
| `layoutSolidsFromPose` slots via `layoutSolidsRow`; one hop from origin **slot** | **Pass** |
| Axis remap `translate3d(x_px, z_px, y_px)` + center correction | **Pass** — formula + Cursor U4/U7 |
| `Solid3D` `originY`/`originZ` + `translate3d`; faces unchanged | **Pass** |
| `Scene3D` calls `layoutSolidsFromPose` only (row helper internal) | **Pass** |
| Same `onSelect` / no 3D edges / no Three.js / no catalog seed | **Pass** |
| No writer cycle / Continuity / orchestrator / version bump | **Pass** — those diffs empty; `0.3.8` |
| P1–P6 + suite **2462** | **Pass** — numbering ≠ IC IDs (N2) |
| UI 31 + typecheck | **Pass** — IC U8/U5/U6 not named in suite (N3) |
| Stale Scene3D “pose deferred” comment | **N1** — required by IC; Cursor fixed in review (comment only) |

---

## Independent verification

| Check | Result |
|---|---|
| `pytest -q` | **2462 passed** |
| New Python file | **6 passed** (plus 27 sibling pose tests green) |
| `npm test` / `typecheck` | **31** / clean |
| Forbidden trees | **empty** — `component_writers.py`, pose assist, `orchestrator.py`, `library/`, visor `package.json` deps, `boardSelection.ts` |
| Shapeless `frame_plate` origin omits DTO **and** `origen pose` | **Confirmed** (IC P4; not a named unit test) |
| Pose DTO + `mountedOn` coexist | **Confirmed** (IC P6) |
| IC U4: ESC `xMm=5` vs FC slot 0 → `{1, 0, 0}` | **Confirmed** |
| IC U7: disk Ø127 `xMm=5` vs FC → `originX=-18.25`, `originY=-28.75` | **Confirmed** |
| IC U8: battery vs posed ESC uses ESC **slot** (`originX=74.25`), not ESC visual (`1` → would be `9.25`) | **Confirmed** |
| IC U10: extra card `x: 9999` ignored | **Confirmed** |
| Fit stub | **QUEUED — DO NOT IMPLEMENT** |
| `pyproject.toml` version | **0.3.8** |

---

## Notes

### N1 — Scene3D module comment still said pose was deferred

IC §3.4 required updating it. Behavior was already wired to `layoutSolidsFromPose`. Cursor replaced the comment in review (no logic change). CSS `.sb-scene3d` still says “no pose” — presentational leftover; retune on next visor CSS touch.

### N2 — Python test IDs ≠ IC P1–P6 labels

Shipped file: single-axis DTO, three-axis + text, disk origin, vanished origin, no pose, omitted axes ≠ 0. That covers IC P1, P2 (no pose), P3 (vanished), P5 (disk). **IC P4** (shapeless plate) and **IC P6** (`mountedOn` orthogonal) are behavior-true, not named tests. Not a FAIL. Add them if this projector is touched again.

### N3 — Layout suite is 7 cases, not IC U3–U10 as listed

Present: unposed slots, 3-axis remap, omitted axes as 0, disk-origin fallback, missing origin, empty list, input order. Wrapper U1/U2 are in `scene3dScale.test.ts`. Missing **named** U5 (`zMm=4` → `originY=2`), U6 (`yMm=10` → `originZ=5`), U7, **U8 no-compose**, U10. Cursor ran those four outside the suite; algorithm matches. U8 is the load-bearing one — **do not drop it** if layout is edited. Prefer adding U8 to `scene3dLayout.test.ts` next touch.

### N4 — `types.ts` “missing x/y/z count as 0 for display”

True for the visor (`?? 0`). The projector still **omits** those keys (P6). Fine if read as visor, not schema default.

### N5 — Demo smoke still needs a Continuity phrase

Live demo still has **zero** `declared_box_pose` (prior census). Until `declara el esc a 5 mm en x respecto al fc`, the 3D pane stays a row. That is expected, not a regression.

---

## Phase

Implementation **CLOSED**. Engineer Board smoke ACCEPT ([smoke](engineer_smoke_geometry_scene3d_from_pose_b1.md)). Mapping rung 2 next (wheelbase on spec). Fit still QUEUED. Package `0.3.8` · suite **2462**.

**Chrome follow-up (2026-09-09, not a new IC):** Scene3D cluster centered in the 3D pane (`clusterCenterPx`). Named vitest **U8** (no chain composition) because `scene3dLayout.ts` was edited. UI tests **34**.
