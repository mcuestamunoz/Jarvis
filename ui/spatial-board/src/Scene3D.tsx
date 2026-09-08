import { useCallback, useRef, useState } from "react";
import { layoutSolidsRow } from "./scene3dLayout";
import { Solid3D } from "./Solid3D";
import type { SpatialNode } from "./types";

const DEFAULT_TILT = { rotateX: 55, rotateY: -30 };
const GAP_PX = 24;
const ZOOM_MIN = 0.5;
const ZOOM_MAX = 2;

type Props = {
  nodes: SpatialNode[];
  selectedId: string | null;
  onSelect: (id: string) => void;
};

/**
 * Board 3D solids B1 — a sibling pane to the 2D `.sb-viewport`, never
 * inside `.sb-world` (mixing 2D absolute card layout and `preserve-3d` on
 * the same elements is not viable). Owns its own view state (tilt/zoom) —
 * deliberately independent of `useCanvasTransform`, which stays the 2D
 * board's own pan/zoom. Layout is a plain row (`layoutSolidsRow`) — never
 * card `x`/`y`, never `mountedOn`/`parent_key`: there is no 3D placement
 * fact anywhere in the system yet (pose stays deferred).
 */
export function Scene3D({ nodes, selectedId, onSelect }: Props) {
  const solids = nodes.filter(
    (n): n is SpatialNode & { geometry: NonNullable<SpatialNode["geometry"]> } =>
      Boolean(n.geometry),
  );

  const [tilt, setTilt] = useState(DEFAULT_TILT);
  const [zoom, setZoom] = useState(1);
  const dragRef = useRef<{
    startX: number;
    startY: number;
    startTilt: typeof DEFAULT_TILT;
  } | null>(null);

  const onMove = useCallback((event: MouseEvent) => {
    const d = dragRef.current;
    if (!d) return;
    const dx = event.clientX - d.startX;
    const dy = event.clientY - d.startY;
    setTilt({
      rotateY: d.startTilt.rotateY + dx * 0.5,
      rotateX: d.startTilt.rotateX - dy * 0.5,
    });
  }, []);

  const onUp = useCallback(() => {
    dragRef.current = null;
    document.removeEventListener("mousemove", onMove);
    document.removeEventListener("mouseup", onUp);
  }, [onMove]);

  const onBackgroundMouseDown = (event: React.MouseEvent) => {
    if (event.button !== 0) return;
    dragRef.current = { startX: event.clientX, startY: event.clientY, startTilt: tilt };
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  };

  const onWheel = (event: React.WheelEvent) => {
    event.preventDefault();
    const factor = event.deltaY > 0 ? 0.9 : 1.1;
    setZoom((z) => Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, z * factor)));
  };

  if (solids.length === 0) return null;

  const laidOut = layoutSolidsRow(
    solids.map((n) => ({ id: n.id, geometry: n.geometry })),
    GAP_PX,
  );
  const originById = new Map(laidOut.map((l) => [l.id, l.originX]));

  return (
    <div className="sb-scene3d" onWheel={onWheel} onMouseDown={onBackgroundMouseDown}>
      <div
        className="sb-scene3d__world"
        style={{
          transform: `scale(${zoom}) rotateX(${tilt.rotateX}deg) rotateY(${tilt.rotateY}deg)`,
        }}
      >
        {solids.map((node) => (
          <Solid3D
            key={node.id}
            id={node.id}
            geometry={node.geometry}
            selected={node.id === selectedId}
            onSelect={onSelect}
            originX={originById.get(node.id) ?? 0}
          />
        ))}
      </div>
    </div>
  );
}
