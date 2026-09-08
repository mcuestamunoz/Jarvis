import { useCallback, useEffect, useRef, useState } from "react";
import { nextSelectedId, reconcileSelection } from "./boardSelection";
import { ZOOM } from "./constants";
import { Minimap } from "./Minimap";
import { MountEdges } from "./DeclaredMountEdges";
import { Scene3D } from "./Scene3D";
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
  // Board click-inspect B1− — session-only selection highlight, never
  // persisted (no localStorage/URL/ProjectState) and never a second
  // selection model: all transitions route through boardSelection.ts.
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const onSelect = useCallback((id: string) => {
    setSelectedId((cur) => nextSelectedId(cur, { type: "select", id }));
  }, []);
  // Board 3D solids B1 — session-only toggle. `null` = no explicit user
  // choice yet -> default to shown iff any live node has `geometry`; once
  // the user toggles, that explicit choice is respected across re-fetches.
  const [show3DOverride, setShow3DOverride] = useState<boolean | null>(null);
  const hasGeometry = nodes.some((n) => n.geometry);
  const show3D = show3DOverride ?? hasGeometry;
  const panRef = useRef<{
    mouseX: number;
    mouseY: number;
    panX: number;
    panY: number;
  } | null>(null);
  const transformRef = useRef(transform);
  transformRef.current = transform;

  // Board click-inspect B1− — Escape clears selection, unless focus is in
  // the toolbar's project <select> (its own native Escape behavior — a
  // dropdown-close keypress must not also wipe an unrelated board selection).
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (event.target instanceof Element && event.target.closest("select")) return;
      setSelectedId((cur) => nextSelectedId(cur, { type: "clear" }));
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);

  // Switching projects always clears selection — a selected id never
  // survives across projects (the ids aren't even comparable).
  useEffect(() => {
    setSelectedId((cur) => nextSelectedId(cur, { type: "clear" }));
  }, [projectId]);

  // A fresh projector read may no longer include the selected node (renamed,
  // removed, or project reloaded) — drop a selection that's gone stale.
  useEffect(() => {
    setSelectedId((cur) => reconcileSelection(cur, nodes.map((n) => n.id)));
  }, [nodes]);

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
    setSelectedId((cur) => nextSelectedId(cur, { type: "clear" }));
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
          {hasGeometry ? (
            <button type="button" onClick={() => setShow3DOverride(!show3D)}>
              {show3D ? "Ocultar 3D" : "Mostrar 3D"}
            </button>
          ) : null}
        </div>
        <span className="sb-toolbar__hint">
          {nodesError
            ? "No se pudieron leer los componentes"
            : `rueda: zoom · arrastrar fondo: pan · card: mover · esquinas: tamaño · click: seleccionar${show3D ? " · 3D: arrastrar vista" : ""}`}
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
          <MountEdges nodes={nodes} />
          {nodes.map((node: SpatialNode) => (
            <SpatialCard
              key={node.id}
              node={node}
              transform={transform}
              selected={node.id === selectedId}
              onSelect={onSelect}
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
      {show3D ? <Scene3D nodes={nodes} selectedId={selectedId} onSelect={onSelect} /> : null}
    </div>
  );
}
