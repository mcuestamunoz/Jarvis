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
