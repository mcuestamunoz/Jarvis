# Investigation Review — Scene3D-from-pose B1 (visor reads `declared_box_pose`)

**Date:** 2026-09-08  
**Reviewer:** Cursor (JES)  
**Contract:** [investigation_contract_geometry_scene3d_from_pose_b1.md](investigation_contract_geometry_scene3d_from_pose_b1.md)  
**Report:** [investigation_report_geometry_scene3d_from_pose_b1.md](investigation_report_geometry_scene3d_from_pose_b1.md)  
**Parents:** mapping path rung 1 · Continuity pose CLOSED @ **2456** · CSS 3D CLOSED @ **2429**

## Verdict

**PASS WITH NOTES**

Lean **B1 — additive DTO + CSS placement, single-level only** is Buy-eligible. **B1+** chain composition is honestly later, not this Buy. **B1−** (DTO with visor still a row) correctly rejected. **B2** Three.js not evidenced. **B0** remains available; not required — DTO gap, axis remap, and remainder-row rule are all answerable.

**IC READY** after Engineer ★ **B1**. Fit stub stays **QUEUED**. Mapping rungs 2–5 stay later ★. Writer cycle-reject is a **named residual**, not this visor Buy’s center.

The report did the job the contract asked: it refused to parse card text, refused to treat the CSS 3D row as already placed, and found two load-bearing visor facts (Y/Z swap; top-left wrapper vs geometric center) plus a real writer hole (mutual-origin cycle) that justifies **not** composing chains this cycle.

---

## Checklist

| Criterion | Result |
|---|---|
| Executive lean + one paragraph | **Pass** — B1, not B1+, with a concrete cycle reason |
| As-is DTO gap / `originX`-only / stale row comment | **Pass** |
| Live census fresh, not memory | **Pass** — 3 box / 1 disk / 10 none; zero live pose (N1) |
| A — DTO vs `fields`; omit rule; projector-only | **Pass with N2** |
| B — origin seat; compose vs single-level; missing origin | **Pass with N3** |
| C — CSS ↔ declared axis table; `pxPerMm`; disk | **Pass with N4** |
| D — remainder row, not all-at-0 | **Pass** |
| E — no 3D mount edges / N-motors / second selection / Three.js | **Pass** |
| F — one lean; B0 evaluated | **Pass** |
| Risks named | **Pass** — axis swap + top-left are the silent-bug pair |
| Rungs 2–5 named not bought; fit QUEUED | **Pass** |
| No code / no IC in the report | **Pass** — `src/` `ui/` `tests/` clean vs `8930c0b` |

---

## Independent verification

| Claim | Cursor check |
|---|---|
| `_emit` optional keys = `geometry` + `mounted_on` only | **Confirmed** — `spatial_board.py:117-143` |
| Projector node extras vs base rect = `{geometry, mountedOn}` | **Confirmed** — `project_spatial_nodes_from_path` on live demo |
| `SpatialNode` has no pose object | **Confirmed** — `types.ts:27-42` |
| `scene3dLayout.ts:9` still says pose B0 DEFERRED | **Confirmed** |
| Live demo: 3 box (FC, ESC, battery), 1 disk (propellers), 10 none | **Confirmed** — `_geometry_from_spec` on `workspace/autonomía-de-10min-9ada1a1b0cca/state.json` (14 keys) |
| `motors` SKU `sunnysky_r2305_2500`, no `diameter_mm` in seed | **Confirmed** — `library/motores/_datos.json:107-114` (thrust/kv/mass/watts/prop/design_space only) |
| All `declared_box_pose` `None` | **Confirmed** — 0 non-null |
| `motors.mounted_on=frame_arm` (live) | **Confirmed** |
| Axis table: CSS width=L, translateZ depth=W, CSS height=H | **Confirmed** — `solidExtentPx` + `Solid3D.tsx:30-45` `{x:w, y:d, z:h}` |
| Naive `translate3d(x,y,z)` mismatches declared +Y/+Z | **Confirmed** — honest remap is CSS `translate3d(x_px, z_px, y_px)` after `mmToPx` |
| Wrapper `position:absolute`, no `top`/`left`; faces `top:0;left:0` | **Confirmed** — `.sb-solid` / `.sb-solid__face` |
| Writer accepts ESC→FC then FC→ESC (2-node cycle) | **Confirmed** — in-memory `set_component_declared_box_pose`; demo file **unchanged** |
| No writer/test coverage of mutual-origin cycles | **Confirmed** — grep `tests/test_geometry_pose_declared_box_frame_b1.py` empty for cycle |
| `_fields` omits pose text iff `origin_key in components` | **Confirmed** — does **not** re-check origin still a box (N2) |
| `Scene3D` shares `onSelect` with cards | **Confirmed** — `InfiniteCanvas.tsx` |
| Fit stub **QUEUED — DO NOT IMPLEMENT** | **Confirmed** |
| `src/` `ui/` `tests/` clean vs `8930c0b` | **Confirmed** |

