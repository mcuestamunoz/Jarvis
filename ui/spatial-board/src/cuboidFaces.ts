/**
 * Taller CSS cuboid faces B1 (`B1-geometry-taller-css-cuboid-faces`) —
 * the six-face `box` layout `Solid3D` already ships, locked into a pure,
 * testable helper.
 *
 * Root cause this fixes: each face used to sit at `left: 0; top: 0`
 * (the `.sb-solid__face` CSS default) regardless of whether the face's
 * own width/height matched the cuboid wrapper's — `front`/`back` do (so
 * they were never wrong), but `left`/`right` (width `d`, not `w`) and
 * `top`/`bottom` (height `d`, not `h`) do not. `transform-origin: 50% 50%`
 * (the CSS default, never overridden) pivots each face about ITS OWN
 * center, not the wrapper's — a face flush against one edge instead of
 * centered rotates about the wrong point and swings out from the
 * cuboid's true corner, most visibly on a thin plate where `d` (or `h`)
 * is tiny next to `w`.
 *
 * Fix: center every face inside the `w x h` wrapper first (`left:
 * (w-fw)/2`, `top: (h-fh)/2`, where `fw`/`fh` are that face's own CSS
 * width/height), THEN rotate about that now-centered origin, THEN
 * `translateZ` by half the extent along that face's own normal. Six
 * `.sb-solid__face` nodes, same as before — no seventh face, no DOM
 * change beyond the `left`/`top`/`transform` values each one gets.
 *
 * Axis remap (unchanged, `scene3dScale.ts`'s own convention): `w` =
 * declared length/+X, `d` = declared width/+Y (the depth axis, never a
 * wrapper CSS dimension — it only appears inside `translateZ`), `h` =
 * declared height/+Z (the wrapper's own CSS height).
 *
 * Visor cuboid != CAD != fit != extra parts != a 2D card's own
 * `.sb-world` origin (a completely separate 2D-card concern, untouched
 * here).
 */

export type CuboidFaceName = "front" | "back" | "left" | "right" | "top" | "bottom";

export type CuboidFaceLayout = {
  name: CuboidFaceName;
  width: number;
  height: number;
  left: number;
  top: number;
  transform: string;
};

/**
 * `w`/`d`/`h` are already in px (post `mmToPx`), matching `Solid3D`'s
 * own `{x: w, y: d, z: h} = solidExtentPx(geometry)` destructure. Pure —
 * no DOM, no React, testable head-on with vitest.
 */
export function cuboidFaceLayout(w: number, d: number, h: number): CuboidFaceLayout[] {
  return [
    { name: "front", width: w, height: h, left: 0, top: 0, transform: `translateZ(${d / 2}px)` },
    { name: "back", width: w, height: h, left: 0, top: 0, transform: `rotateY(180deg) translateZ(${d / 2}px)` },
    { name: "left", width: d, height: h, left: (w - d) / 2, top: 0, transform: `rotateY(-90deg) translateZ(${w / 2}px)` },
    { name: "right", width: d, height: h, left: (w - d) / 2, top: 0, transform: `rotateY(90deg) translateZ(${w / 2}px)` },
    { name: "top", width: w, height: d, left: 0, top: (h - d) / 2, transform: `rotateX(90deg) translateZ(${h / 2}px)` },
    { name: "bottom", width: w, height: d, left: 0, top: (h - d) / 2, transform: `rotateX(-90deg) translateZ(${h / 2}px)` },
  ];
}
