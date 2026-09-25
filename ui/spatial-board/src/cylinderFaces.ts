/**
 * Taller CSS cylinder faces B1 (`B1-geometry-taller-css-cylinder-faces`)
 * — the cylinder layout `Solid3D` already ships (2 disk-caps + 16 flat
 * side slats), locked into a pure, testable helper. Same fix, same
 * class of bug, as `cuboidFaces.ts`'s own box faces (frozen, unchanged
 * by this Buy).
 *
 * Root cause this fixes: each cap is a `D x D` circle (`.sb-solid__disk-face`)
 * that used to sit at `left: 0; top: 0` — correct only when the wrapper's
 * own height `H` equals `D` (a cube-like cylinder). `transform-origin:
 * 50% 50%` (the CSS default, never overridden) pivots each cap about ITS
 * OWN center, not the wrapper's mid-height. When `H` is much smaller
 * than `D` (a short prop hub) or much larger (a tall standoff-shaped
 * post), that pivot sits far from the true cylinder center and
 * `translateY(+-H/2) rotateX(...)` only nudges the cap a tiny axial step
 * from the wrong point — the cap swings out instead of capping the body.
 *
 * Fix: center each cap inside the `D x H` wrapper first (`left: (D-D)/2
 * = 0`, `top: (H-D)/2` — negative when `H < D`, exactly like a cuboid's
 * `top`/`bottom` face), THEN rotate about that now-centered origin, THEN
 * `translateZ(H/2)` (never `translateY` again after centering — that
 * would double-move the same axial step). The 16 side slats already
 * re-centered horizontally before this Buy (`left: (D - chord) / 2`,
 * `chord` = the regular-16-gon inscribed chord length) — that part of
 * the construction was already correct and is reused unchanged here,
 * just relocated into this helper alongside the now-fixed caps.
 *
 * Still exactly 2 `.sb-solid__disk-face` caps and 16 `.sb-solid__face`
 * slats — no 17th face, no invented diameter or height, N=16 frozen.
 *
 * Visor cylinder != CAD != fit != extra parts != round metal != a
 * standoff hole pattern. `cuboidFaces.ts` and the disk (single-face,
 * no axial extent) branch are untouched by this Buy.
 */

const CYLINDER_SIDE_SEGMENTS = 16;

export type CylinderCapName = "top" | "bottom";

export type CylinderCapLayout = {
  name: CylinderCapName;
  width: number;
  height: number;
  left: number;
  top: number;
  transform: string;
};

export type CylinderSlatLayout = {
  index: number;
  width: number;
  height: number;
  left: number;
  top: number;
  transform: string;
};

export type CylinderSolidLayout = {
  caps: CylinderCapLayout[];
  slats: CylinderSlatLayout[];
};

/**
 * `diameterPx`/`heightPx` are already in px (post `mmToPx`), matching
 * `Solid3D`'s own `{x: diameterPx, z: heightPx} = solidExtentPx(geometry)`
 * cylinder read. Pure — no DOM, no React, testable head-on with vitest.
 */
export function cylinderSolidLayout(diameterPx: number, heightPx: number): CylinderSolidLayout {
  const capTop = (heightPx - diameterPx) / 2;
  const capTranslateZ = heightPx / 2;
  const caps: CylinderCapLayout[] = [
    { name: "top", width: diameterPx, height: diameterPx, left: 0, top: capTop, transform: `rotateX(90deg) translateZ(${capTranslateZ}px)` },
    { name: "bottom", width: diameterPx, height: diameterPx, left: 0, top: capTop, transform: `rotateX(-90deg) translateZ(${capTranslateZ}px)` },
  ];

  const radiusPx = diameterPx / 2;
  const angleStep = 360 / CYLINDER_SIDE_SEGMENTS;
  // Chord length for a regular N-gon inscribed at this radius — an
  // honest flat-panel approximation of the curved side, never a claim
  // of a perfectly round surface.
  const chordPx = 2 * radiusPx * Math.sin(Math.PI / CYLINDER_SIDE_SEGMENTS);
  // A slat's own width (the ring chord) is far narrower than the
  // cylinder-body wrapper, so — like the caps above — it must be
  // explicitly re-centered horizontally before the ring transform below.
  const slatLeft = (diameterPx - chordPx) / 2;
  const slats: CylinderSlatLayout[] = Array.from({ length: CYLINDER_SIDE_SEGMENTS }, (_, i) => ({
    index: i,
    width: chordPx,
    height: heightPx,
    left: slatLeft,
    top: 0,
    transform: `rotateY(${i * angleStep}deg) translateZ(${radiusPx}px)`,
  }));

  return { caps, slats };
}
