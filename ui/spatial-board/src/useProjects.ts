import { useEffect, useState } from "react";
import { PROJECT_KEY } from "./constants";
import { fetchProjects, type ProjectSummary } from "./projects";

function readStoredId(): string | null {
  try {
    return localStorage.getItem(PROJECT_KEY);
  } catch {
    return null;
  }
}

export function useProjects() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [projectId, setProjectId] = useState<string | null>(readStoredId);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchProjects()
      .then((payload) => {
        if (cancelled) return;
        setProjects(payload.projects);
        setError(null);
        setProjectId((current) => {
          if (current && payload.projects.some((p) => p.id === current)) {
            return current;
          }
          const next = payload.projects[0]?.id ?? null;
          if (next) {
            try {
              localStorage.setItem(PROJECT_KEY, next);
            } catch {
              /* ignore */
            }
          }
          return next;
        });
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const select = (id: string) => {
    setProjectId(id);
    try {
      localStorage.setItem(PROJECT_KEY, id);
    } catch {
      /* ignore */
    }
  };

  const current = projects.find((p) => p.id === projectId) ?? null;
  return { projects, current, projectId, select, error };
}
