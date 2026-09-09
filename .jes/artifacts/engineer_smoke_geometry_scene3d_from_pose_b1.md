# Engineer smoke — Scene3D-from-pose B1 (2026-09-09)

**Status:** ACCEPT  
**Project:** `autonomía-de-10min`  
**Surface:** IDLE CLI `declared_box_pose` → Board card text **and** CSS 3D placement  
**Parents:** [IC](implementation_contract_geometry_scene3d_from_pose_b1.md) · [review](implementation_review_geometry_scene3d_from_pose_b1.md) PASS WITH NOTES @ suite **2462**

## Walk

| Step | Phrase / action | Expect | Observed 2026-09-09 |
|---|---|---|---|
| 1 | `declara el esc a 5 mm en x respecto al fc.` | `Declarado: esc a 5 mm en x respecto a flight_controller.` + honesty line | **PASS** — CLI paste |
| 2 | Board · card ESC | `origen pose` = `flight_controller` · `Δx mm` = `5` · `ejes pose` honesty | **PASS** — screenshot: those fields; `montado en` still `frame_plate` (orthogonal) |
| 3 | Board · 3D pane | ESC solid **leaves the row**; sits next to FC at declared +X (5 mm is small vs box size — adjacent, not a new quadrotor) | **PASS** — yellow selected prism against the larger FC box; green prop disk remains on the left (unposed remainder slot). Not the old equal-gap row of all solids |
| 4 | Click | same `selectedId` — card outline + solid yellow | **PASS** — ESC card selected and ESC solid yellow together (click origin not filmed separately; shared selection holds) |
| 5 | `quita la pose del esc` | pose fields gone; 3D row again | **not walked** — Continuity CLEAR already ACCEPT @ **2456**; not a reopen |

## Honesty (locked this Buy)

Still **not** the Rooster, **not** four motors, **not** `"cabe"`. One hop, declared L→+X. `mounted_on` stays the 2D edge.

Live solids remain whatever has `geometry` (motors still no disk on this demo).

## Verdict

**ACCEPT.** Scene3D-from-pose B1 closable.

## Next

Mapping path rungs **2–5** later ★ (wheelbase / N-motor sketch / motor height / plate L×W / `"cabe"`). Fit still QUEUED. Engineer names the next rung.
