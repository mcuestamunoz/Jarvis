# Engineer field — Situar lateral drag blocked (2026-09-10)

**Report:** “no me deja mover lateral” with Situar ON, free camera, yellow singleton selected.

## Cause

Screen Δx was written straight to `originX` / `x_mm`. Under `rotateY` (side/back view — the free-camera ask), world X points into the scene, so a lateral screen drag barely moved the solid.

## Hotfix #2 (Cursor)

`screenDeltaToLocalPx` inverts world `rotateX`/`rotateY` before commit/preview.

- Default drag: solid follows **screen plane** (may write `x_mm`/`z_mm`/`y_mm`).
- At tilt 0: same as before (Δx→x, Δy→z, y untouched).
- Shift: only `y_mm` from local depth component.
- Hint: `arrastre: sigue el cursor (plano pantalla)`.

## Re-smoke

**ACCEPT** (Engineer 2026-09-10: “ahora sí”). See [engineer_smoke_board_situar_free_camera_b1.md](engineer_smoke_board_situar_free_camera_b1.md).
