# Implementation Contract — Frame arm envelope + visor X copies B1

**Project:** Jarvis  
**Date:** 2026-09-10  
**Author:** JES / Cursor (Engineer Interface)  
**Implementer:** Claude Code  
**Reviewer:** Cursor against this IC after the edit

**Status:** READY — Engineer “4 arm frames” + juntar sueltas (this Buy = **arms track A1** only)  
**Parents:**
- [Feature lock — Continuity spatial assembly](engineer_lock_continuity_spatial_assembly_feature.md) — product name for this capability
- [Work order](engineer_next_geometry_loose_and_arms.md) — A1 arms · B1 loose · #4 sourced
- Visor X stations **CLOSED** — motors/propellers only; `frame_arm` omitted from `_solid_copies`
- Geometry: `_geometry_from_spec` — box needs L×W×H; `thickness_mm` alone → **no solid**
- Pose origin axes investigation — one `frame_arm` key, not four BOM siblings (N7); **visor copies** (same pattern as motors) are the honest 4-arm silhouette — not four `ComponentSpec`s
- Envelope allowlist today: battery · sensors · kit · `frame_plate*` — **not** `frame_arm`

**Type:** (1) Allow **declared** L×W×H on `frame_arm` via existing envelope writer/parser. (2) When arm has a solid and frame is `quad_x` + finite `wheelbase_mm` and motors `motor_count==4`, emit `solidCopies: 4` + **same** `solidCopyOffsetsMm` quad-X points as motors (reuse `_quad_x_station_points`).  
**Not** inventing arm length from 230. **Not** four BOM `frame_arm_*` keys. **Not** prop_adapter/caps/standoff (B1). **Not** sourced dims. **Not** Conversation Engine. **Not** assembly-root change.

**Baseline:** package **`0.3.8`** · suite **2615** (confirm in report)

**Output:** `.jes/artifacts/implementation_report_geometry_frame_arm_visor_x_b1.md`

**Role lock:** **Claude implements.**

---

## 0. Engineer Buy (locked)

| # | Decision | Lock |
|---|---|---|
| 1 | Buy | **B1-arm-visor-X** — drawable arm box + 4 copies at motor stations |
| 2 | Envelope | Add `frame_arm` to declared-envelope allowlist + subject noun (`brazo`/`brazos`/`arm`/`frame_arm`). SET needs **three** mm (like battery). No thickness→L/W invent. `thickness_mm` may remain on the card untouched |
| 3 | Copies | `_solid_copies`: if `suggested_key=="frame_arm"` and geometry exists, count = cross-read motors’ `motor_count` (same `[2,16]` parse as propellers) — **or** only emit copies when count==4 **and** quad-X stations exist (prefer: same gate as station emit so N=3 stays **one** row solid, never fake 3-station X) |
| 4 | Stations | Reuse existing `_quad_x_wheelbase_mm` + `_quad_x_station_points`. Same points as motors/props. Z=0. Never a second formula |
| 5 | Pose | Arm copies **strip** `declaredBoxPose` (same as motor copies). Do not pose the single arm key onto four places via Continuity |
| 6 | BOM / schema | **One** `frame_arm` ComponentSpec forever this Buy |
| 7 | Library | **No** seed inventing arm L×W from wheelbase |
| 8 | Version | **No** bump |

**Product sentence:**

```text
Declaro L×W×H del brazo; con quad_x y 4 motores el visor pinta 4 cajas
en la misma X que motores/hélices. Un solo frame_arm en el BOM.
```

**Not:**

```text
230 como largo del brazo · 4 keys frame_arm_2… · cylinder · sueltas
prop_adapter/caps · Conversation Engine
```

---

## 1. You (Claude)

- Writer allowlist + envelope parser noun for `frame_arm`.
- `_solid_copies` + `_solid_copy_offsets_mm` for `frame_arm` under the locks above (read existing motors/propellers paths; do not fork a second station math).
- Tests + report. Full pytest (+ ui layout tests if you touch shared expand behavior — arm is DTO-side; Scene3D already expands any `solidCopies`).
- Do **not** implement B1 loose parts. Do **not** invent mm. Do **not** bump version.
- **STOP** if the only way to get an arm solid is stitching wheelbase into length.

---

## 2. Intent

```text
IDLE "declara el brazo 80 x 20 x 4 mm"
  → frame_arm box (Engineer numbers)

Projector: motor_count=4 + quad_x + wheelbase → solidCopies=4 + offsets
Scene3D: four arm boxes at FR/FL/RL/RR stations (same as motors)
```

---

## 3. Tests

| ID | Behavior |
|---|---|
| P1 | Writer SET `frame_arm` 3 mm → properties `source=declared` |
| P2 | Parser `declara el brazo A x B x C mm` → SET `frame_arm` |
| P3 | Projector: arm box + motors count 4 + quad_x + wheelbase → `solidCopies==4` and offsets length 4 matching motors’ station math |
| P4 | N=3 or missing quad_x → no X stations on arm (row / single — document actual) |
| P5 | No `length_mm` invented on Rooster `arm_thickness` seed |
| P6 | Battery/plate/kit envelope regressions still green |

---

## 4. Files (expected)

| Path | Change |
|---|---|
| `src/jarvis/core/component_writers.py` | allowlist `frame_arm` |
| `src/jarvis/core/declared_envelope_declare_assist.py` | brazo noun |
| `src/jarvis/workspace/spatial_board.py` | copies + offsets for arm |
| `tests/test_geometry_frame_arm_visor_x_b1.py` | P1–P6 |
| `.jes/artifacts/implementation_report_geometry_frame_arm_visor_x_b1.md` | write |

---

## 5. Engineer smoke (after review)

1. `declara el brazo <L> x <W> x <H> mm` (your mm — not forced 230)  
2. Reload Board — 4 arm boxes on the X under/near motors  
3. Single `frame_arm` card  

Record [engineer_smoke_geometry_frame_arm_visor_x_b1.md](engineer_smoke_geometry_frame_arm_visor_x_b1.md).

---

## Explicitly not this IC

Loose prop_adapter/caps/standoff · invent arm L from 230 · 4 BOM arms · sourced dims · Conversation Engine · version bump
