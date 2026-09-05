import { useCallback, useEffect, useState } from "react";
import { LAYOUT_KEY } from "./constants";
import { fetchProjectNodes } from "./projects";
import type { SpatialNode } from "./types";

type LayoutMap = Record<string, { x: number; y: number; width: number; height: number }>;

function storageKey(projectId: string | null): string {
  return projectId ? `${LAYOUT_KEY}.${projectId}` : LAYOUT_KEY;
}

function loadOverlay(projectId: string | null): LayoutMap {
  try {
    const raw = localStorage.getItem(storageKey(projectId));
    if (!raw) return {};
    const parsed = JSON.parse(raw) as LayoutMap;
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function persist(projectId: string | null, nodes: SpatialNode[]): void {
  const overlay: LayoutMap = {};
  for (const n of nodes) {
    overlay[n.id] = { x: n.x, y: n.y, width: n.width, height: n.height };
  }
  localStorage.setItem(storageKey(projectId), JSON.stringify(overlay));
}

function applyOverlay(nodes: SpatialNode[], overlay: LayoutMap): SpatialNode[] {
  return nodes.map((n) => (overlay[n.id] ? { ...n, ...overlay[n.id] } : n));
}

export function useBoardNodes(projectId: string | null) {
  const [nodes, setNodes] = useState<SpatialNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) {
      setNodes([]);
      setError(null);
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    fetchProjectNodes(projectId)
      .then((incoming) => {
        if (cancelled) return;
        setNodes(applyOverlay(incoming, loadOverlay(projectId)));
        setError(null);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setNodes([]);
        setError(err instanceof Error ? err.message : "error");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const preview = useCallback((id: string, patch: Partial<SpatialNode>) => {
    setNodes((current) => current.map((n) => (n.id === id ? { ...n, ...patch } : n)));
  }, []);

  const commit = useCallback(
    (id: string, patch: Partial<SpatialNode>) => {
      setNodes((current) => {
        const next = current.map((n) => (n.id === id ? { ...n, ...patch } : n));
        persist(projectId, next);
        return next;
      });
    },
    [projectId],
  );

  return { nodes, preview, commit, loading, error };
}
