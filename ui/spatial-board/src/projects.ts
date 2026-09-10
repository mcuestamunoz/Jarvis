import type { SpatialNode } from "./types";

export type ProjectSummary = {
  id: string;
  slug: string;
  objective: string;
  title: string;
  folder: string;
};

export async function fetchProjects(): Promise<{
  workspace: string;
  projects: ProjectSummary[];
}> {
  const res = await fetch("/api/projects");
  if (!res.ok) {
    throw new Error(`projects ${res.status}`);
  }
  return res.json() as Promise<{ workspace: string; projects: ProjectSummary[] }>;
}

export async function fetchProjectNodes(projectId: string): Promise<SpatialNode[]> {
  const res = await fetch(`/api/projects/${encodeURIComponent(projectId)}/nodes`);
  if (!res.ok) {
    throw new Error(`nodes ${res.status}`);
  }
  const payload = (await res.json()) as { nodes: SpatialNode[] };
  return Array.isArray(payload.nodes) ? payload.nodes : [];
}

export type DragPosePayload = {
  component_key: string;
  origin_key: string;
  x_mm: number | null;
  y_mm: number | null;
  z_mm: number | null;
};

/**
 * Board drag → Continuity pose B1 — the ONE mutation call this package
 * makes. Body shape mirrors `set_component_declared_box_pose` 1:1 (no new
 * fields). On a writer rejection the server responds 4xx with
 * `{error: "<the writer's own ValueError message>"}` — surfaced verbatim,
 * never swallowed into a generic "failed" string, so the Engineer sees the
 * exact same honest refusal the CLI's `declara…` would have given.
 */
export async function postDragPose(projectId: string, payload: DragPosePayload): Promise<void> {
  const res = await fetch(`/api/projects/${encodeURIComponent(projectId)}/pose`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let message = `pose ${res.status}`;
    try {
      const body = (await res.json()) as { error?: string };
      if (body.error) message = body.error;
    } catch {
      // keep the generic status-based message
    }
    throw new Error(message);
  }
}
