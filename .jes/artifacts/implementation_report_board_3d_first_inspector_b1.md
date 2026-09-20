# Implementation Report — Board 3D-first workshop + mount-chain inspector (`B1-board-3d-first-inspector`)

**IC:** [implementation_contract_board_3d_first_inspector_b1.md](implementation_contract_board_3d_first_inspector_b1.md)
**Implementer:** Claude Code
**Date:** 2026-09-19
**Baseline:** package `0.4.2` (unchanged, no version bump) · UI suite **132 passed** (up from 105) · `tsc --noEmit` clean · `vite build` clean

---

## Screens / behavior summary

- **Taller 3D** (new default tab): `Scene3D` renders full-bleed (`flex: 1`, `.sb-scene3d--primary` overriding the old fixed stacked-pane height) as a sibling of a new right-side `InspectorDock` (~320px, scrollable). `.sb-viewport` (the card graph) stays mounted in the DOM but `hidden` — never unmounted, so its `ResizeObserver`/pan-transform state never breaks across tab switches (see "Implementation notes" below for why this mattered).
- **Grafo** (secondary tab, one click away, never removed): identical to the pre-existing behavior — card graph primary, optional Scene3D below via the same "Mostrar 3D"/"Ocultar 3D" toggle as before, no inspector dock, no dimming.
- **Inspector dock**: on selection, shows a **summary** (title/kind/declared name + up to 5 priority fields: `montado en`, `mass_g`, `power_w`, `SKU`, `sobres`, `origen pose` — first-match-wins, never inventing a field the projector didn't already emit) with a **"Ver todo"** button expanding to the exact same full field list `SpatialCard`'s own `<dl>` already shows in Grafo. Below that, an ordered **"Cadena hasta la placa"** list — each ancestor is its own clickable row (`onSelect`), or an honest empty-state string when no chain resolves.
- **3D dimming**: every solid NOT on the selected piece's ancestor chain drops to 28% opacity (still clickable — `pointer-events` untouched); the chain itself stays full opacity. Clearing selection restores everyone. Taller-tab only (Grafo's optional 3D view is untouched, by design — see IC scope).
- **Overlap/stack picker**: the existing Situar-only piece-strip chips are now generalized (Trigger B) — always visible in the Taller tab regardless of Situar state. Situar OFF lists every solid (general inspection, including motor/propeller station copies); Situar ON keeps the pre-existing `isDraggableSolid`-filtered list (only solids the drag arm can act on). Trigger A (multi-hit ray picking on an ambiguous click) was not attempted — named debt per the IC's own §7/acceptance criterion ("strip may be enough").
- **Situar ON** (either tab): unchanged pose-drag mechanics; in Taller, the inspector dock is not rendered at all while Situar is on (the piece strip is the selection affordance instead, per lock #8) — no fat column fighting Situar.

## Ancestor helper definition

`isAssemblyRootPlate(id)` (`mountAncestorChain.ts`) reuses the **existing, already-locked** `ASSEMBLY_ROOT_CANDIDATE_ID = "frame_plate"` constant from `situarOriginCandidates.ts` (Situar's own origin-picker ranking) rather than defining a third copy — `scene3dLayout.ts` has its own private, unexported `ASSEMBLY_ROOT_ID` with the same value, so this reuses the one that was already importable.

`computeAncestorChain(selectedId, nodesById)` walks `mountedOn` exactly per the IC's own pseudocode (§2.3): starts at `[selectedId]`, at each hop breaks honestly on a missing `mountedOn`, a cycle (`seen` set), or a target that isn't a projected node, and stops (inclusive) the moment it reaches the assembly-root plate. Deliberately never reads `declaredBoxPose.originKey` (pose frame ≠ mount graph, per the IC's own lock).

**Verified against the live `dron-de-vigilancia-doméstico` project's real API response** (see "Manual verification" below) — including an honest edge case the fixtures alone wouldn't have caught: `cameras` is mounted on `frame_plate_2` (a sibling plate, not the assembly root), which itself has no further `mountedOn` — the chain correctly stops at `[cameras, frame_plate_2]` rather than inventing a path to the true root. This is exactly the "no invented connection" behavior the IC's lock requires.

## What was reused vs new

**Reused, not duplicated:**
- `ASSEMBLY_ROOT_CANDIDATE_ID` (`situarOriginCandidates.ts`) for the assembly-root check.
- `isDraggableSolid` (`boardPoseDrag.ts`) for the Situar-mode piece-strip filter.
- `SpatialCard`'s own full-fields presentation shape (`<dl>` of `{label, value}` pairs) — "Ver todo" renders the identical `node.fields` array, no new data shape.
- The existing `mountedOn`/`geometry`/`declaredBoxPose` DTO fields on `SpatialNode` — no projector (`spatial_board.py`) change was needed; the IC's own lock #11 preference ("prefer UI walk of `mountedOn` first") held.

**New:**
- `mountAncestorChain.ts` — `isAssemblyRootPlate`, `computeAncestorChain`, `isDimmed` (pure, tested).
- `inspectorSummary.ts` — `pickSummaryFields` (pure, tested).
- `overlapPicker.ts` — `pieceStripSolids` (pure, tested).
- `boardViewMode.ts` — `resolveInitialViewMode`, `viewModeStorageKey` (pure, tested).
- `InspectorDock.tsx` — the new right-dock component.
- `Scene3D`'s `situar` state lifted to a controlled prop (`situar`/`onSituarChange`) so the parent (`InfiniteCanvas`) can decide whether to render the inspector dock; new `primary` prop switches full-bleed styling + the general (non-Situar) piece strip + dimming on.
- `Solid3D`'s new `dimmed` prop → `.sb-solid--dimmed` (opacity only, never touches hit-testing).
- `InfiniteCanvas.tsx`: view-mode tabs, the Taller layout block, `.sb-viewport`'s `hidden` attribute (see implementation note below).

## Situar interaction proof

Situar's own mechanics (drag math, screen→local inverse, origin picker, cluster-freeze, fit attestation) are **byte-for-byte unchanged** — the only edit inside `Scene3D.tsx`'s Situar-specific logic was swapping the local `useState`'s setter for the lifted `onSituarChange` prop callback at the toggle button's `onClick` (same E3 frozen-cluster-reset logic, same shape). All 22 existing `boardPoseDrag.test.ts` cases plus all 8 `situarInteractionState.test.ts` and 8 `situarOriginCandidates.test.ts` cases still pass unmodified. Verified live against the real project API (below): Situar's piece-strip filter (`pieceStripSolids(solids, true)`) correctly drops the 3 station-copy nodes (`motors`, `propellers`, `frame_arm`, all `solidCopies: 4`) from the vigilancia project's 9 solids, leaving exactly the 6 draggable singletons — matching pre-existing behavior exactly.

## Manual verification (and its limits — read this)

**Could not get a real screenshot.** This sandboxed environment has no Chrome/Chromium binary, Node is 18.17.0 (Playwright requires Node ≥ 20), there is no `chromium-cli`, and the `claude-in-chrome` MCP connector is not connected in this session. I did not fabricate or guess what a screenshot would show.

**What I verified instead, in order of strength:**
1. `tsc --noEmit` clean, `vite build` clean (56 modules, no errors).
2. Full automated suite: 132/132 passed (105 pre-existing + 27 new, all pre-existing tests unchanged and still green).
3. **Live server smoke**: started the real `jarvis board` dev server (`npm run dev`, port 5173), confirmed the HTML shell serves, every changed/new `.tsx` module transforms with HTTP 200 (no Vite compile errors), and the real `/api/projects` + `/api/projects/:id/nodes` endpoints return real data for `dron-de-vigilancia-doméstico`.
4. **Live logic proof**: fetched that project's real node payload and ran the actual `computeAncestorChain`/`pickSummaryFields`/`isDimmed`/`pieceStripSolids` functions against it (not synthetic fixtures) — results included in the section above (honest chain-stop on `cameras`→`frame_plate_2`, correct multi-hop `propellers→motors→frame_arm`, correct empty chain for `vtx`, correct 9-vs-6 Situar strip filtering).

This proves the logic and the wiring are correct and that nothing crashes at runtime, but it does **not** prove the CSS actually looks right, that click targets land where expected, or that the layout doesn't visually break at some viewport size — those need an actual rendered screenshot, which I could not produce here. Flagging this explicitly per my own instructions ("if you can't test the UI, say so explicitly rather than claiming success") rather than reporting unconditional success. Recommend either an Engineer smoke pass (IC §6) with real eyes on the screen, or running `/run-skill-generator` once a suitable browser/Node setup exists here, so future UI Buys in this repo don't hit the same wall.

## Tests run + counts

New: `mountAncestorChain.test.ts` (13), `inspectorSummary.test.ts` (4), `overlapPicker.test.ts` (4), `boardViewMode.test.ts` (6) — 27 new tests, all pure-logic (no component-rendering tests — this repo has never used React Testing Library/jsdom; `vitest.config.ts`'s `environment: "node"` and every existing test file confirm this is a deliberate, established convention, not an oversight. T1/T2 (default tab, tab switching) are covered at the pure-logic level via `resolveInitialViewMode`; the actual `<button onClick>` wiring in `InfiniteCanvas.tsx` is exercised the same way every other existing interaction in that file already is — by the live-server smoke above, not a unit test).

Full suite: **132 passed** (`npm test -- --run`), 13 test files, 0 failures.

## Residual notes

- **Hit-test**: CSS 3D (`.sb-scene3d` has `perspective: 900px`, no native z-order hit-list query) makes true multi-hit picking on an ambiguous click impractical without a real raycaster — Trigger A is intentionally not implemented, per the IC's own "strip may be enough" acceptance criterion. Trigger B (always-on strip) is implemented and verified against real stacked data (esc/battery/flight_controller/sensors all mount to `frame_plate` in the live project — exactly the "hard to click, stacked" case the picker exists for).
- **CSS dimming**: implemented as a flat opacity (0.28) on the solid's own faces, not a material/lighting change — matches the IC's own "keep simple, no new physics" instruction.
- **`.sb-viewport` stays mounted, never unmounted, across tab switches** — this was a real bug I caught and avoided before shipping, not a hypothetical: `InfiniteCanvas.tsx`'s `ResizeObserver` is set up in a `useEffect(() => {...}, [])` (empty deps, runs once at the component's own mount) that reads `boardRef.current`. Since Taller is the default view, `.sb-viewport` would never have been in the DOM at that initial mount if I had conditionally rendered it — the observer would have silently never attached, permanently breaking `viewport` sizing (and therefore `Minimap`/`fit`) for the whole session, even after switching to Grafo later. Using the `hidden` attribute instead of conditional rendering keeps the DOM node (and the ref) stable across tab switches.
- **`situar` is one shared state across both tabs** (a deliberate choice, not named debt) — toggling Situar in Taller and then switching to Grafo shows Grafo's own Scene3D already in Situar mode. This reads as more consistent (Situar is a property of "the 3D pane," not of "which tab wraps it") than two independent toggles would.

## Explicit confirmations (IC §3/§9)

- No new Continuity writers, no catalog bind from cards, no invented mounts/poses — pose still writes exclusively through the existing C-113 `postDragPose` call, untouched.
- Pin/compare **not** shipped — single `selectedId`, unchanged.
- Grafo **not** removed — one click away, default-preserved behavior.
- No version bump.
- No Attack-board templates/task cards.
