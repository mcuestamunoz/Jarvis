# Implementation Report — Board Situar multi-box UX B1

**Date:** 2026-09-12  
**IC:** [implementation_contract_board_situar_multibox_ux_b1.md](implementation_contract_board_situar_multibox_ux_b1.md)  
**Implementer:** Cursor (Engineer ★ procede same session)  
**Checkpoint:** package **`0.4.1`** (unchanged) · UI tests **87** (was 83)

## What shipped

| Lock | Delivery |
|---|---|
| Nested-hit kept | Unchanged `pointerEventsNone` + pane → selected drag |
| Hint | `Scene3D.tsx` situar hint: arrastre mueve la **seleccionada**; otras passthrough; Alt órbita; Shift Y |
| Dim peers | `.sb-solid--hit-through` faces `opacity: 0.35` + dashed border |
| Origin ranking | New `situarOriginCandidates.ts` — preferred `mountedOn` (box) + `frame_plate` (box) first; **full** other-box fallback; never silent default |
| Labels | `battery (montado en)` / `frame_plate (placa raíz)` / bare key |
| Cola | [engineer_note_board_situar_work_cola.md](engineer_note_board_situar_work_cola.md) |

## Files

- `ui/spatial-board/src/situarOriginCandidates.ts` (+ `.test.ts`)
- `ui/spatial-board/src/Scene3D.tsx`
- `ui/spatial-board/src/spatial-board.css`
- `.jes/artifacts/implementation_contract_board_situar_multibox_ux_b1.md`
- `.jes/artifacts/engineer_note_board_situar_work_cola.md`
- `docs/IMPLEMENTATION_TASKS.md` PRIORIDAD

## Tests

| ID | Result |
|---|---|
| T1–T3 + label | **Pass** (`situarOriginCandidates.test.ts`) |
| T4–T5 full UI suite | **Pass** — 8 files · **87** tests |

No Python suite change (UI-only). No `workspace/` writes. No version bump.

## Behavior changed

- Situar ON + selection: non-selected solids look dimmed/passthrough (still click-through).
- Hint copy clarifies selected-piece drag.
- Origin `<select>` ranked/labeled; empty mounts still list all other boxes.

## Behavior unchanged

Writers, POST pose, `isDraggableSolid`, cluster recenter, pose-chain composition, Product A racimo.

## Smoke (Engineer)

1. Reload Board on a project with ≥2 box solids (15min OK; ignore wild Δmm as golden).  
2. Situar ON → select card A → peers dim.  
3. Drag near B → **A** moves. Alt+drag → orbit.  
4. Clear pose / pick origin on a solid without origin → preferred labels if `montado en` / placa raíz boxed; else full list.  
5. Never auto-fills origin without “Fijar origen”.

## Residual / cola

See [engineer_note_board_situar_work_cola.md](engineer_note_board_situar_work_cola.md). `B1-origin-assist` likely **B0** after this Option A ranking unless Engineer wants 3D mount edges.

---

## Fix (2026-09-12, same Buy) — Claude Code, after Engineer smoke found the ranking inert

