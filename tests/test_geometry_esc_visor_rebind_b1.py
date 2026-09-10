"""Live ESC visor via sourced SKU rebind B1.

Covers implementation_contract_geometry_esc_visor_rebind_b1.md §3/§4:
bind_esc_from_catalog(base=existing) preserves pose; IDLE cambiar esc
offers the 1-row Hobbywing catalog; pick is singleton expected_keys==["esc"]
only (not the propulsion composite).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.catalog_bind import (
    bind_battery_from_catalog,
    bind_esc_from_catalog,
    bind_frame_from_catalog,
    bind_motor_from_catalog,
    bind_propeller_from_catalog,
    frame_part_specs_from_catalog,
)
from jarvis.core.catalog_rebind_assist import resolve_idle_catalog_rebind
from jarvis.core.component_writers import (
    set_battery_component,
    set_control_component,
    set_frame_material,
    set_motor_component,
    set_propeller_component,
    upsert_frame_part,
)
from jarvis.core.orchestrator import JarvisOrchestrator, MISSING_COMPONENT_DEFINITION
from jarvis.core.state_manager import OrchestratorMode
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import CatalogRef, ComponentSpec, DeclaredBoxPose, PropertyValue
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes

_HOBBYWING = "hobbywing_xrotor_40a_6s"


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _fc_box() -> ComponentSpec:
    return ComponentSpec(
        suggested_key="flight_controller",
        completeness="high",
        source="declared",
        properties={
            "model": PropertyValue(value="pixhawk_4", confidence=0.9),
            "length_mm": PropertyValue(value=44.0, unit="mm", source="declared"),
            "width_mm": PropertyValue(value=84.0, unit="mm", source="declared"),
            "height_mm": PropertyValue(value=12.0, unit="mm", source="declared"),
        },
    )


def _freeform_esc(*, with_pose: bool) -> ComponentSpec:
    pose = (
        DeclaredBoxPose(origin_key="flight_controller", x_mm=5.0, y_mm=0.0, z_mm=0.0)
        if with_pose
        else None
    )
    return ComponentSpec(
        suggested_key="esc",
        completeness="high",
        source="declared",
        properties={"current_a": PropertyValue(value=40.0, unit="A", source="declared")},
        declared_box_pose=pose,
    )


def _projector_state(esc: ComponentSpec) -> ProjectState:
    return ProjectState(
        project_id="p1",
        project_slug="demo",
        objective="demo",
        workspace_path="/tmp/demo",
        design_properties=DesignProperties(
            components={"esc": esc, "flight_controller": _fc_box()}
        ),
    )


def _esc_node(state: ProjectState) -> dict:
    return next(n for n in project_spatial_nodes(state) if n["id"] == "esc")


def test_p1_bind_hobbywing_with_base_preserves_pose_and_projects_box():
    base = _freeform_esc(with_pose=True)
    bound = bind_esc_from_catalog(_HOBBYWING, base=base)
    state = set_control_component(_projector_state(base), bound)
    spec = state.design_properties.components["esc"]
    assert spec.catalog_ref == CatalogRef(family="esc", sku=_HOBBYWING)
    assert spec.declared_box_pose is not None
    assert spec.declared_box_pose.origin_key == "flight_controller"
    assert spec.declared_box_pose.x_mm == pytest.approx(5.0)
    node = _esc_node(state)
    assert node["geometry"] == {
        "shape": "box",
        "length_mm": 50.0,
        "width_mm": 21.6,
        "height_mm": 12.0,
    }
    assert node["declaredBoxPose"]["originKey"] == "flight_controller"
    assert node["declaredBoxPose"]["xMm"] == pytest.approx(5.0)
    assert sum(1 for n in project_spatial_nodes(state) if n["id"] == "esc") == 1


def test_p2_freeform_esc_has_no_geometry():
    node = _esc_node(_projector_state(_freeform_esc(with_pose=True)))
    assert "geometry" not in node
    assert node.get("declaredBoxPose", {}).get("originKey") == "flight_controller"


def test_p3_library_hobbywing_box_and_single_row():
    spec = default_library.get_esc(_HOBBYWING)
    assert spec.length_mm == pytest.approx(50.0)
    assert spec.width_mm == pytest.approx(21.6)
    assert spec.height_mm == pytest.approx(12.0)
    assert [e.name for e in default_library.list_escs()] == [_HOBBYWING]


@pytest.mark.parametrize(
    "phrase,expected",
    [
        ("cambiar esc", "esc"),
        ("ayúdame a elegir esc", "esc"),
        ("cambiar motor", "motors"),
        ("ayúdame a elegir", None),
        ("cambiar esc hobbywing_xrotor_40a_6s", None),
    ],
)
def test_p4_resolver_esc_family(phrase, expected):
    assert resolve_idle_catalog_rebind(phrase) == expected


def _closed_bound(tmp_path: Path) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    motor = max(default_library.list_motors(), key=lambda x: x.thrust_n)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "esc visor rebind b1",
            "payload_kg": 0.3,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "structure_mass_factor": 0.3,
            "safety_factor": 1.1,
            "motors": 4,
            "per_motor_max_thrust_n": motor.thrust_n,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    motor_bind = bind_motor_from_catalog({
        "idx": 1, "name": motor.name, "thrust_n": motor.thrust_n,
        "kv_rating": motor.kv_rating, "weight_g": motor.weight_g,
        "max_watts": motor.max_watts or 200, "is_generic": motor.is_generic,
    })
    ps = set_motor_component(ps, motor_bind, motor.max_watts or 200)
    ps = set_propeller_component(ps, bind_propeller_from_catalog("gemfan_5030"))
    ps = set_battery_component(ps, bind_battery_from_catalog("lipo_4s_5000mah"), 74.0)
    frame_bind = bind_frame_from_catalog("armattan_rooster_5in")
    ps = set_frame_material(
        ps,
        frame_bind.properties["mass_kg"].value,
        frame_bind.properties["material"].value,
        frame_bind.properties["size_class_inch"].value,
        catalog_ref=frame_bind.catalog_ref,
        component_name=frame_bind.name,
    )
    for key, spec in frame_part_specs_from_catalog("armattan_rooster_5in").items():
        ps = upsert_frame_part(ps, key, spec.properties, catalog_ref=spec.catalog_ref)
    sensors = ComponentSpec(
        suggested_key="sensors", completeness="medium", source="declared",
        properties={"gps_model": PropertyValue(value="ublox_m9n")},
    )
    components = dict(ps.design_properties.components)
    components.update({
        "flight_controller": _fc_box(),
        "sensors": sensors,
        "esc": _freeform_esc(with_pose=True),
    })
    dp = ps.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure", "control"],
        "system_priority": ["propulsion", "energy", "structure", "control"],
        "components": components,
    })
    params = dict(ps.current_parameters)
    params.update({
        "motor_count": 4, "per_motor_max_thrust_n": motor.thrust_n,
        "battery_capacity_wh": 74.0, "motor_power_w": motor.max_watts or 200,
    })
    ps = ps.model_copy(update={"design_properties": dp, "current_parameters": params})
    orch.workspace_manager.save_state(ps)
    assert orch._next_pending_block(ps) is None
    return orch


def _reset_idle(orch: JarvisOrchestrator) -> None:
    session = orch.state_manager.get_runtime_session()
    idle = session.model_copy(update={
        "mode": OrchestratorMode.IDLE,
        "pending_missing_params": [],
        "pending_missing_reason": "",
        "pending_define_missing": False,
        "frame_suggestions": [],
        "motor_suggestions": [],
        "propeller_suggestions": [],
        "battery_suggestions": [],
        "esc_suggestions": [],
    })
    orch.state_manager.set_runtime_session(idle)


def test_p5_cambiar_esc_opens_esc_catalog_not_battery(tmp_path: Path):
    orch = _closed_bound(tmp_path)
    _reset_idle(orch)
    result = orch.handle_user_text("cambiar esc", _RefuseLLM())
    suggestions = result.get("esc_suggestions") or []
    assert suggestions
    assert any(s["name"] == _HOBBYWING for s in suggestions)
    assert not result.get("battery_suggestions")
    session = orch.state_manager.get_runtime_session()
    assert session.pending_missing_params == ["esc"]
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS


def test_p6_pick_binds_hobbywing_and_preserves_pose(tmp_path: Path):
    orch = _closed_bound(tmp_path)
    _reset_idle(orch)
    offer = orch.handle_user_text("cambiar esc", _RefuseLLM())
    idx = next(s["idx"] for s in offer["esc_suggestions"] if s["name"] == _HOBBYWING)
    pick = orch.handle_user_text(str(idx), _RefuseLLM())
    assert pick["status"] == "ok"
    state = orch.state_manager.load_active_project(orch.workspace_manager)
    esc = state.design_properties.components["esc"]
    assert esc.catalog_ref == CatalogRef(family="esc", sku=_HOBBYWING)
    assert esc.declared_box_pose is not None
    assert esc.declared_box_pose.origin_key == "flight_controller"
    assert esc.declared_box_pose.x_mm == pytest.approx(5.0)
    node = _esc_node(state)
    assert node["geometry"]["shape"] == "box"
    assert node["geometry"]["length_mm"] == pytest.approx(50.0)


def test_p7_composite_propulsion_does_not_apply_esc_pick(tmp_path: Path):
    orch = _closed_bound(tmp_path)
    _reset_idle(orch)
    leftover = orch.handle_user_text("cambiar esc", _RefuseLLM()).get("esc_suggestions") or []
    assert leftover
    session = orch.state_manager.get_runtime_session()
    composite = session.model_copy(update={
        "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        "pending_missing_params": ["motors", "propellers", "esc"],
        "pending_missing_reason": MISSING_COMPONENT_DEFINITION,
        "param_definition_reason": MISSING_COMPONENT_DEFINITION,
        "esc_suggestions": leftover,
        "motor_suggestions": [],
        "propeller_suggestions": [],
    })
    orch.state_manager.set_runtime_session(composite)
    orch.handle_user_text("1", _RefuseLLM())
    state = orch.state_manager.load_active_project(orch.workspace_manager)
    esc = state.design_properties.components["esc"]
    assert esc.catalog_ref is None
