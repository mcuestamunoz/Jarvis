/**
 * Board Situar experience B1 (`B1-situar-experience`) — pure predicates
 * extracted from `Scene3D.tsx` so the two locked behaviors (E2 nested-hit
 * scope, E3 cluster stability) are unit-testable without a DOM/render
 * harness. No DOM, no fetch, no pose math — `Scene3D.tsx` is the only
 * caller of either function.
 */

export type Point2D = { x: number; y: number };

/**
 * E2 — nested-hit refinement. The prior design (`situar && selectedId &&
 * peer !== selected`) made EVERY other solid click-through the instant
 * ANYTHING was selected — including while fully idle, which is exactly
 * the Engineer's own "click another box under the cursor → ignored"
 * complaint. `pointer-events: none` on peers is only actually load-bearing
 * WHILE a solid drag/preview/commit is in flight (so a background click
 * near a peer keeps moving the piece being dragged, per the ACCEPT
 * nested-hit smoke) — never while merely idle-selected. `busy` is the
 * same "a drag/preview/POST is live" signal `resolveClusterCenter` below
 * also gates on, so the two locks never drift onto two different
 * definitions of "busy."
 */
export function isSolidHitThrough(args: {
  situar: boolean;
  selectedId: string | null;
  solidId: string;
  busy: boolean;
}): boolean {
  return Boolean(
    args.situar && args.selectedId && args.solidId !== args.selectedId && args.busy,
  );
}

/**
 * E3 — stable cluster while Situar is ON. Recomputing the world's
 * camera-center translate from the live layout on every settled pose
 * (the pre-existing `clusterCenterPx` behavior) re-centers the ENTIRE
 * scene the instant any one piece's position changes — every untouched
 * peer visibly slides, reading as "the racimo re-centers on every drop."
 * While `situar` is true, the caller holds `frozenCenter` fixed at
 * whatever it captured when Situar turned on (or at the first settled
 * layout after that) and this function keeps returning THAT value
 * regardless of how `liveCenter` moves — never a second recompute mid
 * session. `situar === false` always returns the live value: Situar OFF
 * is exactly the signal that un-freezes recentering (locked, IC §1 E3).
 */
export function resolveClusterCenter(args: {
  situar: boolean;
  liveCenter: Point2D;
  frozenCenter: Point2D | null;
}): Point2D {
  if (!args.situar) return args.liveCenter;
  return args.frozenCenter ?? args.liveCenter;
}
