# Implementation Report — Board Situar UX (viewport + fluid drag) B1

**IC:** [implementation_contract_board_situar_ux_b1.md](implementation_contract_board_situar_ux_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-10
**Baseline:** package `0.4.0` · suite 2668 (unchanged — this cycle is `ui/`-only). UI: 64 → **70** (+6: 3 `clampZoom` + 3 `computeDragPreviewOffsetPx`).

---

## Files changed

| File | Change |
|---|---|
| `ui/spatial-board/src/scene3dScale.ts` | New `ZOOM_MIN = 0.25`, `ZOOM_MAX = 4` (widened from the old local `0.5`/`2` constants), and `clampZoom(zoom, min?, max?)` — a pure, exported clamp so the bounds are unit-testable without rendering React. |
| `ui/spatial-board/src/scene3dScale.test.ts` | Added `describe("clampZoom")` — U1: asserts the widened bounds directly, and that values above the old max (2) / below the old min (0.5) are now allowed. |
| `ui/spatial-board/src/boardPoseDrag.ts` | New `computeDragPreviewOffsetPx({deltaScreenPxX, deltaScreenPxY, zoom})` — the live-drag preview offset in world px (same space `originX`/`originY` render in), using the EXACT SAME `deltaScreenPx / zoom` un-scale step `computeDragPosePayload` already performs internally before its own `pxToMm` call. No mm conversion happens here — the preview is a pure visual "follow the pointer" effect, never persisted. |
| `ui/spatial-board/src/boardPoseDrag.test.ts` | Added `describe("computeDragPreviewOffsetPx")` — U2: asserts `pxToMm(preview.dxPx/dyPx)` equals `computeDragPosePayload(...).x_mm/y_mm` for the identical delta/zoom inputs (the "matches commit payload math" requirement), plus a zoom-unscaling check and a zero-delta check. |
| `ui/spatial-board/src/Scene3D.tsx` | (1) `onWheel` now calls the shared `clampZoom` instead of a local inline `Math.min/max`. (2) New `dragPreview` state + `zoomRef` (mirrors the existing `nodeRef`-style "ref tracks latest state" pattern from `useNodeGestures.ts`, so a mid-drag wheel-zoom is always read fresh inside the `document`-level mousemove/mouseup listeners, never a stale closure value). (3) `onSolidDragMove` now also computes a live preview offset via `computeDragPreviewOffsetPx` and stores it in state — the dragged solid's rendered `originX`/`originY` gets nudged by that offset every frame; `onSolidDragUp` still computes the FINAL Δmm from start→last and POSTs exactly once, clearing the preview unconditionally (success or failure) so a rejected write never leaves a stale "looks moved but isn't saved" solid. (4) Root `<div>` gets the `sb-scene3d--situar` class while situar is on, for the larger pane. |
| `ui/spatial-board/src/spatial-board.css` | `.sb-scene3d`'s height changed from a fixed `260px` to `max(420px, min(50vh, 640px))` (always ≥420px, capped at 640px on tall viewports). New `.sb-scene3d--situar { height: max(420px, 56vh); }` for the expanded situar pane. |

`board_pose_bridge.py`, `component_writers.py`, `library/`, `workspace/`, `pyproject.toml` — confirmed **untouched** by this cycle (`git status --short` shows no diff on the Python writer/bridge; version still `0.4.0`). No 2D minimap change was made — out of scope per lock #6, and the primary ask (Scene3D) needed no minimap touch at all.

---

## Behavior changed

- **Pane size**: default Scene3D height is now `max(420px, min(50vh, 640px))` — always at least 420px, scaling with the viewport up to a 640px cap. With Situar ON, the pane expands further to `max(420px, 56vh)`.
- **Zoom range**: widened from `0.5–2` to `0.25–4` (via the new shared `clampZoom`, replacing the old inline clamp). The drag math itself (`computeDragPosePayload`/`computeDragPreviewOffsetPx`) already read the live `zoom` value — no change was needed there, exactly as the IC anticipated.
- **Fluid drag preview**: while situar-dragging an eligible singleton, the solid now visually follows the pointer in real time (mirroring the 2D card's own `preview`/`commit` split in `useBoardNodes.ts`). The live preview is a pure rendering nudge (`originX`/`originY` offset by world-px deltas) — it is **never** written anywhere; on mouseup, the existing single `postDragPose` call still fires with the final accumulated Δmm, and the preview is cleared regardless of whether the POST succeeds, so a rejected write never leaves the solid stranded at a wrong-looking spot (the next render falls back to the last-committed `originX`/`originY`).
- **No mid-drag POST storm**: `onSolidDragMove` only ever updates local React state (`setDragPreview`) — the network call still happens exactly once, in `onSolidDragUp`, exactly as before this Buy.
- Axes/eligibility (X/Y only, Z untouched, `solidCopies >= 2` never arms) are completely unchanged — no code in `isDraggableSolid`/`computeDragPosePayload`/the writer/bridge was touched.

---

## Tests added / executed

New, in `scene3dScale.test.ts` (U1, 3 tests): `ZOOM_MIN`/`ZOOM_MAX` values asserted directly; a value above the old max (3) and a value below the old min (0.3) both pass through `clampZoom` unclamped; an explicit min/max override still works.

New, in `boardPoseDrag.test.ts` (U2, 3 tests): the preview offset (converted back to mm via `pxToMm`) exactly matches `computeDragPosePayload`'s own `x_mm`/`y_mm` for identical delta/zoom inputs; the zoom-unscaling step is verified directly; a zero delta yields a zero offset.

**U3** (existing `boardPoseDrag`/`pxToMm`/bridge tests still green): confirmed — `boardPoseDrag.test.ts`'s pre-existing 9 tests and `scene3dScale.test.ts`'s pre-existing `mmToPx`/`pxToMm` tests are untouched and still pass; the full Python bridge suite (`test_board_pose_bridge_b1.py`, 7 tests) is unaffected since no Python file changed this cycle.

**U4** (full suites green): `npm test` → **70 passed** (0 failed), `npm run typecheck` → clean, `python -m pytest -q` → **2668 passed** (0 failed, unchanged from baseline — confirms zero Python drift).

---

## Non-goals honored

No new writer, no writer/bridge code change (`board_pose_bridge.py`/`component_writers.py` both confirmed untouched via `git status`). No card-px→pose wiring (2D canvas untouched). No multi-copy drag — `isDraggableSolid`'s `solidCopies >= 2` gate is unchanged and still enforced identically for both the real drag and the new preview (the preview only ever activates for the same `draggable` nodes the commit path already restricted to). No envelope/resize. No Three.js, no theme system — pure CSS + existing React state patterns. No LLM. No version bump. 2D minimap untouched (out of scope, and the Scene3D-only changes needed no minimap edit to satisfy the primary ask).

---

## Remaining risks

- **No automated visual/browser test drives the pane-size or live-preview rendering itself.** All the underlying math (zoom clamp bounds, preview-vs-commit consistency) is unit-tested and typechecked; the actual on-screen pane height and the smoothness of the live drag were verified by code/CSS inspection, not a rendered screenshot or a Playwright-style E2E run — spinning one up was judged heavier than "cheap" for this thin UX Buy, consistent with the same call made in the parent `board_drag_pose_b1` report for the HTTP route itself.
- **No optional resize handle was implemented.** Lock #2 named a bottom-edge resize handle (persisting height in `sessionStorage`) as explicitly *optional*; given the primary ask was pane size + zoom + fluid drag, and per the IC's own minimalism instruction ("prefer extending existing helpers" / UI-only), this was deliberately skipped to keep the diff small. A future Buy can add it without touching anything built here.
- Perspective foreshortening (noted as a risk in the parent `board_drag_pose_b1` report) is unaffected by this cycle — the live preview uses the identical un-scale step the commit path already used, so it inherits, but does not worsen, that existing approximation.
