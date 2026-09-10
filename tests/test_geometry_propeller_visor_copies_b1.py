"""Propeller visor copies from motors spec motor_count B1.

Covers implementation_contract_geometry_propeller_visor_copies_b1.md
§3.1-3.2:
  P1  motors motor_count=3 without Ø + prop disk -> motors no
      geometry/solidCopies; propellers geometry present, solidCopies==3;
      one node id=="propellers"
  P2  motors disk + motor_count=3 + prop disk -> both solidCopies==3
  P3  motors disk + motor_count=3 + prop without diameter -> motors
      solidCopies==3; propellers no geometry, no solidCopies
  P4  no motor_count + prop disk -> propellers geometry, no solidCopies
  P5  motor_count=4 + prop disk -> propellers solidCopies==4 (declared,
      never a default)
  P6  frame configuration=quad_x + motors motor_count=3 + prop disk ->
      propellers solidCopies==3 (quad_x does not win)
  P7  motor_count=1 + prop disk -> no solidCopies on propellers
  P8  motor_count=3.5 + prop disk -> no solidCopies on propellers
  P9  current_parameters.motor_count=4 + motors spec motor_count=3 + prop
      disk -> propellers solidCopies==3 (params must not win)
  P10 no motors component + prop disk -> no solidCopies on propellers
"""
from __future__ import annotations

from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes


def _motors_spec(
    motor_count: float | None = None, diameter_mm: float | None = None
) -> ComponentSpec:
    props: dict[str, PropertyValue] = {}
    if diameter_mm is not None:
        props["diameter_mm"] = PropertyValue(value=diameter_mm, unit="mm", source="declared")
    if motor_count is not None:
        props["motor_count"] = PropertyValue(value=motor_count, unit="", source="calculated")
    return ComponentSpec(suggested_key="motors", completeness="high", properties=props)


def _propellers_spec(diameter_in: float | None = 5.0) -> ComponentSpec:
    props: dict[str, PropertyValue] = {}
    if diameter_in is not None:
        props["diameter_in"] = PropertyValue(value=diameter_in, unit="in", source="declared")
    return ComponentSpec(suggested_key="propellers", completeness="high", properties=props)


def _state(
    components: dict[str, ComponentSpec], current_parameters: dict | None = None
) -> ProjectState:
    return ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        current_parameters=current_parameters or {},
        design_properties=DesignProperties(components=components),
    )


def _nodes_by_id(state: ProjectState) -> dict[str, dict]:
    return {n["id"]: n for n in project_spatial_nodes(state)}


def test_p1_motors_no_diameter_propellers_disk_solid_copies_3():
    nodes = _nodes_by_id(_state({
        "motors": _motors_spec(motor_count=3, diameter_mm=None),
        "propellers": _propellers_spec(),
    }))
    motors = nodes["motors"]
    propellers = nodes["propellers"]
    assert "geometry" not in motors
    assert "solidCopies" not in motors
    assert propellers["geometry"] == {"shape": "disk", "diameter_mm": 127.0}
    assert propellers["solidCopies"] == 3
    assert sum(1 for n in nodes.values() if n["id"] == "propellers") == 1


def test_p2_both_disks_both_solid_copies_3():
    nodes = _nodes_by_id(_state({
        "motors": _motors_spec(motor_count=3, diameter_mm=27.9),
        "propellers": _propellers_spec(),
    }))
    assert nodes["motors"]["solidCopies"] == 3
    assert nodes["propellers"]["solidCopies"] == 3


def test_p3_propellers_without_diameter_no_geometry_no_copies():
    nodes = _nodes_by_id(_state({
        "motors": _motors_spec(motor_count=3, diameter_mm=27.9),
        "propellers": _propellers_spec(diameter_in=None),
    }))
    assert nodes["motors"]["solidCopies"] == 3
    assert "geometry" not in nodes["propellers"]
    assert "solidCopies" not in nodes["propellers"]


def test_p4_no_motor_count_propellers_geometry_no_copies():
    nodes = _nodes_by_id(_state({
        "motors": _motors_spec(motor_count=None, diameter_mm=None),
        "propellers": _propellers_spec(),
    }))
    propellers = nodes["propellers"]
    assert propellers["geometry"] == {"shape": "disk", "diameter_mm": 127.0}
    assert "solidCopies" not in propellers


def test_p5_motor_count_4_is_honored_when_declared_not_defaulted():
    nodes = _nodes_by_id(_state({
        "motors": _motors_spec(motor_count=4, diameter_mm=None),
        "propellers": _propellers_spec(),
    }))
    assert nodes["propellers"]["solidCopies"] == 4


def test_p6_frame_quad_x_configuration_does_not_override_motor_count():
    frame = ComponentSpec(
        suggested_key="frame", completeness="high",
        properties={"configuration": PropertyValue(value="quad_x", unit="", source="declared")},
    )
    nodes = _nodes_by_id(_state({
        "motors": _motors_spec(motor_count=3, diameter_mm=None),
        "propellers": _propellers_spec(),
        "frame": frame,
    }))
    assert nodes["propellers"]["solidCopies"] == 3


def test_p7_motor_count_1_yields_no_solid_copies_on_propellers():
    nodes = _nodes_by_id(_state({
        "motors": _motors_spec(motor_count=1, diameter_mm=None),
        "propellers": _propellers_spec(),
    }))
    assert "solidCopies" not in nodes["propellers"]


def test_p8_non_integer_motor_count_yields_no_solid_copies_on_propellers():
    nodes = _nodes_by_id(_state({
        "motors": _motors_spec(motor_count=3.5, diameter_mm=None),
        "propellers": _propellers_spec(),
    }))
    assert "solidCopies" not in nodes["propellers"]


def test_p9_current_parameters_motor_count_must_not_win():
    nodes = _nodes_by_id(_state(
        {
            "motors": _motors_spec(motor_count=3, diameter_mm=None),
            "propellers": _propellers_spec(),
        },
        current_parameters={"motor_count": 4},
    ))
    assert nodes["propellers"]["solidCopies"] == 3


def test_p10_no_motors_component_yields_no_solid_copies_on_propellers():
    nodes = _nodes_by_id(_state({"propellers": _propellers_spec()}))
    assert "geometry" in nodes["propellers"]
    assert "solidCopies" not in nodes["propellers"]
