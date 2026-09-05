import { spawnSync } from "node:child_process";
import type { ServerResponse } from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Plugin } from "vite";

export type ProjectSummary = {
  id: string;
  slug: string;
  objective: string;
  title: string;
  folder: string;
};

function repoRoot(): string {
  return fileURLToPath(new URL("../..", import.meta.url));
}

function workspaceRoot(): string {
  if (process.env.JARVIS_WORKSPACE_ROOT) {
    return process.env.JARVIS_WORKSPACE_ROOT;
  }
  return path.join(repoRoot(), "workspace");
}

function listProjects(): ProjectSummary[] {
  const root = workspaceRoot();
  if (!fs.existsSync(root)) return [];
  const byId = new Map<string, ProjectSummary & { mtime: number }>();
  for (const name of fs.readdirSync(root)) {
    const folder = path.join(root, name);
    const statePath = path.join(folder, "state.json");
    if (!fs.statSync(folder).isDirectory() || !fs.existsSync(statePath)) continue;
    try {
      const data = JSON.parse(fs.readFileSync(statePath, "utf8")) as {
        project_id?: string;
        project_slug?: string;
        objective?: string;
      };
      const id = String(data.project_id || name);
      const slug = String(data.project_slug || name);
      const objective = String(data.objective || "").trim();
      const mtime = fs.statSync(statePath).mtimeMs;
      const prev = byId.get(id);
      if (prev && prev.mtime >= mtime) continue;
      byId.set(id, {
        id,
        slug,
        objective,
        title: objective || slug,
        folder: name,
        mtime,
      });
    } catch {
      continue;
    }
  }
  return [...byId.values()]
    .sort((a, b) => b.mtime - a.mtime)
    .map((row) => ({
      id: row.id,
      slug: row.slug,
      objective: row.objective,
      title: row.title,
      folder: row.folder,
    }));
}

function statePathFor(projectId: string): string | null {
  const root = workspaceRoot();
  if (!fs.existsSync(root)) return null;
  const suffix = `-${projectId}`;
  for (const name of fs.readdirSync(root)) {
    if (!name.endsWith(suffix)) continue;
    const statePath = path.join(root, name, "state.json");
    if (fs.existsSync(statePath)) return statePath;
  }
  return null;
}

function pythonBin(): string {
  const root = repoRoot();
  const candidates = [
    process.env.JARVIS_PYTHON,
    process.env.VIRTUAL_ENV
      ? path.join(process.env.VIRTUAL_ENV, "bin", "python")
      : "",
    path.join(root, ".venv", "bin", "python"),
  ].filter(Boolean);
  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) return candidate;
  }
  return "python3";
}

function projectNodes(statePath: string): { nodes: unknown } {
  const src = path.join(repoRoot(), "src");
  const result = spawnSync(
    pythonBin(),
    ["-m", "jarvis.workspace.spatial_board", statePath],
    {
      encoding: "utf8",
      cwd: repoRoot(),
      env: {
        ...process.env,
        PYTHONPATH: [src, process.env.PYTHONPATH || ""]
          .filter(Boolean)
          .join(path.delimiter),
      },
    },
  );
  if (result.status !== 0) {
    const err = (result.stderr || result.stdout || `python exit ${result.status}`).trim();
    throw new Error(err.slice(0, 800));
  }
  return JSON.parse(result.stdout) as { nodes: unknown };
}

function sendJson(res: ServerResponse, body: unknown, status = 200) {
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.end(JSON.stringify(body));
}

export function jarvisProjectsPlugin(): Plugin {
  return {
    name: "jarvis-projects",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (req.method !== "GET" || !req.url) {
          next();
          return;
        }
        const pathname = req.url.split("?")[0] ?? "";
        if (pathname === "/api/projects") {
          sendJson(res, {
            workspace: workspaceRoot(),
            projects: listProjects(),
          });
          return;
        }
        const nodesMatch = /^\/api\/projects\/([^/]+)\/nodes$/.exec(pathname);
        if (nodesMatch) {
          const id = decodeURIComponent(nodesMatch[1]);
          const statePath = statePathFor(id);
          if (!statePath) {
            sendJson(res, { error: "project not found" }, 404);
            return;
          }
          try {
            sendJson(res, projectNodes(statePath));
          } catch (err) {
            const message = err instanceof Error ? err.message : "projector failed";
            sendJson(res, { error: message }, 500);
          }
          return;
        }
        next();
      });
    },
  };
}
