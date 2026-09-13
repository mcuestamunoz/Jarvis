"""Standoff visor layout N≠4 (B7 / 6·8 perimeter).

Covers implementation_contract_geometry_standoff_layout_n_ne4_b7.md §3-4 —
`frame_standoff`'s `solidCopies`/`solidCopyOffsetsMm` widen from
corners-only (N=4, B4-min) to also place N=6/N=8 posts on the Main Plate
perimeter: 4 corners always, plus midpoints of the longer edge pair for
N=6, plus all four edge midpoints for N=8. N=4 stays byte-identical to
B4-min. Any other in-range N (2,3,5,7,9..16), missing, or non-numeric
`count` still fails closed (see test_geometry_standoff_count_gate_b4.py
for that coverage, updated in this Buy so N=6 is no longer in the
"rejected" parametrize). Fixture numbers: standoff 5x5, plate 100x100 (or
120x80 / 80x120 for the long/short-edge tie-break) -> half-inset 47.5 /
57.5 / 37.5. Never 230, never an invented Rooster count, never a row
layout (propeller pattern).

  P1  count=4 regression — same 4 points as B4-min corners
  P2  count absent -> no copies
  P3  count=3 -> no copies
  P4  count=6 + 100x100/5x5 -> solidCopies==6; corners U {(0,±47.5,0)}
  P5  count=8 + same -> solidCopies==8; corners U 4 edge mids
  P6  count=6 + Lp>Wp fixture -> long-edge mids on ±hy
  P7  count=6 + Wp>Lp fixture -> long-edge mids on ±hx
  P8  Fail-closed: oversized standoff / missing plate
  P9  One frame_standoff node; motors/props/arm/adapter X regressions green
  P10 Offsets still != quad-X stations when wheelbase=230 present
"""
from __future__ import annotations

from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes


def _standoff_spec(
    length_mm: float | None = 5.0, width_mm: float | None = 5.0, height_mm: float | None = 25.0,
    count: float | None = 4.0,
) -> ComponentSpec:
    props: dict[str, PropertyValue] = {}
    if length_mm is not None:
        props["length_mm"] = PropertyValue(value=length_mm, unit="mm", source="declared")
    if width_mm is not None:
        props["width_mm"] = PropertyValue(value=width_mm, unit="mm", source="declared")
    if height_mm is not None:
        props["height_mm"] = PropertyValue(value=height_mm, unit="mm", source="declared")
    if count is not None:
        props["count"] = PropertyValue(value=count, unit="", source="declared")
    return ComponentSpec(suggested_key="frame_standoff", completeness="high", properties=props)


def _plate_spec(length_mm: float | None = 100.0, width_mm: float | None = 100.0, height_mm: float | None = 4.0) -> ComponentSpec:
    props: dict[str, PropertyValue] = {}
    if length_mm is not None:
        props["length_mm"] = PropertyValue(value=length_mm, unit="mm", source="declared")
    if width_mm is not None:
        props["width_mm"] = PropertyValue(value=width_mm, unit="mm", source="declared")
    if height_mm is not None:
        props["height_mm"] = PropertyValue(value=height_mm, unit="mm", source="declared")
    return ComponentSpec(suggested_key="frame_plate", completeness="high", properties=props)


def _motors_spec(motor_count: float | None = 4) -> ComponentSpec:
    props: dict[str, PropertyValue] = {"diameter_mm": PropertyValue(value=27.9, unit="mm", source="declared")}
    if motor_count is not None:
        props["motor_count"] = PropertyValue(value=motor_count, unit="", source="declared")
    return ComponentSpec(suggested_key="motors", completeness="high", properties=props)


def _propellers_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="propellers", completeness="high",
        properties={"diameter_in": PropertyValue(value=5.0, unit="in", source="declared")},
    )


def _frame_arm_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="frame_arm", completeness="high",
        properties={
            "length_mm": PropertyValue(value=80.0, unit="mm", source="declared"),
            "width_mm": PropertyValue(value=20.0, unit="mm", source="declared"),
            "height_mm": PropertyValue(value=4.0, unit="mm", source="declared"),
        },
    )


def _prop_adapter_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="prop_adapter", completeness="medium",
        properties={
            "length_mm": PropertyValue(value=12.0, unit="mm", source="declared"),
            "width_mm": PropertyValue(value=12.0, unit="mm", source="declared"),
            "height_mm": PropertyValue(value=8.0, unit="mm", source="declared"),
        },
    )


def _frame_spec(configuration: str = "quad_x", wheelbase_mm: float = 230.0) -> ComponentSpec:
    return ComponentSpec(
        suggested_key="frame", completeness="high",
        properties={
            "configuration": PropertyValue(value=configuration, unit="", source="declared"),
            "wheelbase_mm": PropertyValue(value=wheelbase_mm, unit="mm", source="declared"),
        },
    )


def _state(components: dict) -> ProjectState:
    return ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=DesignProperties(components=components),
    )


def _nodes_by_id(state: ProjectState) -> dict[str, dict]:
    return {n["id"]: n for n in project_spatial_nodes(state)}


def _points(offsets: list[dict]) -> set[tuple[float, float]]:
    return {(o["xMm"], o["yMm"]) for o in offsets}


_CORNERS_100 = {(47.5, 47.5), (47.5, -47.5), (-47.5, -47.5), (-47.5, 47.5)}


def test_p1_count_4_regression_same_corner_points():
    nodes = _nodes_by_id(_state({
        "frame_standoff": _standoff_spec(count=4.0),
        "frame_plate": _plate_spec(),
    }))
    standoff = nodes["frame_standoff"]
    assert standoff["solidCopies"] == 4
    assert _points(standoff["solidCopyOffsetsMm"]) == _CORNERS_100
    assert all(o["zMm"] == 0.0 for o in standoff["solidCopyOffsetsMm"])


