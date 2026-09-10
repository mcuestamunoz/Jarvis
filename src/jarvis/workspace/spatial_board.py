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

from jarvis.core.system_architecture_catalog import (
    BLOCK_TO_COMPONENTS,
    KIT_HOME_BLOCK,
    kit_component_keys,
)
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

    vehicle_type = (state.current_parameters or {}).get("vehicle_type")
    expected_by_column = _expected_keys_by_column(blocks, vehicle_type, components)

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
        solid_copies = _solid_copies(spec, components)
        solid_copy_offsets_mm = _solid_copy_offsets_mm(spec, components, solid_copies)
        _emit(
            key, col, spec.name or "", "part" if spec.parent_key else "component", fields,
            geometry=geometry,
            mounted_on=mounted_dto,
            declared_box_pose=declared_box_pose,
            solid_copies=solid_copies,
            solid_copy_offsets_mm=solid_copy_offsets_mm,
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
        solid_copies: int | None = None,
        solid_copy_offsets_mm: list[dict[str, float]] | None = None,
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
        if solid_copies is not None:
            node["solidCopies"] = solid_copies
        if solid_copy_offsets_mm is not None:
            node["solidCopyOffsetsMm"] = solid_copy_offsets_mm
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


def _expected_keys_by_column(
    blocks: list[str],
    vehicle_type: str | None = None,
    components: dict[str, ComponentSpec] | None = None,
) -> dict[int, list[str]]:
    """Declared-block expected keys, first-match deduped (a key owned by
    multiple blocks — e.g. ``motors`` in propulsion+energy — is listed
    once, at the first block that names it), in ``BLOCK_TO_COMPONENTS``
    order within each column. Empty for an undeclared/no-blocks project —
    the "no inventa para bloques no declarados" virtue (§2.1).

    Assembly kit template B1-min: after the architecture keys, each kit key
    (``system_architecture_catalog.kit_component_keys`` — gated on
    ``vehicle_type``'s domain AND its home block being declared) is appended
    to the column of its own ``KIT_HOME_BLOCK`` — never a new column, never
    BLOCK_TO_COMPONENTS. ``vehicle_type`` omitted/unknown → zero kit keys,
    byte-identical to pre-B1-min output.

    Prop adapter ask B1: ``components`` is forwarded to ``kit_component_keys``
    so a component-gated kit key (``prop_adapter`` — requires ``motors``/
    ``propellers`` already present) resolves correctly; omitted → that key
    fails closed (never shown), same as no ``vehicle_type``.
    """
    result: dict[int, list[str]] = {}
    seen: set[str] = set()
    for i, block in enumerate(blocks):
        for key in BLOCK_TO_COMPONENTS.get(block, []):
            if key in seen:
                continue
            seen.add(key)
            result.setdefault(i, []).append(key)
    for key in kit_component_keys(vehicle_type, blocks, components):
        if key in seen:
            continue
        col = blocks.index(KIT_HOME_BLOCK[key])
        seen.add(key)
        result.setdefault(col, []).append(key)
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


# Motor visor copies B1 — a count only ever taken from the `motors` spec's
# own `motor_count` property. Never a default of 4, never
# `configuration=quad_x` (a frame fact, not a motors fact), never
# `current_parameters.motor_count` (a different, possibly-drifted field).
_SOLID_COPIES_MIN = 2
_SOLID_COPIES_MAX = 16


def _parse_solid_copies_count(raw_value: Any) -> int | None:
    """Shared whole-number-in-[2,16] gate for a solid-copy count — never a
    public API, just avoids duplicating the float/is_integer/range check
    between motors' own ``motor_count`` read and propellers' cross-read of
    motors' ``motor_count`` (Propeller visor copies B1)."""
    if raw_value is None:
        return None
    try:
        raw = float(raw_value)
    except (TypeError, ValueError):
        return None
    if not raw.is_integer():
        return None
    count = int(raw)
    if not (_SOLID_COPIES_MIN <= count <= _SOLID_COPIES_MAX):
        return None
    return count


def _solid_copies(
    spec: ComponentSpec, components: dict[str, ComponentSpec]
) -> int | None:
    """How many solid copies to draw for this ONE ``ComponentSpec`` (never
    N specs, never N BOM nodes). Omitted (``None``) unless a real solid
    already exists for THIS spec (``_geometry_from_spec``) and a
    ``motor_count`` whole number in ``[2, 16]`` is found — missing, ``1``,
    ``0``, non-integer, or out of range all omit, so the visor shows
    exactly what it showed before this Buy (0 or 1 solid, from
    ``geometry`` alone).

    Motor visor copies B1 (unchanged, byte-identical): for ``motors``, the
    count comes from THIS spec's own ``motor_count`` property only.

    Propeller visor copies B1 / Prop adapter visor X copies B1: for
    ``propellers`` and ``prop_adapter`` alike, geometry is this spec's OWN
    (a propeller/adapter may have dims with no motor Ø, or vice versa — the
    two gates are independent), but the count is a CROSS-read of the
    sibling ``motors`` spec's own ``motor_count`` property — the same
    documented "1 per motor" convention ``project_closure._bom_quantity``
    already ships for propellers, applied here to a second family and this
    second (visor) surface. Never ``current_parameters["motor_count"]``
    (that stays the params-first source `_bom_quantity` itself uses —
    untouched here), never a dedicated ``*_count`` field (none exists),
    never a default of 4, never ``configuration=quad_x``. Any other key
    always omits.
    """
    if spec.suggested_key == "motors":
        if _geometry_from_spec(spec) is None:
            return None
        prop = (spec.properties or {}).get("motor_count")
        return _parse_solid_copies_count(prop.value if prop is not None else None)
    if spec.suggested_key in ("propellers", "prop_adapter"):
        # Prop adapter visor X copies B1: `prop_adapter` follows the exact
        # same pattern as `propellers` (own geometry gate, cross-read of
        # motors' `motor_count`, any valid N in [2,16] gets a row) —
        # deliberately NOT the stricter frame_arm gate below. One adapter
        # per motor is a real, honest fallback shape for any N (unlike an
        # arm, which only means something at its own quad-X station); the
        # station OFFSETS (`_solid_copy_offsets_mm`) still only apply when
        # N==4 and quad_x+wheelbase hold — this branch only decides the
        # copy COUNT.
        if _geometry_from_spec(spec) is None:
            return None
        motors_spec = components.get("motors")
        if motors_spec is None:
            return None
        prop = (motors_spec.properties or {}).get("motor_count")
        return _parse_solid_copies_count(prop.value if prop is not None else None)
    if spec.suggested_key == "frame_arm":
        # Frame arm envelope + visor X copies B1: unlike motors/propellers,
        # a "row of N arms" is not an honest fallback — an arm's whole
        # reason for being N copies is sitting at the N quad-X motor
        # stations, so this gate is deliberately STRICTER than the
        # propellers cross-read above: copies are emitted ONLY when the
        # count is exactly 4 AND the frame's own quad_x+wheelbase facts
        # hold (the same gate `_solid_copy_offsets_mm` uses for the
        # offsets themselves) — never a bare N=3 row, never a fake
        # 3-station X. Any other count, or missing quad_x/wheelbase, omits
        # entirely — the arm then renders as ONE single box, not a row.
        if _geometry_from_spec(spec) is None:
            return None
        motors_spec = components.get("motors")
        if motors_spec is None:
            return None
        prop = (motors_spec.properties or {}).get("motor_count")
        count = _parse_solid_copies_count(prop.value if prop is not None else None)
        if count != _QUAD_X_STATION_COUNT:
            return None
        if _quad_x_wheelbase_mm(components) is None:
            return None
        return count
    if spec.suggested_key == "frame_standoff":
        # Frame standoff x4 at Main Plate corners B1 — a DIFFERENT gate and
        # formula from every branch above: fixed count of 4 this Buy, never
        # read from motors/motor_count/quad_x/wheelbase (that math belongs
        # to the quad-X families only — a standoff sandwich post is a
        # Main-Plate-footprint fact, not a propulsion one). Count and
        # offsets are computed by the SAME helper
        # (`_frame_standoff_corner_offsets_mm`) so they can never drift
        # apart; a missing/non-box standoff or Main Plate, or a standoff
        # footprint larger than the plate in either axis, omits both.
        if _frame_standoff_corner_offsets_mm(spec, components) is not None:
            return _STANDOFF_CORNER_COUNT
        return None
    return None


# Visor X stations B1 — four declared-mm stations, derived ONLY from a
# CITED frame fact (`configuration == "quad_x"` + `wheelbase_mm`, motor-to-
# motor per the Rooster source_note) and the same `motor_count == 4` gate
# `_solid_copies` already enforces. Never a default, never inferred from N
# alone (`quad_x` with N=3 stays a row), never read from
# `current_parameters`. Z is 0 this Buy (coplanar silhouette) — height_mm
# is a card fact only, never stacked here.
_QUAD_X_STATION_COUNT = 4


def _quad_x_wheelbase_mm(components: dict[str, ComponentSpec]) -> float | None:
    """The one shared frame-fact gate for both motors and propellers: frame
    must exist, declare `configuration == "quad_x"` (exact string, never
    inferred from a motor count) AND a finite positive `wheelbase_mm`.
    Either missing/wrong → None, so callers keep today's row."""
    frame = components.get("frame")
    if frame is None:
        return None
    props = frame.properties or {}
    config = props.get("configuration")
    if config is None or config.value != "quad_x":
        return None
    wheelbase = props.get("wheelbase_mm")
    if wheelbase is None or wheelbase.value is None:
        return None
    try:
        wheelbase_mm = float(wheelbase.value)
    except (TypeError, ValueError):
        return None
    if not (wheelbase_mm > 0):
        return None
    return wheelbase_mm


def _quad_x_station_points(wheelbase_mm: float) -> list[dict[str, float]]:
    """Opposite motor centers = `wheelbase_mm` (cited motor-to-motor);
    center-to-motor = W/2; quad-X at 45°. Index 0..3 = FR, FL, RL, RR in
    the declared frame (L->+X, W->+Y, H->+Z), Z=0. Opposite pair (0 vs 2,
    1 vs 3) distance is exactly `wheelbase_mm`."""
    a = wheelbase_mm / (2 * (2 ** 0.5))
    return [
        {"xMm": a, "yMm": a, "zMm": 0.0},
        {"xMm": a, "yMm": -a, "zMm": 0.0},
        {"xMm": -a, "yMm": -a, "zMm": 0.0},
        {"xMm": -a, "yMm": a, "zMm": 0.0},
    ]


# Frame standoff x4 at Main Plate corners B1 — a fixed count, unrelated to
# the quad-X families above. `_STANDOFF_CORNER_COUNT` is a separate
# constant (even though it happens to also be 4) to keep this concept
# textually distinct from `_QUAD_X_STATION_COUNT` — a future N!=4 declared
# `standoff_count` Buy changes only this constant/branch, never the
# quad-X ones.
_STANDOFF_CORNER_COUNT = 4


def _main_plate_corner_points(
    plate_geometry: dict[str, float | str], standoff_geometry: dict[str, float | str]
) -> list[dict[str, float]] | None:
    """Four Main Plate corner points in the declared plate axes (L->+X,
    W->+Y), Z=0 — NOT wheelbase math, no 45°, never `_quad_x_station_points`.
    `hx = Lp/2 - Ls/2`, `hy = Wp/2 - Ws/2` (half the plate footprint minus
    half the standoff's own footprint, so a post sits inset from the plate
    edge by its own half-width rather than centered on the edge itself).
    Either inset going negative (a standoff footprint larger than the
    plate in that axis) fails closed — `None`, never a negative/inverted
    inset. Index order FR/FL/RL/RR, mirroring the quad-X convention purely
    for readability."""
    hx = plate_geometry["length_mm"] / 2 - standoff_geometry["length_mm"] / 2
    hy = plate_geometry["width_mm"] / 2 - standoff_geometry["width_mm"] / 2
    if hx < 0 or hy < 0:
        return None
    return [
        {"xMm": hx, "yMm": hy, "zMm": 0.0},
        {"xMm": hx, "yMm": -hy, "zMm": 0.0},
        {"xMm": -hx, "yMm": -hy, "zMm": 0.0},
        {"xMm": -hx, "yMm": hy, "zMm": 0.0},
    ]


def _frame_standoff_corner_offsets_mm(
    standoff_spec: ComponentSpec, components: dict[str, ComponentSpec]
) -> list[dict[str, float]] | None:
    """The ONE gate + formula shared by `_solid_copies` (decides
    ``count == 4``) and `_solid_copy_offsets_mm` (emits the actual points)
    for `frame_standoff`, so the two can never drift apart. Requires the
    standoff's OWN geometry to be a box (`_geometry_from_spec`) AND the
    literal `frame_plate` key (Main Plate — never an ordinal sibling like
    `frame_plate_2`) to exist with a box geometry. Fixed count of 4 this
    Buy — never reads motors/motor_count/quad_x/wheelbase; a declared,
    generalist `standoff_count` is a later, separate Buy."""
    standoff_geometry = _geometry_from_spec(standoff_spec)
    if standoff_geometry is None or standoff_geometry.get("shape") != "box":
        return None
    plate_spec = components.get("frame_plate")
    if plate_spec is None:
        return None
    plate_geometry = _geometry_from_spec(plate_spec)
    if plate_geometry is None or plate_geometry.get("shape") != "box":
        return None
    return _main_plate_corner_points(plate_geometry, standoff_geometry)


def _solid_copy_offsets_mm(
    spec: ComponentSpec, components: dict[str, ComponentSpec], solid_copies: int | None
) -> list[dict[str, float]] | None:
    """Additive DTO alongside `solidCopies` — four declared-mm points for
    `motors`/`propellers`/`frame_arm`/`prop_adapter` iff the count is
    EXACTLY 4 (never coerced) and the frame's own `quad_x` + `wheelbase_mm`
    facts hold (`_quad_x_wheelbase_mm`). `solid_copies` is passed in rather
    than recomputed so the emitted `solidCopies` and `solidCopyOffsetsMm`
    counts can never drift apart — both come from the exact same
    already-computed number. Independent of the spec's OWN geometry gate
    (already enforced by `_solid_copies` itself returning ``None`` when
    geometry is absent) — a mute-Ø motors spec with `solid_copies is None`
    always omits here too, but propellers/frame_arm/prop_adapter can still
    station on the same points as long as ITS OWN `_solid_copies` is 4
    (for `frame_arm`, `_solid_copies` already re-checks this same
    wheelbase gate itself, so the two calls never disagree; for
    `prop_adapter`, this function's own wheelbase check below is the ONLY
    place that gate is enforced — its `_solid_copies` branch does not
    re-check it, exactly mirroring propellers).

    `frame_standoff` is a SEPARATE branch entirely — Main Plate corner
    points via `_frame_standoff_corner_offsets_mm`, never the quad-X
    wheelbase math above."""
    if spec.suggested_key == "frame_standoff":
        if solid_copies != _STANDOFF_CORNER_COUNT:
            return None
        return _frame_standoff_corner_offsets_mm(spec, components)
    if spec.suggested_key not in ("motors", "propellers", "frame_arm", "prop_adapter"):
        return None
    if solid_copies != _QUAD_X_STATION_COUNT:
        return None
    wheelbase_mm = _quad_x_wheelbase_mm(components)
    if wheelbase_mm is None:
        return None
    return _quad_x_station_points(wheelbase_mm)


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
        # Geometry assembly fit B1-min: same gate as the pose text above
        # (origin already confirmed a box) — a screening-only fact, never
        # "cabe"/VERIFIED, never a new declaredBoxPose/machine DTO key.
        from jarvis.core.pose_envelope_screening import format_screening, screen_posed_envelope

        screening = screen_posed_envelope(spec, components)
        fields.append({"label": "sobres", "value": format_screening(screening)})
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
