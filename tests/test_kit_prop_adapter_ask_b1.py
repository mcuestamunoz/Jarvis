"""Prop adapter ask B1 (after hélices; gated kit hole).

Covers implementation_contract_kit_prop_adapter_ask_b1.md §3-3.7:
  T0  dron, empty components -> Board slots = seven + connector + harness;
      no prop_adapter. BLOCK_TO_COMPONENTS["propulsion"] unchanged
  T1  motors present, no propellers -> no adapter slot / not in BOM missing
  T2  motors+propellers present, esc/adapter absent -> Board has
      prop_adapter in the propulsion column; BOM missing has esc+adapter
  T3  Orchestrator: save hélices (motors already present) -> next message
      is the adapter Brief, not ESC; pending[0] == "prop_adapter"
  T4  From T3, "va directa" -> prop_adapter spec saved, no catalog_ref;
      follow-up is the ESC Brief
  T5  From T3, "no lo sé" -> no prop_adapter spec; follow-up is ESC; BOM
      still lists prop_adapter in missing
  T6  vehicle_type=robot + motors + propellers -> zero adapter
  T7  Twin: _block_progress_status("propulsion") equals the no-vehicle_type
      clone (both "complete")
  T8  kit_component_keys("dron", blocks) without components -> no
      prop_adapter (fail closed)
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.project_closure import build_component_bom
from jarvis.core.system_architecture_catalog import (
    BLOCK_TO_COMPONENTS,
    kit_component_keys,
)
from jarvis.schemas.action_schema import ComponentSpec
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import project_spatial_nodes

_ARCH_BLOCKS = ["propulsion", "energy", "structure", "control"]
_ARCH_KEYS = {
    "motors", "propellers", "esc", "battery", "frame", "flight_controller", "sensors",
}
_FULL_PARAMS = {
    "motor_count": 4, "per_motor_max_thrust_n": 20.0,
    "battery_capacity_wh": 100.0, "motor_power_w": 50.0,
}


def _stub(completeness: str = "medium") -> ComponentSpec:
    return ComponentSpec(component_type="generic_component", completeness=completeness, source="declared")


def _dron_state(*, components: dict | None = None) -> ProjectState:
    dp = DesignProperties(
        system_defined=True,
        system_blocks=_ARCH_BLOCKS,
        system_priority=_ARCH_BLOCKS,
        components=components or {},
    )
    return ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        current_parameters={**_FULL_PARAMS, "vehicle_type": "dron"},
        design_properties=dp,
    )


def _slot_ids(state: ProjectState) -> set[str]:
    return {n["id"] for n in project_spatial_nodes(state) if n["kind"] == "slot"}


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def test_t0_empty_components_seven_plus_two_kit_no_adapter():
    state = _dron_state()
    assert _slot_ids(state) == _ARCH_KEYS | {"power_connector", "signal_harness"}
    assert BLOCK_TO_COMPONENTS["propulsion"] == ["motors", "propellers", "esc"]


def test_t1_motors_only_no_propellers_no_adapter():
    state = _dron_state(components={"motors": _stub()})
    slots = _slot_ids(state)
    assert "prop_adapter" not in slots
    bom = build_component_bom(state)
    assert "prop_adapter" not in bom["missing"]


def test_t2_motors_and_propellers_present_esc_absent_adapter_slot_appears():
    state = _dron_state(components={"motors": _stub(), "propellers": _stub()})
    nodes = project_spatial_nodes(state)
    adapter_node = next(n for n in nodes if n["id"] == "prop_adapter")
    esc_node = next(n for n in nodes if n["id"] == "esc")
    assert adapter_node["kind"] == "slot"
    # same column as the rest of propulsion (motors is a real card, esc a slot;
    # both occupy the propulsion block's own column index).
    motors_node = next(n for n in nodes if n["id"] == "motors")
    assert adapter_node["x"] == motors_node["x"] == esc_node["x"]

    bom = build_component_bom(state)
    assert "esc" in bom["missing"]
    assert "prop_adapter" in bom["missing"]


def _orch_propulsion_wizard(tmp_path: Path, *, motors_saved: bool) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "adapter test", "payload_kg": 1.0,
            "restrictions": "ninguna", "detail_level": "conceptual",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    dp = ps.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": _ARCH_BLOCKS,
        "system_priority": _ARCH_BLOCKS,
    })
    orch.workspace_manager.save_state(ps.model_copy(update={"design_properties": dp}))
    orch.handle_user_text("declarar motores", _RefuseLLM())
    if motors_saved:
        orch.handle_user_text("4 motores 2306 2400kv 50w", _RefuseLLM())
    return orch


def test_t3_saving_helices_shows_adapter_brief_not_esc(tmp_path: Path):
    orch = _orch_propulsion_wizard(tmp_path, motors_saved=True)
    result = orch.handle_user_text("helices 10x4.5", _RefuseLLM())
    assert result["status"] == "ok"
    assert "¿Cómo montas la hélice?" in result["message"]
    assert "ESC" not in result["message"]
    session = orch.state_manager.get_runtime_session()
    assert session.pending_missing_params[0] == "prop_adapter"


def test_t4_va_directa_saves_adapter_then_shows_esc_brief(tmp_path: Path):
    orch = _orch_propulsion_wizard(tmp_path, motors_saved=True)
    orch.handle_user_text("helices 10x4.5", _RefuseLLM())
    result = orch.handle_user_text("va directa", _RefuseLLM())
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    adapter = ps.design_properties.components.get("prop_adapter")
    assert adapter is not None
    assert adapter.catalog_ref is None
    assert adapter.completeness != "low"
    assert "ESC" in result["message"]


def test_t5_no_lo_se_skips_adapter_advances_to_esc_hole_stays_in_bom(tmp_path: Path):
    orch = _orch_propulsion_wizard(tmp_path, motors_saved=True)
    orch.handle_user_text("helices 10x4.5", _RefuseLLM())
    result = orch.handle_user_text("no lo sé", _RefuseLLM())
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    assert ps.design_properties.components.get("prop_adapter") is None
    assert "ESC" in result["message"]
    bom = build_component_bom(ps)
    assert "prop_adapter" in bom["missing"]


def test_t6_robot_with_motors_and_propellers_zero_adapter():
    robot_blocks = ["actuation", "transmission", "energy", "control"]
    dp = DesignProperties(
        system_defined=True, system_blocks=robot_blocks, system_priority=robot_blocks,
        components={"motors": _stub(), "propellers": _stub()},
    )
    state = ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        current_parameters={"vehicle_type": "robot"}, design_properties=dp,
    )
    assert "prop_adapter" not in _slot_ids(state)
    assert "prop_adapter" not in build_component_bom(state)["missing"]


def test_t7_twin_block_progress_status_unaffected_by_adapter_gate():
    components = {
        "motors": _stub(), "propellers": _stub(), "esc": _stub(),
        "battery": _stub(), "frame": _stub(), "flight_controller": _stub(), "sensors": _stub(),
    }
    with_kit = _dron_state(components=components)
    no_vehicle = ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        current_parameters=dict(_FULL_PARAMS),
        design_properties=with_kit.design_properties,
    )
    status_kit = JarvisOrchestrator._block_progress_status(
        "propulsion", with_kit.design_properties, with_kit.current_parameters
    )
    status_no_kit = JarvisOrchestrator._block_progress_status(
        "propulsion", no_vehicle.design_properties, no_vehicle.current_parameters
    )
    assert status_kit == status_no_kit == "complete"


def test_t8_kit_component_keys_without_components_fails_closed():
    keys = kit_component_keys("dron", _ARCH_BLOCKS)
    assert "prop_adapter" not in keys
    assert set(keys) == {"power_connector", "signal_harness"}
