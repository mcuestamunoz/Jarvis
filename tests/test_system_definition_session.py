"""Tests for SystemDefinitionSession and system_architecture_catalog."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from jarvis.core.system_architecture_catalog import (
    blocks_to_component_keys,
    get_domain_architecture,
    get_param_reason_for_block,
    normalize_block_alias,
)
from jarvis.core.system_definition_session import (
    _SOURCE_RANK,
    _build_component_stubs,
    _should_skip,
)
from jarvis.schemas.action_schema import ComponentSpec, InteractiveSessionState, OrchestratorMode


# ── Helpers ───────────────────────────────────────────────────────────────────


def _create_project(orchestrator, vehicle_type: str = "dron", detail_level: str = "detallado") -> dict:
    return orchestrator.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": vehicle_type,
            "objective": "test objective",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
            "detail_level": detail_level,
            "structure_mass_factor": 0.6,
            "safety_factor": 1.2,
        },
    })


def _make_orchestrator_with_project(tmp_path: Path, vehicle_type: str = "dron", detail_level: str = "detallado"):
    from jarvis.core.orchestrator import JarvisOrchestrator
    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    _create_project(orchestrator, vehicle_type=vehicle_type, detail_level=detail_level)
    return orchestrator


# ── Catálogo: sin objetos de dominio ─────────────────────────────────────────


def test_catalog_blocks_to_component_keys_returns_strings():
    keys = blocks_to_component_keys(["propulsion", "energy"])
    assert all(isinstance(k, str) for k in keys)


def test_catalog_blocks_to_component_keys_no_schema_objects():
    keys = blocks_to_component_keys(["propulsion", "energy", "structure", "control"])
    assert not any(isinstance(k, ComponentSpec) for k in keys)


def test_catalog_get_domain_architecture_returns_primitive_dict():
    arch = get_domain_architecture("dron")
    assert isinstance(arch, dict)
    assert all(isinstance(b, str) for b in arch["blocks"])


def test_catalog_get_domain_architecture_unknown_returns_none():
    assert get_domain_architecture("submarino") is None


def test_catalog_alias_drone_eq_dron():
    assert get_domain_architecture("drone")["blocks"] == get_domain_architecture("dron")["blocks"]


def test_catalog_get_param_reason_propulsion():
    assert get_param_reason_for_block("propulsion") == "missing_propulsion_parameters"


def test_catalog_get_param_reason_actuation():
    assert get_param_reason_for_block("actuation") == "missing_transmission_parameters"


def test_catalog_get_param_reason_energy_returns_missing_energy_parameters():
    # energy is param-driven: battery_capacity_wh + motor_power_w
    assert get_param_reason_for_block("energy") == "missing_energy_parameters"


# ── Prioridades ───────────────────────────────────────────────────────────────


def test_source_rank_user_is_max():
    assert _SOURCE_RANK["user"] > _SOURCE_RANK["inferred"] > _SOURCE_RANK["declared"]


def test_should_skip_high_completeness():
    assert _should_skip(ComponentSpec(completeness="high", source="declared")) is True


def test_should_skip_medium_completeness():
    assert _should_skip(ComponentSpec(completeness="medium", source="declared")) is True


def test_should_skip_low_declared_no_skip():
    assert _should_skip(ComponentSpec(completeness="low", source="declared")) is False


def test_should_skip_inferred_source():
    assert _should_skip(ComponentSpec(completeness="low", source="inferred")) is True


# ── _build_component_stubs ───────────────────────────────────────────────────


def test_build_stubs_creates_low_declared():
    stubs = _build_component_stubs(["motors", "battery"], existing={})
    assert stubs["motors"].completeness == "low"
    assert stubs["motors"].source == "declared"


def test_build_stubs_does_not_overwrite_high_completeness():
    existing = {"motors": ComponentSpec(completeness="high", source="declared")}
    stubs = _build_component_stubs(["motors", "battery"], existing=existing)
    assert "motors" not in stubs
    assert "battery" in stubs


def test_build_stubs_does_not_overwrite_inferred():
    existing = {"motors": ComponentSpec(completeness="low", source="inferred")}
    stubs = _build_component_stubs(["motors", "battery"], existing=existing)
    assert "motors" not in stubs
    assert "battery" in stubs


def test_build_stubs_overwrites_low_declared():
    existing = {"motors": ComponentSpec(completeness="low", source="declared")}
    stubs = _build_component_stubs(["motors"], existing=existing)
    assert "motors" in stubs


# ── normalize_block_alias ─────────────────────────────────────────────────────


def test_normalize_alias_vision_artificial():
    assert normalize_block_alias("visión artificial") == "perception"


def test_normalize_alias_comunicacion():
    assert normalize_block_alias("comunicacion") == "communication"


def test_normalize_alias_unknown_returns_none():
    assert normalize_block_alias("xyz_sistema_raro_inventado") is None


# ── SystemDefinitionSession.start() ──────────────────────────────────────────


def test_start_drone_returns_interactive(tmp_path):
    orchestrator = _make_orchestrator_with_project(tmp_path, "dron")
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    result = orchestrator.system_definition_session.start("dron", project_state)
    assert result["status"] == "interactive"
    assert result["mode"] == OrchestratorMode.SYSTEM_DEFINITION.value
    assert "Propulsión" in result["message"]
    assert "Energía" in result["message"]


def test_start_car_returns_actuation_in_message(tmp_path):
    orchestrator = _make_orchestrator_with_project(tmp_path, "coche")
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    result = orchestrator.system_definition_session.start("coche", project_state)
    msg = result["message"]
    assert "Actuación" in msg or "actuation" in msg.lower()


def test_start_unknown_domain_goes_to_step_1(tmp_path):
    orchestrator = _make_orchestrator_with_project(tmp_path, "dron")
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    result = orchestrator.system_definition_session.start("submarino", project_state)
    assert result["step"] == 1


def test_start_conceptual_mentions_skip(tmp_path):
    orchestrator = _make_orchestrator_with_project(tmp_path, "dron", detail_level="conceptual")
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    result = orchestrator.system_definition_session.start("dron", project_state)
    assert result["status"] == "interactive"
    assert "conceptual" in result["message"].lower()


# ── SystemDefinitionSession.answer() ─────────────────────────────────────────


def test_answer_a_applies_core_stubs(tmp_path):
    orchestrator = _make_orchestrator_with_project(tmp_path, "dron")
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    orchestrator.system_definition_session.start("dron", project_state)
    result = orchestrator.system_definition_session.answer("a")

    assert result.get("status") in ("ok", "interactive")
    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert saved.design_properties.system_defined is True
    assert "motors" in saved.design_properties.components
    assert "battery" in saved.design_properties.components
    assert "frame" in saved.design_properties.components


def test_answer_a_stubs_have_low_completeness_declared(tmp_path):
    orchestrator = _make_orchestrator_with_project(tmp_path, "dron")
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    orchestrator.system_definition_session.start("dron", project_state)
    orchestrator.system_definition_session.answer("a")

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    for key in ("motors", "battery", "frame"):
        spec = saved.design_properties.components.get(key)
        assert spec is not None, f"Expected {key} in components"
        assert spec.completeness == "low"
        assert spec.source == "declared"


def test_answer_a_saves_system_blocks(tmp_path):
    orchestrator = _make_orchestrator_with_project(tmp_path, "dron")
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    orchestrator.system_definition_session.start("dron", project_state)
    orchestrator.system_definition_session.answer("a")

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    expected_blocks = get_domain_architecture("dron")["blocks"]
    assert saved.design_properties.system_blocks == expected_blocks


def test_answer_c_skips_no_changes(tmp_path):
    orchestrator = _make_orchestrator_with_project(tmp_path, "dron")
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    orchestrator.system_definition_session.start("dron", project_state)
    result = orchestrator.system_definition_session.answer("c")

    assert result["status"] == "ok"
    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert saved.design_properties.system_defined is False


def test_answer_escape_clears_session(tmp_path):
    orchestrator = _make_orchestrator_with_project(tmp_path, "dron")
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    orchestrator.system_definition_session.start("dron", project_state)
    orchestrator.system_definition_session.answer("cancelar")

    assert orchestrator.state_manager.get_runtime_session().mode == OrchestratorMode.IDLE


def test_answer_b_then_vision_then_listo(tmp_path):
    orchestrator = _make_orchestrator_with_project(tmp_path, "dron")
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    orchestrator.system_definition_session.start("dron", project_state)

    r1 = orchestrator.system_definition_session.answer("b")
    assert r1["status"] == "interactive" and r1["step"] == 1

    r2 = orchestrator.system_definition_session.answer("visión artificial")
    assert r2["status"] == "interactive"

    r3 = orchestrator.system_definition_session.answer("listo")
    assert r3.get("status") in ("ok", "interactive")

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    # perception expands to both cameras AND lidar
    assert "cameras" in saved.design_properties.components
    assert "lidar" in saved.design_properties.components


def test_custom_block_without_alias_not_expanded_to_component_keys(tmp_path):
    """Free text blocks that have no alias stay in system_blocks but don't generate component keys."""
    orchestrator = _make_orchestrator_with_project(tmp_path, "dron")
    # Start session in mode B directly
    session = InteractiveSessionState(
        mode=OrchestratorMode.SYSTEM_DEFINITION,
        step=1,
        memory_context={
            "vehicle_type": "dron",
            "proposed_blocks": [],
            "proposed_component_keys": [],
            "recommended_start": None,
            "custom_blocks": [],
        },
    )
    orchestrator.state_manager.set_runtime_session(session)

    # Enter a completely unknown block
    orchestrator.system_definition_session.answer("sistema de enfriamiento experimental")
    orchestrator.system_definition_session.answer("listo")

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    # The free-text block must NOT appear as a component key
    assert "sistema de enfriamiento experimental" not in saved.design_properties.components
    assert "sistema_de_enfriamiento_experimental" not in saved.design_properties.components


