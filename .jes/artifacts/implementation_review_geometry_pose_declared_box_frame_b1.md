# Implementation Review — Geometry pose declared box-local frame B1

**Date:** 2026-09-08  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_geometry_pose_declared_box_frame_b1.md](implementation_contract_geometry_pose_declared_box_frame_b1.md)  
**Report:** [implementation_report_geometry_pose_declared_box_frame_b1.md](implementation_report_geometry_pose_declared_box_frame_b1.md)  
**Buy:** Engineer ★ B1 — box center + declared L→+X W→+Y H→+Z; Board text; no Scene3D move

## Verdict

**PASS WITH NOTES**

IC locks held. Schema + writer + projector text only. 3D visor untouched. Fit stub still QUEUED. Closable: this slice is programmatic (writer), same sequencing as `mounted_on` before Continuity.

---

## Checklist

| Criterion | Result |
|---|---|
| `DeclaredBoxPose` + `declared_box_pose` after `mounted_on` | **Pass** |
| Honesty in docstring (declared axes, not catalog/gravity/airframe) | **Pass** |
| Writer reuses `_geometry_from_spec`; reject disk / shapeless / missing / self | **Pass** |
| `_fields`: `origen pose` / `ejes pose` / optional Δ· mm | **Pass** — string exact |
| Omit pose block if origin key gone | **Pass** — Cursor live check (N1: no dedicated test) |
| No Scene3D / `layoutSolidsRow` / `scene3dScale` / `Solid3D` | **Pass** — `git diff` empty |
| No Continuity pose parser | **Pass** |
| Refresh preserves field | **Pass** — T6 |
| T1–T6 + suite | **Pass** — Cursor **2438** |
| Version | **None** — `0.3.8` |

---

## Independent verification

| Check | Result |
|---|---|
| `pytest -q` | **2438 passed** |
| New file | **9 passed** |
| Vanished origin: pose labels omitted, other fields remain | **Confirmed** — synthetic ESC `mass_g` only |
| `POSE_AXES_HONESTY_LABEL` | **Exact** IC string |
| `pyproject.toml` version | **0.3.8** |
| Fit stub | **QUEUED — DO NOT IMPLEMENT** |
| `ui/spatial-board/src/Scene3D.tsx` + `scene3dLayout.ts` | **diff empty** |

---

## Notes

### N1 — Vanished-origin omit has no unit test

Behavior is correct. Add a T8 later if we touch `_fields` again. Not a FAIL.

### N2 — Report wording

“empty `fields` list” for vanished origin is only true when the spec has no other rows. With `mass_g`, fields stay `['mass_g']`. Mechanism still honest.

### N3 — Demo Board will not show pose until something writes it

No Continuity phrase this Buy. Live `autonomía-de-10min` cards stay as today unless a writer call sets `declared_box_pose`. Smoke = 3D row unchanged + cards still load — **not** “I see Δx on ESC.”

### N4 — `spatial_board` module docstring

Still describes glyphs + `mounted_on` only. Tiny. Pose is in `_fields` comments.

---

## Phase

Implementation **CLOSED**. Engineer ACCEPT ([smoke](engineer_smoke_geometry_pose_declared_box_frame_b1.md)). Continuity pose later ★. Package `0.3.8` · suite **2438**.
