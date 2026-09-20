import { useEffect, useState } from "react";
import { computeAncestorChain } from "./mountAncestorChain";
import { pickSummaryFields } from "./inspectorSummary";
import type { SpatialNode } from "./types";

type Props = {
  nodes: SpatialNode[];
  selectedId: string | null;
  onSelect: (id: string) => void;
};

/**
 * Board 3D-first workshop + mount-chain inspector B1
 * (`B1-board-3d-first-inspector`) — right-side dock shown in Taller mode
 * while Situar is OFF (IC §2.2/§2.6: Situar ON collapses this entirely,
 * the piece strip is the selection affordance there instead).
 *
 * Detail on demand only: default is a short **summary** (`pickSummaryFields`)
 * plus the mount-ancestor chain up to the assembly-root plate
 * (`computeAncestorChain` — declared `mountedOn` relations only, never 3D
 * proximity, never `declaredBoxPose.originKey`). "Ver todo" expands to the
 * SAME full `fields` list `SpatialCard`'s own `<dl>` already renders in
 * Grafo — no new data, just a collapsed-by-default presentation of it.
 */
export function InspectorDock({ nodes, selectedId, onSelect }: Props) {
  const [expanded, setExpanded] = useState(false);

  // A fresh selection always re-opens on the summary view — "Ver todo"
  // is a per-selection choice, never sticky across a different piece.
  useEffect(() => {
    setExpanded(false);
  }, [selectedId]);

  if (!selectedId) {
    return (
      <aside className="sb-inspector sb-inspector--empty">
        <p className="sb-inspector__hint">
          Selecciona una pieza en el taller 3D para inspeccionarla.
        </p>
      </aside>
    );
  }

  const nodesById = new Map(nodes.map((n) => [n.id, n]));
  const selected = nodesById.get(selectedId);
  if (!selected) {
    // Stale selection (e.g. mid-refetch after a pose commit) — never
    // throw, fall back to the same honest empty state.
    return (
      <aside className="sb-inspector sb-inspector--empty">
        <p className="sb-inspector__hint">
          Selecciona una pieza en el taller 3D para inspeccionarla.
        </p>
      </aside>
    );
  }

  const chain = computeAncestorChain(selectedId, nodesById);
  const ancestorIds = chain.slice(1);
  const summaryFields = pickSummaryFields(selected.fields);
  const fieldsToShow = expanded ? selected.fields : summaryFields;
  const canToggle = selected.fields.length > summaryFields.length;

  return (
    <aside className="sb-inspector">
      <section className="sb-inspector__selected">
        <header className="sb-inspector__selected-header">
          <span className="sb-inspector__title">{selected.title}</span>
          <span className="sb-inspector__kind">{selected.kind}</span>
        </header>
        {selected.declaredName ? (
          <p className="sb-inspector__name">{selected.declaredName}</p>
        ) : (
          <p className="sb-inspector__name sb-inspector__name--empty">
            sin nombre declarado
          </p>
        )}
        {fieldsToShow.length > 0 ? (
          <dl className="sb-inspector__fields">
            {fieldsToShow.map((f) => (
              <div key={f.label}>
                <dt>{f.label}</dt>
                <dd>{f.value}</dd>
              </div>
            ))}
          </dl>
        ) : null}
        {canToggle ? (
          <button
            type="button"
            className="sb-inspector__toggle"
            onClick={() => setExpanded((e) => !e)}
          >
            {expanded ? "Resumen" : "Ver todo"}
          </button>
        ) : null}
      </section>
      <section className="sb-inspector__chain">
        <h3 className="sb-inspector__chain-title">Cadena hasta la placa</h3>
        {ancestorIds.length === 0 ? (
          <p className="sb-inspector__hint">
            Sin cadena de montaje declarada hasta la placa.
          </p>
        ) : (
          <ol className="sb-inspector__chain-list">
            {ancestorIds.map((id) => {
              const node = nodesById.get(id);
              return (
                <li key={id}>
                  <button
                    type="button"
                    className="sb-inspector__chain-row"
                    onClick={() => onSelect(id)}
                  >
                    <span className="sb-inspector__chain-row-title">
                      {node?.title ?? id}
                    </span>
                    {node?.declaredName ? (
                      <span className="sb-inspector__chain-row-name">
                        {node.declaredName}
                      </span>
                    ) : null}
                  </button>
                </li>
              );
            })}
          </ol>
        )}
      </section>
    </aside>
  );
}