# ── Bridge orquestador: system_definition → param_definition ─────────────────


def test_orchestrator_bridge_launches_param_session_after_architecture(tmp_path):
    """After answer('a') on a dron project, orchestrator auto-launches DEFINE_MISSING_PARAMETERS."""
    orchestrator = _make_orchestrator_with_project(tmp_path, "dron")
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    orchestrator.system_definition_session.start("dron", project_state)

    result = orchestrator.handle_user_text("a", MagicMock())

    # Session must now be in DEFINE_MISSING_PARAMETERS mode
    active_mode = orchestrator.state_manager.get_runtime_session().mode
    assert active_mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS, (
        f"Expected DEFINE_MISSING_PARAMETERS, got mode={active_mode}"
    )
    # Combined message must include both architecture confirmation and param question
    assert "Arquitectura" in result["message"] or "arquitectura" in result["message"]


def test_orchestrator_bridge_auto_asks_propulsion_params(tmp_path):
    """Bridge combined message must mention propulsion-related parameters."""
    orchestrator = _make_orchestrator_with_project(tmp_path, "dron")
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    orchestrator.system_definition_session.start("dron", project_state)

    result = orchestrator.handle_user_text("a", MagicMock())

    combined = result.get("message", "") + result.get("question", "")
    assert any(
        word in combined.lower()
        for word in ("motor", "empuje", "thrust", "propuls")
    ), f"Expected propulsion param hints in combined message, got: {combined[:200]}"


