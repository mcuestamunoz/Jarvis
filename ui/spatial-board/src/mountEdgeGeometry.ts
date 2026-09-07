import type { SpatialNode } from "./types";

export type MountEdgeSegment = {
  fromId: string;
  toId: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
};

/** Pure: drawable mount segments from current node rects (incl. overlay). */
export function mountEdgeSegments(nodes: SpatialNode[]): MountEdgeSegment[] {
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const edges: MountEdgeSegment[] = [];
  for (const node of nodes) {
    const targetId = node.mountedOn;
    if (!targetId) continue;
    const target = byId.get(targetId);
    if (!target) continue;
    edges.push({
      fromId: node.id,
      toId: targetId,
      // Source mid-bottom → target mid-top (stable, readable across lanes).
      x1: node.x + node.width / 2,
      y1: node.y + node.height,
      x2: target.x + target.width / 2,
      y2: target.y,
    });
  }
  return edges;
}
