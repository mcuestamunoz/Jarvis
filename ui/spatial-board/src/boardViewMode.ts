/**
 * Board 3D-first workshop + mount-chain inspector B1
 * (`B1-board-3d-first-inspector`) — pure view-mode resolution. Two tabs
 * only: "taller" (3D-first workshop, the default — IC lock #2) and
 * "grafo" (the existing InfiniteCanvas card graph, IC lock #3). Persisted
 * per-project in `localStorage` — presentation-only, same tier as the
 * card-layout overlay `useBoardNodes.ts` already persists there, never
 * `ProjectState`.
 */

export type BoardViewMode = "taller" | "grafo";

const VALID_MODES: readonly string[] = ["taller", "grafo"];

function isBoardViewMode(value: string): value is BoardViewMode {
  return VALID_MODES.includes(value);
}

/**
 * Default on first visit, a missing stored value, or a corrupted/unknown
 * stored value: always `"taller"` (IC lock #2 — 3D-first is the default,
 * never a Grafo-primary first paint; T1).
 */
export function resolveInitialViewMode(stored: string | null): BoardViewMode {
  if (stored !== null && isBoardViewMode(stored)) return stored;
  return "taller";
}

export function viewModeStorageKey(projectId: string | null): string {
  const base = "jarvis.spatial-board.view-mode.v1";
  return projectId ? `${base}.${projectId}` : base;
}
