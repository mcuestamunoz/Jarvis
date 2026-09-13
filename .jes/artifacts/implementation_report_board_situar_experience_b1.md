# Implementation Report — Board Situar experience B1 (`B1-situar-experience`)

Status: Done — awaiting Engineer smoke (S1–S5)
Parent: `implementation_contract_board_situar_experience_b1.md`
Baseline: package `0.4.1` (unchanged) · UI `91` → `99` (8 new) · Python suite `2747` (unaffected — UI-only)

## Summary

Three experience locks (E1–E3) shipped, all UI-only, no writer/POST/pose-math
touched, no version bump, no `workspace/` mutation.

## E1 — 2D stays usable with Situar ON (Option A **and** B)

Given genuine uncertainty about whether height tuning alone is enough on
every real laptop size, both suggested approaches were implemented
together, per the IC's own "Prefer A+B if A alone still leaves cards
under the pane":

- **Option A** (`spatial-board.css`): `.sb-viewport` gained an explicit
  `min-height: 280px` (the exact number the IC itself suggested).
  `.sb-scene3d--situar`'s height dropped from `max(420px, 56vh)` to
  `max(360px, min(50vh, 560px))` — the old floor alone (420px) left the 2D
  pane under ~230px on a typical ~700px-tall laptop viewport (toolbar
  ~45px + situar pane 420px-floor); the new floor/cap combination,
  together with the viewport's own `min-height`, guarantees the 2D card
  row a documented minimum instead of being squeezed toward zero.
- **Option B** (`Scene3D.tsx`): a compact `.sb-scene3d__piece-strip` of
  chip buttons rendered inside the 3D pane itself, one per
  situar-draggable singleton box (`solids.filter(isDraggableSolid)` — the
  exact same gate the drag arm itself uses, so the strip never lists a
  copy/disk that could never be selected-to-drag anyway). Each chip calls
  the same `onSelect` the 2D card and 3D solids already use — no second
  selection model. The currently-selected piece's chip is highlighted.
  This makes piece-picking independent of whatever height the 2D pane
  ends up with on a given screen.

## E2 — click a solid → select that solid (idle only)

Root cause of "click another box under the cursor → ignored": the prior
design made **every** non-selected solid `pointer-events: none` the
instant **anything** was selected — including while fully idle. Extracted
a pure predicate, `isSolidHitThrough` (`situarInteractionState.ts`), now
gated on a `busy` flag (`Boolean(dragPreview) || posting`) instead of bare
"something is selected." Idle + Situar ON: a peer solid is fully
clickable — clicking it calls `onSelect` (and arms its own drag
immediately if it's draggable, via `Solid3D`'s existing `onMouseDown`
handler, per the IC's own "may arm drag per existing Solid3D handler").
Once a drag/preview/POST is actually live, peers go click-through exactly
as before — the ACCEPT nested-hit smoke (card `esc` → drag anywhere in
the pane moves `esc`) is unaffected, since `onBackgroundMouseDown`'s own
"drag the selected piece" fallback was never touched, and pointer-events
on peers only ever matters for a *new* mousedown, never for an
already-in-flight drag's document-level mousemove/mouseup listeners.

## E3 — stable cluster while Situar is ON

Extracted a second pure function, `resolveClusterCenter`
(`situarInteractionState.ts`): while `situar` is true, the world's
camera-center translate stays fixed at whatever it was captured to be the
moment Situar turned on (a ref, `situarFrozenClusterRef`), never
recomputed from the live layout — this supersedes and widens the prior,
narrower "freeze only during an active drag" fix, since the Engineer's
own field note was about **every** settled drop re-centering the whole
scene, not only the one currently being dragged. The ref resets to `null`
(re-capture-on-next-ON) when Situar turns off, and a new **"Recentrar
3D"** button (optional per the IC, shipped since it was cheap and gives
an explicit escape hatch) also clears it and forces a re-render. Situar
OFF always uses the live value — exactly the IC's own "recompute when
Situar turns OFF" instruction.

## Files

