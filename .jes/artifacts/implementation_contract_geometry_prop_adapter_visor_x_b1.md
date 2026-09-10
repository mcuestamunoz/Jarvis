# Implementation Contract — Prop adapter visor X copies B1

**Project:** Jarvis  
**Date:** 2026-09-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** CLOSED — REVIEWED PASS WITH NOTES @ **2646** + smoke **ACCEPT**  
**Parents:**
- [Feature lock — Continuity spatial assembly](engineer_lock_continuity_spatial_assembly_feature.md)
- Loose structure envelope+pose B1 **implemented** @ **2640** — `prop_adapter` can be a declared box + posed; **one** solid today
- Propeller visor copies **CLOSED** @ **2550** — count = motors `motor_count`
- Visor X stations **CLOSED** @ **2562** — same `_quad_x_station_points` for motors/props
- Frame arm visor X **CLOSED** @ **2622** — arm copies only when N=4 + quad_x + W
- Live 5min: adapter 12×12×8 declared; single pose vs `frame_plate` at ~(81,81,16) — **wrong product** (one FR stand-in)

**Type:** Projector only — when `prop_adapter` has geometry, emit `solidCopies` from motors’ `motor_count` (same `[2,16]` parse as propellers) and, when count==4 **and** quad_x+wheelbase, emit the **same** `solidCopyOffsetsMm` as motors/props/arms.  
**Not** four BOM `prop_adapter_*` keys. **Not** standoff corner copies (separate ★). **Not** disk-origin pose. **Not** inventing adapter mm. **Not** Conversation Engine.

**Baseline:** package **`0.3.8`** · suite **2640** (confirm in report)

**Output:** `.jes/artifacts/implementation_report_geometry_prop_adapter_visor_x_b1.md`

**Role lock:** **Claude implements.**

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B1-adapter-visor-X** — N adapter boxes, 1:1 with motors/hélices |
| 2 | Count | Cross-read motors `motor_count` via `_parse_solid_copies_count` — **same** as propellers. Never `current_parameters`. Never default 4. Never invent |
| 3 | Geometry gate | Own `prop_adapter` box required (`_geometry_from_spec`). No box → no copies |
| 4 | Stations | If count==4 **and** `_quad_x_wheelbase_mm` holds → `_quad_x_station_points` (reuse; never a second formula). Else: like propellers — emit `solidCopies` for any valid N in `[2,16]` **without** offsets (row), **or** omit copies when N≠4 (prefer **propeller pattern**: row for N=3). Document actual in report |
| 5 | Pose | Copies **strip** `declaredBoxPose` (existing `expandSolidCopies`). Do **not** compose the single FR pose onto four places. After this Buy, Engineer may clear the orphan FR pose or leave it (stripped when copies≥2) |
| 6 | BOM / cards | **One** `prop_adapter` forever |
| 7 | Standoff / cage / plates | **Out** |
| 8 | `ui/` | No behavior change required (expand already generic) |
| 9 | Version | **No** bump |

**Product sentence:**

```text
Un adaptador/collet por motor: N cajas en la misma X (o fila) que
motores/hélices. Una card prop_adapter.
```

**Not:**

```text
4 BOM adapters · standoff esquinas · pose FR única como verdad ·
Conversation Engine
```

---

## 1. You (Claude)

- Extend `_solid_copies` + `_solid_copy_offsets_mm` for `prop_adapter` (read propellers + arm paths; do not fork station math).
- Prefer propeller-style count (any N∈[2,16]) + X offsets only when N=4+quad_x+W — unless a one-line conflict forces arm-strict; then document.
- Tests + report. Full pytest. `ui/` empty unless proven hole.
- Do **not** implement standoff multiplicity. Do **not** invent mm. Do **not** bump version.
- **STOP** if you need a second station formula or four ComponentSpecs.

---

## 2. Intent

```text
prop_adapter box + motors.motor_count=4 + quad_x + wheelbase
  → solidCopies=4 + same offsets as motors
Scene3D: four adapter boxes at FR/FL/RL/RR (pose on copies stripped)
```

---

## 3. Tests

| ID | Behavior |
|---|---|
| P1 | Adapter box + motors count 4 + quad_x + W → `solidCopies==4`, offsets == motors’ |
| P2 | N=3 + adapter box → copies without X fake (row **or** omit — document; never 3-station X) |
| P3 | No adapter geometry → no `solidCopies` |
| P4 | Exactly one `prop_adapter` node |
| P5 | Motors/props/arm copy regressions still green |
| P6 | Library / version untouched |

---

## 4. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/workspace/spatial_board.py` | `_solid_copies` / `_solid_copy_offsets_mm` for `prop_adapter` |
| `tests/test_geometry_prop_adapter_visor_x_b1.py` | P1–P6 |
| `.jes/artifacts/implementation_report_geometry_prop_adapter_visor_x_b1.md` | write |

---

## 5. Engineer smoke (after review)

1. 5min with adapter box already declared  
2. Reload Board — **4** adapter boxes on the X (under/near motors)  
3. One `prop_adapter` card  

Optional: `quita la pose del adaptador` if the stripped FR pose confuses the card fields.

Record [engineer_smoke_geometry_prop_adapter_visor_x_b1.md](engineer_smoke_geometry_prop_adapter_visor_x_b1.md).

---

## Explicitly not this IC

`frame_standoff` corner ×4 · cage copies · plate label noun fix · sourced #4 · Conversation Engine · version bump
