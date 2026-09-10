# Implementation Contract — Frame standoff ×4 at Main Plate corners B1

**Project:** Jarvis  
**Date:** 2026-09-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** READY — Engineer “procede de momento con la de +4” (cuarteto central). Declared `standoff_count` generalista = **cola**, not this Buy.  
**Parents:**
- [Feature lock — Continuity spatial assembly](engineer_lock_continuity_spatial_assembly_feature.md)
- [Work order](engineer_next_geometry_loose_and_arms.md) — B3 this · B2 adapter landing · count-declared standoffs deferred
- Loose envelope+pose **CLOSED path** — `frame_standoff` can be a declared box + posed; **one** solid today
- Live 5min: standoff 5×5×25 + orphan single pose ~(30,30,4) — wrong product for “pilares del sandwich”
- Prop adapter / motors / arms X stations — **different math** (wheelbase). Do **not** reuse `_quad_x_station_points` here

**Type:** Projector only — when `frame_standoff` has a box **and** Main Plate (`frame_plate`) has a box L×W, emit `solidCopies: 4` + four corner offsets on the Main Plate footprint (inset by half the standoff’s own L×W).  
**Not** `standoff_count` Continuity declare (next Buy). **Not** N from `motor_count` / `quad_x` / wheelbase. **Not** four BOM keys. **Not** camera/VTX extra posts. **Not** inventing mm. **Not** Conversation Engine.

**Baseline:** package **`0.3.8`** · suite **2646** (confirm in report; after adapter if that landed first)

**Output:** `.jes/artifacts/implementation_report_geometry_frame_standoff_corners_b1.md`

**Role lock:** **Claude implements** (after / when PRIORIDAD hands off from adapter).

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B1-standoff-corners-4** — four identical sandwich posts at Main Plate corners |
| 2 | Count this Buy | **Fixed 4.** Never read motors. Never invent from `quad_x`. Never default when gates fail — omit copies |
| 3 | Geometry gate | `_geometry_from_spec(frame_standoff)` is a **box**. `_geometry_from_spec(frame_plate)` is a **box** with finite L×W > 0. Missing either → no `solidCopies` |
| 4 | Corner formula (only) | Let `Lp, Wp` = Main Plate length/width; `Ls, Ws` = standoff length/width. `hx = Lp/2 − Ls/2`, `hy = Wp/2 − Ws/2`. If `hx < 0` or `hy < 0` → **omit** offsets and copies (standoff larger than plate — fail closed). Else four points, Z=0: `(+hx,+hy)`, `(+hx,−hy)`, `(−hx,−hy)`, `(−hx,+hy)`. Index order FR/FL/RL/RR in declared plate axes (L→+X, W→+Y). **Never** wheelbase / 45° X |
| 5 | Helper | New private helper e.g. `_main_plate_corner_points(plate_geom, standoff_geom)` — do **not** overload `_quad_x_station_points` |
| 6 | Pose | Copies strip `declaredBoxPose` (`expandSolidCopies`). Orphan single pose may remain on the card |
| 7 | BOM / cards | **One** `frame_standoff` forever |
| 8 | Generalist count | **Out.** Document in report: next Buy = declared `standoff_count` (+ row or Engineer offsets when N≠4) |
| 9 | `ui/` / version | No UI change required · **no** bump |

**Product sentence:**

```text
Con standoff en caja y Main Plate en caja, el visor pinta 4 pilares
en las esquinas del sandwich. Una card. Sin inventar N desde el X.
```

**Not:**

```text
standoff_count Continuity · 4 BOM · estaciones de motor 230 ·
pilares de cámara/VTX · Conversation Engine
```

---

## 1. You (Claude)

- `_solid_copies`: `frame_standoff` → `4` iff both boxes and corner helper succeeds (or return 4 only when helper would emit 4 points — keep copies/offsets in lockstep).
- `_solid_copy_offsets_mm`: allow `frame_standoff`; call corner helper; never `_quad_x_station_points`.
- Tests + report. Full pytest.
- Do **not** implement `standoff_count` declare. Do **not** touch adapter/arm/motor X math beyond allowing the new key in the offsets allowlist carefully.
- Do **not** invent mm / bump version / mutate `workspace/`.
- **STOP** if the only path is hardcoding 230 or motor stations.

---

## 2. Intent

```text
frame_standoff box 5×5×25 + frame_plate box 100×100
  → solidCopies=4
  → offsets at (±47.5, ±47.5, 0)   # 100/2 − 5/2
Scene3D: four posts on Main Plate corners (pose stripped)
```

---

## 3. Tests

| ID | Behavior |
|---|---|
| P1 | Standoff box + Main Plate 100×100 + standoff 5×5 → `solidCopies==4`, offsets match formula (±47.5, ±47.5, 0) all sign combos |
| P2 | Missing standoff box or missing plate L×W → no `solidCopies` |
| P3 | Standoff L or W larger than plate → no copies (fail closed) |
| P4 | Offsets **≠** motors’ quad-X points (same fixture W=230) |
| P5 | Exactly one `frame_standoff` node |
| P6 | Motors/props/arm/adapter copy regressions still green |

---

## 4. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/workspace/spatial_board.py` | copies + corner helper + offsets branch |
| `tests/test_geometry_frame_standoff_corners_b1.py` | P1–P6 |
| `.jes/artifacts/implementation_report_geometry_frame_standoff_corners_b1.md` | write |

---

## 5. Engineer smoke (after review)

1. 5min: standoff already 5×5×25, Main Plate 100×100  
2. Reload Board — **4** posts at plate corners (not on motor X)  
3. One `frame_standoff` card  

Record [engineer_smoke_geometry_frame_standoff_corners_b1.md](engineer_smoke_geometry_frame_standoff_corners_b1.md).

---

## Explicitly not this IC

Declared `standoff_count` · N≠4 layouts · adapter reopen · plate label noun · sourced #4 · Conversation Engine · version bump
