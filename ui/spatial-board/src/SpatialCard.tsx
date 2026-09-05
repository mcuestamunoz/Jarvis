import { useNodeGestures } from "./useNodeGestures";
import type { CanvasTransform, ResizeHandle, SpatialNode } from "./types";

const HANDLES: ResizeHandle[] = ["nw", "ne", "sw", "se"];

type Props = {
  node: SpatialNode;
  transform: CanvasTransform;
  onPreview: (id: string, patch: Partial<SpatialNode>) => void;
  onCommit: (id: string, patch: Partial<SpatialNode>) => void;
};

export function SpatialCard({ node, transform, onPreview, onCommit }: Props) {
  const { startDrag, startResize } = useNodeGestures(
    node,
    transform,
    onPreview,
    onCommit,
  );

  return (
    <article
      className={`sb-card sb-card--${node.kind}`}
      data-node-id={node.id}
      style={{
        left: node.x,
        top: node.y,
        width: node.width,
        height: node.height,
      }}
    >
      <header className="sb-card__grip" onMouseDown={startDrag}>
        <span className="sb-card__title">{node.title}</span>
        <span className="sb-card__kind">{node.kind}</span>
      </header>
      <div className="sb-card__body">
        {node.declaredName ? (
          <p className="sb-card__name">{node.declaredName}</p>
        ) : (
          <p className="sb-card__name sb-card__name--empty">sin nombre declarado</p>
        )}
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
