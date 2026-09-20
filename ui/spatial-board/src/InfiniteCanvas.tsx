import { useCallback, useEffect, useRef, useState } from "react";
import { nextSelectedId, reconcileSelection } from "./boardSelection";
import { resolveInitialViewMode, viewModeStorageKey, type BoardViewMode } from "./boardViewMode";
import { ZOOM } from "./constants";
import { InspectorDock } from "./InspectorDock";
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
  const { nodes, preview, commit, refetch, loading, error: nodesError } = useBoardNodes(projectId);
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
  // Grafo-tab only (IC §2.1/§2.7) — Taller always shows its own Scene3D.
  const [show3DOverride, setShow3DOverride] = useState<boolean | null>(null);
  const hasGeometry = nodes.some((n) => n.geometry);
  const show3D = show3DOverride ?? hasGeometry;

  // Board 3D-first workshop + mount-chain inspector B1 — two tabs, Taller
  // (3D-first, default) and Grafo (today's card graph). Presentation-only,
  // persisted per-project in localStorage (never ProjectState) — same tier
  // as the card-layout overlay `useBoardNodes.ts` already persists there.
  // Default before a project is known is "taller" (IC lock #2); once
  // `projectId` resolves, re-derive from that project's own stored value
  // (mirrors `useBoardNodes`'s own per-project overlay read).
  const [viewMode, setViewModeState] = useState<BoardViewMode>("taller");
  useEffect(() => {
    if (!projectId) return;
    let stored: string | null = null;
    try {
      stored = localStorage.getItem(viewModeStorageKey(projectId));
    } catch {
      stored = null;
    }
    setViewModeState(resolveInitialViewMode(stored));
  }, [projectId]);
  const setViewMode = useCallback(
    (next: BoardViewMode) => {
      setViewModeState(next);
      try {
        localStorage.setItem(viewModeStorageKey(projectId), next);
      } catch {
        // Presentation-only preference — a storage failure (private mode,
        // quota) must never block the tab switch itself.
      }
    },
    [projectId],
  );
  // Situar B1, lifted out of Scene3D (IC §2.6) — the parent needs to know
  // whether Situar is ON to decide whether to render the Taller inspector
  // dock at all. Shared across both tabs (one Scene3D concept, not two
  // independent toggles) — reset whenever the project changes, same as
  // selection, so it never leaks a stale mode into a freshly-opened project.
  const [situar, setSituar] = useState(false);
  useEffect(() => {
    setSituar(false);
  }, [projectId]);
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
          {viewMode === "grafo" && hasGeometry ? (
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
      <div className="sb-tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={viewMode === "taller"}
          className={`sb-tab${viewMode === "taller" ? " sb-tab--active" : ""}`}
          onClick={() => setViewMode("taller")}
        >
          Taller 3D
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={viewMode === "grafo"}
          className={`sb-tab${viewMode === "grafo" ? " sb-tab--active" : ""}`}
          onClick={() => setViewMode("grafo")}
        >
          Grafo
        </button>
      </div>
      {viewMode === "taller" ? (
        <div className="sb-taller">
          <Scene3D
            nodes={nodes}
            selectedId={selectedId}
            onSelect={onSelect}
            projectId={projectId}
            onPoseCommitted={refetch}
            situar={situar}
            onSituarChange={setSituar}
            primary
          />
          {!situar ? (
            <InspectorDock nodes={nodes} selectedId={selectedId} onSelect={onSelect} />
          ) : null}
        </div>
      ) : null}
      <div
        ref={boardRef}
        className="sb-viewport"
        hidden={viewMode !== "grafo"}
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
      {viewMode === "grafo" && show3D ? (
        <Scene3D
          nodes={nodes}
          selectedId={selectedId}
          onSelect={onSelect}
          projectId={projectId}
          onPoseCommitted={refetch}
          situar={situar}
          onSituarChange={setSituar}
        />
      ) : null}
    </div>
  );
}
