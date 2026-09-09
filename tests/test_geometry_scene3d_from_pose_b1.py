"""Scene3D-from-pose B1 (visor reads declared_box_pose).

Covers implementation_contract_geometry_scene3d_from_pose_b1.md's projector
side — the ``declaredBoxPose`` DTO key on ``project_spatial_nodes`` output,
which is the ONE gate (``_declared_box_pose_dto``) shared with the existing
"origen pose" text fields:
  P1  Box origin, single axis -> DTO present with only that axis key
  P2  Box origin, all three axes -> DTO + text fields both show all three
  P3  Disk origin -> DTO omitted AND text fields omitted (not just DTO)
  P4  Origin key vanished from components -> DTO + text fields omitted
  P5  No declared_box_pose at all -> no declaredBoxPose key on the node
  P6  Omitted axis (only x_mm set) never appears as 0 in the DTO or text
"""
from __future__ import annotations

import pytest

from jarvis.schemas.action_schema import ComponentSpec, DeclaredBoxPose, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes


def _fc_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="flight_controller", completeness="high",
        properties={
            "length_mm": PropertyValue(value=44.0, unit="mm", source="declared"),
            "width_mm": PropertyValue(value=84.0, unit="mm", source="declared"),
            "height_mm": PropertyValue(value=12.0, unit="mm", source="declared"),
        },
    )


def _state(esc: ComponentSpec, extra: dict | None = None) -> ProjectState:
    components = {
        "esc": esc,
        "flight_controller": _fc_spec(),
        "motors": ComponentSpec(
            suggested_key="motors", completeness="high",
            properties={"diameter_mm": PropertyValue(value=27.9, unit="mm", source="declared")},
        ),
    }
    if extra:
        components.update(extra)
    return ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=DesignProperties(components=components),
    )


def _esc_node(state: ProjectState) -> dict:
    nodes = project_spatial_nodes(state)
    return next(n for n in nodes if n["id"] == "esc")


def test_p1_box_origin_single_axis_dto_has_only_that_axis():
    esc = ComponentSpec(
        suggested_key="esc", completeness="high",
        declared_box_pose=DeclaredBoxPose(origin_key="flight_controller", x_mm=5.0),
    )
    node = _esc_node(_state(esc))
    assert node["declaredBoxPose"] == {"originKey": "flight_controller", "xMm": 5.0}


def test_p2_box_origin_all_three_axes_dto_and_text_both_show_all_three():
    esc = ComponentSpec(
        suggested_key="esc", completeness="high",
        declared_box_pose=DeclaredBoxPose(
            origin_key="flight_controller", x_mm=5.0, y_mm=3.0, z_mm=-2.0
        ),
    )
    node = _esc_node(_state(esc))
    assert node["declaredBoxPose"] == {
        "originKey": "flight_controller", "xMm": 5.0, "yMm": 3.0, "zMm": -2.0,
    }
    assert {"label": "Δx mm", "value": "5"} in node["fields"]
    assert {"label": "Δy mm", "value": "3"} in node["fields"]
    assert {"label": "Δz mm", "value": "-2"} in node["fields"]


def test_p3_disk_origin_omits_dto_and_text():
    esc = ComponentSpec(
        suggested_key="esc", completeness="high",
        declared_box_pose=DeclaredBoxPose(origin_key="motors", x_mm=5.0),
    )
    node = _esc_node(_state(esc))
    assert "declaredBoxPose" not in node
    assert not any(f["label"] == "origen pose" for f in node["fields"])
    assert not any(f["label"] == "Δx mm" for f in node["fields"])


def test_p4_vanished_origin_key_omits_dto_and_text():
    esc = ComponentSpec(
        suggested_key="esc", completeness="high",
        declared_box_pose=DeclaredBoxPose(origin_key="does_not_exist", x_mm=5.0),
    )
    node = _esc_node(_state(esc))
    assert "declaredBoxPose" not in node
    assert not any(f["label"] == "origen pose" for f in node["fields"])


def test_p5_no_pose_no_dto_key_at_all():
    esc = ComponentSpec(suggested_key="esc", completeness="high")
    node = _esc_node(_state(esc))
    assert "declaredBoxPose" not in node
    assert not any(f["label"] == "origen pose" for f in node["fields"])


def test_p6_omitted_axis_never_appears_as_zero():
    esc = ComponentSpec(
        suggested_key="esc", completeness="high",
        declared_box_pose=DeclaredBoxPose(origin_key="flight_controller", x_mm=5.0),
    )
    node = _esc_node(_state(esc))
    assert "yMm" not in node["declaredBoxPose"]
    assert "zMm" not in node["declaredBoxPose"]
    assert not any(f["label"] == "Δy mm" for f in node["fields"])
    assert not any(f["label"] == "Δz mm" for f in node["fields"])
