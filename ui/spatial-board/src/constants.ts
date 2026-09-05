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
