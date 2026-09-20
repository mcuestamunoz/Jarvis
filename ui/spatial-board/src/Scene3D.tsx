import { useCallback, useEffect, useRef, useState } from "react";
import { computeDragPosePayload, computeDragPreviewOffsetPx, isDraggableSolid } from "./boardPoseDrag";
import { isOverlapScreeningCopy } from "./fitAttestationUi";
import { postDragPose, postFitAttestation } from "./projects";
import { clusterCenterPx, expandSolidCopies, layoutSolidsFromPose } from "./scene3dLayout";
import { clampZoom } from "./scene3dScale";
import { computeAncestorChain, isDimmed } from "./mountAncestorChain";
import { pieceStripSolids } from "./overlapPicker";
import { isSolidHitThrough, resolveClusterCenter } from "./situarInteractionState";
import { formatOriginCandidateLabel, rankBoxOriginCandidates } from "./situarOriginCandidates";
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
  /**
   * Board 3D-first workshop + mount-chain inspector B1 — Situar is now a
   * CONTROLLED prop (lifted out of this component) so the parent can
   * decide whether to render the Taller-mode `InspectorDock` alongside
   * this pane (IC §2.6: Situar ON collapses the dock to chips — the
   * parent needs to know Situar's state to make that call).
   */
  situar: boolean;
  onSituarChange: (next: boolean) => void;
  /**
   * True when this pane is the Taller tab's primary workspace (full-bleed
   * styling, always-on piece strip, ancestor-chain dimming). False (or
   * omitted) preserves the exact pre-existing Grafo-tab behavior: fixed
   * height, no dimming, piece strip only while Situar is ON.
   */
  primary?: boolean;
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
export function Scene3D({
  nodes, selectedId, onSelect, projectId, onPoseCommitted, situar, onSituarChange, primary = false,
}: Props) {
  const solids = nodes.filter(
    (n): n is SpatialNode & { geometry: NonNullable<SpatialNode["geometry"]> } =>
      Boolean(n.geometry),
  );

  const [tilt, setTilt] = useState(DEFAULT_TILT);
  const [zoom, setZoom] = useState(1);
  const [pickerNodeId, setPickerNodeId] = useState<string | null>(null);
  const [pickerOriginKey, setPickerOriginKey] = useState("");
  const [posting, setPosting] = useState(false);
  const [postError, setPostError] = useState<string | null>(null);
  const [attesting, setAttesting] = useState(false);
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
  // Situar experience B1 (E3) — the cluster center captured once Situar
  // turns on (or at the next manual "Recentrar 3D"); `null` means "not
  // captured yet, use the live value" (see `resolveClusterCenter`). Reset
  // to `null` whenever Situar turns off, so the NEXT time it turns on
  // captures a fresh baseline rather than reusing a stale one.
  const situarFrozenClusterRef = useRef<{ x: number; y: number } | null>(null);
  // Value itself is never read — bumping it only forces the re-render that
  // "Recentrar 3D" needs after clearing the ref above (mutating a ref
  // alone does not schedule one).
  const [, setRecenterTick] = useState(0);

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
    document.removeEventListener("mousemove", onSolidDragMove);
    document.removeEventListener("mouseup", onSolidDragUp);
    if (!d || !d.moved || !projectId) {
      // Nothing was actually dragged (or no live project) — no POST is
      // coming, so there is no async gap to bridge; clear the preview now.
      setDragPreview(null);
      return;
    }
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
    // Situar drop honesty fix (2026-09-12): do NOT clear `dragPreview`
    // here. The old behavior cleared it immediately on mouseup, which made
    // the solid visibly SNAP BACK to its stale pre-drag layout position for
    // the whole POST+refetch round trip, then jump again once fresh nodes
    // arrived — reading as "it jumped away" even for the piece the
    // Engineer actually meant to move. The preview now stays live (holding
    // the solid exactly where it was dropped) until the `nodes` effect
    // below sees the re-fetched, committed pose and clears it — see that
    // effect's own comment. On failure, clear immediately (nothing will
    // ever commit, so there's nothing to hold the preview for).
    postDragPose(projectId, payload)
      .then(() => onPoseCommitted?.())
      .catch((err: unknown) => {
        setPostError(err instanceof Error ? err.message : "pose write failed");
        setDragPreview(null);
      })
      .finally(() => setPosting(false));
  }, [onSolidDragMove, projectId, onPoseCommitted]);

  // Situar drop honesty fix (2026-09-12): clear a pending preview only once
  // the PARENT's re-fetched `nodes` prop actually lands (a new array
  // reference after `onPoseCommitted` → `refetch`). Until then the preview
  // offset keeps the just-dropped solid visually anchored at the drop
  // point — see `onSolidDragUp`'s own comment for why. A no-op whenever no
  // preview is pending (including the very first render).
  useEffect(() => {
    setDragPreview((current) => (current ? null : current));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes]);

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

  const onBackgroundMouseDown = (event: React.MouseEvent) => {
    if (event.button !== 0) return;
    // Nested-hit hotfix #2 (Engineer: still couldn't grab ESC inside a
    // box): CSS 3D hit-testing does not match visuals — clicks on the
    // nested solid fall through to this pane after outer boxes are
    // pointer-events:none. With Situar ON + a card-selected draggable,
    // treat pane mousedown as pose-drag for THAT solid. Alt/Meta+drag
    // keeps camera orbit available.
    if (
      situar &&
      selectedId &&
      !event.altKey &&
      !event.metaKey
    ) {
      const node = solids.find((n) => n.id === selectedId);
      if (node && isDraggableSolid(node)) {
        handleSolidDragStart(event, selectedId);
        return;
      }
    }
    dragRef.current = { startX: event.clientX, startY: event.clientY, startTilt: tilt };
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  };

  // Fit attestation B1 — "Declarar verificado" / "Quitar verificación".
  // Singleton-only (never a `solidCopies >= 2` station, same guarantee
  // `isDraggableSolid` already gives the drag path — this is the ONE
  // shared gate, not a second multiplicity rule): the button only ever
  // targets the currently SELECTED singleton solid. Eligibility mirrors
  // the writer's overlap gate via `isOverlapScreeningCopy` (NOT bare
  // `"se solapan"` — that false-positives on `"no se solapan"`). The
  // writer remains the one true gate; this is only a UX hint.
  const selectedSolid = selectedId ? solids.find((n) => n.id === selectedId) : undefined;
  const selectedSingleton = selectedSolid && isDraggableSolid(selectedSolid);
  const selectedSobres = selectedSingleton
    ? selectedSolid.fields.find((f) => f.label === "sobres")
    : undefined;
  const selectedAttested = selectedSingleton
    ? selectedSolid.fields.some((f) => f.label === "verificación")
    : false;
  const canAttest = Boolean(
    selectedSobres && isOverlapScreeningCopy(selectedSobres.value) && !selectedAttested,
  );
  const canClearAttest = Boolean(selectedSingleton && selectedAttested);

  const handleFitAttestation = (attest: boolean) => {
    if (!projectId || !selectedId || posting || attesting) return;
    setAttesting(true);
    setPostError(null);
    postFitAttestation(projectId, { component_key: selectedId, attest })
      .then(() => onPoseCommitted?.())
      .catch((err: unknown) => setPostError(err instanceof Error ? err.message : "fit attestation write failed"))
      .finally(() => setAttesting(false));
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
  // Situar experience B1 (E3, supersedes the narrower drop-only freeze):
  // while Situar is ON, the world's camera-center translate stays fixed at
  // whatever it was the moment Situar turned on (or the last "Recentrar
  // 3D"), never recomputed from the live layout — including across a
  // settled drop. Recomputing on every settle re-centers the ENTIRE scene
  // whenever ANY one piece's bounding box changes, so every untouched
  // peer visibly slides — "the racimo re-centers on every drop" from the
  // Engineer's own field note. `resolveClusterCenter` (pure, unit-tested)
  // makes the decision; this component only owns WHEN to (re)capture the
  // frozen value: on the first render with Situar on and nothing captured
  // yet, or right after "Recentrar 3D" clears the ref.
  const liveCluster = clusterCenterPx(
    laidOut,
    expanded.map((e) => ({ id: e.layoutId, geometry: e.geometry })),
  );
  if (situar && situarFrozenClusterRef.current === null) {
    situarFrozenClusterRef.current = liveCluster;
  }
  const cluster = resolveClusterCenter({
    situar,
    liveCenter: liveCluster,
    frozenCenter: situarFrozenClusterRef.current,
  });
  // E2 — nested-hit is only load-bearing WHILE a drag/preview/POST is
  // actually in flight (see `isSolidHitThrough`'s own docstring); idle
  // selection alone must never make peers click-through.
  const situarBusy = Boolean(dragPreview) || posting;
  const draggableBySelectId = new Map(solids.map((n) => [n.id, isDraggableSolid(n)]));
  // Board Situar multi-box UX B1 — rank preferred (mountedOn / placa raíz)
  // first; always keep the full box fallback when mounts are empty.
  const boxOriginCandidates = pickerNodeId
    ? rankBoxOriginCandidates(pickerNodeId, solids)
    : [];

  // Board 3D-first workshop + mount-chain inspector B1 — ancestor chain +
  // dimming, Taller (primary) pane only (IC §2.4/§2.6). Grafo's own 3D
  // view keeps its exact pre-existing look (no dimming) even with a
  // selection active.
  const nodesById = new Map(nodes.map((n) => [n.id, n]));
  const chain = primary && selectedId ? computeAncestorChain(selectedId, nodesById) : [];
  // Overlap/stack picker (IC §2.5) — Trigger B, always available in the
  // Taller pane regardless of Situar; Situar ON narrows to draggable
  // singletons only (unchanged from the pre-existing Situar-only strip).
  const stripSolids = pieceStripSolids(solids, situar);
  const showStrip = situar || primary;

  return (
    <div
      className={`sb-scene3d${situar ? " sb-scene3d--situar" : ""}${primary ? " sb-scene3d--primary" : ""}`}
      onWheel={onWheel}
      onMouseDown={onBackgroundMouseDown}
    >
      {projectId ? (
        <button
          type="button"
          className={`sb-scene3d__situar-toggle${situar ? " sb-scene3d__situar-toggle--on" : ""}`}
          onMouseDown={(event) => event.stopPropagation()}
          onClick={() => {
            const next = !situar;
            // E3: turning OFF drops the frozen baseline so the NEXT time
            // Situar turns on captures a fresh one, never a stale value
            // from a previous session.
            if (!next) situarFrozenClusterRef.current = null;
            onSituarChange(next);
            setPickerNodeId(null);
            setPostError(null);
          }}
        >
          {situar ? "Situar: ON" : "Situar"}
        </button>
      ) : null}
      {situar ? (
        <button
          type="button"
          className="sb-scene3d__recenter-toggle"
          onMouseDown={(event) => event.stopPropagation()}
          onClick={() => {
            situarFrozenClusterRef.current = null;
            setRecenterTick((t) => t + 1);
          }}
        >
          Recentrar 3D
        </button>
      ) : null}
      {projectId && canAttest ? (
        <button
          type="button"
          className="sb-scene3d__attest-toggle"
          disabled={attesting}
          onMouseDown={(event) => event.stopPropagation()}
          onClick={() => handleFitAttestation(true)}
        >
          Declarar verificado
        </button>
      ) : null}
      {projectId && canClearAttest ? (
        <button
          type="button"
          className="sb-scene3d__attest-toggle"
          disabled={attesting}
          onMouseDown={(event) => event.stopPropagation()}
          onClick={() => handleFitAttestation(false)}
        >
          Quitar verificación
        </button>
      ) : null}
      {situar ? (
        <div className="sb-scene3d__situar-hint">
          click en una caja: elegir · arrastre (fondo o caja): mueve la seleccionada ·
          Alt+arrastre: órbita · Shift: profundidad (Y)
        </div>
      ) : null}
      {showStrip ? (
        // E1 (Option B), generalized by the overlap/stack picker (IC §2.5,
        // Trigger B) — a compact piece strip inside the 3D pane itself, so
        // picking a piece never depends on precise 3D hit-testing (CSS 3D
        // has no reliable multi-hit ray query) nor on the 2D card row
        // having enough room to be usable at the same time. While Situar
        // is ON, lists only situar-draggable singletons (same
        // `isDraggableSolid` gate the drag arm itself uses) — copies/disks
        // are never listed there since they can never be selected-to-drag
        // either. In the Taller pane with Situar OFF, lists every solid
        // (including station copies) — this is the general-purpose
        // inspector picker, not a drag-eligibility list.
        <div className="sb-scene3d__piece-strip" onMouseDown={(event) => event.stopPropagation()}>
          {stripSolids.map((s) => (
            <button
              key={s.id}
              type="button"
              className={`sb-scene3d__piece-chip${s.id === selectedId ? " sb-scene3d__piece-chip--selected" : ""}`}
              onClick={() => onSelect(s.id)}
            >
              {s.id}
            </button>
          ))}
        </div>
      ) : null}
      <div
        className="sb-scene3d__world"
        style={{
          transform: `translate(${-cluster.x}px, ${-cluster.y}px) scale(${zoom}) rotateX(${tilt.rotateX}deg) rotateY(${tilt.rotateY}deg)`,
        }}
      >
        {[...expanded]
          .sort((a, b) => {
            // Paint selected last so its faces win sibling hit-tests when
            // bounds do overlap in 2D projection.
            if (!selectedId) return 0;
            if (a.selectId === selectedId && b.selectId !== selectedId) return 1;
            if (b.selectId === selectedId && a.selectId !== selectedId) return -1;
            return 0;
          })
          .map((e) => {
          const origin = originById.get(e.layoutId);
          // Copies (`layoutId !== selectId`) never drag — same guarantee
          // as `isDraggableSolid`'s own `solidCopies >= 2` check, applied
          // here as a second, redundant-but-cheap safety net.
          const isSingleton = e.layoutId === e.selectId;
          const draggable = situar && isSingleton && Boolean(draggableBySelectId.get(e.selectId));
          const needsOrigin = draggable && !e.declaredBoxPose?.originKey;
          // Situar experience B1 (E2): peers are click-through ONLY while
          // a drag/preview/POST is actually live (`situarBusy`) — idle
          // selection alone must let a click on a different draggable
          // solid select it (the Engineer's own "click another box under
          // the cursor → ignored" complaint). The ACCEPT nested-hit smoke
          // (card esc → drag anywhere in pane moves esc) still holds:
          // once a drag/preview starts, peers go click-through exactly as
          // before, so a background click near a peer still moves the
          // piece actually being dragged.
          const pointerEventsNone = isSolidHitThrough({
            situar,
            selectedId,
            solidId: e.selectId,
            busy: situarBusy,
          });
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
              yawDeg={origin?.yawDeg}
              draggable={draggable}
              needsOrigin={needsOrigin}
              dimmed={isDimmed(e.selectId, chain)}
              pointerEventsNone={pointerEventsNone}
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
            {boxOriginCandidates.map((c) => (
              <option key={c.id} value={c.id}>{formatOriginCandidateLabel(c)}</option>
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
