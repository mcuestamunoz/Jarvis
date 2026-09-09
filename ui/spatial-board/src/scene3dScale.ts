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

export type SolidExtentPx = { x: number; y: number; z: number };

/**
 * Display-axis extent of a solid, in px, at the given scale.
 * Box: length_mm -> x, width_mm -> y, height_mm -> z (a visor display
 * convention only, not a CAD/body reference frame — no pose implied).
 * Disk: diameter_mm -> x and y (its footprint), z is ALWAYS 0 — a disk is
 * a flat plane, never a cylinder; there is no sourced axial height to put
 * here (see Solid3D.tsx / _geometry_from_spec — the DTO itself carries no
 * height key for a disk, so there is nothing to invent even by accident).
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
  const d = mmToPx(geometry.diameter_mm, pxPerMm);
  return { x: d, y: d, z: 0 };
}

export type SolidWrapperPx = { width: number; height: number };

/**
 * Scene3D-from-pose B1 — the on-screen footprint of a solid's OUTER wrapper
 * div, in px: `Solid3D`'s box wrapper is `{width: extent.x, height: extent.z}`
 * (CSS width = declared length/+X, CSS height = declared height/+Z — the
 * depth/+Y axis lives entirely in `translateZ`, never in the wrapper's own
 * box). A disk wrapper is `{width: extent.x, height: extent.x}` — its own
 * CSS height/width are both the diameter (see `Solid3D`'s disk branch);
 * never `extent.z`, which is always 0 for a disk and is not its on-screen
 * height at all.
 */
export function solidWrapperPx(
  geometry: SpatialGeometry,
  pxPerMm: number = SCENE3D.pxPerMm,
): SolidWrapperPx {
  const extent = solidExtentPx(geometry, pxPerMm);
  if (geometry.shape === "box") {
    return { width: extent.x, height: extent.z };
  }
  return { width: extent.x, height: extent.x };
}
