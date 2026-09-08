# Engineer smoke — Continuity declared box-local pose B1 (2026-09-08)

**Status:** ACCEPT  
**Project:** `autonomía-de-10min` (`9ada1a1b0cca`)  
**Surface:** IDLE CLI → `declared_box_pose` → Board card text (3D row unchanged)  
**Parents:** [IC](implementation_contract_continuity_declared_box_pose_b1.md) · [review](implementation_review_continuity_declared_box_pose_b1.md) PASS WITH NOTES @ suite **2456**

## Walk

| Step | Phrase / action | Expect | Observed 2026-09-08 |
|---|---|---|---|
| 1 | `declara el esc a 5 mm en x respecto al fc` | `Declarado: esc a 5 mm en x respecto a flight_controller.` + honesty line | **PASS** — CLI paste exact |
| 2 | Board · card ESC | `origen pose` = `flight_controller` · `Δx mm` = `5` · 3D still a **row** | **PASS** — screenshot: those fields + `ejes pose`; visor still clustered/row solids, not ESC offset 5 mm from FC |
| 3 | `esc montado en frame_plate` | still mount, not pose | already declared on card (not re-walked) |
| 4 | `quita la pose del esc` | pose fields gone; 3D still unchanged | **PASS** — second screenshot: ESC card has `montado en` only, no `origen pose` / `Δx` |
| 5 | `declarar el esc` | not a pose write | not walked |

## 3D visor (locked this Buy)

`layoutSolidsRow` does **not** read `declared_box_pose`. Five solids stay a presentation row. Engineer confirmed: no 3D change is the expected outcome.

## Verdict

**ACCEPT.** Continuity declared box-local pose B1 closable.

## Next

Rung 1 of [3D mapping path](engineer_lock_geometry_3d_mapping_path.md): Scene3D-from-pose investigation next. Fit still QUEUED.
