import { solidExtentPx } from "./scene3dScale";
import type { SpatialGeometry } from "./types";

/**
 * Board 3D solids B1 — a row layout for solids, deliberately independent
 * of card layout. Never reads `node.x`/`node.y` (2D pixel layout, drag
 * state), never `mountedOn`/`parent_key` (declared relations, not spatial
 * placement) — a 3D "where does this sit relative to the others" fact
 * does not exist anywhere in the system yet (pose stays B0 DEFERRED), so
 * this is a presentation-only row, not a placement claim.
 */
export function layoutSolidsRow(
  items: { id: string; geometry: SpatialGeometry }[],
  gapPx: number,
  pxPerMm?: number,
): { id: string; originX: number }[] {
  const result: { id: string; originX: number }[] = [];
  let cursor = 0;
  for (const item of items) {
    result.push({ id: item.id, originX: cursor });
    const extent = solidExtentPx(item.geometry, pxPerMm);
    cursor += Math.max(extent.x, extent.y) + gapPx;
  }
  return result;
}
