/**
 * Board click-inspect B1− — pure selection-state transitions, no React.
 * Single selection only (no multi-select), never persisted (no localStorage,
 * no URL, no ProjectState) — purely a client highlight over an already-open
 * card (every card already shows all its fields unconditionally; selection
 * never reveals anything new, it only highlights which one is "current").
 */

export type BoardSelectionAction =
  | { type: "select"; id: string }
  | { type: "clear" };

/** select -> replace (clicking the already-selected card keeps it selected,
 * never toggles off). clear -> null. `_current` is part of the reducer-style
 * signature (mirrors reconcileSelection's shape) but unused by either
 * branch today — both outcomes are fully determined by `action` alone. */
export function nextSelectedId(
  _current: string | null,
  action: BoardSelectionAction,
): string | null {
  if (action.type === "clear") return null;
  return action.id;
}

/** Drop a selection that no longer corresponds to a live node (e.g. the
 * selected component was removed/renamed between projector reads). */
export function reconcileSelection(
  selectedId: string | null,
  nodeIds: Iterable<string>,
): string | null {
  if (selectedId === null) return null;
  const ids = nodeIds instanceof Set ? nodeIds : new Set(nodeIds);
  return ids.has(selectedId) ? selectedId : null;
}
