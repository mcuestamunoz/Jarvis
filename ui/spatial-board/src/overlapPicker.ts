/**
 * Board 3D-first workshop + mount-chain inspector B1
 * (`B1-board-3d-first-inspector`) — overlap/stack picker (IC §2.5).
 * Trigger B (an always-available piece strip) is the one this Buy
 * implements robustly; Trigger A (multi-hit ray picking on an ambiguous
 * click) is explicitly named debt (IC §7) — CSS 3D hit-testing does not
 * reliably expose a full z-order hit list here, and the IC's own
 * acceptance criterion says the strip alone is sufficient for PASS.
 *
 * Situar ON keeps the narrower `isDraggableSolid` filter (only solids the
 * drag arm can actually act on — listing a non-draggable station copy
 * there would look selectable but do nothing once the background-drag
 * flow tries to arm it). Situar OFF (general Taller-mode inspection)
 * lists every solid, including motor/propeller copies, since inspection
 * never needs drag eligibility — it only needs a stable id to select.
 */
import { isDraggableSolid, type DraggableNode } from "./boardPoseDrag";

export function pieceStripSolids<T extends DraggableNode>(
  solids: readonly T[],
  situar: boolean,
): T[] {
  return situar ? solids.filter(isDraggableSolid) : [...solids];
}
