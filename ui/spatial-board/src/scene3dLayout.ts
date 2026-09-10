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

// Visor assembly root B1 — the exact, single root key this Buy recognizes.
// Never `frame_plate_2`/any other plate, never `frame` root — silently
// picking a different plate as "the" assembly root is explicitly forbidden
// (locked #2); a `frame_plate` that isn't a box (no envelope declared yet)
// also does not activate root behavior.
const ASSEMBLY_ROOT_ID = "frame_plate";

type PoseItem = {
  id: string;
  geometry: SpatialGeometry;
  declaredBoxPose?: { originKey: string; xMm?: number; yMm?: number; zMm?: number };
  offsetMm?: { xMm: number; yMm: number; zMm: number };
};

type CenterPx = { x: number; y: number; z: number };

/**
 * Scene3D-from-pose + multi-hop B1 — placement algorithm. Every item first
 * gets a row slot via `layoutSolidsRow` (broken/missing pose never vanishes).
 * An item whose `declaredBoxPose.originKey` resolves to a BOX-shaped item is
 * placed center-to-center from that origin's **composed** center: if the
 * origin is itself posed (to another box), walk the chain (Pose multi-hop B1).
 * Cycle → break on the revisited id's row-slot center (or world 0 if root).
 *
 * Axis remap: declared +X -> CSS X (`originX`), +Z -> CSS Y (`originY`),
 * +Y -> CSS Z/depth (`originZ`). Wrapper top-left correction on X/Y only.
 *
 * Visor assembly root B1: `frame_plate` box → world (0,0,0). `offsetMm`
 * stations stay absolute around world 0 and never enter the pose chain.
 * N1 tidy: root + `offsetMm` items are excluded from the row cursor.
 */
