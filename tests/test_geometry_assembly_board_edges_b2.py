"""Geometry Assembly Board edges B2 (`mountedOn` projector DTO).

Covers implementation_contract_geometry_assembly_board_edges_b2.md §4 T1–T5.
"""
from __future__ import annotations

from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes


def _state(components: dict[str, ComponentSpec]) -> ProjectState:
    return ProjectState(
        project_id="edges-b2",
        project_slug="edges-b2",
        objective="board edges b2",
        workspace_path="/tmp/edges-b2",
        design_properties=DesignProperties(
            system_defined=True,
            system_blocks=["control", "structure"],
            components=components,
        ),
    )


def test_t1_mounted_on_target_present_emits_mounted_on_dto():
    state = _state({
        "flight_controller": ComponentSpec(
            suggested_key="flight_controller",
            completeness="high",
            mounted_on="frame_plate",
        ),
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_plate": ComponentSpec(
            suggested_key="frame_plate",
            component_type="structure_part",
            parent_key="frame",
            completeness="medium",
        ),
    })
    nodes = project_spatial_nodes(state)
    fc = next(n for n in nodes if n["id"] == "flight_controller")
    assert fc["mountedOn"] == "frame_plate"


def test_t2_stale_target_omits_mounted_on_keeps_text_field():
    state = _state({
        "flight_controller": ComponentSpec(
            suggested_key="flight_controller",
            completeness="high",
            mounted_on="frame_plate_gone",
            properties={"model": PropertyValue(value="pixhawk")},
        ),
    })
    nodes = project_spatial_nodes(state)
    fc = next(n for n in nodes if n["id"] == "flight_controller")
    assert "mountedOn" not in fc
    assert {"label": "montado en", "value": "frame_plate_gone"} in fc["fields"]


def test_t3_no_mounted_on_omits_dto_key():
    state = _state({
        "flight_controller": ComponentSpec(
            suggested_key="flight_controller", completeness="high",
        ),
    })
    nodes = project_spatial_nodes(state)
    fc = next(n for n in nodes if n["id"] == "flight_controller")
    assert "mountedOn" not in fc


def test_t4_mounted_on_dto_does_not_change_layout_or_kind():
    base = {
        "motors": ComponentSpec(suggested_key="motors", completeness="high"),
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_arm": ComponentSpec(
            suggested_key="frame_arm",
            component_type="structure_part",
            parent_key="frame",
            completeness="medium",
        ),
    }
    unset = project_spatial_nodes(_state(base))
    mounted = project_spatial_nodes(_state({
        **base,
        "motors": ComponentSpec(
            suggested_key="motors", completeness="high", mounted_on="frame_arm",
        ),
    }))
    a = next(n for n in unset if n["id"] == "motors")
    b = next(n for n in mounted if n["id"] == "motors")
    assert a["kind"] == b["kind"] == "component"
    assert a["x"] == b["x"]
    assert a["y"] == b["y"]
    assert b["mountedOn"] == "frame_arm"


def test_t5_montado_en_text_field_still_emitted_when_set():
    state = _state({
        "esc": ComponentSpec(
            suggested_key="esc", completeness="high", mounted_on="frame_plate",
        ),
        "frame": ComponentSpec(suggested_key="frame", completeness="high"),
        "frame_plate": ComponentSpec(
            suggested_key="frame_plate",
            component_type="structure_part",
            parent_key="frame",
            completeness="medium",
        ),
    })
    nodes = project_spatial_nodes(state)
    esc = next(n for n in nodes if n["id"] == "esc")
    assert {"label": "montado en", "value": "frame_plate"} in esc["fields"]
    assert esc["mountedOn"] == "frame_plate"
