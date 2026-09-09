"""Assembly kit template B1-min (power_connector + signal_harness).

Covers implementation_contract_assembly_kit_template_b1.md §3-3.6:
  T0  4 aerial blocks, no vehicle_type, empty components -> Board slot ids
      are the seven architecture keys only (regression)
  T1  vehicle_type=dron, 7 roots present, kit absent -> Board slots
      power_connector/signal_harness; architecture still 4/4
  T2  Same state -> BOM missing == [power_connector, signal_harness];
      vehicle_type-unset clone -> those keys not in missing
  T3  Continuity: next_step names power_connector; next_why has the B3
      sentence + both kit keys
  T4  Orchestrator IDLE "declara el conector" on a 4/4 dron -> opens a
      single-key wizard for power_connector, never [battery, motors]
  T5  Twin: _block_progress_status on the T1 (kit-aware) state equals the
      no-vehicle_type clone
  T6  vehicle_type=robot -> zero kit slots
  T7  T1 + stub power_connector spec -> that slot gone, signal_harness
      slot remains, propulsion still complete
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.project_closure import build_component_bom
from jarvis.core.project_continuity import build_project_continuity
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


def _dron_state(*, vehicle_type: str | None = "dron", extra_components: dict | None = None) -> ProjectState:
    components = {key: _stub() for key in _ARCH_KEYS}
    if extra_components:
        components.update(extra_components)
    dp = DesignProperties(
        system_defined=True,
        system_blocks=_ARCH_BLOCKS,
        system_priority=_ARCH_BLOCKS,
        components=components,
    )
    params = dict(_FULL_PARAMS)
    if vehicle_type is not None:
        params["vehicle_type"] = vehicle_type
    return ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        current_parameters=params, design_properties=dp,
    )


def _slot_ids(state: ProjectState) -> set[str]:
    return {n["id"] for n in project_spatial_nodes(state) if n["kind"] == "slot"}


def test_t0_no_vehicle_type_seven_slots_only():
    dp = DesignProperties(system_blocks=_ARCH_BLOCKS, components={})
    state = ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        design_properties=dp,
    )
    assert _slot_ids(state) == _ARCH_KEYS


def test_t1_dron_kit_slots_appear_architecture_still_4_of_4():
    """Prop adapter ask B1 (implementation_contract_kit_prop_adapter_ask_b1.md
    §3.8): a 7-key dron with motors+propellers both present now also gets a
    prop_adapter slot — the third kit hole, gated on the sibling components
    this fixture already declares. Grown from the kit B1-min baseline of
    two, not a weaken."""
    state = _dron_state()
    assert _slot_ids(state) == {"power_connector", "signal_harness", "prop_adapter"}

    from jarvis.core.engineering_readiness import derive_architecture_progress

    progress = derive_architecture_progress(state)
    assert progress["progress"] == "4/4"
    assert progress["is_complete"] is True


def test_t2_bom_missing_is_exactly_the_three_kit_keys_order_preserved():
    """Grown from two to three kit keys (prop_adapter B1) — same reasoning
    as test_t1 above."""
    state = _dron_state()
    bom = build_component_bom(state)
    assert bom["missing"] == ["power_connector", "signal_harness", "prop_adapter"]

    clone = _dron_state(vehicle_type=None)
    bom_clone = build_component_bom(clone)
    assert "power_connector" not in bom_clone["missing"]
    assert "signal_harness" not in bom_clone["missing"]
    assert "prop_adapter" not in bom_clone["missing"]
    assert bom_clone["missing"] == []


def test_t3_continuity_names_kit_hole_and_b3_sentence():
    bom = {
        "defined": [], "incomplete": [],
        "missing": ["power_connector", "signal_harness", "prop_adapter"],
        "declarative": [],
    }
    cont = build_project_continuity(
        project_state=_dron_state(),
        status_type="nominal",
        status_reason=None,
        phase="complete",
        architecture_progress="4/4",
        next_architecture_label=None,
        next_block_status=None,
        proactive_question=None,
        suggested_action=None,
        physical_requirements={},
        component_bom=bom,
        energy_model_note=None,
        motor_catalog_gap=None,
        motor_catalog_matches=[],
    )
    assert "power_connector" in cont["next_useful_step"]
    assert "La arquitectura 4/4 no es la lista de montaje" in cont["next_useful_why"]
    assert "power_connector" in cont["next_useful_why"]
    assert "signal_harness" in cont["next_useful_why"]
    assert "prop_adapter" in cont["next_useful_why"]


class _RefuseLLM:
    def interpret(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def analyze(self, *a, **kw):
        raise AssertionError("LLM must not be called")

    def generate(self, *a, **kw):
        raise AssertionError("LLM must not be called")


def _orch_with_state(tmp_path: Path, state: ProjectState) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron", "objective": "kit test", "payload_kg": 1.0,
            "restrictions": "ninguna", "detail_level": "conceptual",
            "structure_mass_factor": 0.5, "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    merged = ps.model_copy(update={
        "design_properties": state.design_properties,
        "current_parameters": {**ps.current_parameters, **state.current_parameters},
    })
    orch.workspace_manager.save_state(merged)
    return orch


def test_t4_idle_declare_conector_opens_power_connector_wizard_only(tmp_path: Path):
    orch = _orch_with_state(tmp_path, _dron_state())
    result = orch.handle_user_text("declara el conector", _RefuseLLM())
    assert result["status"] == "interactive"
    assert result["pending"] == ["power_connector"]
    assert result["pending"] != ["battery", "motors"]


def test_t4b_idle_declare_harness_opens_signal_harness_wizard(tmp_path: Path):
    orch = _orch_with_state(tmp_path, _dron_state())
    result = orch.handle_user_text("declara el harness", _RefuseLLM())
    assert result["status"] == "interactive"
    assert result["pending"] == ["signal_harness"]


def test_t4c_kit_describe_saves_with_low_or_declarative_completeness(tmp_path: Path):
    orch = _orch_with_state(tmp_path, _dron_state())
    orch.handle_user_text("declara el conector", _RefuseLLM())
    result = orch.handle_user_text("XT60 amarillo bullet connector", _RefuseLLM())
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    saved = ps.design_properties.components.get("power_connector")
    assert saved is not None
    assert saved.catalog_ref is None
    assert "geometry" not in (result or {})


def test_t4d_brief_example_xt60_single_token_saves_and_closes_wizard(tmp_path: Path):
    """Smoke loop: Brief says Ej: 'XT60'; one token used to be completeness low
    and re-prompted the same Brief forever."""
    orch = _orch_with_state(tmp_path, _dron_state())
    orch.handle_user_text("declara el conector", _RefuseLLM())
    result = orch.handle_user_text("XT60", _RefuseLLM())
    assert result["status"] == "ok"
    assert result["action"] == "component_description_saved"
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    saved = ps.design_properties.components.get("power_connector")
    assert saved is not None
    assert saved.suggested_key == "power_connector"
    assert saved.catalog_ref is None
    assert saved.completeness != "low"
    from jarvis.workspace.spatial_board import project_spatial_nodes
    slots = {n["id"] for n in project_spatial_nodes(ps) if n["kind"] == "slot"}
    assert "power_connector" not in slots
    assert "signal_harness" in slots


def test_t5_twin_block_progress_status_unaffected_by_kit(tmp_path: Path):
    state = _dron_state()
    clone = _dron_state(vehicle_type=None)
    for block in _ARCH_BLOCKS:
        status_kit = JarvisOrchestrator._block_progress_status(
            block, state.design_properties, state.current_parameters
        )
        status_no_kit = JarvisOrchestrator._block_progress_status(
            block, clone.design_properties, clone.current_parameters
        )
        assert status_kit == status_no_kit == "complete"


def test_t6_robot_vehicle_type_zero_kit_slots():
    robot_blocks = ["actuation", "transmission", "energy", "control"]
    dp = DesignProperties(
        system_defined=True, system_blocks=robot_blocks, system_priority=robot_blocks,
        components={"motors": _stub(), "battery": _stub()},
    )
    state = ProjectState(
        project_id="p1", project_slug="demo", objective="demo", workspace_path="/tmp/demo",
        current_parameters={"vehicle_type": "robot"}, design_properties=dp,
    )
    slots = _slot_ids(state)
    assert "power_connector" not in slots
    assert "signal_harness" not in slots


def test_t7_declared_power_connector_removes_its_slot_keeps_harness_and_adapter():
    """Grown to include prop_adapter (B1) alongside signal_harness — same
    reasoning as test_t1/test_t2 above."""
    state = _dron_state(extra_components={"power_connector": _stub("low")})
    slots = _slot_ids(state)
    assert slots == {"signal_harness", "prop_adapter"}

    status = JarvisOrchestrator._block_progress_status(
        "propulsion", state.design_properties, state.current_parameters
    )
    assert status == "complete"
