import { useCallback, useRef, useState } from "react";
import { clusterCenterPx, layoutSolidsFromPose } from "./scene3dLayout";
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
 * Board 3D solids B1 + Scene3D-from-pose B1 — sibling pane to the 2D
 * `.sb-viewport`, never inside `.sb-world`. Owns its own view chrome
 * (tilt/zoom), independent of `useCanvasTransform`. Unposed solids keep
 * the presentation row (`layoutSolidsRow` slots). A resolvable
 * `declaredBoxPose` moves that solid one hop from the origin's **row
 * slot** (not from a composed chain; never card `x`/`y`, never `mountedOn`).
 * The cluster is translated so its 2D bounding-box center sits at the
 * pane center (visor chrome, not pose).
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

  const laidOut = layoutSolidsFromPose(
    solids.map((n) => ({ id: n.id, geometry: n.geometry, declaredBoxPose: n.declaredBoxPose })),
    GAP_PX,
  );
  const originById = new Map(laidOut.map((l) => [l.id, l]));
  const cluster = clusterCenterPx(
    laidOut,
    solids.map((n) => ({ id: n.id, geometry: n.geometry })),
  );

  return (
    <div className="sb-scene3d" onWheel={onWheel} onMouseDown={onBackgroundMouseDown}>
      <div
        className="sb-scene3d__world"
        style={{
          transform: `translate(${-cluster.x}px, ${-cluster.y}px) scale(${zoom}) rotateX(${tilt.rotateX}deg) rotateY(${tilt.rotateY}deg)`,
        }}
      >
        {solids.map((node) => {
          const origin = originById.get(node.id);
          return (
            <Solid3D
              key={node.id}
              id={node.id}
              geometry={node.geometry}
              selected={node.id === selectedId}
              onSelect={onSelect}
              originX={origin?.originX ?? 0}
              originY={origin?.originY ?? 0}
              originZ={origin?.originZ ?? 0}
            />
          );
        })}
      </div>
    </div>
  );
}
