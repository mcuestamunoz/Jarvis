"""Motor visor copies from the project's motor_count B1.

Covers implementation_contract_geometry_motor_count_instances_b1.md §3.1/§3.2:
  P1  motor_count=3 + disk -> geometry present, solidCopies==3; propellers
      untouched; still one node id=="motors"
  P2  motor_count=3 without diameter -> no geometry, no solidCopies
  P3  no motor_count + disk -> geometry present, no solidCopies key
  P4  motor_count=4 + disk -> solidCopies==4 (declared, never a default)
  P5  frame configuration=quad_x + motors motor_count=3 -> still 3 (quad_x
      does not win)
  P6  motor_count=1 + disk -> no solidCopies key
  P7  motor_count=3.5 + disk -> no solidCopies key
"""
from __future__ import annotations

from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes


def _motors_spec(motor_count: float | None = None, diameter_mm: float | None = 27.9) -> ComponentSpec:
    props: dict[str, PropertyValue] = {}
    if diameter_mm is not None:
        props["diameter_mm"] = PropertyValue(value=diameter_mm, unit="mm", source="declared")
    if motor_count is not None:
        props["motor_count"] = PropertyValue(value=motor_count, unit="", source="calculated")
    return ComponentSpec(suggested_key="motors", completeness="high", properties=props)


def _propellers_spec() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="propellers", completeness="high",
        properties={"diameter_in": PropertyValue(value=5.0, unit="in", source="declared")},
    )


def _state(motors: ComponentSpec, extra: dict[str, ComponentSpec] | None = None) -> ProjectState:
    components = {"motors": motors, "propellers": _propellers_spec()}
    if extra:
        components.update(extra)
    return ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=DesignProperties(components=components),
    )


def _nodes_by_id(state: ProjectState) -> dict[str, dict]:
    return {n["id"]: n for n in project_spatial_nodes(state)}


def test_p1_motor_count_3_with_disk_geometry_yields_solid_copies_3():
    nodes = _nodes_by_id(_state(_motors_spec(motor_count=3)))
    motors = nodes["motors"]
    assert motors["geometry"] == {"shape": "disk", "diameter_mm": 27.9}
    assert motors["solidCopies"] == 3
    assert "solidCopies" not in nodes["propellers"]
    assert sum(1 for n in nodes.values() if n["id"] == "motors") == 1


def test_p2_motor_count_without_geometry_yields_no_geometry_and_no_copies():
    nodes = _nodes_by_id(_state(_motors_spec(motor_count=3, diameter_mm=None)))
    motors = nodes["motors"]
    assert "geometry" not in motors
    assert "solidCopies" not in motors


def test_p3_geometry_without_motor_count_yields_geometry_but_no_copies():
    nodes = _nodes_by_id(_state(_motors_spec(motor_count=None)))
    motors = nodes["motors"]
    assert motors["geometry"] == {"shape": "disk", "diameter_mm": 27.9}
    assert "solidCopies" not in motors


def test_p4_motor_count_4_is_honored_when_declared_not_defaulted():
    nodes = _nodes_by_id(_state(_motors_spec(motor_count=4)))
    assert nodes["motors"]["solidCopies"] == 4


def test_p5_frame_quad_x_configuration_does_not_override_motor_count():
    frame = ComponentSpec(
        suggested_key="frame", completeness="high",
        properties={"configuration": PropertyValue(value="quad_x", unit="", source="declared")},
    )
    nodes = _nodes_by_id(_state(_motors_spec(motor_count=3), extra={"frame": frame}))
    assert nodes["motors"]["solidCopies"] == 3


def test_p6_motor_count_1_yields_no_solid_copies_key():
    nodes = _nodes_by_id(_state(_motors_spec(motor_count=1)))
    assert "solidCopies" not in nodes["motors"]


def test_p7_non_integer_motor_count_yields_no_solid_copies_key():
    nodes = _nodes_by_id(_state(_motors_spec(motor_count=3.5)))
    assert "solidCopies" not in nodes["motors"]