# ── DependencyGraph + PriorityEngine ─────────────────────────────────────────


from jarvis.core.system_dependency_catalog import get_domain_dependencies
from jarvis.core.system_dependency_graph import DependencyGraph, build_dependency_graph
from jarvis.core.priority_engine import compute_priority_order


def test_priority_order_dron():
    graph = build_dependency_graph("dron", ["propulsion", "energy", "structure", "control"])
    order = compute_priority_order(graph)
    assert order == ["propulsion", "energy", "structure", "control"]


def test_priority_order_robot():
    graph = build_dependency_graph("robot", ["actuation", "transmission", "energy", "control"])
    order = compute_priority_order(graph)
    # transmission and energy both depend on actuation → actuation must be first
    assert order[0] == "actuation"
    # control depends on energy → energy before control
    assert order.index("energy") < order.index("control")


def test_priority_first_matches_old_recommended_start():
    """priority[0] must equal the former hardcoded recommended_start for all known domains."""
    for vehicle_type, expected_first in [
        ("dron",   "propulsion"),
        ("uav",    "propulsion"),
        ("robot",  "actuation"),
        ("coche",  "actuation"),
        ("rover",  "actuation"),
    ]:
        arch = get_domain_architecture(vehicle_type)
        graph = build_dependency_graph(vehicle_type, arch["blocks"])
        order = compute_priority_order(graph)
        assert order[0] == expected_first, (
            f"{vehicle_type}: expected first={expected_first}, got {order[0]}"
        )


def test_build_graph_filters_absent_blocks():
    """Dependencies are limited to blocks actually in the provided list."""
    graph = build_dependency_graph("dron", ["propulsion", "energy"])
    # structure and control are absent → energy's deps must only contain present blocks
    assert graph.get_dependencies("energy") == ["propulsion"]
    assert "structure" not in graph.dependencies
    assert "control" not in graph.dependencies


def test_build_graph_custom_block_no_deps():
    """A custom block with no catalog entry gets empty dependencies — doesn't break sort."""
    graph = build_dependency_graph("dron", ["propulsion", "sistema_enfriamiento"])
    assert graph.get_dependencies("sistema_enfriamiento") == []
    order = compute_priority_order(graph)
    assert "sistema_enfriamiento" in order


def test_priority_cycle_protection():
    """A cyclic graph must not cause infinite recursion — emits warning and returns partial order."""
    import warnings
    cyclic_graph = DependencyGraph(dependencies={"a": ["b"], "b": ["a"]})
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        order = compute_priority_order(cyclic_graph)
    # Must not crash; must emit at least one warning
    assert len(caught) >= 1
    assert any("ciclo" in str(w.message).lower() for w in caught)
    # All nodes must appear in the output despite the cycle
    assert set(order) == {"a", "b"}


def test_system_priority_persisted_after_answer_a(tmp_path):
    """system_priority must be saved in DesignProperties after answer('a')."""
    orchestrator = _make_orchestrator_with_project(tmp_path, "dron")
    project_state = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    orchestrator.system_definition_session.start("dron", project_state)
    orchestrator.system_definition_session.answer("a")

    saved = orchestrator.state_manager.load_active_project(orchestrator.workspace_manager)
    assert saved.design_properties.system_priority == ["propulsion", "energy", "structure", "control"]


def test_vehicle_type_alias_drone_resolves_dependency():
    """'drone' alias must resolve to dron dependencies via get_domain_dependencies."""
    deps = get_domain_dependencies("drone")
    assert deps == get_domain_dependencies("dron")
    assert deps != {}