def test_p2_count_absent_yields_no_copies():
    nodes = _nodes_by_id(_state({
        "frame_standoff": _standoff_spec(count=None),
        "frame_plate": _plate_spec(),
    }))
    standoff = nodes["frame_standoff"]
    assert "solidCopies" not in standoff
    assert "solidCopyOffsetsMm" not in standoff


def test_p3_count_3_yields_no_copies():
    nodes = _nodes_by_id(_state({
        "frame_standoff": _standoff_spec(count=3.0),
        "frame_plate": _plate_spec(),
    }))
    standoff = nodes["frame_standoff"]
    assert "solidCopies" not in standoff
    assert "solidCopyOffsetsMm" not in standoff


def test_p4_count_6_yields_six_perimeter_points():
    nodes = _nodes_by_id(_state({
        "frame_standoff": _standoff_spec(count=6.0),
        "frame_plate": _plate_spec(),
    }))
    standoff = nodes["frame_standoff"]
    assert standoff["solidCopies"] == 6
    expected = _CORNERS_100 | {(0.0, 47.5), (0.0, -47.5)}
    assert _points(standoff["solidCopyOffsetsMm"]) == expected
    assert all(o["zMm"] == 0.0 for o in standoff["solidCopyOffsetsMm"])


def test_p5_count_8_yields_eight_perimeter_points():
    nodes = _nodes_by_id(_state({
        "frame_standoff": _standoff_spec(count=8.0),
        "frame_plate": _plate_spec(),
    }))
    standoff = nodes["frame_standoff"]
    assert standoff["solidCopies"] == 8
    expected = _CORNERS_100 | {(0.0, 47.5), (0.0, -47.5), (47.5, 0.0), (-47.5, 0.0)}
    assert _points(standoff["solidCopyOffsetsMm"]) == expected


def test_p6_count_6_lp_greater_than_wp_mids_on_hy():
    # Plate 120x80: Lp=120 >= Wp=80 -> long edges are the ones at
    # constant y=±hy. hx = 60-2.5=57.5, hy = 40-2.5=37.5.
    nodes = _nodes_by_id(_state({
        "frame_standoff": _standoff_spec(count=6.0),
        "frame_plate": _plate_spec(length_mm=120.0, width_mm=80.0),
    }))
    offsets = nodes["frame_standoff"]["solidCopyOffsetsMm"]
    corners = {(57.5, 37.5), (57.5, -37.5), (-57.5, -37.5), (-57.5, 37.5)}
    mids = {(0.0, 37.5), (0.0, -37.5)}
    assert _points(offsets) == corners | mids


def test_p7_count_6_wp_greater_than_lp_mids_on_hx():
    # Plate 80x120: Wp=120 > Lp=80 -> long edges are the ones at
    # constant x=±hx. hx = 40-2.5=37.5, hy = 60-2.5=57.5.
    nodes = _nodes_by_id(_state({
        "frame_standoff": _standoff_spec(count=6.0),
        "frame_plate": _plate_spec(length_mm=80.0, width_mm=120.0),
    }))
    offsets = nodes["frame_standoff"]["solidCopyOffsetsMm"]
    corners = {(37.5, 57.5), (37.5, -57.5), (-37.5, -57.5), (-37.5, 57.5)}
    mids = {(37.5, 0.0), (-37.5, 0.0)}
    assert _points(offsets) == corners | mids


def test_p8_fail_closed_oversized_standoff_or_missing_plate():
    oversized = _nodes_by_id(_state({
        "frame_standoff": _standoff_spec(length_mm=200.0, count=6.0),
        "frame_plate": _plate_spec(),
    }))
    assert "solidCopies" not in oversized["frame_standoff"]
    assert "solidCopyOffsetsMm" not in oversized["frame_standoff"]

    no_plate = _nodes_by_id(_state({"frame_standoff": _standoff_spec(count=8.0)}))
    assert "solidCopies" not in no_plate["frame_standoff"]
    assert "solidCopyOffsetsMm" not in no_plate["frame_standoff"]


def test_p9_one_node_and_motor_family_regressions_green():
    node_list = project_spatial_nodes(_state({
        "motors": _motors_spec(),
        "propellers": _propellers_spec(),
        "frame_arm": _frame_arm_spec(),
        "prop_adapter": _prop_adapter_spec(),
        "frame_standoff": _standoff_spec(count=6.0),
        "frame_plate": _plate_spec(),
        "frame": _frame_spec(),
    }))
    assert sum(1 for n in node_list if n["id"] == "frame_standoff") == 1
    nodes = {n["id"]: n for n in node_list}
    assert nodes["motors"]["solidCopies"] == 4
    assert nodes["propellers"]["solidCopies"] == 4
    assert nodes["frame_arm"]["solidCopies"] == 4
    assert nodes["prop_adapter"]["solidCopies"] == 4
    assert nodes["frame_standoff"]["solidCopies"] == 6


def test_p10_offsets_still_differ_from_quad_x_stations():
    nodes = _nodes_by_id(_state({
        "frame_standoff": _standoff_spec(count=8.0),
        "frame_plate": _plate_spec(),
        "motors": _motors_spec(),
        "frame": _frame_spec(),
    }))
    standoff_offsets = nodes["frame_standoff"]["solidCopyOffsetsMm"]
    motors_offsets = nodes["motors"]["solidCopyOffsetsMm"]
    assert standoff_offsets != motors_offsets
    assert len(standoff_offsets) != len(motors_offsets)
