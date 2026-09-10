# Implementation Report — Board Situar free camera B1

**IC:** [implementation_contract_board_situar_free_camera_b1.md](implementation_contract_board_situar_free_camera_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-10
**Baseline:** package `0.4.0` · Python 2668 (unchanged — this cycle is `ui/`-only) · UI 70 → **74** (+4 in `boardPoseDrag.test.ts`).

---

## Files changed

| File | Change |
|---|---|
| `ui/spatial-board/src/boardPoseDrag.ts` | `computeDragPosePayload` gained an `axisMode?: "xy" \| "z"` parameter (default `"xy"`, fully backward-compatible — every existing call site and test still passes unchanged). `"z"` mode uses ONLY the vertical screen delta, writes it to `z_mm` (adding to the prior value, defaulting to 0 if none), and leaves `x_mm`/`y_mm` at their prior values verbatim — horizontal is deliberately ignored (locked choice). Module and function docstrings rewritten to document the free-camera consequence: the screen→world linear un-scale is now an accepted orthographic-style approximation at ANY tilt, not just the old forced `(0,0)`. |
| `ui/spatial-board/src/boardPoseDrag.test.ts` | Added 4 tests: U1 (default `"xy"` mode's `z_mm` behavior is unaffected by the new parameter, including an explicit-vs-omitted-default equality check) and U2 ×3 (Shift/`"z"` mode changes `z_mm` by `pxToMm(Δy/zoom)`, horizontal fully ignored even with a large Δx; starts from 0 with no prior pose; respects zoom the same way `"xy"` does). |
| `ui/spatial-board/src/scene3dScale.ts` | `pxToMm`'s doc comment updated — no longer claims validity "ONLY in the untilted situar camera"; now documents the accepted orthographic-style approximation at any tilt. |
| `ui/spatial-board/src/Scene3D.tsx` | (1) Removed `SITUAR_TILT` and `effectiveTilt` entirely — the world's `rotateX`/`rotateY` now always render from the single `tilt` state, whether or not Situar is on (lock #2). (2) `onBackgroundMouseDown`'s `if (situar) return;` early-out removed — camera orbit works identically whether Situar is on or off (lock #3); a solid's own mousedown already `stopPropagation()`s before it would ever reach this handler, so the two gestures still never collide, unchanged from before. (3) `SolidDragState` gained a `zMode: boolean` field, captured ONCE from `event.shiftKey` at drag start in `handleSolidDragStart` and never re-checked mid-gesture (a predictable, locked-for-the-whole-drag contract, not a per-frame modifier check). (4) `onSolidDragMove`'s live preview now zeroes the horizontal offset when `zMode` is true (matching what will actually be written) and carries `zMode` through the preview state. (5) `onSolidDragUp` passes `axisMode: d.zMode ? "z" : "xy"` into `computeDragPosePayload`. (6) Added a one-line hint (`"fondo: órbita · arrastre: XY · Shift+arrastre: Z"`, lock #8) shown only while Situar is on; toggle label/behavior otherwise unchanged. |
| `ui/spatial-board/src/spatial-board.css` | New `.sb-scene3d__situar-hint` rule (small, `pointer-events: none` so it never intercepts the orbit gesture underneath it). No other CSS changed — the Situar UX B1 pane-size rules (`.sb-scene3d--situar`) are untouched, since pane size is orthogonal to camera behavior. |

`board_pose_bridge.py`, `component_writers.py`, `vite-plugin-jarvis-projects.ts`, `library/`, `workspace/`, `pyproject.toml` — confirmed **untouched** by this cycle (`git status --short` shows no diff on any of them from this turn; version still `0.4.0`). Per lock #7, no bridge/HTTP change was needed — the POST payload already accepted `z_mm`.

---

## Behavior changed

- **Situar no longer touches the camera.** Turning Situar on/off never calls `setTilt` — whatever orbit angle the Engineer already had (including a view "from behind") is exactly what they keep. Verified by direct source inspection (U3): `setTilt` is called in exactly one place (`onMove`, the orbit-drag handler) and nowhere near the Situar toggle's own click handler; `SITUAR_TILT` no longer exists in the file at all.
- **Orbit and pose-drag coexist while Situar is on.** Background mousedown still starts a camera orbit exactly as when Situar is off; a solid's own mousedown still arms a pose-drag instead, via the pre-existing `stopPropagation()` in `Solid3D.tsx` (unchanged) — the Engineer can now orbit to any angle, then drag a solid, without ever leaving Situar mode.
- **Plain drag still writes X/Y** via the unchanged `"xy"` mode — now explicitly documented as an honest orthographic-style approximation valid at any tilt (previously it was only ever exercised at the forced `(0,0)` tilt; the math itself did not change, only the camera state it's now used under).
- **Shift+drag writes Z.** Holding Shift when starting a drag locks that whole gesture to the vertical axis only: the live preview moves purely vertically (horizontal ignored), and on drop the POST payload adds `pxToMm(Δy/zoom)` to the prior `z_mm` (or starts from 0), leaving `x_mm`/`y_mm` untouched. This mapping is genuinely self-consistent with the existing renderer (`layoutSolidsFromPose`'s `pose.zMm -> originY` — the ONE axis with no Y↔Z swap to fight), unlike the default `"xy"` mode's already-documented simplification.
- Eligibility (`isDraggableSolid`, `solidCopies >= 2` never arms) and the writer/HTTP path are completely unchanged.

---

## Tests added / executed

New, in `boardPoseDrag.test.ts` (4 tests): U1 confirms the new `axisMode` parameter doesn't change default `"xy"` behavior (including that an explicit `"xy"` and the omitted default produce identical output). U2 (×3) confirms `"z"` mode's math: `z_mm` changes by `pxToMm(Δy/zoom)` with horizontal fully ignored even for a deliberately large `Δx`; starts from `0` with no prior pose; respects `zoom` the same way `"xy"` does.

**U3** (no code path resets tilt when enabling Situar): verified by direct source inspection rather than a rendered-component test — the project's Vitest config runs in a `"node"` environment with no `@testing-library/react` (or equivalent) dependency, so simulating a real toggle-click-then-inspect-tilt interaction isn't supported by the current test infrastructure; adding that infrastructure for one invariant was judged disproportionate for this "UI-only, minimal" Buy, matching the IC's own offered alternative ("grep/test or Scene3D invariant"). Confirmed: `grep -n "SITUAR_TILT\|setTilt" Scene3D.tsx` shows `setTilt` used exactly once (inside `onMove`, the orbit handler) and `SITUAR_TILT` no longer exists anywhere in the file.

**U4** (full suites green): `npm test` → **74 passed** (0 failed), `npm run typecheck` → clean, `python -m pytest -q` → **2668 passed** (0 failed, unchanged from baseline — confirms zero Python drift, expected for a `ui/`-only Buy).

---

## Non-goals honored

No true perspective/ray-plane unprojection was built — the `"z"` mode's screen→mm math is the same linear un-scale as `"xy"`, just applied to the vertical axis, and both are explicitly documented as an accepted orthographic-style approximation at any tilt, never a CAD-grade unproject. No multi-copy drag change (`isDraggableSolid` untouched). No envelope/resize. No version bump. No LLM. No 2D minimap touch. `SITUAR_TILT` was not reintroduced as any kind of default, per the IC's own explicit instruction.

---

## Remaining risks

- **No automated test drives the live orbit-plus-drag interaction or the actual on-screen Shift+drag gesture** — the pure math (`axisMode` behavior) is fully unit-tested, and the "Situar never resets tilt" invariant was confirmed by direct source inspection (documented above) rather than a rendered-component test, since the current Vitest setup has no React-rendering test infrastructure. An Engineer smoke pass (orbit to a side/rear view, drag a solid in XY, Shift+drag the same solid in Z) is the way this actually gets exercised end to end, per the IC's own handoff.
- The orthographic-style approximation (already an accepted risk from the prior two Situar cycles) now applies at any tilt, not just `(0,0)` — a solid with a large existing Z offset dragged under a steep tilt could in principle show slightly more visible drift than at `(0,0)`, since `.sb-scene3d`'s real `perspective: 900px` is unaffected by this Buy. This is named, not silently assumed away, per lock #4's own instruction.
- The one-line hint is static text, not interactive help — if the three gestures (orbit / XY-drag / Shift-drag) turn out to need more explanation in practice, that's a small follow-up, not a redesign of anything built here.
