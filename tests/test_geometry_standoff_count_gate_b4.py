"""Standoff count gate for corner copies B4-min.

Covers implementation_contract_geometry_standoff_count_gate_b4.md §3 —
`frame_standoff`'s corner `solidCopies`/`solidCopyOffsetsMm` (Frame
standoff x4 at Main Plate corners B1) now ALSO require the standoff's own
declared `properties["count"]` to parse (`_parse_solid_copies_count`,
whole number in [2,16]) to EXACTLY 4 — the same source
`frame_part_specs_from_catalog` already projects from a catalog
`FrameSpec.standoff_count` when a seed states it. Missing, non-numeric,
out-of-range, or any N != 4 all omit BOTH keys — this supersedes B3's own
unconditional default of 4 (a standoff box + Main Plate box alone is no
longer sufficient). The corner formula itself (Main Plate footprint inset)
is completely unchanged — see test_geometry_frame_standoff_corners_b1.py
for that coverage. Fixture numbers: standoff 5/5/25, plate 100/100/4 ->
offsets (±47.5, ±47.5, 0). Never 230, never an invented Rooster count.

  P1  Standoff box + Main Plate 100x100 + standoff 5x5 + count=4 ->
      solidCopies==4, offsets (±47.5, ±47.5, 0)
  P2  Same boxes, count ABSENT -> no solidCopies (regression vs B3's own
      default — this must NOT stay green)
  P3  Same boxes, count=6 (or 3) -> no copies
  P4  count=4 but missing standoff box or plate L×W -> no copies
  P5  count=4 but standoff larger than plate -> no copies
  P6  Offsets still != motors' quad-X points (wheelbase 230 present)
  P7  Exactly one frame_standoff node
  P8  Motors/propellers/frame_arm/prop_adapter copy regressions still
      green
"""
from __future__ import annotations

import pytest

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


def test_p1_count_4_yields_corner_copies():
    nodes = _nodes_by_id(_state({
        "frame_standoff": _standoff_spec(count=4.0),
        "frame_plate": _plate_spec(),
    }))
    standoff = nodes["frame_standoff"]
    assert standoff["solidCopies"] == 4
    offsets = standoff["solidCopyOffsetsMm"]
    expected = {(47.5, 47.5), (47.5, -47.5), (-47.5, -47.5), (-47.5, 47.5)}
    actual = {(o["xMm"], o["yMm"]) for o in offsets}
    assert actual == expected


def test_p2_count_absent_yields_no_copies_regression_vs_b3_default():
    nodes = _nodes_by_id(_state({
        "frame_standoff": _standoff_spec(count=None),
        "frame_plate": _plate_spec(),
    }))
    standoff = nodes["frame_standoff"]
    # B3 used to draw 4 unconditionally here — B4-min removes that default.
    assert "solidCopies" not in standoff
    assert "solidCopyOffsetsMm" not in standoff
    # The single box is still honestly drawn — just never copied.
    assert standoff["geometry"] == {"shape": "box", "length_mm": 5.0, "width_mm": 5.0, "height_mm": 25.0}


@pytest.mark.parametrize("count", [3, 6])
def test_p3_count_not_4_yields_no_copies(count):
    nodes = _nodes_by_id(_state({
        "frame_standoff": _standoff_spec(count=count),
        "frame_plate": _plate_spec(),
    }))
    standoff = nodes["frame_standoff"]
    assert "solidCopies" not in standoff
    assert "solidCopyOffsetsMm" not in standoff


def test_p4_count_4_but_missing_standoff_or_plate_geometry_yields_no_copies():
    no_standoff_geom = _nodes_by_id(_state({
        "frame_standoff": ComponentSpec(
            suggested_key="frame_standoff", completeness="medium",
            properties={"count": PropertyValue(value=4, unit="", source="declared")},
        ),
        "frame_plate": _plate_spec(),
    }))
    assert "solidCopies" not in no_standoff_geom["frame_standoff"]

    no_plate = _nodes_by_id(_state({"frame_standoff": _standoff_spec(count=4.0)}))
    assert "solidCopies" not in no_plate["frame_standoff"]

    plate_no_lxw = _nodes_by_id(_state({
        "frame_standoff": _standoff_spec(count=4.0),
        "frame_plate": _plate_spec(length_mm=None, width_mm=None, height_mm=4.0),
    }))
    assert "solidCopies" not in plate_no_lxw["frame_standoff"]


def test_p5_count_4_but_standoff_larger_than_plate_fails_closed():
    nodes = _nodes_by_id(_state({
        "frame_standoff": _standoff_spec(length_mm=200.0, count=4.0),
        "frame_plate": _plate_spec(),
    }))
    standoff = nodes["frame_standoff"]
    assert "solidCopies" not in standoff
    assert "solidCopyOffsetsMm" not in standoff


def test_p6_offsets_differ_from_motors_quad_x_points():
    nodes = _nodes_by_id(_state({
        "frame_standoff": _standoff_spec(count=4.0),
        "frame_plate": _plate_spec(),
        "motors": _motors_spec(),
        "frame": _frame_spec(),
    }))
    standoff_offsets = nodes["frame_standoff"]["solidCopyOffsetsMm"]
    motors_offsets = nodes["motors"]["solidCopyOffsetsMm"]
    assert standoff_offsets != motors_offsets
    for o in standoff_offsets:
        assert abs(o["xMm"]) == 47.5
        assert abs(o["yMm"]) == 47.5


def test_p7_exactly_one_frame_standoff_node():
    node_list = project_spatial_nodes(_state({
        "frame_standoff": _standoff_spec(count=4.0),
        "frame_plate": _plate_spec(),
    }))
    assert sum(1 for n in node_list if n["id"] == "frame_standoff") == 1


def test_p8_motors_propellers_arm_adapter_regressions_still_green():
    nodes = _nodes_by_id(_state({
        "motors": _motors_spec(),
        "propellers": _propellers_spec(),
        "frame_arm": _frame_arm_spec(),
        "prop_adapter": _prop_adapter_spec(),
        "frame_standoff": _standoff_spec(count=4.0),
        "frame_plate": _plate_spec(),
        "frame": _frame_spec(),
    }))
    assert nodes["motors"]["solidCopies"] == 4
    assert nodes["propellers"]["solidCopies"] == 4
    assert nodes["frame_arm"]["solidCopies"] == 4
    assert nodes["prop_adapter"]["solidCopies"] == 4
    quad_x_offsets = nodes["motors"]["solidCopyOffsetsMm"]
    assert nodes["propellers"]["solidCopyOffsetsMm"] == quad_x_offsets
    assert nodes["frame_arm"]["solidCopyOffsetsMm"] == quad_x_offsets
    assert nodes["prop_adapter"]["solidCopyOffsetsMm"] == quad_x_offsets
    assert nodes["frame_standoff"]["solidCopies"] == 4
    assert nodes["frame_standoff"]["solidCopyOffsetsMm"] != quad_x_offsets