**Implementer:** Claude Code (per review N1's own "Cursor stops at IC + cola docs; Claude implements" going forward)
**Checkpoint:** package **`0.4.1`** (unchanged) · UI tests **91** (was 87)

### What was wrong

The Engineer's live smoke reported the ranking/labels produced nothing
visible. Root-caused with hard evidence, not guesswork: a throwaway vitest
run of the actual shipped `rankBoxOriginCandidates` against the **real**
`autonomía-de-5min` project data showed every returned candidate with an
**empty label** on every subject tried. Cause: the original two "preferred"
tiers both required a `mounted_on` **target**, or `frame_plate` itself, to
carry box geometry — but on every real project, `mounted_on` always points
at a frame part (`frame_plate`/`frame_plate_2`/`frame`), and frame parts
never carry box geometry (the still-open plate L×W citation gap). Verified
this is true on `autonomía-de-5min`, `autonomía-de-10min`, and
`autonomía-15min` — zero exceptions. The feature was correct against its
own synthetic unit-test fixtures (which invented a scenario — a box
mounted directly on another box — that does not occur anywhere in this
codebase's real data) and dead on arrival against real data.

### Fix — Engineer-directed (Option 1 + Option 2, in that priority order)

Two new preferred tiers added to `rankBoxOriginCandidates`
(`situarOriginCandidates.ts`), inserted between the original two (which
stay, dormant, for whenever a boxed mount target or a boxed `frame_plate`
eventually exists):

1. **Tier 2 — "mount-siblings"**: another box declared `mounted_on` the
   SAME target as the subject (e.g. `esc` and `flight_controller` both
   `mounted_on: "frame_plate"` on `autonomía-de-5min`) → labeled `"mismo
   montaje"`. Fires whenever `mounted_on` is declared at all, even though
   the shared target itself is never a box.
2. **Tier 3 — "already an origin"**: a box already used as ANOTHER
   sibling's `declared_box_pose.origin_key` → labeled `"origen de otra
   pieza"`. Fires even with **zero** `mounted_on` data anywhere — the one
   tier proven to work on `autonomía-15min`, which declares no `mounted_on`
   relation at all but does have a real pose chain
   (`esc`→`battery`→`flight_controller`).

Tier priority (most-specific first): direct-mount-as-box (original tier 1,
rarely fires) → mount-sibling (new) → already-an-origin (new) →
`frame_plate`-if-boxed (original tier 4) → full unranked fallback (never
dropped). A candidate already claimed by an earlier tier keeps that tier's
label — verified by a dedicated priority test (T6). No millimetre or plate
footprint was invented anywhere in this fix — both new tiers read data the
project already declares.

**Verified against BOTH live projects post-fix** (same throwaway-script
method used to find the bug, this time proving the fix): `autonomía-de-5min`
now shows `flight_controller (mismo montaje)` / `esc (mismo montaje)` for
each other's pickers and `flight_controller (origen de otra pieza)` for
`battery`/`sensors`; `autonomía-15min` (zero `mounted_on` anywhere) now
shows `battery (origen de otra pieza)` / `flight_controller (origen de
otra pieza)` — real, non-empty, meaningful preferred entries on both, where
before there were none on either.

### Second fix, same Buy (Engineer-approved as "thin enough") — the drop-settle jump

Separately, the Engineer asked to also address the drag-drop visual jump
if it fit in scope. Two related, genuinely thin causes, both in
`Scene3D.tsx`, neither touching the writer/POST/pose math:

- **Preview cleared too early.** `onSolidDragUp` used to call
  `setDragPreview(null)` immediately on mouseup, before the POST even
  started. Since the rendered origin comes from the (still-stale) `nodes`
  prop until the parent's refetch completes, this made the just-dropped
  solid visibly **snap back** to its pre-drag position for the whole
  POST+refetch round trip, then **jump again** once fresh data arrived —
  independently of anything else, this alone reads as "it jumped away."
  Fixed by holding the preview open (still rendering the solid exactly
  where it was dropped) until a new `useEffect` on the `nodes` prop
  confirms the parent's refetch actually landed; cleared immediately on
  abort (no real drag) or POST failure (nothing will ever commit).
- **Cluster recenter at the same instant.** `clusterCenterPx` recomputes
  the world's camera-center translate from every solid's current layout
  position, every render. The one moment new `nodes` finally arrive and
  the moved solid's real layout position updates, the overall bounding box
  changes and the ENTIRE scene re-centers — every OTHER, untouched solid
  visibly slides on screen. Fixed by freezing the cluster center to its
  last settled value (a ref) for as long as a preview is pending OR a POST
  is in flight, recomputing fresh only once both clear.

Both fixes are pure UI-render-timing changes — no writer, no POST payload
shape, no pose math, no test file needed beyond the existing
`situarOriginCandidates` coverage (no dedicated Scene3D component-render
test exists in this codebase to extend; `npm run typecheck` + the full
`npm test` suite are the verification available for this file).

### Files (fix)

- `ui/spatial-board/src/situarOriginCandidates.ts` — tiers 2/3 added.
- `ui/spatial-board/src/situarOriginCandidates.test.ts` — T4 (5min-shaped
  mount-sibling), T5 (15min-shaped already-an-origin), T6 (tier priority),
  T7 (still never invents with zero data). T1–T3 unchanged, still green.
- `ui/spatial-board/src/Scene3D.tsx` — preview-hold `useEffect` + frozen
  `lastClusterRef`. No writer/bridge/CSS change.

### Tests (fix)

- `npx vitest run src/situarOriginCandidates.test.ts` → **8 passed** (4
  original + 4 new).
- `npm test` (full UI suite) → **91 passed** (8 files; was 87).
- `npm run typecheck` → clean.
- `python -m pytest -q` (full suite) → **2747 passed**, unaffected
  (UI-only change).
- Manual verification against the real, live `autonomía-de-5min` and
  `autonomía-15min` project data (read-only — no `workspace/` write) via a
  throwaway vitest file, both before (proving the bug) and after (proving
  the fix), per this file's own "What was wrong" / "Fix" sections above.

### Non-goals honored (fix)

No plate/arm L×W invented. No writer/POST/pose-math change. No version
bump (`0.4.1` unchanged). No silhouette, copy-situar, or novice-pack work
folded in. No new architectural subsystem — both fixes are corrections to
data the feature already declares (mounted_on siblings, existing pose
origins) or to render-timing within the already-shipped component, never
a second source of truth.

### Remaining risk (fix)

- The cluster freeze holds the LAST rendered center, not a
  recomputed-from-final-truth center, for the duration of the async gap —
  if the drop is aborted server-side in a way that changes the layout
  drastically (e.g. the origin picker path, which resets to a fresh pose
  of `{0,0,null}`), the eventual unfreeze could still show a one-time
  shift; this is strictly smaller than before (no shift during the
  hold-open window itself) and was not separately smoke-tested — worth
  an explicit Engineer check during the next smoke pass.
