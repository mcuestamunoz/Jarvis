# Implementation Review — Board Situar free camera B1

**Date:** 2026-09-10  
**Reviewer:** Cursor (JES)  
**Contract:** [implementation_contract_board_situar_free_camera_b1.md](implementation_contract_board_situar_free_camera_b1.md)  
**Report:** [implementation_report_board_situar_free_camera_b1.md](implementation_report_board_situar_free_camera_b1.md)  
**Engineer field:** (1) arrastre invertido / no guarda · (2) “no me deja mover lateral”

## Verdict

**PASS WITH NOTES** (after axis/save hotfix **+ lateral screen-plane hotfix #2**).

Original Claude cut: free camera + orbit OK; **axis map FAIL**. Hotfix #1: WYSIWYG x/z + `write_json(state_path)`. Hotfix #2: inverse camera rotation so screen-lateral drag works at side/back view. UI **80**. Closable after Engineer re-smoke.

---

## Checklist

| Criterion | Result |
|---|---|
| Situar does not force tilt `(0,0)` | **Pass** — no `SITUAR_TILT` / `effectiveTilt` |
| Orbit while Situar ON | **Pass** — background mousedown; solid `stopPropagation` |
| Default drag WYSIWYG | **Pass** (#1+#2) — untilted Δx→`x_mm`/Δy→`z_mm`; tilted = screen-plane inverse |
| Lateral drag at side view | **Pass** (#2) — screen-X → local depth/`y_mm` when `rotateY≈90` |
| Shift+drag = depth | **Pass** — local `dz` → `y_mm` |
| Preview ↔ commit | **Pass** — same inverse |
| POST → same writer | **Pass** — `board_pose_bridge` |
| Save to Vite `state_path` | **Pass** (#1) — `write_json(state_path)` |
| Singleton-only | **Pass** |
| No version bump | **Pass** — `0.4.0` |
| Suites | **Pass** — UI **80** / typecheck clean |

---

## Notes

### N1 — IC lock #5 wording superseded

IC said Shift→`z_mm`. Hotfix #1: Shift→`y_mm` (CSS depth). Mode id `"z"` kept.

### N2 — Orthographic approximation remains

Inverse rotation, not CAD ray-plane unproject. Named risk.

### N3 — Re-smoke

Reload → Situar ON → orbit side/back → drag left/right on screen → solid follows cursor; drop = preview. Shift = profundidad.

### N4 — Field note

[engineer_note_situar_lateral_drag_hotfix.md](engineer_note_situar_lateral_drag_hotfix.md)

---

## Phase

Implementation **CLOSED**. Engineer smoke **ACCEPT** ([smoke](engineer_smoke_board_situar_free_camera_b1.md)). Package `0.4.0` · UI **80**.
