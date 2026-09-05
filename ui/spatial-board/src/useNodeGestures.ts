import { useCallback, useEffect, useRef } from "react";
import { CARD, WORLD } from "./constants";
import { screenToWorldDelta } from "./transform";
import type { CanvasTransform, ResizeHandle, SpatialNode } from "./types";

function clampPos(n: number): number {
  return Math.max(-WORLD.maxAbs, Math.min(WORLD.maxAbs, n));
}

export function useNodeGestures(
  node: SpatialNode,
  transform: CanvasTransform,
  onPreview: (id: string, patch: Partial<SpatialNode>) => void,
  onCommit: (id: string, patch: Partial<SpatialNode>) => void,
) {
  const nodeRef = useRef(node);
  nodeRef.current = node;
  const transformRef = useRef(transform);
  transformRef.current = transform;

  const drag = useRef<{
    mouseX: number;
    mouseY: number;
    x: number;
    y: number;
    moved: boolean;
  } | null>(null);

  const resize = useRef<{
    handle: ResizeHandle;
    mouseX: number;
    mouseY: number;
    x: number;
    y: number;
    w: number;
    h: number;
    moved: boolean;
  } | null>(null);

  const lastPatch = useRef<Partial<SpatialNode>>({});

  const onMove = useCallback(
    (event: MouseEvent) => {
      const t = transformRef.current;
      const n = nodeRef.current;
      if (drag.current) {
        const dx = event.clientX - drag.current.mouseX;
        const dy = event.clientY - drag.current.mouseY;
        if (!drag.current.moved && Math.abs(dx) < 3 && Math.abs(dy) < 3) return;
        drag.current.moved = true;
        const world = screenToWorldDelta(dx, dy, t);
        const patch = {
          x: clampPos(drag.current.x + world.x),
          y: clampPos(drag.current.y + world.y),
        };
        lastPatch.current = patch;
        onPreview(n.id, patch);
        return;
      }
      if (resize.current) {
        const dx = event.clientX - resize.current.mouseX;
        const dy = event.clientY - resize.current.mouseY;
        if (!resize.current.moved && Math.hypot(dx, dy) < 3) return;
        resize.current.moved = true;
        const world = screenToWorldDelta(dx, dy, t);
        const { handle, x, y, w, h } = resize.current;
        let next = { x, y, width: w, height: h };
        if (handle === "se") {
          next = { x, y, width: w + world.x, height: h + world.y };
        } else if (handle === "ne") {
          next = { x, y: y + world.y, width: w + world.x, height: h - world.y };
        } else if (handle === "sw") {
          next = { x: x + world.x, y, width: w - world.x, height: h + world.y };
        } else {
          next = {
            x: x + world.x,
            y: y + world.y,
            width: w - world.x,
            height: h - world.y,
          };
        }
        next.width = Math.max(CARD.minWidth, next.width);
        next.height = Math.max(CARD.minHeight, next.height);
        next.x = clampPos(next.x);
        next.y = clampPos(next.y);
        lastPatch.current = next;
        onPreview(n.id, next);
      }
    },
    [onPreview],
  );

  const onUp = useCallback(() => {
    const n = nodeRef.current;
    const d = drag.current;
    const r = resize.current;
    drag.current = null;
    resize.current = null;
    document.removeEventListener("mousemove", onMove);
    document.removeEventListener("mouseup", onUp);
    document.body.style.userSelect = "";
    if ((d?.moved || r?.moved) && lastPatch.current) {
      onCommit(n.id, lastPatch.current);
    }
    lastPatch.current = {};
  }, [onCommit, onMove]);

  useEffect(() => () => {
    document.removeEventListener("mousemove", onMove);
    document.removeEventListener("mouseup", onUp);
  }, [onMove, onUp]);

  const startDrag = useCallback(
    (event: React.MouseEvent) => {
      if (event.button !== 0) return;
      event.preventDefault();
      event.stopPropagation();
      const n = nodeRef.current;
      drag.current = {
        mouseX: event.clientX,
        mouseY: event.clientY,
        x: n.x,
        y: n.y,
        moved: false,
      };
      document.body.style.userSelect = "none";
      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    },
    [onMove, onUp],
  );

  const startResize = useCallback(
    (event: React.MouseEvent, handle: ResizeHandle) => {
      if (event.button !== 0) return;
      event.preventDefault();
      event.stopPropagation();
      const n = nodeRef.current;
      resize.current = {
        handle,
        mouseX: event.clientX,
        mouseY: event.clientY,
        x: n.x,
        y: n.y,
        w: n.width,
        h: n.height,
        moved: false,
      };
      document.body.style.userSelect = "none";
      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    },
    [onMove, onUp],
  );

  return { startDrag, startResize };
}