- `ui/spatial-board/src/situarInteractionState.ts` (new) — `isSolidHitThrough`, `resolveClusterCenter`.
- `ui/spatial-board/src/situarInteractionState.test.ts` (new) — T1–T3 plus 5 more edge cases (self-exclusion, situar-off, no-selection, frozen-vs-live, situar-off-ignores-frozen).
- `ui/spatial-board/src/Scene3D.tsx` — wired both helpers; added the piece strip; added the "Recentrar 3D" button; updated the situar hint copy to match E2's actual behavior (`"click en una caja: elegir · arrastre (fondo o caja): mueve la seleccionada · Alt+arrastre: órbita · Shift: profundidad (Y)"`).
- `ui/spatial-board/src/spatial-board.css` — `.sb-viewport` min-height; `.sb-scene3d--situar` height reduced; new `.sb-scene3d__recenter-toggle`/`.sb-scene3d__piece-strip`/`.sb-scene3d__piece-chip(--selected)` rules; `.sb-scene3d__situar-hint`'s `right` edge adjusted to clear the new recenter button.

**Not touched** (per the IC's own lock #4/§3): `board_pose_bridge.py`, any
writer, `situarOriginCandidates.ts`'s ranking tiers, the POST payload
shape, `boardPoseDrag.ts`'s pose math, `pyproject.toml` (version still
`0.4.1`), `workspace/` (confirmed via `git status --short -- workspace/`,
empty).

## Tests

- `situarInteractionState.test.ts` (new, 8 tests): T1 (hit-through false
  when idle), T2 (hit-through true when busy), self-exclusion, situar-off
  never hit-through, no-selection never hit-through, T3 (frozen center
  ignores a live bbox change), frozen-falls-back-to-live when nothing
  captured yet, situar-off always returns live regardless of a stale
  frozen value.
- Existing `situarOriginCandidates.test.ts` (8) and `boardPoseDrag.test.ts`
  (22) re-run unmodified — still green (ranking tiers and pose math both
  untouched by this Buy).
- `npm test` (full UI suite) → **99 passed** (9 files; was 91).
- `npm run typecheck` → clean.
- `python -m pytest -q` (full suite) → **2747 passed**, unaffected.

## Behavior changed

- Situar ON no longer visually starves the 2D card row (documented
  min-heights on both panes) and offers an in-pane piece strip as a
  height-independent alternative.
- Idle + Situar ON: clicking a different box in 3D selects it (previously
  ignored while anything was selected).
- The whole scene no longer re-centers on every settled drop while Situar
  is ON; a manual "Recentrar 3D" control is available if the user wants a
  fresh center.
- Situar hint copy updated to describe the actual current behavior.

## Behavior unchanged

Writers, POST pose payload shape, `isDraggableSolid` eligibility, origin
ranking tiers (mount-sibling / already-an-origin / direct-mount /
frame_plate), the ACCEPT nested-hit "drag the selected piece from
anywhere in the pane while busy" mechanism, pose composition math,
Product A racimo (no silhouette work).

## Smoke (Engineer) — S1–S5, per the IC's own table

1. **S1**: Situar ON → 2D card row and/or the new piece strip stay usable
   for selecting a piece.
2. **S2**: Idle, click box B in 3D → B selected (yellow outline); then
   drag → B moves.
3. **S3**: Nested ESC path — select `esc` (card, strip, or idle click if
   visible) → Situar ON → drag on pane background → `esc` moves.
4. **S4**: Drop a piece → no whole-racimo recenter; piece stays where
   dropped (preview-hold from the prior fix, now combined with the E3
   freeze, holds through the whole session, not just the drop's own async
   gap).
5. **S5**: Situar OFF → cluster recomputes live again on the next render.

## Non-goals honored

No silhouette/plate-L×W work, no copy-family (`motors`/`propellers`)
situar, no Three.js, no Conversation Engine, no invented millimetres, no
version bump, no writer or POST-shape change, no ranking-tier change.

## Remaining risk

- The piece strip currently shows bare component keys (`esc`, `battery`,
  ...), not a friendlier display name — matches the existing origin
  picker's own bare-key fallback convention, but a future novice-facing
  pass (already cola, `B1-novice-pack`, parked) could improve this.
- "Recentrar 3D" was shipped as a small extra since it was cheap, but was
  not explicitly requested as required — flagging in case the Engineer
  would rather it not exist yet; trivial to remove if so.
