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
};

/**
 * Board 3D solids B1 — an honest CSS 3D presentation of the projector's
 * `geometry` DTO. Box: a real six-face cuboid from the sourced L×W×H
 * triple. Disk: ONE flat circular face at the sourced diameter — never a
 * cylinder, never a translateZ'd second face, never an invented thickness.
 * A disk has no height key in the DTO at all (see `_geometry_from_spec`);
 * this component has nothing to misuse into a fake axial extent even by
 * accident.
 */
export function Solid3D({ id, geometry, selected, onSelect, originX = 0, originY = 0, originZ = 0 }: Props) {
  const extent = solidExtentPx(geometry);

  const handleMouseDown = (event: React.MouseEvent) => {
    event.stopPropagation();
    onSelect(id);
  };

  if (geometry.shape === "box") {
    const { x: w, y: d, z: h } = extent;
    return (
      <div
        className={`sb-solid sb-solid--box${selected ? " sb-solid--selected" : ""}`}
        data-node-id={id}
        aria-current={selected ? "true" : undefined}
        onMouseDown={handleMouseDown}
        style={{ transform: `translate3d(${originX}px, ${originY}px, ${originZ}px)`, width: w, height: h }}
      >
        <div className="sb-solid__cuboid" style={{ width: w, height: h }}>
          <div className="sb-solid__face sb-solid__face--front" style={{ width: w, height: h, transform: `translateZ(${d / 2}px)` }} />
          <div className="sb-solid__face sb-solid__face--back" style={{ width: w, height: h, transform: `translateZ(${-d / 2}px) rotateY(180deg)` }} />
          <div className="sb-solid__face sb-solid__face--left" style={{ width: d, height: h, transform: `translateX(${-w / 2}px) rotateY(-90deg)` }} />
          <div className="sb-solid__face sb-solid__face--right" style={{ width: d, height: h, transform: `translateX(${w / 2}px) rotateY(90deg)` }} />
          <div className="sb-solid__face sb-solid__face--top" style={{ width: w, height: d, transform: `translateY(${-h / 2}px) rotateX(90deg)` }} />
          <div className="sb-solid__face sb-solid__face--bottom" style={{ width: w, height: d, transform: `translateY(${h / 2}px) rotateX(-90deg)` }} />
        </div>
      </div>
    );
  }

  const size = extent.x;
  return (
    <div
      className={`sb-solid sb-solid--disk${selected ? " sb-solid--selected" : ""}`}
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
