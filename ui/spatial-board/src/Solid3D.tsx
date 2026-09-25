import { cuboidFaceLayout } from "./cuboidFaces";
import { cylinderSolidLayout } from "./cylinderFaces";
import { solidExtentPx } from "./scene3dScale";
import type { SpatialGeometry } from "./types";

type Props = {
  id: string;
  geometry: SpatialGeometry;
  selected: boolean;
  onSelect: (id: string) => void;
  originX?: number;
  originY?: number;
  originZ?: number;
  /**
   * Arm radial Visor B1 — degrees, rotates the box about its own center
   * so its declared-length axis (local `w`, CSS X) points along the
   * origin->station ray before the box is translated to `originX/Y/Z`.
   * `undefined`/disks never rotate. See the derivation comment on the
   * `rotateY` transform below for the sign convention.
   */
  yawDeg?: number;
  /** Board drag → Continuity pose B1 — situar mode only; undefined outside it. */
  draggable?: boolean;
  needsOrigin?: boolean;
  onDragStart?: (event: React.MouseEvent, id: string) => void;
  /**
   * Situar nested-hit hotfix: when Situar is ON and another solid is
   * already selected (usually from the 2D card), non-selected solids
   * must not steal pointer events — otherwise an outer/overlapping box
   * (FC, plate) captures the ESC forever.
   */
  pointerEventsNone?: boolean;
  /**
   * Board 3D-first workshop + mount-chain inspector B1 — true when this
   * solid is NOT on the selected piece's mount-ancestor chain (IC §2.4).
   * Presentation-only (CSS opacity); never changes hit-testing/selection
   * eligibility — a dimmed solid stays clickable.
   */
  dimmed?: boolean;
};

/**
 * Board 3D solids B1, extended by Disk axial Visor from cited dims B1
 * (`B1-disk-axial-visor`) — an honest CSS 3D presentation of the
 * projector's `geometry` DTO. Box: a real six-face cuboid from the
 * sourced L×W×H triple, laid out by `cuboidFaceLayout` (Taller CSS
 * cuboid faces B1). Cylinder: two circular caps (reusing the exact
 * `sb-solid__disk-face` style a flat disk already uses — a cap IS a disk
 * face) plus 16 flat side slats, laid out by `cylinderSolidLayout`
 * (Taller CSS cylinder faces B1) — all from the
 * sourced diameter + cited axial extent (`_geometry_from_spec`'s own
 * Motor `height_mm` / Propeller `hub_thickness_mm` gate) — never a
 * fabricated thickness. Disk: ONE flat circular face at the sourced
 * diameter — no axial extent at all (that is the projector's own gate for
 * staying a disk instead of a cylinder), so there is nothing to misuse
 * into a fake extent even by accident.
 */
export function Solid3D({
  id, geometry, selected, onSelect, originX = 0, originY = 0, originZ = 0, yawDeg,
  draggable = false, needsOrigin = false, onDragStart, pointerEventsNone = false,
  dimmed = false,
}: Props) {
  const extent = solidExtentPx(geometry);
  // Arm radial Visor B1 — declared +X (length) -> CSS X, declared +Y
  // (width) -> CSS Z/depth (module-level axis remap, see
  // scene3dLayout.ts). The projector's `yawDeg = atan2(station.y,
  // station.x)` is the declared angle a local +X unit vector must end up
  // pointing at. Per the CSS Transforms rotateY(a) matrix
  // (x' = cos(a)x + sin(a)z, z' = -sin(a)x + cos(a)z), a local (1,0,0)
  // lands at world (cos(a), 0, -sin(a)) — so `a = -yawDeg` is the angle
  // that makes it land at (cos(yawDeg), 0, sin(yawDeg)), matching the
  // declared (x, y) direction 1:1 (no negation elsewhere in the Y->Z
  // remap). Written as `translate3d(...) rotateY(...)` in the transform
  // string below — `rotateY` (rightmost) applies first, about the box's
  // own local center, and `translate3d` then moves the already-rotated
  // box to its world position, never rotating about the world origin.
  const rotateYDeg = yawDeg !== undefined ? -yawDeg : 0;

  const handleMouseDown = (event: React.MouseEvent) => {
    event.stopPropagation();
    onSelect(id);
    if (onDragStart) onDragStart(event, id);
  };

  const modifierClass =
    `${draggable ? " sb-solid--draggable" : ""}` +
    `${needsOrigin ? " sb-solid--needs-origin" : ""}` +
    `${pointerEventsNone ? " sb-solid--hit-through" : ""}` +
    `${dimmed ? " sb-solid--dimmed" : ""}`;

  if (geometry.shape === "box") {
    const { x: w, y: d, z: h } = extent;
    const faces = cuboidFaceLayout(w, d, h);
    return (
      <div
        className={`sb-solid sb-solid--box${selected ? " sb-solid--selected" : ""}${modifierClass}`}
        data-node-id={id}
        aria-current={selected ? "true" : undefined}
        onMouseDown={handleMouseDown}
        style={{
          transform: `translate3d(${originX}px, ${originY}px, ${originZ}px) rotateY(${rotateYDeg}deg)`,
          width: w, height: h,
        }}
      >
        <div className="sb-solid__cuboid" style={{ width: w, height: h }}>
          {faces.map((face) => (
            <div
              key={face.name}
              className={`sb-solid__face sb-solid__face--${face.name}`}
              style={{ width: face.width, height: face.height, left: face.left, top: face.top, transform: face.transform }}
            />
          ))}
        </div>
      </div>
    );
  }

  if (geometry.shape === "cylinder") {
    const diameterPx = extent.x;
    const heightPx = extent.z;
    const { caps, slats } = cylinderSolidLayout(diameterPx, heightPx);
    return (
      <div
        className={`sb-solid sb-solid--cylinder${selected ? " sb-solid--selected" : ""}${modifierClass}`}
        data-node-id={id}
        aria-current={selected ? "true" : undefined}
        onMouseDown={handleMouseDown}
        style={{
          transform: `translate3d(${originX}px, ${originY}px, ${originZ}px) rotateY(${rotateYDeg}deg)`,
          width: diameterPx, height: heightPx,
        }}
      >
        <div className="sb-solid__cylinder-body" style={{ width: diameterPx, height: heightPx }}>
          {caps.map((cap) => (
            <div
              key={cap.name}
              className="sb-solid__disk-face"
              style={{ width: cap.width, height: cap.height, left: cap.left, top: cap.top, transform: cap.transform }}
            />
          ))}
          {slats.map((slat) => (
            <div
              key={slat.index}
              className="sb-solid__face"
              style={{ width: slat.width, height: slat.height, left: slat.left, top: slat.top, transform: slat.transform }}
            />
          ))}
        </div>
      </div>
    );
  }

  const size = extent.x;
  return (
    <div
      className={`sb-solid sb-solid--disk${selected ? " sb-solid--selected" : ""}${modifierClass}`}
      data-node-id={id}
      aria-current={selected ? "true" : undefined}
      onMouseDown={handleMouseDown}
      style={{ transform: `translate3d(${originX}px, ${originY}px, ${originZ}px)`, width: size, height: size }}
    >
      <div
        className="sb-solid__disk-face"
        style={{ width: size, height: size, transform: "rotateX(90deg)" }}
      />
    </div>
  );
}
