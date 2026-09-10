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
  /**
   * Declared mount target key (Assembly Board edges B2). Present only when
   * `ComponentSpec.mounted_on` is set AND that target is still among projected
   * components — never inferred from card layout. Independent of the text
   * field `"montado en"` (which may still show a stale key).
   */
  mountedOn?: string;
  /**
   * Declared box-local pose (Scene3D-from-pose B1). Present only when
   * `ComponentSpec.declared_box_pose` is set AND its origin still resolves
   * to a `box`-shaped component among projected components — the same
   * "honest absence" gate as `mountedOn` above, never a looser one. Axis
   * units are millimetres, in the DECLARED frame (L->+X, W->+Y, H->+Z) —
   * not a CAD/body/gravity frame. Missing x/y/z counts as 0 for display.
   */
  declaredBoxPose?: { originKey: string; xMm?: number; yMm?: number; zMm?: number };
  /**
   * Motor visor copies (Motor visor copies from motor_count B1). Present
   * only on the `motors` node, only when it has `geometry` AND its own
   * `motor_count` property is a whole number in [2, 16] — never a default
   * of 4, never derived from `configuration`/`current_parameters`. Still
   * ONE `ComponentSpec`/card/BOM node; this only tells the 3D visor how
   * many solid copies to draw.
   */
  solidCopies?: number;
  /**
   * Visor X stations (Visor X stations from cited wheelbase B1). Present
   * only alongside `solidCopies === 4`, and only when the sibling `frame`
   * declares `configuration === "quad_x"` AND a finite positive
   * `wheelbase_mm` (motor-to-motor). Four declared-mm points (L->+X,
   * W->+Y, H->+Z; Z is 0 this Buy), length always matches `solidCopies`
   * when present. Absent (any other N, or a missing/wrong frame fact) ->
   * the visor keeps today's presentation row.
   */
  solidCopyOffsetsMm?: { xMm: number; yMm: number; zMm: number }[];
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
