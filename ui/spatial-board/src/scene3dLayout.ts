import { mmToPx, solidExtentPx, solidWrapperPx } from "./scene3dScale";
import type { SpatialGeometry } from "./types";

/**
 * Board 3D solids B1 — a row layout for solids, deliberately independent
 * of card layout. Never reads `node.x`/`node.y` (2D pixel layout, drag
 * state), never `mountedOn`/`parent_key` (declared relations, not spatial
 * placement). Still used as the base "everyone gets a slot" fallback by
 * `layoutSolidsFromPose` below — this function itself still does not read
 * `declaredBoxPose` at all (N5: unposed items, and every item's OWN slot
 * before pose correction, always come from here).
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

export type SolidLayout = { id: string; originX: number; originY: number; originZ: number };

/**
 * Scene3D-from-pose B1 — the placement algorithm. Every item first gets a
 * row slot via the unchanged `layoutSolidsRow` above (so an item with a
 * broken/missing pose still renders, never vanishes). An item whose
 * `declaredBoxPose.originKey` resolves to another BOX-shaped item in the
 * same list is then repositioned to a center-to-center offset from that
 * origin's own row slot — single-level only, never recursing into the
 * origin's own pose (no chain composition; see the parent IC's own
 * cycle-detection-gap finding for why).
 *
 * Axis remap (locked, derived from Solid3D's existing, already-shipped
 * face geometry): declared +X -> CSS X (`originX`, aligned), declared +Z
 * -> CSS Y (`originY`), declared +Y -> CSS Z/depth (`originZ`) — Y and Z
 * swap relative to the declared schema order.
 *
 * Center correction: `.sb-solid` wrappers are anchored top-left, not
 * centered, on both their X and Y (CSS height) axes, so those two axes
 * need a `+/- wrapperExtent/2` correction; the CSS Z/depth axis is already
 * symmetric about 0 in the existing face code, so `originZ` needs no such
 * correction.
 */
export function layoutSolidsFromPose(
  items: {
    id: string;
    geometry: SpatialGeometry;
    declaredBoxPose?: { originKey: string; xMm?: number; yMm?: number; zMm?: number };
  }[],
  gapPx: number,
  pxPerMm?: number,
): SolidLayout[] {
  const slots = layoutSolidsRow(
    items.map((item) => ({ id: item.id, geometry: item.geometry })),
    gapPx,
    pxPerMm,
  );
  const slotXById = new Map(slots.map((slot) => [slot.id, slot.originX]));
  const itemById = new Map(items.map((item) => [item.id, item]));

  return items.map((item) => {
    const slotX = slotXById.get(item.id) ?? 0;
    const pose = item.declaredBoxPose;
    const origin = pose ? itemById.get(pose.originKey) : undefined;

    if (!pose || !origin || origin.geometry.shape !== "box") {
      return { id: item.id, originX: slotX, originY: 0, originZ: 0 };
    }

    const originSlotX = slotXById.get(pose.originKey) ?? 0;
    const originWrap = solidWrapperPx(origin.geometry, pxPerMm);
    const childWrap = solidWrapperPx(item.geometry, pxPerMm);
    const originCenterX = originSlotX + originWrap.width / 2;
    const originCenterY = originWrap.height / 2;

    const xMm = pose.xMm ?? 0;
    const yMm = pose.yMm ?? 0;
    const zMm = pose.zMm ?? 0;

    return {
      id: item.id,
      originX: originCenterX + mmToPx(xMm, pxPerMm) - childWrap.width / 2,
      originY: originCenterY + mmToPx(zMm, pxPerMm) - childWrap.height / 2,
      originZ: mmToPx(yMm, pxPerMm),
    };
  });
}

/**
 * Visor chrome only — 2D axis-aligned center of the laid-out wrappers, in
 * the same px space as `originX`/`originY`. Scene3D translates the world
 * so this point sits at the pane center. Not pose, not millimetre SoT.
 */
export function clusterCenterPx(
  laid: SolidLayout[],
  items: { id: string; geometry: SpatialGeometry }[],
  pxPerMm?: number,
): { x: number; y: number } {
  if (laid.length === 0) return { x: 0, y: 0 };
  const geomById = new Map(items.map((item) => [item.id, item.geometry]));
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  for (const slot of laid) {
    const geometry = geomById.get(slot.id);
    if (!geometry) continue;
    const wrap = solidWrapperPx(geometry, pxPerMm);
    minX = Math.min(minX, slot.originX);
    maxX = Math.max(maxX, slot.originX + wrap.width);
    minY = Math.min(minY, slot.originY);
    maxY = Math.max(maxY, slot.originY + wrap.height);
  }
  if (!Number.isFinite(minX)) return { x: 0, y: 0 };
  return { x: (minX + maxX) / 2, y: (minY + maxY) / 2 };
}
