# Implementation Report — Board drag → Continuity pose B1

**IC:** [implementation_contract_board_drag_pose_b1.md](implementation_contract_board_drag_pose_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-10
**Baseline:** package `0.4.0` · suite 2661 → **2668** (2661 + 7 new Python). UI: 47 → **64** (+17: 9 `boardPoseDrag` + 3 `pxToMm` round-trip + 5 existing).

---

## Files changed

| File | Change |
|---|---|
| `src/jarvis/workspace/board_pose_bridge.py` | **New.** `apply_drag_pose(state_path, payload)` — load → `set_component_declared_box_pose` (unchanged, CLOSED writer) → `WorkspaceManager().save_state(...)` (same SoT the CLI itself uses) → `project_spatial_nodes` reprint. `main(argv)` CLI entry mirroring `spatial_board.main`'s own shape (`python -m jarvis.workspace.board_pose_bridge <state.json> <json_payload>`). No LLM, no orchestrator. |
| `tests/test_board_pose_bridge_b1.py` | **New.** 7 tests: valid write persists (P1), self-origin/disk-origin reject with no partial save (P2 ×2), missing required fields raise, missing project file raises, CLI happy path + reject path via `main()`. |
| `ui/spatial-board/src/scene3dScale.ts` | New `pxToMm(px, pxPerMm)` — the literal inverse of `mmToPx`, documented as valid only in the untilted "situar" camera. |
| `ui/spatial-board/src/scene3dScale.test.ts` | Added round-trip tests (P3): exact values, a range of mm/scale combinations, and the default-scale case. |
| `ui/spatial-board/src/boardPoseDrag.ts` | **New.** Pure helpers: `isDraggableSolid(node)` (geometry present AND `solidCopies` absent or `< 2` — P4) and `computeDragPosePayload(...)` (screen-delta → Δmm → new pose payload; `z_mm` always carries the prior value verbatim, `null` if never set — P5). No DOM, no fetch. |
| `ui/spatial-board/src/boardPoseDrag.test.ts` | **New.** 9 tests covering P4 (eligibility at `solidCopies` 0/1/2/4) and P5 (no-prior-pose case, prior-pose-present case, undefined-zMm case, zoom un-scaling). |
| `ui/spatial-board/src/Solid3D.tsx` | Added optional `draggable`/`needsOrigin`/`onDragStart` props; `handleMouseDown` now also calls `onDragStart` (selection is unchanged, always fires). Two new CSS modifier classes wired through. |
| `ui/spatial-board/src/Scene3D.tsx` | New "Situar" toggle (locks tilt to `{rotateX:0, rotateY:0}`, disables camera-orbit while on). New per-solid drag session (`solidDragRef`) armed only for singleton solids with an already-known origin; an eligible solid with no origin opens a minimal inline picker (box-shaped candidates only) instead. On drop (`onSolidDragUp`), computes the final Δmm via `computeDragPosePayload` and POSTs once via `postDragPose` — no live-preview re-layout during the drag itself, matching the product intent's own "on drop" wording. Success calls `onPoseCommitted` (wired to a GET refetch); failure surfaces the writer's own message in a small error banner. |
| `ui/spatial-board/src/useBoardNodes.ts` | Added `refetch()` — re-runs the same GET the initial load used and re-applies the `localStorage` layout overlay, so a pose write shows up the same honest way a page reload would (no optimistic local mutation). |
| `ui/spatial-board/src/InfiniteCanvas.tsx` | Passes `projectId` and `onPoseCommitted={refetch}` down to `Scene3D`. |
| `ui/spatial-board/src/projects.ts` | New `postDragPose(projectId, payload)` — POSTs to the new route; on a non-2xx response, surfaces the server's own `{error}` message verbatim (never a generic "failed" string). |
| `ui/spatial-board/src/spatial-board.css` | New minimal styles: situar toggle button, draggable/needs-origin solid cursor/outline, origin-picker and pose-error panels. No theme system, no Three.js. |
| `ui/spatial-board/vite-plugin-jarvis-projects.ts` | Factored the existing `spawnSync` boilerplate into `runPythonBridge(moduleArgs)`; `projectNodes` now calls it. New `applyDragPose(statePath, payload)` calls the same helper against `board_pose_bridge`. New `readRequestBody(req)`. Middleware restructured: GET routes unchanged (still exactly `/api/projects` and `/api/projects/:id/nodes`); new **POST** `/api/projects/:id/pose` reads the body, JSON-parses it, calls `applyDragPose`, and responds 400 with the writer's own message on any `ValueError`, or 404 if the project id doesn't resolve. This is the ONE new mutation route on an otherwise GET-only plugin. |
| `docs/system_map/CONNECTIONS.md` | Added **C-113** (`🟢`) for the new route → bridge → writer chain. Added a dated chronology entry. Narrowed the single old absence row ("Board drag/resize → pose/envelope writers") into four precise rows: C-113 itself (now green), resize/envelope (still `NOT IMPLEMENTED`, named as the future `B1+`), multi-copy drag (still `NOT IMPLEMENTED`, structural — `isDraggableSolid` fails closed), and 2D card-px drag (still `NOT IMPLEMENTED` by design — `localStorage` overlay only). Registry count `65→66`, `64🟢→65` is reflected as `64🟢`→ updated header count (`65 unique`→`66 unique`, `63🟢`→`64🟢` in the header summary line, consistent with the existing counting convention). |

`library/`, `workspace/` — confirmed **untouched** (`git status --short` empty for both). Version still `0.4.0`.

---

## Chosen screen→mm mapping (lock #5, documented as required)

The "situar" camera is locked to `rotateX: 0, rotateY: 0` (lock #2's own exact numbers) — the world transform reduces to a pure `translate + scale(zoom)`, so a screen-px delta maps linearly to a world-px delta via `Δworld = Δscreen / zoom`, with no rotation/perspective distortion to invert. `pxToMm(Δworld)` then gives the Δmm.

**Mapping:** screen Δx adds to the prior `x_mm` (declared +X, length axis) — unambiguous, matching `layoutSolidsFromPose`'s own `pose.xMm → originX` remap exactly. Screen Δy adds to the prior `y_mm` (declared +Y, width axis) — a **deliberate, simpler** choice than following the renderer's own Y↔Z swap (which feeds `zMm` into screen-Y and `yMm` into CSS depth): inventing genuine per-frame perspective unprojection for a Z-mapped screen axis was judged out of scope for a "thin B1," and the untilted situar view has no rendered depth cue to contradict this input-side choice. `z_mm` is **never** touched by a drag — `computeDragPosePayload` always carries the prior `zMm` verbatim (`null` if it was never set), tested directly (P5).

---

## Tests added / executed

**Python** — `tests/test_board_pose_bridge_b1.py`, 7/7 passing (P1, P2 ×3, plus CLI-level coverage of both).

**TypeScript** — `scene3dScale.test.ts` (+3, P3) and `boardPoseDrag.test.ts` (+9, P4/P5), all passing. Full UI suite: `npm test` → **64 passed**, `npm run typecheck` → clean.

**Full Python suite:** `python -m pytest -q` → **2668 passed**, 0 failed (existing Continuity pose CLI tests — P6 — untouched and still green, confirmed by the unchanged pass count on those files).

---

## Live verification (end-to-end, real HTTP — never the real `workspace/`)

Copied `autonomía-de-5min` into a temp directory (with `workspace_path` patched to point at the copy, so `WorkspaceManager.save_state` could never write back to the real demo even by mistake), started the actual Vite dev server against it via `JARVIS_WORKSPACE_ROOT`, and exercised the real HTTP surface with `curl`:

- `GET /api/projects` → confirms the server reads the temp workspace.
- `POST /api/projects/4b63337fd4fd/pose` with `{component_key: "battery", origin_key: "frame_plate_2", x_mm: 42, y_mm: 7, z_mm: 13}` → 200, returned nodes show `battery.declaredBoxPose == {originKey: "frame_plate_2", xMm: 42, yMm: 7, zMm: 13}`.
- A follow-up `GET .../nodes` confirms the same value persisted (not just echoed) — and the temp `state.json` on disk carries it too.
- `POST` with `origin_key: "battery"` (self-origin) → **400**, body `{"error": "'battery' no puede ser el origen de su propia pose."}` — the writer's own message, verbatim.
- `POST` to an unknown project id → **404**.
- `git status --short -- workspace/` on the real repo — **empty**, confirming the real demo was never touched.

---

## Non-goals honored

No envelope/resize route (`B1+`, deferred). No card-px→pose wiring (2D `useNodeGestures` untouched). No drag arming for any `solidCopies >= 2` node — `isDraggableSolid` fails closed, verified directly (P4) and via the redundant `layoutId === selectId` check in `Scene3D.tsx`. No silent default origin — an unposed eligible solid always opens the picker first (verified by code inspection: `handleSolidDragStart` returns early into `setPickerNodeId` whenever `originKey` is falsy). No second pose schema — every write goes through the exact same `set_component_declared_box_pose`/`DeclaredBoxPose` the CLI already used. No LLM/orchestrator in the write path — `board_pose_bridge` is a thin, deterministic I/O shell. No Fit `"VERIFIED"` flip. No Three.js rewrite, no theming. No version bump.

---

## Remaining risks

- **Perspective foreshortening is not modeled.** `.sb-scene3d` has `perspective: 900px`; a solid whose existing (untouched) `z_mm`/depth offset is large could in principle see a slightly non-linear screen↔world relationship even at `rotateX=0`. This Buy treats the mapping as an orthographic zoom-only approximation — acceptable for typical component sizes/positions today, but worth Cursor's attention if a future Engineer smoke reports drift on a deeply-offset solid.
- **No automated integration test drives the actual HTTP route** (the Python bridge and the TS pure helpers are both fully unit-tested; the route itself was verified live, by hand, as documented above, not via an automated test in CI). Spinning up a real Vite dev server in the test suite was judged heavier than "cheap" per lock #12's own minimalism instruction; flagged here rather than silently assumed covered.
- **The origin picker is intentionally minimal** — a native `<select>` listing every box-shaped key, no search/filter, no preview of where the origin actually sits. Fine for today's small component counts; would need revisiting if a project ever has dozens of boxes.
- Envelope/resize (`B1+`) and any per-copy pose mechanism for `solidCopies >= 2` nodes remain explicitly unimplemented, as scoped.
