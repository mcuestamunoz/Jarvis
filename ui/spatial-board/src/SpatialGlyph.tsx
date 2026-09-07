import { GLYPH } from "./constants";
import type { SpatialGeometry } from "./types";

type Props = {
  geometry: SpatialGeometry;
};

/** Fixed mm→px scale (not viewport-relative) so every glyph on the Board
 * stays proportionally correct relative to every other glyph — a 5" prop
 * and a 44mm FC board must look proportionally right next to each other. */
function scaled(mm: number): number {
  return Math.min(mm * GLYPH.pxPerMm, GLYPH.maxPx);
}

function formatMm(value: number): string {
  return Number.isInteger(value) ? `${value}` : value.toFixed(1);
}

/**
 * Board glyphs (Geometry Progression Lock B1, `visualizar`) — draws the
 * declarative shape the projector already decided (`box` or `disk`).
 * Purely presentational: no pose, no fit, no comparison against any other
 * node. Absence of `geometry` on a node means "no glyph," handled by the
 * caller (`SpatialCard`) never rendering this component at all — this
 * component never invents a shape for missing dims.
 */
export function SpatialGlyph({ geometry }: Props) {
  if (geometry.shape === "box") {
    return (
      <div className="sb-glyph sb-glyph--box">
        <div
          className="sb-glyph__box"
          aria-hidden="true"
          style={{
            width: scaled(geometry.length_mm),
            height: scaled(geometry.width_mm),
          }}
        />
        <span className="sb-glyph__caption">
          {formatMm(geometry.length_mm)}×{formatMm(geometry.width_mm)}×
          {formatMm(geometry.height_mm)} mm
        </span>
      </div>
    );
  }

  const sizePx = scaled(geometry.diameter_mm);
  return (
    <div className="sb-glyph sb-glyph--disk">
      <div className="sb-glyph__disk" aria-hidden="true" style={{ width: sizePx, height: sizePx }} />
      <span className="sb-glyph__caption">Ø {formatMm(geometry.diameter_mm)} mm</span>
    </div>
  );
}