export function layoutSolidsFromPose(
  items: PoseItem[],
  gapPx: number,
  pxPerMm?: number,
): SolidLayout[] {
  const root = items.find(
    (item) => item.id === ASSEMBLY_ROOT_ID && item.geometry.shape === "box",
  );

  const rowItems = items.filter(
    (item) => !item.offsetMm && !(root && item.id === root.id),
  );
  const slots = layoutSolidsRow(
    rowItems.map((item) => ({ id: item.id, geometry: item.geometry })),
    gapPx,
    pxPerMm,
  );
  const slotXById = new Map(slots.map((slot) => [slot.id, slot.originX]));
  const itemById = new Map(items.map((item) => [item.id, item]));

  const rowSlotCenter = (id: string): CenterPx => {
    if (root && id === root.id) return { x: 0, y: 0, z: 0 };
    const target = itemById.get(id);
    if (!target) return { x: 0, y: 0, z: 0 };
    const wrap = solidWrapperPx(target.geometry, pxPerMm);
    const slotX = slotXById.get(id) ?? 0;
    return { x: slotX + wrap.width / 2, y: wrap.height / 2, z: 0 };
  };

  const resolveComposedCenter = (id: string, visiting: Set<string>): CenterPx => {
    if (root && id === root.id) return { x: 0, y: 0, z: 0 };
    if (visiting.has(id)) return rowSlotCenter(id);

    const target = itemById.get(id);
    if (!target) return { x: 0, y: 0, z: 0 };

    const pose = target.declaredBoxPose;
    const origin = pose ? itemById.get(pose.originKey) : undefined;
    if (!pose || !origin || origin.geometry.shape !== "box") {
      return rowSlotCenter(id);
    }

    const nextVisiting = new Set(visiting);
    nextVisiting.add(id);
    const parent = resolveComposedCenter(pose.originKey, nextVisiting);
    return {
      x: parent.x + mmToPx(pose.xMm ?? 0, pxPerMm),
      y: parent.y + mmToPx(pose.zMm ?? 0, pxPerMm),
      z: parent.z + mmToPx(pose.yMm ?? 0, pxPerMm),
    };
  };

  return items.map((item) => {
    if (root && item.id === root.id) {
      const wrap = solidWrapperPx(item.geometry, pxPerMm);
      return { id: item.id, originX: -wrap.width / 2, originY: -wrap.height / 2, originZ: 0 };
    }

    // Visor X stations — absolute mm around world 0; never pose-composed.
    if (item.offsetMm) {
      const wrap = solidWrapperPx(item.geometry, pxPerMm);
      return {
        id: item.id,
        originX: mmToPx(item.offsetMm.xMm, pxPerMm) - wrap.width / 2,
        originY: mmToPx(item.offsetMm.zMm, pxPerMm) - wrap.height / 2,
        originZ: mmToPx(item.offsetMm.yMm, pxPerMm),
      };
    }

    const slotX = slotXById.get(item.id) ?? 0;
    const pose = item.declaredBoxPose;
    const origin = pose ? itemById.get(pose.originKey) : undefined;

    if (!pose || !origin || origin.geometry.shape !== "box") {
      return { id: item.id, originX: slotX, originY: 0, originZ: 0 };
    }

    const originCenter = resolveComposedCenter(pose.originKey, new Set());
    const childWrap = solidWrapperPx(item.geometry, pxPerMm);
    const xMm = pose.xMm ?? 0;
    const yMm = pose.yMm ?? 0;
    const zMm = pose.zMm ?? 0;

    return {
      id: item.id,
      originX: originCenter.x + mmToPx(xMm, pxPerMm) - childWrap.width / 2,
      originY: originCenter.y + mmToPx(zMm, pxPerMm) - childWrap.height / 2,
      originZ: originCenter.z + mmToPx(yMm, pxPerMm),
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

export type ExpandedSolid = {
  layoutId: string;
  selectId: string;
  geometry: SpatialGeometry;
  declaredBoxPose?: { originKey: string; xMm?: number; yMm?: number; zMm?: number };
  offsetMm?: { xMm: number; yMm: number; zMm: number };
};

/**
 * Motor visor copies B1 — turns one node with `solidCopies: N` into N
 * presentation-only layout entries sharing one `selectId` (so clicking any
 * copy still selects the ONE card — never N `ComponentSpec`/BOM nodes).
 * A copied node's `declaredBoxPose` is deliberately stripped (composing
 * pose onto N copies would stack them at the same point); an uncopied node
 * (no `solidCopies`, or `< 2`) passes through as a single entry with its
 * pose intact, in input order. `layoutId` is what
 * `layoutSolidsFromPose`/`clusterCenterPx` must use as their own `id` —
 * three nodes sharing `id: "motors"` would collide.
 *
 * Key-agnostic by construction — Propeller visor copies B1 relies on this:
 * a `propellers` node with `solidCopies: N` (cross-read from the sibling
 * `motors` spec's own `motor_count`, projected server-side) expands the
 * same way, with no `id === "motors"` special-case here.
 *
 * Visor X stations B1: when the node also carries `solidCopyOffsetsMm`
 * with EXACTLY `solidCopies` points, each copy `i` gets that point as its
 * `offsetMm` instead of a row slot (see `layoutSolidsFromPose`). A length
 * mismatch (or no offsets at all) falls back to the plain row, same as
 * before this Buy — never a partial/misaligned station set.
 */
export function expandSolidCopies(
  nodes: {
    id: string;
    geometry: SpatialGeometry;
    declaredBoxPose?: { originKey: string; xMm?: number; yMm?: number; zMm?: number };
    solidCopies?: number;
    solidCopyOffsetsMm?: { xMm: number; yMm: number; zMm: number }[];
  }[],
): ExpandedSolid[] {
  const result: ExpandedSolid[] = [];
  for (const node of nodes) {
    if (typeof node.solidCopies === "number" && node.solidCopies >= 2) {
      const offsets =
        node.solidCopyOffsetsMm && node.solidCopyOffsetsMm.length === node.solidCopies
          ? node.solidCopyOffsetsMm
          : undefined;
      for (let i = 0; i < node.solidCopies; i++) {
        result.push({
          layoutId: `${node.id}#${i}`,
          selectId: node.id,
          geometry: node.geometry,
          offsetMm: offsets ? offsets[i] : undefined,
        });
      }
    } else {
      result.push({
        layoutId: node.id,
        selectId: node.id,
        geometry: node.geometry,
        declaredBoxPose: node.declaredBoxPose,
      });
    }
  }
  return result;
}
