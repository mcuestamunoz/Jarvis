import { pxToMm } from "./scene3dScale";

/**
 * Board drag → Continuity pose B1, extended by Board Situar free camera
 * B1 — pure helpers, no DOM, no fetch, so the drag math itself is
 * unit-testable without a browser. `Scene3D.tsx` is the only caller.
 *
 * Free-camera honesty (2026-09-10 hotfix #2): screen Δ must be converted
 * through the **inverse** of the world's `rotateX`/`rotateY` before it is
 * written to declared mm. Applying raw screen Δx→`originX` alone fails in
 * a side/back view — world X points into the scene, so lateral screen
 * drag barely moves the solid (Engineer: "no me deja mover lateral").
 *
 * Still an ORTHOGRAPHIC-STYLE APPROXIMATION (no perspective unproject):
 * `.sb-scene3d` has `perspective: 900px`. Named, accepted risk.
 */

export type DraggableNode = {
  geometry?: unknown;
  solidCopies?: number;
};

/**
 * A solid is drag-eligible only when it has a real geometry AND is NOT a
 * station copy (`solidCopies >= 2` — the same threshold `expandSolidCopies`
 * itself uses to decide "this shares one identity across N places"). A
 * copied node has no single coherent origin/Δmm to drag onto — see the
 * parent investigation's own honesty-collision finding (a drag on any one
 * of N copies could only ever write ONE shared pose, which would then be
 * stripped again by `expandSolidCopies` on the very next render). Never
 * invents a per-copy pose mechanism here.
 */
export function isDraggableSolid(node: DraggableNode): boolean {
  if (!node.geometry) return false;
  return typeof node.solidCopies !== "number" || node.solidCopies < 2;
}

export type DeclaredBoxPoseDto = { originKey: string; xMm?: number; yMm?: number; zMm?: number };

export type DragPosePayload = {
  component_key: string;
  origin_key: string;
  x_mm: number;
  y_mm: number;
  z_mm: number | null;
};

export type DragPreviewOffsetPx = { dxPx: number; dyPx: number; dzPx: number };

/**
 * Map a screen-plane delta into local CSS px (`originX`/`Y`/`Z` space)
 * by inverting the world's CSS `rotateX(rx) rotateY(ry)` (ry applied
 * first). View-plane vector is `(sx/zoom, sy/zoom, 0)`.
 *
 * At tilt (0,0) this is identity: dx=sx/zoom, dy=sy/zoom, dz=0 — same as
 * the previous untilted WYSIWYG mapping.
 */
export function screenDeltaToLocalPx(args: {
  deltaScreenPxX: number;
  deltaScreenPxY: number;
  zoom: number;
  rotateXDeg?: number;
  rotateYDeg?: number;
}): DragPreviewOffsetPx {
  const sx = args.deltaScreenPxX / args.zoom;
  const sy = args.deltaScreenPxY / args.zoom;
  const rx = ((args.rotateXDeg ?? 0) * Math.PI) / 180;
  const ry = ((args.rotateYDeg ?? 0) * Math.PI) / 180;
  const cosX = Math.cos(rx);
  const sinX = Math.sin(rx);
  const cosY = Math.cos(ry);
  const sinY = Math.sin(ry);
  // Inverse Rx then inverse Ry, with view Z = 0 (screen plane).
  const x1 = sx;
  const y1 = sy * cosX;
  const z1 = -sy * sinX;
  return {
    dxPx: x1 * cosY - z1 * sinY,
    dyPx: y1,
    dzPx: x1 * sinY + z1 * cosY,
  };
}

/**
 * Compute the POST payload for one drag gesture.
 *
 * Layout map (unchanged): `x_mm`→`originX`, `z_mm`→`originY`, `y_mm`→`originZ`.
 *
 * `"xy"` (default) — solid follows the **screen plane** at the current
 * tilt: local (dx,dy,dz) from `screenDeltaToLocalPx` → x/z/y_mm. At
 * tilt 0 this reduces to Δx→x_mm, Δy→z_mm, y_mm untouched.
 *
 * `"z"` (Shift) — only declared depth (`y_mm` / `originZ`); x/z unchanged.
 * Uses the local `dz` of the same screen-plane inverse so a side-view
 * horizontal drag can still push depth.
 */
export function computeDragPosePayload(args: {
  componentKey: string;
  originKey: string;
  priorPose?: DeclaredBoxPoseDto;
  deltaScreenPxX: number;
  deltaScreenPxY: number;
  zoom: number;
  pxPerMm?: number;
  axisMode?: "xy" | "z";
  rotateXDeg?: number;
  rotateYDeg?: number;
}): DragPosePayload {
  const {
    componentKey,
    originKey,
    priorPose,
    deltaScreenPxX,
    deltaScreenPxY,
    zoom,
    pxPerMm,
    axisMode = "xy",
    rotateXDeg = 0,
    rotateYDeg = 0,
  } = args;
  const priorX = priorPose?.xMm ?? 0;
  const priorY = priorPose?.yMm ?? 0;
  const priorZ = priorPose?.zMm ?? null;

  const local = screenDeltaToLocalPx({
    deltaScreenPxX,
    deltaScreenPxY,
    zoom,
    rotateXDeg,
    rotateYDeg,
  });

  if (axisMode === "z") {
    const deltaDepthMm = pxToMm(local.dzPx, pxPerMm);
    return {
      component_key: componentKey,
      origin_key: originKey,
      x_mm: priorX,
      y_mm: priorY + deltaDepthMm,
      z_mm: priorZ,
    };
  }

  const deltaXMm = pxToMm(local.dxPx, pxPerMm);
  const deltaZMm = pxToMm(local.dyPx, pxPerMm);
  const deltaYMm = pxToMm(local.dzPx, pxPerMm);
  const nextZ =
    priorZ == null && deltaZMm === 0 ? null : (priorZ ?? 0) + deltaZMm;
  return {
    component_key: componentKey,
    origin_key: originKey,
    x_mm: priorX + deltaXMm,
    y_mm: priorY + deltaYMm,
    z_mm: nextZ,
  };
}

/**
 * Live drag preview in the same local px space as `originX`/`Y`/`Z`.
 * Same inverse as `computeDragPosePayload` — never an mm round-trip.
 *
 * `axisMode: "z"` zeroes dx/dy so only depth previews (matches commit).
 */
export function computeDragPreviewOffsetPx(args: {
  deltaScreenPxX: number;
  deltaScreenPxY: number;
  zoom: number;
  rotateXDeg?: number;
  rotateYDeg?: number;
  axisMode?: "xy" | "z";
}): DragPreviewOffsetPx {
  const local = screenDeltaToLocalPx(args);
  if (args.axisMode === "z") {
    return { dxPx: 0, dyPx: 0, dzPx: local.dzPx };
  }
  return local;
}
