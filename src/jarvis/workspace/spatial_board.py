"""spatial_board
==============
Proyecta ProjectState → cards del visor (`ui/spatial-board`).

Solo lee estado — no muta ingeniería, no clasifica BOM. Una ComponentSpec
= una card (`kind` "component"/"part"). Additive honesty (B3, Spatial
Board Product Limits): una clave esperada por `BLOCK_TO_COMPONENTS` de un
bloque **declarado** (`system_blocks`) que no está en `components` se
proyecta como `kind: "slot"` — un hueco de arquitectura, nunca inventado
para un bloque no declarado, nunca una clasificación BOM
(`incomplete`/`declarative`/`✗`), nunca un `ComponentSpec`. Layout inicial
por carriles 4/4; el visor overlay de {x,y,width,height} manda después del
primer gesto.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jarvis.core.system_architecture_catalog import BLOCK_TO_COMPONENTS
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import ProjectState

# Match ui/spatial-board/src/constants.ts CARD — presentation only.
CARD_WIDTH = 280
CARD_MIN_HEIGHT = 120
CARD_MAX_HEIGHT = 320
LANE_GAP = 40
ROW_GAP = 20
ORIGIN_X = 40
ORIGIN_Y = 80


def project_spatial_nodes(state: ProjectState) -> list[dict[str, Any]]:
    """Deterministic DTO list for the spatial visor. No completeness / BOM.

    B3 (Spatial Board Product Limits, honest absence): a declared block's
    expected key that isn't in ``components`` becomes a display-only
    ``kind: "slot"`` node (§2.1) — so an engineer can tell "not yet
    declared" apart from "doesn't apply to this architecture." Slots are
    never emitted for a block that isn't in ``system_blocks``, never for
    frame parts (not in ``BLOCK_TO_COMPONENTS``), and never duplicate a key
    that's already present in ``components`` under any form (root or
    child) — presence, not root-ness, is what suppresses a slot.
    """
    components = state.design_properties.components
    blocks = list(state.design_properties.system_blocks or [])
    if not components and not blocks:
        return []

    children: dict[str, list[str]] = {}
    roots: list[str] = []
    for key, spec in components.items():
        parent = spec.parent_key
        if parent:
            children.setdefault(parent, []).append(key)
        else:
            roots.append(key)

    lanes: dict[int, list[str]] = {}
    for key in roots:
        lanes.setdefault(_lane_index(key, components[key], blocks), []).append(key)

    orphans = [
        key
        for key, spec in components.items()
        if spec.parent_key and spec.parent_key not in components
    ]

    expected_by_column = _expected_keys_by_column(blocks)

    nodes: list[dict[str, Any]] = []
    next_y: dict[int, int] = {}
    emitted: set[str] = set()

    def place(key: str, col: int) -> None:
        spec = components[key]
        fields = _fields(spec)
        _emit(key, col, spec.name or "", "part" if spec.parent_key else "component", fields)

    def place_slot(key: str, col: int) -> None:
        _emit(key, col, "", "slot", [{"label": "estado", "value": "no declarado"}])

    def _emit(key: str, col: int, declared_name: str, kind: str, fields: list[dict[str, str]]) -> None:
        height = _default_height(len(fields))
        y = next_y.get(col, ORIGIN_Y)
        nodes.append(
            {
                "id": key,
                "title": key,
                "declaredName": declared_name,
                "kind": kind,
                "fields": fields,
                "x": ORIGIN_X + col * (CARD_WIDTH + LANE_GAP),
                "y": y,
                "width": CARD_WIDTH,
                "height": height,
            }
        )
        next_y[col] = y + height + ROW_GAP
        emitted.add(key)

    # Slots require walking every declared block's own column, not just
    # columns that already have a real root (review N-lane: otherwise a
    # project with only "motors" would never show the battery/frame/control
    # slots at all).
    lane_count = max(len(blocks), max(lanes, default=-1) + 1)
    for col in range(lane_count):
        for key in expected_by_column.get(col, []):
            if key in components:
                place(key, col)
                for child_key in children.get(key, []):
                    place(child_key, col)
            else:
                place_slot(key, col)
        for root_key in _sort_roots(col, lanes.get(col, []), blocks, components):
            if root_key in emitted:
                continue
            place(root_key, col)
            for child_key in children.get(root_key, []):
                place(child_key, col)
        for key in orphans:
            if key in emitted:
                continue
            if _lane_index(key, components[key], blocks) == col:
                place(key, col)

    for key in orphans:
        if key not in emitted:
            place(key, _lane_index(key, components[key], blocks))

    return nodes


def _expected_keys_by_column(blocks: list[str]) -> dict[int, list[str]]:
    """Declared-block expected keys, first-match deduped (a key owned by
    multiple blocks — e.g. ``motors`` in propulsion+energy — is listed
    once, at the first block that names it), in ``BLOCK_TO_COMPONENTS``
    order within each column. Empty for an undeclared/no-blocks project —
    the "no inventa para bloques no declarados" virtue (§2.1)."""
    result: dict[int, list[str]] = {}
    seen: set[str] = set()
    for i, block in enumerate(blocks):
        for key in BLOCK_TO_COMPONENTS.get(block, []):
            if key in seen:
                continue
            seen.add(key)
            result.setdefault(i, []).append(key)
    return result


def project_spatial_nodes_from_path(path: Path) -> list[dict[str, Any]]:
    state = ProjectState.model_validate_json(path.read_text(encoding="utf-8"))
    return project_spatial_nodes(state)


def _lane_index(key: str, spec: ComponentSpec, blocks: list[str]) -> int:
    lookup = spec.parent_key or key
    for i, block in enumerate(blocks):
        if lookup in BLOCK_TO_COMPONENTS.get(block, []):
            return i
    return len(blocks)


def _sort_roots(
    col: int,
    keys: list[str],
    blocks: list[str],
    components: dict[str, ComponentSpec],
) -> list[str]:
    if col >= len(blocks):
        return keys
    order = BLOCK_TO_COMPONENTS.get(blocks[col], [])
    rank = {name: i for i, name in enumerate(order)}
    insertion = {name: i for i, name in enumerate(components)}
    return sorted(keys, key=lambda k: (rank.get(k, 1000), insertion[k]))


def _fields(spec: ComponentSpec) -> list[dict[str, str]]:
    fields = [
        {"label": key, "value": _format_property(value)}
        for key, value in spec.properties.items()
    ]
    sku = spec.catalog_ref.sku if spec.catalog_ref else None
    if sku:
        fields.append({"label": "SKU", "value": sku})
    return fields


def _format_property(value: PropertyValue) -> str:
    raw = value.value
    if raw is None or raw == "":
        text = "—"
    elif isinstance(raw, float) and raw.is_integer():
        text = str(int(raw))
    else:
        text = str(raw)
    if value.unit and text != "—":
        return f"{text} {value.unit}"
    return text


def _default_height(n_fields: int) -> int:
    return max(CARD_MIN_HEIGHT, min(CARD_MAX_HEIGHT, 72 + 22 * max(n_fields, 1)))


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        sys.stderr.write("usage: python -m jarvis.workspace.spatial_board <state.json>\n")
        return 2
    path = Path(args[0])
    payload = {"nodes": project_spatial_nodes_from_path(path)}
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
