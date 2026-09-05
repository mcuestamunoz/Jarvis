import { ZOOM } from "./constants";
import type {
  CanvasTransform,
  ContentBounds,
  Point,
  SpatialRect,
  ViewportSize,
} from "./types";

export function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

export function worldToScreen(
  world: Point,
  t: CanvasTransform,
): Point {
  return {
    x: (world.x + t.panX) * t.zoom,
    y: (world.y + t.panY) * t.zoom,
  };
}

export function screenToWorld(
  screen: Point,
  t: CanvasTransform,
): Point {
  return {
    x: screen.x / t.zoom - t.panX,
    y: screen.y / t.zoom - t.panY,
  };
}

export function screenToWorldDelta(
  dx: number,
  dy: number,
  t: CanvasTransform,
): Point {
  return { x: dx / t.zoom, y: dy / t.zoom };
}

/** Q1: zoom so `screen` stays over the same world point. */
export function applyZoomToPoint(
  t: CanvasTransform,
  screen: Point,
  nextZoom: number,
): CanvasTransform {
  const zoom = clamp(nextZoom, ZOOM.min, ZOOM.max);
  const world = screenToWorld(screen, t);
  return {
    zoom,
    panX: screen.x / zoom - world.x,
    panY: screen.y / zoom - world.y,
  };
}

export function applyPan(
  t: CanvasTransform,
  screenDeltaX: number,
  screenDeltaY: number,
): CanvasTransform {
  const d = screenToWorldDelta(screenDeltaX, screenDeltaY, t);
  return { ...t, panX: t.panX + d.x, panY: t.panY + d.y };
}

export function getContentBounds(
  rects: SpatialRect[],
  padding = 50,
): ContentBounds {
  if (rects.length === 0) {
    return { minX: 0, minY: 0, maxX: 0, maxY: 0, width: 0, height: 0 };
  }
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const r of rects) {
    minX = Math.min(minX, r.x);
    minY = Math.min(minY, r.y);
    maxX = Math.max(maxX, r.x + r.width);
    maxY = Math.max(maxY, r.y + r.height);
  }
  minX -= padding;
  minY -= padding;
  maxX += padding;
  maxY += padding;
  return { minX, minY, maxX, maxY, width: maxX - minX, height: maxY - minY };
}

export function fitToScreen(
  bounds: ContentBounds,
  viewport: ViewportSize,
  padding = 50,
): CanvasTransform {
  if (bounds.width <= 0 || bounds.height <= 0) {
    return { zoom: 1, panX: 0, panY: 0 };
  }
  const availableW = Math.max(1, viewport.width - padding * 2);
  const availableH = Math.max(1, viewport.height - padding * 2);
  const zoom = clamp(
    Math.min(availableW / bounds.width, availableH / bounds.height, 1),
    ZOOM.min,
    ZOOM.max,
  );
  const cx = bounds.minX + bounds.width / 2;
  const cy = bounds.minY + bounds.height / 2;
  return {
    zoom,
    panX: viewport.width / 2 / zoom - cx,
    panY: viewport.height / 2 / zoom - cy,
  };
}

export function viewportWorldRect(
  t: CanvasTransform,
  viewport: ViewportSize,
): SpatialRect {
  const tl = screenToWorld({ x: 0, y: 0 }, t);
  const br = screenToWorld({ x: viewport.width, y: viewport.height }, t);
  return {
    x: tl.x,
    y: tl.y,
    width: br.x - tl.x,
    height: br.y - tl.y,
  };
}
