/**
 * Board 3D-first workshop + mount-chain inspector B1
 * (`B1-board-3d-first-inspector`) — pure ancestor walk over the projector's
 * own `mountedOn` DTO field (Assembly Board edges B2). Never 3D proximity,
 * never `declaredBoxPose.originKey` (pose frame ≠ mount graph, IC §2.3
 * lock) — only the declared relation graph.
 *
 * `isAssemblyRootPlate` reuses the SAME locked assembly-root key
 * `situarOriginCandidates.ASSEMBLY_ROOT_CANDIDATE_ID` already uses for
 * Situar's own origin-picker ranking (and the private, unexported twin in
 * `scene3dLayout.ts`'s own `ASSEMBLY_ROOT_ID`) — never a third, possibly
 * diverging definition of "the" assembly root.
 */
import { ASSEMBLY_ROOT_CANDIDATE_ID } from "./situarOriginCandidates";

export function isAssemblyRootPlate(id: string): boolean {
  return id === ASSEMBLY_ROOT_CANDIDATE_ID;
}

export type AncestorChainNode = { id: string; mountedOn?: string };

/**
 * Ordered `[selectedId, ...ancestors]` walking `mountedOn` up to (and
 * including) the assembly-root plate. Algorithm lock (IC §2.3):
 *
 *   - `parent is None` (no declared mount) -> honest stop, chain of 1.
 *   - `parent in seen` -> cycle guard, stop (never throws, never loops).
 *   - `parent` not a projected node -> honest stop (stale/removed target).
 *   - reaching `isAssemblyRootPlate(parent)` -> append it, then stop.
 *
 * Pure function over a `Map` the caller builds once per render from the
 * live `nodes` array — never re-reads global state, never mutates its
 * input.
 */
/**
 * 3D dimming (IC §2.4/§2.6): solids on the chain (selection + ancestors)
 * stay full opacity; every other solid dims. `chain` empty (no selection)
 * -> nothing dims (full opacity restored, matching the "clear selection"
 * lock). Pure — the caller applies whatever CSS/material the boolean maps
 * to; this only decides which ids qualify.
 */
export function isDimmed(id: string, chain: readonly string[]): boolean {
  if (chain.length === 0) return false;
  return !chain.includes(id);
}

export function computeAncestorChain(
  selectedId: string,
  nodesById: Map<string, AncestorChainNode>,
): string[] {
  const chain: string[] = [selectedId];
  const seen = new Set<string>([selectedId]);
  let cur = selectedId;
  // Cap matches Map size — a well-formed graph can never need more hops
  // than there are distinct nodes; this is a defensive backstop only,
  // `seen` already guards against a real cycle.
  const maxHops = nodesById.size;
  for (let hop = 0; hop < maxHops; hop += 1) {
    const node = nodesById.get(cur);
    const parent = node?.mountedOn;
    if (!parent) break;
    if (seen.has(parent)) break;
    if (!nodesById.has(parent)) break;
    chain.push(parent);
    seen.add(parent);
    cur = parent;
    if (isAssemblyRootPlate(parent)) break;
  }
  return chain;
}
