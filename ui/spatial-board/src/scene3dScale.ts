import type { SpatialGeometry } from "./types";

/**
 * Board 3D solids B1 — a genuinely LINEAR mm->px scale, deliberately
 * separate from `constants.ts`'s `GLYPH` (which caps at `maxPx` so a 2D
 * glyph fits inside a small, fixed-size card body). That cap breaks
 * proportionality above 240mm and must never leak into a "declared scale"
 * 3D claim — a 127mm propeller and a 50mm ESC must stay proportional to
 * each other here, uncapped. The 3D scene's own zoom (not a per-object
 * clamp) is what lets the user see everything.
 */
export const SCENE3D = { pxPerMm: 0.5 } as const;

export function mmToPx(mm: number, pxPerMm: number = SCENE3D.pxPerMm): number {
  return mm * pxPerMm;
}

/**
 * Board drag → Continuity pose B1 — the inverse of `mmToPx`, so a drag
 * gesture can turn a world-px delta back into declared mm.
 *
 * Board Situar free camera B1: originally valid ONLY in the untilted
 * "situar" camera (`rotateX: 0, rotateY: 0`), where the world transform is
 * a pure 2D scale+translate and a screen-px delta maps linearly to a
 * world-px delta with no rotation/perspective distortion to invert. The
 * Engineer's free-camera ask means this is now used at ANY tilt too — an
 * accepted, documented ORTHOGRAPHIC-STYLE APPROXIMATION (see
 * `boardPoseDrag.ts`'s own module doc), not a true perspective
 * unprojection.
 */
export function pxToMm(px: number, pxPerMm: number = SCENE3D.pxPerMm): number {
  return px / pxPerMm;
}

/**
 * Situar UX B1 — widened from the original 0.5–2 cap so the Engineer can
 * actually zoom in enough to place small parts (adapters, standoffs)
 * precisely. `pxToMm`/`computeDragPosePayload` already read the LIVE
 * `zoom` value, so widening this range needed no change to the drag math
 * itself — only to how far `onWheel` is allowed to push it.
 */
export const ZOOM_MIN = 0.25;
export const ZOOM_MAX = 4;

export function clampZoom(zoom: number, min: number = ZOOM_MIN, max: number = ZOOM_MAX): number {
  return Math.min(max, Math.max(min, zoom));
}

export type SolidExtentPx = { x: number; y: number; z: number };

/**
 * Display-axis extent of a solid, in px, at the given scale.
 * Box: length_mm -> x, width_mm -> y, height_mm -> z (a visor display
 * convention only, not a CAD/body reference frame — no pose implied).
 * Cylinder (Disk axial Visor B1, `B1-disk-axial-visor`): diameter_mm ->
 * x and y (its circular footprint), height_mm -> z — the ONE cited axial
 * fact the projector already gated on (Motor `height_mm` or Propeller
 * `hub_thickness_mm`; see `_geometry_from_spec`), never invented here.
 * Disk: diameter_mm -> x and y (its footprint), z is ALWAYS 0 — a disk
 * has no cited axial extent at all (that's exactly what makes it a disk
 * and not a cylinder; see `_geometry_from_spec`), so there is nothing to
 * invent even by accident.
 */
export function solidExtentPx(
  geometry: SpatialGeometry,
  pxPerMm: number = SCENE3D.pxPerMm,
): SolidExtentPx {
  if (geometry.shape === "box") {
    return {
      x: mmToPx(geometry.length_mm, pxPerMm),
      y: mmToPx(geometry.width_mm, pxPerMm),
      z: mmToPx(geometry.height_mm, pxPerMm),
    };
  }
  if (geometry.shape === "cylinder") {
    const d = mmToPx(geometry.diameter_mm, pxPerMm);
    return { x: d, y: d, z: mmToPx(geometry.height_mm, pxPerMm) };
  }
  const d = mmToPx(geometry.diameter_mm, pxPerMm);
  return { x: d, y: d, z: 0 };
}

export type SolidWrapperPx = { width: number; height: number };

/**
 * Scene3D-from-pose B1 — the on-screen footprint of a solid's OUTER wrapper
 * div, in px: `Solid3D`'s box wrapper is `{width: extent.x, height: extent.z}`
 * (CSS width = declared length/+X, CSS height = declared height/+Z — the
 * depth/+Y axis lives entirely in `translateZ`, never in the wrapper's own
 * box). Disk axial Visor B1: a cylinder wrapper uses the SAME formula as a
 * box — `{width: extent.x, height: extent.z}` — since it also stands with
 * its axial extent along the declared +Z/screen-vertical axis (diameter on
 * X, cited height on screen height), never the disk-style square wrapper.
 * A disk wrapper is `{width: extent.x, height: extent.x}` — its own CSS
 * height/width are both the diameter (see `Solid3D`'s disk branch); never
 * `extent.z`, which is always 0 for a disk and is not its on-screen height
 * at all.
 */
export function solidWrapperPx(
  geometry: SpatialGeometry,
  pxPerMm: number = SCENE3D.pxPerMm,
): SolidWrapperPx {
  const extent = solidExtentPx(geometry, pxPerMm);
  if (geometry.shape === "box" || geometry.shape === "cylinder") {
    return { width: extent.x, height: extent.z };
  }
  return { width: extent.x, height: extent.x };
}
