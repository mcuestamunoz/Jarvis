export type Point = { x: number; y: number };

export type CanvasTransform = {
  zoom: number;
  panX: number;
  panY: number;
};

export type SpatialRect = {
  x: number;
  y: number;
  width: number;
  height: number;
};

/**
 * Board glyphs (Geometry Progression Lock B1, `visualizar`) — a
 * declarative 2D shape hint computed server-side by the projector from
 * dimensions already declared/sourced. Never present on `kind: "slot"`
 * nodes. Independent of `SpatialRect.width`/`height`, which stay the
 * card's on-canvas pixel layout (drag/resize state) — never physical mm.
 */
export type SpatialGeometry =
  | { shape: "box"; length_mm: number; width_mm: number; height_mm: number }
  | { shape: "disk"; diameter_mm: number };

export type SpatialNode = SpatialRect & {
  id: string;
  title: string;
  /** Declared identity shown above property rows (ComponentSpec.name). */
  declaredName: string;
  kind: "component" | "slot" | "part";
  fields: { label: string; value: string }[];
  /** Present only when the projector found sufficient declared dims. */
  geometry?: SpatialGeometry;
};

export type ContentBounds = {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  width: number;
  height: number;
};

export type ViewportSize = { width: number; height: number };

export type ResizeHandle = "nw" | "ne" | "sw" | "se";
