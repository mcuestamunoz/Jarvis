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

Geometry Progression Lock B1 (`visualizar`): un nodo `component`/`part`
(nunca `slot`) puede llevar un `geometry` opcional (`box`/`disk`) derivado
de dimensiones ya declaradas — "sé qué componente es y sé qué volumen
físico declarado ocupa," nunca ensamblado ni "cabe." `width`/`height` del
nodo siguen siendo el layout en píxeles de la card, nunca la geometría
física — ver `_geometry_from_spec`.

Geometry Assembly Espacial B1 (`mounted_on`, relation-only): cuando
`ComponentSpec.mounted_on` está declarado, la card lleva un campo de texto
extra `"montado en"` (ver `_fields`) — ninguna posición/orientación, ningún
cambio a `kind`/carril/`x`/`y`. Ortogonal a `parent_key` (topología BOM del
frame, siempre literal `"frame"`): `mounted_on` nombra cualquier clave
declarada.

Geometry Assembly Board edges B2: si el target de `mounted_on` también está
en `components` (nodo proyectable), el DTO lleva `mountedOn` (clave máquina)
para que el visor dibuje una arista — el texto `"montado en"` se mantiene.
Si el target ya no existe en `components`, se omite `mountedOn` (sin arista)
pero el campo de texto puede seguir mostrando la clave guardada.
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
        fields = _fields(spec, components)
        geometry = _geometry_from_spec(spec)
        mounted_on = spec.mounted_on
        # B2: machine edge endpoint only when the target is still a declared
        # component (will be projected). Stale keys keep the text field only.
        mounted_dto = (
            mounted_on if mounted_on and mounted_on in components else None
        )
        declared_box_pose = _declared_box_pose_dto(spec, components)
        _emit(
            key, col, spec.name or "", "part" if spec.parent_key else "component", fields,
            geometry=geometry,
            mounted_on=mounted_dto,
            declared_box_pose=declared_box_pose,
        )

    def place_slot(key: str, col: int) -> None:
        _emit(key, col, "", "slot", [{"label": "estado", "value": "no declarado"}])

    def _emit(
        key: str,
        col: int,
        declared_name: str,
        kind: str,
        fields: list[dict[str, str]],
        *,
        geometry: dict[str, float | str] | None = None,
        mounted_on: str | None = None,
        declared_box_pose: dict[str, Any] | None = None,
    ) -> None:
        height = _default_height(len(fields))
        y = next_y.get(col, ORIGIN_Y)
        node: dict[str, Any] = {
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
        if geometry is not None:
            node["geometry"] = geometry
        if mounted_on is not None:
            node["mountedOn"] = mounted_on
        if declared_box_pose is not None:
            node["declaredBoxPose"] = declared_box_pose
        nodes.append(node)
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


_MM_PER_INCH = 25.4


def _geometry_from_spec(spec: ComponentSpec) -> dict[str, float | str] | None:
    """Board glyphs (Geometry Progression Lock B1, `visualizar`) — a
    declarative 2D shape hint derived from whichever dimension
    ``PropertyValue`` keys are actually present on ``spec``. Shape is
    chosen by which keys exist, never a hardcoded per-family table
    (investigation report §C) — this is why Motor and Propeller, two
    unrelated families, both resolve to ``disk`` today.

    ``box`` requires the full ``length_mm``/``width_mm``/``height_mm``
    triple (a complete box always wins over any diameter also present).
    ``disk`` requires exactly one diameter path: ``diameter_mm`` if
    present, else ``diameter_in`` converted to an mm-equivalent purely for
    drawing scale (a lossless physical-constant conversion, never altering
    the declared unit shown in ``fields``). A diameter alongside an
    unrelated height (e.g. Motor's ``stator_height_mm``) never becomes a
    cylinder — this function never stitches two different physical
    references together (investigation report §E). Returns ``None`` when
    dims are insufficient — no partial/dashed geometry is ever invented.
    """
    props = spec.properties or {}

    def _num(key: str) -> float | None:
        prop = props.get(key)
        if prop is None or prop.value is None:
            return None
        try:
            return float(prop.value)
        except (TypeError, ValueError):
            return None

    length_mm = _num("length_mm")
    width_mm = _num("width_mm")
    height_mm = _num("height_mm")
    if length_mm is not None and width_mm is not None and height_mm is not None:
        return {
            "shape": "box",
            "length_mm": length_mm,
            "width_mm": width_mm,
            "height_mm": height_mm,
        }

    diameter_mm = _num("diameter_mm")
    if diameter_mm is None:
        diameter_in = _num("diameter_in")
        if diameter_in is not None:
            diameter_mm = diameter_in * _MM_PER_INCH
    if diameter_mm is not None:
        return {"shape": "disk", "diameter_mm": diameter_mm}

    return None


# Geometry Pose Declared Box-Local Frame B1 — the ONE honesty label for
# every declared_box_pose text field. Not manufacturer heading, not
# gravity: every seeded box's own source_note states its L/W/H order is
# "verbatim print order" (investigation_report_geometry_pose_box_anchor.md
# §3) — this string exists specifically so the Board never lets a reader
# mistake this convention for a sourced fact.
POSE_AXES_HONESTY_LABEL = "locales declarados (L→+X, W→+Y, H→+Z); no morro; no gravedad"


def _declared_box_pose_dto(
    spec: ComponentSpec, components: dict[str, ComponentSpec]
) -> dict[str, Any] | None:
    """Scene3D-from-pose B1 — the ONE gate for whether a declared pose is
    honest to show at all, shared by the machine DTO (``_emit``) and the
    human text fields (``_fields``) — never forked into two rules. Requires
    the origin to still exist AND still resolve to a ``box`` via
    ``_geometry_from_spec`` (the exact same check the writer itself already
    enforces at declare-time — never a second, looser rule here). Returns
    ``None`` (never a fallback origin) when either check fails — the same
    "honest absence" class as B2's own ``mountedOn`` DTO omission.
    """
    pose = spec.declared_box_pose
    if pose is None:
        return None
    origin = components.get(pose.origin_key)
    if origin is None:
        return None
    geometry = _geometry_from_spec(origin)
    if geometry is None or geometry.get("shape") != "box":
        return None
    dto: dict[str, Any] = {"originKey": pose.origin_key}
    if pose.x_mm is not None:
        dto["xMm"] = pose.x_mm
    if pose.y_mm is not None:
        dto["yMm"] = pose.y_mm
    if pose.z_mm is not None:
        dto["zMm"] = pose.z_mm
    return dto


def _fields(spec: ComponentSpec, components: dict[str, ComponentSpec]) -> list[dict[str, str]]:
    fields = [
        {"label": key, "value": _format_property(value)}
        for key, value in spec.properties.items()
    ]
    sku = spec.catalog_ref.sku if spec.catalog_ref else None
    if sku:
        fields.append({"label": "SKU", "value": sku})
    # Geometry Assembly Espacial B1: a declared mount relation shows as a
    # plain text field — orthogonal to parent_key / kind / lane. B2 adds a
    # separate machine ``mountedOn`` on the node DTO when the target exists.
    if spec.mounted_on:
        fields.append({"label": "montado en", "value": spec.mounted_on})
    # Geometry Pose Declared Box-Local Frame B1 / Scene3D-from-pose B1: text
    # only, never moves a glyph/solid by itself — the same gate as the
    # machine ``declaredBoxPose`` DTO key (``_declared_box_pose_dto``),
    # never a looser one. A stale/shapeless/disk origin omits BOTH the text
    # and the DTO — no "origen pose" survives on its own once the machine
    # key would be omitted.
    pose = spec.declared_box_pose
    if pose is not None and _declared_box_pose_dto(spec, components) is not None:
        fields.append({"label": "origen pose", "value": pose.origin_key})
        fields.append({"label": "ejes pose", "value": POSE_AXES_HONESTY_LABEL})
        if pose.x_mm is not None:
            fields.append({"label": "Δx mm", "value": _format_number(pose.x_mm)})
        if pose.y_mm is not None:
            fields.append({"label": "Δy mm", "value": _format_number(pose.y_mm)})
        if pose.z_mm is not None:
            fields.append({"label": "Δz mm", "value": _format_number(pose.z_mm)})
    return fields


def _format_number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)


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
