export const ZOOM = {
  min: 0.1,
  max: 5,
  default: 1,
  step: 1.1,
} as const;

export const CARD = {
  minWidth: 180,
  minHeight: 120,
  defaultWidth: 280,
  defaultHeight: 200,
} as const;

export const WORLD = {
  maxAbs: 50_000,
} as const;

export const MINIMAP = {
  width: 200,
  height: 150,
} as const;

export const LAYOUT_KEY = "jarvis.spatial-board.layout.v1";
export const PROJECT_KEY = "jarvis.spatial-board.project.v1";

// Board glyphs (Geometry Progression Lock B1, `visualizar`). A fixed
// mm→px scale (not viewport-relative) so every glyph on screen — a 5"
// prop, a 44mm FC — stays proportionally correct relative to every other
// glyph. Chosen so a 200mm edge (a large-ish battery/frame part) renders
// at ~100 CSS px: readable inside a card without dominating it.
export const GLYPH = {
  pxPerMm: 0.5,
  maxPx: 120,
} as const;