---

## Agreement with report core

1. **Machine DTO, not `fields` parse** — agree. Same honesty class as `mountedOn`.  
2. **B1− is too thin** — agree. Card text already exists; another unread key repeats the gap.  
3. **Remainder row for unposed solids** — agree. Origin box stays in the row; child offsets from that row slot (not a new scene-zero). Better than the contract’s optional “first origin at 0.”  
4. **Keep CSS 3D** — agree. The gap is arithmetic (`mmToPx` + axis swap + center correction), not a renderer.  
5. **No `motor_count` instancing / no 3D mount edges / click-inspect reuse** — agree.  
6. **B1+ deferred because writer has no cycle guard and live chains are zero** — agree as **this Buy’s cut**. Not an argument that composition is dishonest forever (N3).  
7. **Census drift is real** — agree. Do not write an IC that assumes “5 solids” or “motors is a disk” from earlier reports.

---

## Notes for ★ / IC

### N1 — Live solids are 4, not 5; motors currently have no envelope

`sunnysky_r2305_2500` has no `diameter_mm` (unlike EMAX / SunnySky R2205 rows). `motors` is **shapeless** on the live demo. B1 places **whatever currently has `geometry`**. Do **not** seed motor diameter, wheelbase, or plate L×W in this IC. Pre-assembly lock already named the SKU move as a walk side-effect.

Writer tests that reject `motors` as origin because it is a **disk** (`test_t3`) use a **fixture** with `diameter_mm`. Live demo is a different shape class (`None`). IC visor tests should use explicit box/disk fixtures, not “the demo’s motors node.”

### N2 — DTO omit rule must be stricter than `_fields`

`_fields` shows pose text when `origin_key in components` even if that origin **lost its box** after the write. The DTO should omit unless origin is still present **and** `_geometry_from_spec` is still `box` — the same gate the writer uses at write time. That is the honest-absence rule to lock, not a verbatim copy of `_fields`.

### N3 — Single-level is a visor honesty lock, not a Continuity lock

Continuity can already persist a chain (ESC→FC **and** battery→ESC; or a 2-node cycle). B1 visor **must not** silently compose and **must not** crash-recurse. Lock copy:

```text
This node sits relative to its origin’s current row slot, one hop.
If the origin is itself posed, that origin pose is not applied to children this Buy.
```

Do **not** add writer cycle-reject in this IC unless Engineer ★ that rider separately. Named residual: visor compose + visited-set **or** writer cycle reject, when a live multi-level chain exists.

### N4 — Axis remap is in **px**; center correction is wrapper top-left vs `(w/2, h/2)`

Report’s `translate3d(x_mm, z_mm, y_mm)` is the **axis** table, not CSS units. IC: `mmToPx` / `SCENE3D.pxPerMm` (uncapped). CSS Z of the cuboid is already symmetric about wrapper `0` (`±d/2` faces), so the silent-bug pair is:

1. swap declared Y↔CSS Z and declared Z↔CSS Y;  
2. do not apply pose mm onto the wrapper’s **top-left** as if it were the geometric center.

Lock a center-to-center formula in the IC (origin row slot + half origin extent − half child extent + remapped offset). Disks use the **same** remap for **position**; still flat (`z` extent 0); no cylinder.

### N5 — Stale `layoutSolidsRow` comment

One-line docstring fix when that file is touched: pose exists in `ProjectState`; this function still does not read it (remainder-row helper).

---

## Buy options (reviewer)

| Option | Reviewer |
|---|---|
| B0 keep row | Honest spare; **not** recommended — facts are sufficient |
| **B1 DTO + CSS place, single-level** | **Recommend ★** |
| B1− DTO only | **Reject** this cycle |
| B1+ compose chains | **Reject** this cycle (N3) |
| B2 Three.js | **Reject** |
| Parse `fields` / place by `mounted_on` / N motors | **Reject** |

---

## Closable

Investigation **CLOSED** for Buy. Engineer ★ **B1** (`escribe IC` 2026-09-08). IC: [implementation_contract_geometry_scene3d_from_pose_b1.md](implementation_contract_geometry_scene3d_from_pose_b1.md). Package `0.3.8` · suite **2456** · HEAD `8930c0b`.
