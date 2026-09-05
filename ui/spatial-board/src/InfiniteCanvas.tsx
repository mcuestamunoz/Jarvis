import { useCallback, useEffect, useRef, useState } from "react";
import { ZOOM } from "./constants";
import { Minimap } from "./Minimap";
import { SpatialCard } from "./SpatialCard";
import { ProjectSwitcher } from "./ProjectSwitcher";
import { useBoardNodes } from "./useBoardNodes";
import { useCanvasTransform } from "./useCanvasTransform";
import { useProjects } from "./useProjects";
import type { SpatialNode } from "./types";

function shouldIgnorePan(target: EventTarget | null): boolean {
  if (!(target instanceof Element)) return false;
  return Boolean(
    target.closest("[data-node-id]") ||
      target.closest(".sb-handle") ||
      target.closest("button") ||
      target.closest(".sb-minimap") ||
      target.closest(".sb-toolbar") ||
      target.closest("select"),
  );
}

export function InfiniteCanvas() {
  const boardRef = useRef<HTMLDivElement>(null);
  const { projects, current, projectId, select, error } = useProjects();
  const { nodes, preview, commit, loading, error: nodesError } = useBoardNodes(projectId);
  const { transform, setTransform, zoomToPoint, reset, fit, css } =
    useCanvasTransform();
  const [viewport, setViewport] = useState({ width: 800, height: 600 });
  const panRef = useRef<{
    mouseX: number;
    mouseY: number;
    panX: number;
    panY: number;
  } | null>(null);
  const transformRef = useRef(transform);
  transformRef.current = transform;

  useEffect(() => {
    const el = boardRef.current;
    if (!el) return;
    const measure = () => {
      const r = el.getBoundingClientRect();
      setViewport({ width: r.width, height: r.height });
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    const el = boardRef.current;
    if (!el) return;
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      const rect = el.getBoundingClientRect();
      const screen = {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      };
      const factor = event.ctrlKey || event.metaKey ? 1.3 : ZOOM.step;
      const t = transformRef.current;
      const next = event.deltaY > 0 ? t.zoom / factor : t.zoom * factor;
      zoomToPoint(screen, next);
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, [zoomToPoint]);

  const onPanMove = useCallback((event: MouseEvent) => {
    const p = panRef.current;
    if (!p) return;
    const t = transformRef.current;
    const dx = event.clientX - p.mouseX;
    const dy = event.clientY - p.mouseY;
    setTransform({
      ...t,
      panX: p.panX + dx / t.zoom,
      panY: p.panY + dy / t.zoom,
    });
  }, [setTransform]);

  const onPanEnd = useCallback(() => {
    panRef.current = null;
    document.removeEventListener("mousemove", onPanMove);
    document.removeEventListener("mouseup", onPanEnd);
    document.body.style.userSelect = "";
  }, [onPanMove]);

  const onPanStart = (event: React.MouseEvent) => {
    if (event.button !== 0 || shouldIgnorePan(event.target)) return;
    event.preventDefault();
    panRef.current = {
      mouseX: event.clientX,
      mouseY: event.clientY,
      panX: transform.panX,
      panY: transform.panY,
    };
    document.body.style.userSelect = "none";
    document.addEventListener("mousemove", onPanMove);
    document.addEventListener("mouseup", onPanEnd);
  };

  const navigateKeepZoom = (worldX: number, worldY: number) => {
    const z = transform.zoom;
    setTransform({
      zoom: z,
      panX: viewport.width / 2 / z - worldX,
      panY: viewport.height / 2 / z - worldY,
    });
  };

  return (
    <div className="spatial-board">
      <header className="sb-toolbar">
        <ProjectSwitcher
          current={current}
          projects={projects}
          error={error}
          onSelect={select}
        />
        <div className="sb-toolbar__tools">
          <span>{Math.round(transform.zoom * 100)}%</span>
          <button type="button" onClick={() => fit(nodes, viewport)}>
            Encajar
          </button>
          <button type="button" onClick={reset}>
            100%
          </button>
        </div>
        <span className="sb-toolbar__hint">
          {nodesError
            ? "No se pudieron leer los componentes"
            : "rueda: zoom · arrastrar fondo: pan · card: mover · esquinas: tamaño"}
        </span>
      </header>
      <div
        ref={boardRef}
        className="sb-viewport"
        onMouseDown={onPanStart}
      >
        {!loading && !nodesError && nodes.length === 0 && projectId ? (
          <p className="sb-empty">Este proyecto no tiene componentes declarados</p>
        ) : null}
        <div className="sb-world" style={{ transform: css }}>
          {nodes.map((node: SpatialNode) => (
            <SpatialCard
              key={node.id}
              node={node}
              transform={transform}
              onPreview={preview}
              onCommit={commit}
            />
          ))}
        </div>
        <Minimap
          nodes={nodes}
          transform={transform}
          viewport={viewport}
          onNavigate={navigateKeepZoom}
        />
      </div>
    </div>
  );
}
