# Implementation Report — Board Click-inspect B1− (2D Selection)

**IC:** [implementation_contract_geometry_board_click_inspect_b1minus.md](implementation_contract_geometry_board_click_inspect_b1minus.md)  
**Review:** [implementation_review_geometry_board_click_inspect_b1minus.md](implementation_review_geometry_board_click_inspect_b1minus.md) — PASS WITH NOTES
**Implementer:** Claude Code
**Date:** 2026-09-08
**Baseline:** package `0.3.8` · suite 2429

---

## Files changed

- `ui/spatial-board/src/boardSelection.ts` (**new**) — pure, React-free selection-transition logic exactly per §3.1: `nextSelectedId(current, action)` (`select` replaces unconditionally including the same-id case, `clear` returns `null`; the `current` parameter is unused by either branch — kept in the signature per the IC's own reducer-style shape, renamed to `_current` only to satisfy this project's `noUnusedParameters: true` tsconfig, a cosmetic identifier change with zero effect on callers since TS parameters are positional) and `reconcileSelection(selectedId, nodeIds)` (drops a selection whose id is no longer among the live nodes).
- `ui/spatial-board/src/boardSelection.test.ts` (**new**) — U1–U8, verbatim per §4.
- `ui/spatial-board/src/InfiniteCanvas.tsx` — **§3.2**: added `selectedId` state and a memoized `onSelect` routed through `nextSelectedId`; three new effects — Escape-clears (skipped when focus is inside the toolbar's `<select>`, so closing the project dropdown doesn't also wipe the board selection), project-switch-clears (`[projectId]` dependency), and post-fetch reconcile (`[nodes]` dependency, via `reconcileSelection`); `onPanStart` now also clears selection, but **only** on the same branch that already represents a genuine empty-viewport interaction (`shouldIgnorePan(event.target)` false — cards/handles/buttons/minimap/toolbar/select are all already excluded there, unchanged). `SpatialCard` now receives `selected={node.id === selectedId}` and `onSelect`. Toolbar hint string gained `· click: seleccionar`, appended, not replacing the existing zoom/pan/mover/tamaño copy.
- `ui/spatial-board/src/SpatialCard.tsx` — **§3.3**: new `selected`/`onSelect` props. `<article>` gains `sb-card--selected` in its className and `aria-current="true"` (omitted, not `"false"`, when not selected — matches the lock's "omit/false" wording via `undefined`) when selected. Header's `onMouseDown` now calls `onSelect(node.id)` then `startDrag(e)` in that order, in the same handler — selecting and dragging are not competing gestures, both simply run. Body (`sb-card__body`) gained `onMouseDown={() => onSelect(node.id)}` only — no drag start from the body, matching today's existing behavior (the body never had a drag handler before this IC either). Resize handles are **untouched** — still only `onMouseDown={(e) => startResize(e, h)}`, confirmed they never call `onSelect`.
- `ui/spatial-board/src/spatial-board.css` — **§3.4**: new `.sb-card--selected` rule using `outline: 2px solid #5b9dd9; outline-offset: 1px` — outline (not border/box-shadow-with-layout-effect) specifically because it never changes the box model, so no layout shift and no interference with the existing fixed `border: 1px solid #3a3a3a` on `.sb-card`. No z-index change.

## Behavior changed

- Clicking a card's header or body now highlights it with a visible outline; clicking a different card moves the highlight (single selection, no toggle-off on re-clicking the same card — confirmed by U3). Clicking empty canvas background, pressing Escape (outside the project `<select>`), switching projects, or the selected node disappearing from a fresh projector read all clear the highlight.
- **Nothing else changed about what a card shows** — `fields`, `geometry`/glyph, and the `"montado en"` text remain unconditionally rendered exactly as before this IC; selection is a highlight over an already-fully-open card, never a reveal, matching the locked honest sentence ("la card correspondiente se destaca," not "abre la card").
- Drag and resize gestures are unaffected: dragging a card still works exactly as before (confirmed — the header's existing `startDrag` still runs, now just preceded by a synchronous `onSelect` call in the same event handler, which has no effect on the drag state machine in `useNodeGestures.ts`, untouched by this IC). Resizing likewise unaffected — the handles never touch selection.
- Selection is never written to `localStorage`, the URL, or `ProjectState` — confirmed: `useBoardNodes.ts` (the only file that reads/writes the `localStorage` layout overlay) was not touched, and `selectedId` lives only in `InfiniteCanvas`'s own `useState`, never passed to `preview`/`commit`/`fetchProjectNodes`, all of which are unmodified.
- No Python file, DTO shape, writer, Continuity module, or catalog seed was touched — confirmed via `git status --short -- src/ tests/ library/`, empty for this cycle.

## Tests

**UI:** `cd ui/spatial-board && npm test` → **15 passed** (8 new `boardSelection.test.ts` + 3 pre-existing `mountEdgeGeometry.test.ts` + 4 pre-existing `transform.test.ts`, all green, zero regressions). `npm run typecheck` → clean (one `noUnusedParameters` error surfaced and fixed during implementation — see "Fix made during implementation" below). `npm run build` (extra smoke, not IC-required) → succeeds, 43 modules, no errors.

**Python:** `python -m pytest -q` → **2429 passed**, exactly unchanged from baseline, as locked (§4: "Python: none... Suite count stays 2429"). No `tests/test_*click*` file was added, per the explicit instruction not to.

## Fix made during implementation (worth flagging)

`nextSelectedId`'s first parameter (`current`, per the IC's own exact signature) is genuinely unused by either branch of the function body — `select` returns `action.id` unconditionally and `clear` returns `null` unconditionally, so neither outcome depends on the current value. This tripped `noUnusedParameters: true` in `ui/spatial-board/tsconfig.json`. Fixed by renaming the parameter to `_current` (a purely cosmetic identifier change — TypeScript/JavaScript parameters are positional, so this has zero effect on any caller, including `InfiniteCanvas.tsx`'s own `nextSelectedId(cur, {...})` calls) rather than changing the function's logic or signature shape, which the IC locks exactly. Documented in the function's own docstring so a future reader isn't confused about why the parameter exists but is prefixed.

## Non-goals honored

No 3D, no CSS 3D transforms, no Three.js/r3f/canvas/WebGL, no second Board view — confirmed via `git status --short`, only the five files listed above changed. `_geometry_from_spec`, the `geometry` DTO shape, and the glyph scale constant (`GLYPH.pxPerMm`/`maxPx`, still `0.5`/`120`) are untouched — confirmed via diff, zero changes to `spatial_board.py`, `SpatialGlyph.tsx`, or `constants.ts`. No motor cylinder, no invented disk height. No Python projector, writer, Continuity, or catalog file touched. Selection is never treated as pose or `"cabe"` — it carries no spatial/physical meaning at all, purely a UI highlight. No `scrollIntoView`/auto-pan was added — confirmed, the selected card is highlighted wherever it already is on screen, never moved to. No multi-select — `selectedId` is a single `string | null`, never a set/array. No persistence anywhere. No package version bump (`pyproject.toml` still `0.3.8`). No test weakened — both new UI test files are additive; the two pre-existing UI test files were re-run unmodified and still pass in full; the Python suite is untouched at exactly its baseline count.

## Remaining risk / notes for review

- Per the IC's own §6 done-criteria, an **Engineer Board smoke** (click ESC / motors / fondo / Escape, in the real browser) is still the recommended acceptance step before closing this item — this report covers code/tests/types/build only, the same discipline every prior visor-facing IC in this project has followed.
- The Escape-vs-`<select>` guard checks `event.target.closest("select")` — this covers the toolbar's native `<select>` element (`ProjectSwitcher`, confirmed by reading `shouldIgnorePan`'s own identical `.closest("select")` check used for the pan-ignore list, so this reuses an already-established DOM-targeting convention in this file rather than inventing a new one).
