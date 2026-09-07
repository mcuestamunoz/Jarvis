import { mountEdgeSegments } from "./mountEdgeGeometry";
import type { SpatialNode } from "./types";

type Props = {
  nodes: SpatialNode[];
};

/** Presentation-only SVG edges for declared mountedOn relations (B2). */
export function MountEdges({ nodes }: Props) {
  const edges = mountEdgeSegments(nodes);
  if (edges.length === 0) return null;
  return (
    <svg className="sb-mount-edges" aria-hidden="true">
      {edges.map((e) => (
        <line
          key={`${e.fromId}->${e.toId}`}
          className="sb-mount-edge"
          x1={e.x1}
          y1={e.y1}
          x2={e.x2}
          y2={e.y2}
        />
      ))}
    </svg>
  );
}
