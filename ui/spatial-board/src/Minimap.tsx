import { MINIMAP } from "./constants";
import { getContentBounds, viewportWorldRect } from "./transform";
import type { CanvasTransform, SpatialNode, ViewportSize } from "./types";

type Props = {
  nodes: SpatialNode[];
  transform: CanvasTransform;
  viewport: ViewportSize;
  onNavigate: (worldX: number, worldY: number) => void;
};

export function Minimap({ nodes, transform, viewport, onNavigate }: Props) {
  const bounds = getContentBounds(nodes, 80);
  const scale = Math.min(
    MINIMAP.width / Math.max(bounds.width, 1),
    MINIMAP.height / Math.max(bounds.height, 1),
  );
  const view = viewportWorldRect(transform, viewport);
  const vx = (view.x - bounds.minX) * scale;
  const vy = (view.y - bounds.minY) * scale;
  const vw = view.width * scale;
  const vh = view.height * scale;

  return (
    <div className="sb-minimap">
      <div className="sb-minimap__label">Mapa</div>
      <svg
        width={MINIMAP.width}
        height={MINIMAP.height}
        className="sb-minimap__svg"
        onClick={(event) => {
          const rect = event.currentTarget.getBoundingClientRect();
          const mx = event.clientX - rect.left;
          const my = event.clientY - rect.top;
          onNavigate(mx / scale + bounds.minX, my / scale + bounds.minY);
        }}
      >
        <rect width={MINIMAP.width} height={MINIMAP.height} className="sb-minimap__bg" />
        {nodes.map((n) => (
          <rect
            key={n.id}
            x={(n.x - bounds.minX) * scale}
            y={(n.y - bounds.minY) * scale}
            width={Math.max(3, n.width * scale)}
            height={Math.max(3, n.height * scale)}
            className={`sb-minimap__dot sb-minimap__dot--${n.kind}`}
          />
        ))}
        <rect
          x={vx}
          y={vy}
          width={vw}
          height={vh}
          className="sb-minimap__view"
        />
      </svg>
      <div className="sb-minimap__meta">
        {nodes.length} cards · {Math.round(transform.zoom * 100)}%
      </div>
    </div>
  );
}
