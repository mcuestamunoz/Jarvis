import { useCallback, useState } from "react";
import { applyPan, applyZoomToPoint, fitToScreen, getContentBounds } from "./transform";
import type { CanvasTransform, Point, SpatialRect, ViewportSize } from "./types";

const identity: CanvasTransform = { zoom: 1, panX: 0, panY: 0 };

export function useCanvasTransform() {
  const [transform, setTransform] = useState<CanvasTransform>(identity);

  const zoomToPoint = useCallback((screen: Point, nextZoom: number) => {
    setTransform((t) => applyZoomToPoint(t, screen, nextZoom));
  }, []);

  const panBy = useCallback((dx: number, dy: number) => {
    setTransform((t) => applyPan(t, dx, dy));
  }, []);

  const reset = useCallback(() => setTransform(identity), []);

  const fit = useCallback((rects: SpatialRect[], viewport: ViewportSize) => {
    setTransform(fitToScreen(getContentBounds(rects), viewport));
  }, []);

  const css = `scale(${transform.zoom}) translate(${transform.panX}px, ${transform.panY}px)`;

  return { transform, setTransform, zoomToPoint, panBy, reset, fit, css };
}
