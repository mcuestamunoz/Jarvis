"""FN-ESC-acquisition — UX/routing hardening post-ERF-2.

Ensures ESC can be acquired through normal CLI paths and that current_a
reaches electrical_compatibility → engineering_readiness.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.acquisition_target import COMPONENT_PROMPTS, COMPONENT_TERM_ALIASES, resolve_acquisition_mention
from jarvis.core.engineering_readiness import build_engineering_readiness
from jarvis.core.orchestrator import JarvisOrchestrator, OrchestratorMode
from jarvis.core.parameter_requirements import MISSING_COMPONENT_DEFINITION
from jarvis.core.system_architecture_catalog import SYSTEM_ARCHITECTURES
from jarvis.schemas.action_schema import ComponentSpec, InteractiveSessionState, PropertyValue
from jarvis.schemas.state_schema import ProjectState


def test_esc_in_component_term_aliases_and_prompts():
    assert COMPONENT_TERM_ALIASES.get("esc") == "esc"
    assert "esc" in COMPONENT_PROMPTS
    assert "30A" in COMPONENT_PROMPTS["esc"] or "30a" in COMPONENT_PROMPTS["esc"].lower()


def test_propulsion_block_label_includes_esc():
    label = SYSTEM_ARCHITECTURES["dron"]["block_labels"]["propulsion"]
    assert "ESC" in label
    assert "hélices" in label


def _orch_with_propulsion_gap(tmp_path: Path) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle({
        "action": "create_project",
        "parameters": {
            "vehicle_type": "dron",
            "objective": "esc acquisition test",
            "payload_kg": 1.0,
            "restrictions": "ninguna",
            "detail_level": "conceptual",
            "structure_mass_factor": 0.6,
            "safety_factor": 1.2,
        },
    })
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    motors = ComponentSpec(
        name="4x 2306 2400KV",
        component_type="propulsion_active",
        suggested_key="motors",
        completeness="high",
        source="declared",
        properties={
            "motor_count": PropertyValue(value=4),
            "kv_rating": PropertyValue(value=2400.0, unit="KV"),
            "power_w": PropertyValue(value=500.0, unit="W"),
        },
    )
    propellers = ComponentSpec(
        name="helices 10x4.5",
        component_type="propulsion_passive",
        suggested_key="propellers",
        completeness="high",
        source="declared",
        properties={
            "diameter_in": PropertyValue(value=10.0, unit="in"),
            "pitch_in": PropertyValue(value=4.5, unit="in"),
        },
    )
    battery = ComponentSpec(
        name="LiPo 6S",
        component_type="energy_storage",
        suggested_key="battery",
        completeness="high",
        source="declared",
        properties={"cell_count": PropertyValue(value=6, unit="S")},
    )
    dp = ps.design_properties.model_copy(update={
        "system_defined": True,
        "system_blocks": ["propulsion", "energy", "structure", "control"],
        "system_priority": ["propulsion", "energy", "structure", "control"],
        "components": {"motors": motors, "propellers": propellers, "battery": battery},
    })
    params = dict(ps.current_parameters or {})
    params.update({"motor_count": 4, "motor_power_w": 500.0, "battery_cell_count": 6})
    updated = ps.model_copy(update={"design_properties": dp, "current_parameters": params})
    orch.workspace_manager.save_state(updated)
    orch.state_manager.clear_runtime_session()
    return orch


def test_definir_esc_resolves_acquisition_mention(tmp_path: Path):
    orch = _orch_with_propulsion_gap(tmp_path)
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    mention = resolve_acquisition_mention("definir esc", ps)
    assert mention is not None
    assert mention["kind"] == "component"
    assert mention["key"] == "esc"


def test_definir_esc_opens_esc_prompt(tmp_path: Path):
    orch = _orch_with_propulsion_gap(tmp_path)
    result = orch.handle_user_text("definir esc", llm_interface=None)
    assert result.get("action") == "define_missing_params"
    question = result.get("question") or ""
    assert "ESC" in question or "esc" in question.lower()


def test_esc_20a_while_wizard_expects_motors_still_saves_esc(tmp_path: Path):
    """Regression: stale motors pending must not swallow 'esc 20a'."""
    orch = _orch_with_propulsion_gap(tmp_path)
    orch.state_manager.set_runtime_session(InteractiveSessionState(
        mode=OrchestratorMode.DEFINE_MISSING_PARAMETERS,
        pending_missing_params=["motors"],
        pending_param_definitions=["motors"],
        param_definition_reason=MISSING_COMPONENT_DEFINITION,
        pending_define_missing=True,
    ))
    result = orch.handle_user_text("esc 20a", llm_interface=None)
    assert result.get("action") == "component_description_saved"
    assert "ESC registrado: 20A" in (result.get("message") or "")
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    esc = ps.design_properties.components.get("esc")
    assert esc is not None
    assert esc.properties["current_a"].value == 20.0


def test_esc_20a_end_to_end_incompatible_when_undersized(tmp_path: Path):
    """Full circuit: language → ESC current_a → readiness INCOMPATIBLE."""
    orch = _orch_with_propulsion_gap(tmp_path)
    result = orch.handle_user_text("esc 20a", llm_interface=None)
    assert "ESC registrado: 20A" in (result.get("message") or "")

    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    readiness = build_engineering_readiness(ps)
    gap_types = {g.gap_type for g in readiness.gaps}
    assert "GAP-ESC-UNDERSIZED" in gap_types
    assert readiness.subsystems["electronics"].verdict == "INCOMPATIBLE"
    assert readiness.subsystems["propulsion"].verdict == "INCOMPATIBLE"
    assert readiness.subsystems["energy"].verdict != "INCOMPATIBLE"
