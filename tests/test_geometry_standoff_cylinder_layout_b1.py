"""Standoff cylinder visor layout B1.

Covers implementation_contract_geometry_standoff_cylinder_layout_b1.md
§3-4 — `frame_standoff` with cylinder glyph (Ø×H) uses the same 4/6/8
Main-Plate perimeter as box posts, with Ø as both inset axes. Box path
stays byte-identical (P2 re-asserts B7 count=8 / 5×5 / 100×100). Disk
(Ø, no axial H) omits. Catalog L×W is never invented.

  P1  MY5 fixture: plate 161×42 box + Ø6×30 cylinder + count=8
      → solidCopies==8, cylinder glyph, §0.1 point set
  P2  B7 box count=8 100×100 / 5×5 still 8 pts @ 47.5
  P3  Cylinder count=4 → 4 corners (±77.5, ±18, 0)
  P4  Oversized Ø vs plate width → no copies
  P5  Disk (Ø, no H) → no copies
  P6  Exactly one frame_standoff node
  P7  Offsets ≠ quad-X stations when wheelbase=225 present
"""
from __future__ import annotations

import pytest

from jarvis.core.catalog_bind import bind_frame_from_catalog, frame_part_specs_from_catalog
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes

_SKU = "hglrc_my5_5in"

_MY5_CORNERS = {(77.5, 18.0), (77.5, -18.0), (-77.5, -18.0), (-77.5, 18.0)}
_MY5_MIDS = {(77.5, 0.0), (-77.5, 0.0), (0.0, 18.0), (0.0, -18.0)}
_MY5_N8 = _MY5_CORNERS | _MY5_MIDS
_B7_CORNERS_100 = {(47.5, 47.5), (47.5, -47.5), (-47.5, -47.5), (-47.5, 47.5)}
_B7_N8 = _B7_CORNERS_100 | {(0.0, 47.5), (0.0, -47.5), (47.5, 0.0), (-47.5, 0.0)}


def _cylinder_standoff(
    *,
    diameter_mm: float | None = 6.0,
    height_mm: float | None = 30.0,
    count: float | None = 8.0,
) -> ComponentSpec:
    props: dict[str, PropertyValue] = {}
    if diameter_mm is not None:
        props["diameter_mm"] = PropertyValue(value=diameter_mm, unit="mm", source="declared")
    if height_mm is not None:
        props["height_mm"] = PropertyValue(value=height_mm, unit="mm", source="declared")
    if count is not None:
        props["count"] = PropertyValue(value=count, unit="", source="declared")
    return ComponentSpec(suggested_key="frame_standoff", completeness="high", properties=props)


def _box_standoff(
    length_mm: float = 5.0, width_mm: float = 5.0, height_mm: float = 25.0, count: float = 8.0,
) -> ComponentSpec:
    return ComponentSpec(
        suggested_key="frame_standoff", completeness="high",
        properties={
            "length_mm": PropertyValue(value=length_mm, unit="mm", source="declared"),
            "width_mm": PropertyValue(value=width_mm, unit="mm", source="declared"),
            "height_mm": PropertyValue(value=height_mm, unit="mm", source="declared"),
            "count": PropertyValue(value=count, unit="", source="declared"),
        },
    )


def _plate_spec(length_mm: float = 161.0, width_mm: float = 42.0, height_mm: float = 2.0) -> ComponentSpec:
    return ComponentSpec(
        suggested_key="frame_plate", completeness="high",
        properties={
            "length_mm": PropertyValue(value=length_mm, unit="mm", source="declared"),
            "width_mm": PropertyValue(value=width_mm, unit="mm", source="declared"),
            "height_mm": PropertyValue(value=height_mm, unit="mm", source="declared"),
        },
    )


def _motors_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="motors", completeness="high",
        properties={
            "diameter_mm": PropertyValue(value=27.9, unit="mm", source="declared"),
            "motor_count": PropertyValue(value=4, unit="", source="declared"),
        },
    )


