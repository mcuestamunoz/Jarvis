"""Kit SKUs D B1 (XT60 / JST-SH into existing holes).

Covers implementation_contract_kit_connector_harness_skus_d.md §3-3.7:
  T0  Loader: exactly two SKUs; frozen kit_key pair; has_kit_hardware true;
      no length_mm/height_mm on either spec
  T1  bind pololu_xt60_pair -> family kit_hardware, suggested_key
      power_connector, catalog_ref.sku set, no current_a, no geometry
  T2  bind harness SKU -> suggested_key signal_harness; no length_mm
  T3  _geometry_from_spec on both bound specs is None
  T4  _bom_sku_resolved true for kit_hardware/pololu_xt60_pair
  T5  Orchestrator 4/4 dron, "declara el conector" then "ayúdame a elegir"
      -> lists pololu_xt60_pair only, peer lists empty
  T6  From T5, pick "1" -> catalog_ref set, slot gone, propulsion complete
  T7  4/4, "declara el conector" then "XT60" (no pick) -> catalog_ref None
  T8  vehicle_type=robot -> IDLE kit wizard does not open
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.catalog_bind import bind_kit_hardware_from_catalog
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.project_closure import _bom_sku_resolved
from jarvis.knowledge.library import default_library
from jarvis.schemas.action_schema import ComponentSpec
from jarvis.schemas.state_schema import DesignProperties, ProjectState
from jarvis.workspace.spatial_board import _geometry_from_spec, project_spatial_nodes

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


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def test_t0_loader_exactly_two_frozen_kit_keys_no_geometry_fields():
    items = default_library.list_kit_hardware()
    assert {i.name for i in items} == {"pololu_xt60_pair", "pihut_jst_sh_6pin_cab1009"}
    assert {i.kit_key for i in items} == {"power_connector", "signal_harness"}
    assert default_library.has_kit_hardware("pololu_xt60_pair")
    for item in items:
        assert not hasattr(item, "length_mm")
        assert not hasattr(item, "height_mm")
        assert not hasattr(item, "width_mm")
        assert not hasattr(item, "diameter_mm")


def test_t1_bind_power_connector_no_current_a_no_geometry():
    spec = bind_kit_hardware_from_catalog("pololu_xt60_pair")
    assert spec.catalog_ref.family == "kit_hardware"
    assert spec.catalog_ref.sku == "pololu_xt60_pair"
    assert spec.suggested_key == "power_connector"
    assert "current_a" not in spec.properties
    for geo_key in ("length_mm", "width_mm", "height_mm", "diameter_mm", "diameter_in"):
        assert geo_key not in spec.properties
    assert spec.properties["color"].value == "yellow"
    assert spec.properties["pin_config"].value == "1x2"


def test_t2_bind_signal_harness_no_length_mm():
    spec = bind_kit_hardware_from_catalog("pihut_jst_sh_6pin_cab1009")
    assert spec.suggested_key == "signal_harness"
    assert "length_mm" not in spec.properties
    assert spec.properties["pin_count"].value == 6
    assert spec.properties["pitch_mm"].value == 1.0
    assert spec.properties["wire_gauge_awg"].value == 26


def test_t3_geometry_from_spec_is_none_for_both():
    connector = bind_kit_hardware_from_catalog("pololu_xt60_pair")
    harness = bind_kit_hardware_from_catalog("pihut_jst_sh_6pin_cab1009")
    assert _geometry_from_spec(connector) is None
    assert _geometry_from_spec(harness) is None


def test_t4_bom_sku_resolved_true_for_kit_hardware():
    assert _bom_sku_resolved({"family": "kit_hardware", "sku": "pololu_xt60_pair"}) is True
    assert _bom_sku_resolved({"family": "kit_hardware", "sku": "does_not_exist"}) is False


def _orch_dron_4_of_4(tmp_path: Path) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "kit sku test", "payload_kg": 1.0,
            "restrictions": "ninguna", "detail_level": "conceptual",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    components = {k: _stub() for k in _ARCH_KEYS}
    dp = ps.design_properties.model_copy(update={
        "system_defined": True, "system_blocks": _ARCH_BLOCKS, "system_priority": _ARCH_BLOCKS,
        "components": components,
    })
    merged = ps.model_copy(update={
        "design_properties": dp,
        "current_parameters": {**ps.current_parameters, **_FULL_PARAMS},
    })
    orch.workspace_manager.save_state(merged)
    return orch


def test_t5_help_choose_lists_only_connector_sku_peer_lists_empty(tmp_path: Path):
    orch = _orch_dron_4_of_4(tmp_path)
    orch.handle_user_text("declara el conector", _RefuseLLM())
    result = orch.handle_user_text("ayúdame a elegir", _RefuseLLM())
    assert "pololu_xt60_pair" in result["message"] or "Pololu" in result["message"] or "XT60" in result["message"]
    assert "CAB1009" not in result["message"]
    suggestions = result.get("kit_hardware_suggestions") or []
    assert suggestions
    assert all(s["kit_key"] == "power_connector" for s in suggestions)
    session = orch.state_manager.get_runtime_session()
    assert session.motor_suggestions == []
    assert session.propeller_suggestions == []
    assert session.battery_suggestions == []
    assert session.frame_suggestions == []


def test_t6_pick_binds_catalog_ref_slot_gone_propulsion_complete(tmp_path: Path):
    orch = _orch_dron_4_of_4(tmp_path)
    orch.handle_user_text("declara el conector", _RefuseLLM())
    orch.handle_user_text("ayúdame a elegir", _RefuseLLM())
    result = orch.handle_user_text("1", _RefuseLLM())
    assert result["status"] == "ok"
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    spec = ps.design_properties.components.get("power_connector")
    assert spec is not None
    assert spec.catalog_ref is not None
    assert spec.catalog_ref.sku == "pololu_xt60_pair"

    slots = {n["id"] for n in project_spatial_nodes(ps) if n["kind"] == "slot"}
    assert "power_connector" not in slots

    status = JarvisOrchestrator._block_progress_status(
        "propulsion", ps.design_properties, ps.current_parameters
    )
    assert status == "complete"


def test_t7_free_text_still_saves_without_catalog_ref(tmp_path: Path):
    orch = _orch_dron_4_of_4(tmp_path)
    orch.handle_user_text("declara el conector", _RefuseLLM())
    orch.handle_user_text("XT60", _RefuseLLM())
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    spec = ps.design_properties.components.get("power_connector")
    assert spec is not None
    assert spec.catalog_ref is None


def test_t8_robot_vehicle_type_idle_kit_wizard_does_not_open(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "robot", "objective": "ground test", "payload_kg": 1.0,
            "restrictions": "ninguna", "detail_level": "conceptual",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    robot_blocks = ["actuation", "transmission", "energy", "control"]
    dp = ps.design_properties.model_copy(update={
        "system_defined": True, "system_blocks": robot_blocks, "system_priority": robot_blocks,
        "components": {"motors": _stub(), "battery": _stub()},
    })
    orch.workspace_manager.save_state(ps.model_copy(update={"design_properties": dp}))
    # Library still has rows for this kit_key; the IDLE bridge must still
    # refuse to open the wizard for a non-dron/uav domain. Asserted directly
    # at the dispatch method (same pattern as kit B1-min's own T11/T4-style
    # proofs) rather than through the full LLM-backed pipeline — this
    # phrase falls through to the LLM on a robot project (pre-existing,
    # unrelated routing), which is not this test's subject.
    assert default_library.list_kit_hardware(kit_key="power_connector")
    assert orch._try_start_kit_component_from_mention("declara el conector") is None
