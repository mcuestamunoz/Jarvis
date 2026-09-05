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

export type SpatialNode = SpatialRect & {
  id: string;
  title: string;
  /** Declared identity shown above property rows (ComponentSpec.name). */
  declaredName: string;
  kind: "component" | "slot" | "part";
  fields: { label: string; value: string }[];
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