def _frame_spec(wheelbase_mm: float = 225.0) -> ComponentSpec:
    return ComponentSpec(
        suggested_key="frame", completeness="high",
        properties={
            "configuration": PropertyValue(value="quad_x", unit="", source="declared"),
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


def test_p1_my5_cylinder_count_8_perimeter():
    nodes = _nodes_by_id(_state({
        "frame_standoff": _cylinder_standoff(),
        "frame_plate": _plate_spec(),
    }))
    standoff = nodes["frame_standoff"]
    assert standoff["geometry"]["shape"] == "cylinder"
    assert standoff["geometry"]["diameter_mm"] == pytest.approx(6.0)
    assert standoff["geometry"]["height_mm"] == pytest.approx(30.0)
    assert "length_mm" not in standoff["geometry"]
    assert standoff["solidCopies"] == 8
    assert _points(standoff["solidCopyOffsetsMm"]) == _MY5_N8
    assert all(o["zMm"] == 0.0 for o in standoff["solidCopyOffsetsMm"])


def test_p2_box_count_8_b7_regression():
    nodes = _nodes_by_id(_state({
        "frame_standoff": _box_standoff(),
        "frame_plate": _plate_spec(length_mm=100.0, width_mm=100.0, height_mm=4.0),
    }))
    standoff = nodes["frame_standoff"]
    assert standoff["geometry"]["shape"] == "box"
    assert standoff["solidCopies"] == 8
    assert _points(standoff["solidCopyOffsetsMm"]) == _B7_N8


def test_p3_cylinder_count_4_corners_only():
    nodes = _nodes_by_id(_state({
        "frame_standoff": _cylinder_standoff(count=4.0),
        "frame_plate": _plate_spec(),
    }))
    standoff = nodes["frame_standoff"]
    assert standoff["solidCopies"] == 4
    assert _points(standoff["solidCopyOffsetsMm"]) == _MY5_CORNERS
    assert all(o["zMm"] == 0.0 for o in standoff["solidCopyOffsetsMm"])


def test_p4_oversized_diameter_omits():
    # Ø50 vs plate width 42 → hy = 21 - 25 < 0
    nodes = _nodes_by_id(_state({
        "frame_standoff": _cylinder_standoff(diameter_mm=50.0),
        "frame_plate": _plate_spec(),
    }))
    standoff = nodes["frame_standoff"]
    assert "solidCopies" not in standoff
    assert "solidCopyOffsetsMm" not in standoff


def test_p5_disk_omits():
    nodes = _nodes_by_id(_state({
        "frame_standoff": _cylinder_standoff(height_mm=None),
        "frame_plate": _plate_spec(),
    }))
    standoff = nodes["frame_standoff"]
    assert standoff["geometry"]["shape"] == "disk"
    assert "solidCopies" not in standoff
    assert "solidCopyOffsetsMm" not in standoff


def test_p6_exactly_one_frame_standoff_node():
    node_list = project_spatial_nodes(_state({
        "frame_standoff": _cylinder_standoff(),
        "frame_plate": _plate_spec(),
    }))
    assert sum(1 for n in node_list if n["id"] == "frame_standoff") == 1


def test_p7_offsets_differ_from_quad_x_stations():
    nodes = _nodes_by_id(_state({
        "frame_standoff": _cylinder_standoff(),
        "frame_plate": _plate_spec(),
        "motors": _motors_spec(),
        "frame": _frame_spec(wheelbase_mm=225.0),
    }))
    standoff_offsets = nodes["frame_standoff"]["solidCopyOffsetsMm"]
    motors_offsets = nodes["motors"]["solidCopyOffsetsMm"]
    assert standoff_offsets != motors_offsets
    assert len(standoff_offsets) != len(motors_offsets)


def test_p1_catalog_my5_bind_does_not_invent_standoff_box():
    parts = frame_part_specs_from_catalog(_SKU)
    standoff = parts["frame_standoff"]
    assert "length_mm" not in standoff.properties
    assert "width_mm" not in standoff.properties
    assert standoff.properties["diameter_mm"].value == pytest.approx(6.0)

    components = {"frame": bind_frame_from_catalog(_SKU)}
    components.update(parts)
    nodes = _nodes_by_id(_state(components))
    node = nodes["frame_standoff"]
    assert node["geometry"]["shape"] == "cylinder"
    assert node["solidCopies"] == 8
    assert _points(node["solidCopyOffsetsMm"]) == _MY5_N8
