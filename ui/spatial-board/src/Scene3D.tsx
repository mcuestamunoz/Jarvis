import { useCallback, useRef, useState } from "react";
import { computeDragPosePayload, computeDragPreviewOffsetPx, isDraggableSolid } from "./boardPoseDrag";
import { postDragPose } from "./projects";
import { clusterCenterPx, expandSolidCopies, layoutSolidsFromPose } from "./scene3dLayout";
import { clampZoom } from "./scene3dScale";
import { Solid3D } from "./Solid3D";
import type { SpatialNode } from "./types";

const DEFAULT_TILT = { rotateX: 55, rotateY: -30 };
const GAP_PX = 24;
const DRAG_MOVE_THRESHOLD_PX = 3;

type Props = {
  nodes: SpatialNode[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  /** Board drag → Continuity pose B1 — undefined disables situar mode entirely (e.g. no active project). */
  projectId?: string | null;
  /** Called after a successful pose POST so the caller can re-GET nodes (never localStorage). */
  onPoseCommitted?: () => void;
};

type SolidDragState = {
  nodeId: string;
  originKey: string;
  priorPose?: { originKey: string; xMm?: number; yMm?: number; zMm?: number };
  startX: number;
  startY: number;
  lastX: number;
  lastY: number;
  moved: boolean;
  /** Board Situar free camera B1 — Shift held at drag START locks the
   * whole gesture to declared depth / `y_mm` (never flips mid-drag). */
  zMode: boolean;
  /** Camera tilt locked at drag start — screen→local inverse must use
   * the same angles for every move/up of this gesture (orbit mid-drag
   * is blocked while a solid drag is live anyway). */
  rotateXDeg: number;
  rotateYDeg: number;
};

/**
 * Board 3D solids B1 + Scene3D-from-pose B1 — sibling pane to the 2D
 * `.sb-viewport`, never inside `.sb-world`. Owns its own view chrome
 * (tilt/zoom), independent of `useCanvasTransform`. Unposed solids keep
 * the presentation row (`layoutSolidsRow` slots). A resolvable
 * `declaredBoxPose` moves that solid one hop from the origin's **row
 * slot** (not from a composed chain; never card `x`/`y`, never `mountedOn`).
 * A node's `solidCopies` (Motor visor copies B1) expands it into N row
 * occupants sharing one `selectId` BEFORE layout — still one card/BOM
 * node, never N `ComponentSpec`s; a copy's own pose is stripped (would
 * stack). The cluster is translated so its 2D bounding-box center sits at
 * the pane center (visor chrome, not pose).
 *
 * Board drag → Continuity pose B1, extended by Board Situar free camera
 * B1 — a "Situar" toggle arms per-solid drag WITHOUT touching the camera
 * at all (no forced tilt, orbit stays live even while situating — the
 * Engineer's own ask: "the angle I already have, not a forced top-down").
 * Each SINGLETON solid (never a `solidCopies >= 2` station copy —
 * `isDraggableSolid`) can be dragged. A plain drag follows the **screen
 * plane** at the current tilt (inverse of `rotateX`/`rotateY` → local
 * `originX`/`Y`/`Z` → `x_mm`/`z_mm`/`y_mm`). At tilt 0 that is still
 * Δx→`x_mm`, Δy→`z_mm`. Holding **Shift** locks the gesture to declared
 * depth (`y_mm` / `originZ`). An eligible solid with no
 * `declaredBoxPose.originKey` yet opens a small origin picker instead of
 * arming a drag (never a silent default origin — lock #4). On drop, the
 * same single `postDragPose`/Python-bridge call persists through
 * `set_component_declared_box_pose` — the SAME writer/SoT `declara…`
 * already used; on success the caller re-GETs nodes (`onPoseCommitted`),
 * never an optimistic local mutation.
 */
export function Scene3D({ nodes, selectedId, onSelect, projectId, onPoseCommitted }: Props) {
  const solids = nodes.filter(
    (n): n is SpatialNode & { geometry: NonNullable<SpatialNode["geometry"]> } =>
      Boolean(n.geometry),
  );

  const [tilt, setTilt] = useState(DEFAULT_TILT);
  const [zoom, setZoom] = useState(1);
  const [situar, setSituar] = useState(false);
  const [pickerNodeId, setPickerNodeId] = useState<string | null>(null);
  const [pickerOriginKey, setPickerOriginKey] = useState("");
  const [posting, setPosting] = useState(false);
  const [postError, setPostError] = useState<string | null>(null);
  // Situar UX B1 — live drag preview, mirroring the 2D card's own
  // preview/commit split. Never persisted; cleared on every mouseup
  // regardless of outcome (see onSolidDragUp).
  const [dragPreview, setDragPreview] = useState<{
    nodeId: string;
    dxPx: number;
    dyPx: number;
    dzPx: number;
    zMode: boolean;
  } | null>(null);
  // Read inside the mousemove/mouseup document listeners (added once per
  // drag, not re-bound on every zoom tick) so a wheel-zoom mid-drag is
  // always read fresh, never a stale closure value — same "ref mirrors
  // latest state" pattern useNodeGestures.ts already uses.
  const zoomRef = useRef(1);
  zoomRef.current = zoom;
  const dragRef = useRef<{
    startX: number;
    startY: number;
    startTilt: typeof DEFAULT_TILT;
  } | null>(null);
  const solidDragRef = useRef<SolidDragState | null>(null);

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
    // Board Situar free camera B1: orbit stays live even while situating
    // — a solid's own mousedown already `stopPropagation()`s (Solid3D.tsx)
    // before it ever reaches here, so the two gestures never collide.
    if (event.button !== 0) return;
    dragRef.current = { startX: event.clientX, startY: event.clientY, startTilt: tilt };
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  };

  const onWheel = (event: React.WheelEvent) => {
    event.preventDefault();
    const factor = event.deltaY > 0 ? 0.9 : 1.1;
    setZoom((z) => clampZoom(z * factor));
  };

  // Situar UX B1 / free-camera hotfix #2 — preview uses the same
  // screen→local inverse as commit (`computeDragPreviewOffsetPx`), so the
  // solid tracks the pointer at ANY tilt (not only untilted).
  const onSolidDragMove = useCallback((event: MouseEvent) => {
    const d = solidDragRef.current;
    if (!d) return;
    d.lastX = event.clientX;
    d.lastY = event.clientY;
    const dx = event.clientX - d.startX;
    const dy = event.clientY - d.startY;
    if (!d.moved && Math.hypot(dx, dy) >= DRAG_MOVE_THRESHOLD_PX) d.moved = true;
    if (d.moved) {
      const offset = computeDragPreviewOffsetPx({
        deltaScreenPxX: dx,
        deltaScreenPxY: dy,
        zoom: zoomRef.current,
        rotateXDeg: d.rotateXDeg,
        rotateYDeg: d.rotateYDeg,
        axisMode: d.zMode ? "z" : "xy",
      });
      setDragPreview({
        nodeId: d.nodeId,
        dxPx: offset.dxPx,
        dyPx: offset.dyPx,
        dzPx: offset.dzPx,
        zMode: d.zMode,
      });
    }
  }, []);

  const onSolidDragUp = useCallback(() => {
    const d = solidDragRef.current;
    solidDragRef.current = null;
    setDragPreview(null);
    document.removeEventListener("mousemove", onSolidDragMove);
    document.removeEventListener("mouseup", onSolidDragUp);
    if (!d || !d.moved || !projectId) return;
    const payload = computeDragPosePayload({
      componentKey: d.nodeId,
      originKey: d.originKey,
      priorPose: d.priorPose,
      deltaScreenPxX: d.lastX - d.startX,
      deltaScreenPxY: d.lastY - d.startY,
      zoom: zoomRef.current,
      axisMode: d.zMode ? "z" : "xy",
      rotateXDeg: d.rotateXDeg,
      rotateYDeg: d.rotateYDeg,
    });
    setPosting(true);
    setPostError(null);
    postDragPose(projectId, payload)
      .then(() => onPoseCommitted?.())
      .catch((err: unknown) => setPostError(err instanceof Error ? err.message : "pose write failed"))
      .finally(() => setPosting(false));
  }, [onSolidDragMove, projectId, onPoseCommitted]);

  const handleSolidDragStart = (event: React.MouseEvent, id: string) => {
    if (!situar || posting) return;
    const node = solids.find((n) => n.id === id);
    if (!node || !isDraggableSolid(node)) return;
    const originKey = node.declaredBoxPose?.originKey;
    if (!originKey) {
      // Board drag → Continuity pose B1 lock #4: never a silent default
      // origin — open the small picker instead of arming a drag.
      setPickerNodeId(id);
      setPickerOriginKey("");
      return;
    }
    solidDragRef.current = {
      nodeId: id,
      originKey,
      priorPose: node.declaredBoxPose,
      startX: event.clientX,
      startY: event.clientY,
      lastX: event.clientX,
      lastY: event.clientY,
      moved: false,
      zMode: event.shiftKey,
      rotateXDeg: tilt.rotateX,
      rotateYDeg: tilt.rotateY,
    };
    document.addEventListener("mousemove", onSolidDragMove);
    document.addEventListener("mouseup", onSolidDragUp);
  };

  const confirmPickedOrigin = () => {
    if (!pickerNodeId || !pickerOriginKey || !projectId) return;
    setPosting(true);
    setPostError(null);
    postDragPose(projectId, {
      component_key: pickerNodeId,
      origin_key: pickerOriginKey,
      x_mm: 0,
      y_mm: 0,
      z_mm: null,
    })
      .then(() => {
        setPickerNodeId(null);
        onPoseCommitted?.();
      })
      .catch((err: unknown) => setPostError(err instanceof Error ? err.message : "pose write failed"))
      .finally(() => setPosting(false));
  };

  if (solids.length === 0) return null;

  const expanded = expandSolidCopies(
    solids.map((n) => ({
      id: n.id,
      geometry: n.geometry,
      declaredBoxPose: n.declaredBoxPose,
      solidCopies: n.solidCopies,
      solidCopyOffsetsMm: n.solidCopyOffsetsMm,
    })),
  );
  const laidOut = layoutSolidsFromPose(
    expanded.map((e) => ({
      id: e.layoutId,
      geometry: e.geometry,
      declaredBoxPose: e.declaredBoxPose,
      offsetMm: e.offsetMm,
    })),
    GAP_PX,
  );
  const originById = new Map(laidOut.map((l) => [l.id, l]));
  const cluster = clusterCenterPx(
    laidOut,
    expanded.map((e) => ({ id: e.layoutId, geometry: e.geometry })),
  );
  const draggableBySelectId = new Map(solids.map((n) => [n.id, isDraggableSolid(n)]));
  const boxOriginCandidates = pickerNodeId
    ? solids.filter((n) => n.geometry?.shape === "box" && n.id !== pickerNodeId).map((n) => n.id)
    : [];

  return (
    <div
      className={`sb-scene3d${situar ? " sb-scene3d--situar" : ""}`}
      onWheel={onWheel}
      onMouseDown={onBackgroundMouseDown}
    >
      {projectId ? (
        <button
          type="button"
          className={`sb-scene3d__situar-toggle${situar ? " sb-scene3d__situar-toggle--on" : ""}`}
          onMouseDown={(event) => event.stopPropagation()}
          onClick={() => {
            setSituar((s) => !s);
            setPickerNodeId(null);
            setPostError(null);
          }}
        >
          {situar ? "Situar: ON" : "Situar"}
        </button>
      ) : null}
      {situar ? (
        <div className="sb-scene3d__situar-hint">
          fondo: órbita · arrastre: sigue el cursor (plano pantalla) · Shift+arrastre: profundidad (Y)
        </div>
      ) : null}
      <div
        className="sb-scene3d__world"
        style={{
          transform: `translate(${-cluster.x}px, ${-cluster.y}px) scale(${zoom}) rotateX(${tilt.rotateX}deg) rotateY(${tilt.rotateY}deg)`,
        }}
      >
        {expanded.map((e) => {
          const origin = originById.get(e.layoutId);
          // Copies (`layoutId !== selectId`) never drag — same guarantee
          // as `isDraggableSolid`'s own `solidCopies >= 2` check, applied
          // here as a second, redundant-but-cheap safety net.
          const isSingleton = e.layoutId === e.selectId;
          const draggable = situar && isSingleton && Boolean(draggableBySelectId.get(e.selectId));
          const needsOrigin = draggable && !e.declaredBoxPose?.originKey;
          // Situar UX B1 — live preview: only the one solid currently
          // being dragged gets its rendered origin nudged by the pointer
          // offset (world px, same space originX/Y already render in).
          // Never persisted — a fresh GET after commit is what actually
          // moves it for real (see onPoseCommitted).
          const preview = dragPreview?.nodeId === e.selectId ? dragPreview : null;
          return (
            <Solid3D
              key={e.layoutId}
              id={e.selectId}
              geometry={e.geometry}
              selected={e.selectId === selectedId}
              onSelect={onSelect}
              originX={(origin?.originX ?? 0) + (preview?.dxPx ?? 0)}
              originY={(origin?.originY ?? 0) + (preview?.dyPx ?? 0)}
              originZ={(origin?.originZ ?? 0) + (preview?.dzPx ?? 0)}
              draggable={draggable}
              needsOrigin={needsOrigin}
              onDragStart={draggable ? handleSolidDragStart : undefined}
            />
          );
        })}
      </div>
      {pickerNodeId ? (
        <div className="sb-scene3d__origin-picker" onMouseDown={(event) => event.stopPropagation()}>
          <span>Origen para {pickerNodeId}:</span>
          <select value={pickerOriginKey} onChange={(event) => setPickerOriginKey(event.target.value)}>
            <option value="">— elegir —</option>
            {boxOriginCandidates.map((key) => (
              <option key={key} value={key}>{key}</option>
            ))}
          </select>
          <button type="button" disabled={!pickerOriginKey || posting} onClick={confirmPickedOrigin}>
            Fijar origen
          </button>
          <button type="button" onClick={() => setPickerNodeId(null)}>Cancelar</button>
        </div>
      ) : postError ? (
        <div className="sb-scene3d__pose-error" onMouseDown={(event) => event.stopPropagation()}>
          {postError}
        </div>
      ) : null}
    </div>
  );
}
