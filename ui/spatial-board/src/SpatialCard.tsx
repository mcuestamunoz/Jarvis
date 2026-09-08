import { SpatialGlyph } from "./SpatialGlyph";
import { useNodeGestures } from "./useNodeGestures";
import type { CanvasTransform, ResizeHandle, SpatialNode } from "./types";

const HANDLES: ResizeHandle[] = ["nw", "ne", "sw", "se"];

type Props = {
  node: SpatialNode;
  transform: CanvasTransform;
  selected: boolean;
  onSelect: (id: string) => void;
  onPreview: (id: string, patch: Partial<SpatialNode>) => void;
  onCommit: (id: string, patch: Partial<SpatialNode>) => void;
};

export function SpatialCard({ node, transform, selected, onSelect, onPreview, onCommit }: Props) {
  const { startDrag, startResize } = useNodeGestures(
    node,
    transform,
    onPreview,
    onCommit,
  );

  return (
    <article
      className={`sb-card sb-card--${node.kind}${selected ? " sb-card--selected" : ""}`}
      data-node-id={node.id}
      aria-current={selected ? "true" : undefined}
      style={{
        left: node.x,
        top: node.y,
        width: node.width,
        height: node.height,
      }}
    >
      <header
        className="sb-card__grip"
        onMouseDown={(e) => {
          onSelect(node.id);
          startDrag(e);
        }}
      >
        <span className="sb-card__title">{node.title}</span>
        <span className="sb-card__kind">{node.kind}</span>
      </header>
      <div className="sb-card__body" onMouseDown={() => onSelect(node.id)}>
        {node.declaredName ? (
          <p className="sb-card__name">{node.declaredName}</p>
        ) : (
          <p className="sb-card__name sb-card__name--empty">sin nombre declarado</p>
        )}
        {node.geometry ? <SpatialGlyph geometry={node.geometry} /> : null}
        <dl className="sb-card__fields">
          {node.fields.map((f) => (
            <div key={f.label}>
              <dt>{f.label}</dt>
              <dd>{f.value}</dd>
            </div>
          ))}
        </dl>
      </div>
      {HANDLES.map((h) => (
        <button
          key={h}
          type="button"
          aria-label={`resize ${h}`}
          className={`sb-handle sb-handle--${h}`}
          onMouseDown={(e) => startResize(e, h)}
        />
      ))}
    </article>
  );
}
