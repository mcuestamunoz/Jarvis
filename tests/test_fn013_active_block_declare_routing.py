"""FN-013 — Active block declaration routing inside DEFINE_MISSING.

When acquisition is already open, definir/declarar/completar + the active block
must re-prompt the current pending parameter: 0 LLM, no session restart, no
cross-block jump.
"""
from __future__ import annotations

from pathlib import Path

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import MISSING_PROPULSION_PARAMETERS
from jarvis.schemas.action_schema import (
    ComponentSpec,
    InteractiveSessionState,
    OrchestratorMode,
    PropertyValue,
)


class _RefuseLLM:
    def interpret(self, *args, **kwargs):
        raise AssertionError("LLM.interpret must not be called")

    def analyze(self, *args, **kwargs):
        raise AssertionError("LLM.analyze must not be called")

    def generate(self, *args, **kwargs):
        raise AssertionError("LLM.generate must not be called")


def _project_with_active_propulsion(
    tmp_path: Path, *, components_done: bool = False
) -> JarvisOrchestrator:
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    orch.handle(
        {
            "action": "create_project",
            "parameters": {
                "vehicle_type": "dron",
                "objective": "transporte de carga",
                "payload_kg": 2.0,
                "restrictions": "ninguna",
                "detail_level": "conceptual",
                "structure_mass_factor": 0.6,
                "safety_factor": 1.2,
            },
        }
    )
    ps = orch.state_manager.load_active_project(orch.workspace_manager)
    components = {}
    if components_done:
        components = {
            "motors": ComponentSpec(
                name="4 motores 920kv",
                component_type="propulsion_active",
                suggested_key="motors",
                completeness="high",
                source="declared",
                properties={
                    "motor_count": PropertyValue(value=4),
                    "kv_rating": PropertyValue(value=920),
                },
            ),
            "propellers": ComponentSpec(
                name="helices 10x4.5",
                component_type="propulsion_passive",
                suggested_key="propellers",
                completeness="high",
                source="declared",
                properties={"diameter_in": PropertyValue(value=10.0)},
            ),
            # ERF-2 ★5: esc is now part of BLOCK_TO_COMPONENTS["propulsion"].
            "esc": ComponentSpec(
                name="ESC 30A",
                component_type="propulsion_active",
                suggested_key="esc",
                completeness="high",
                source="declared",
                properties={"current_a": PropertyValue(value=30.0)},
            ),
        }
    dp = ps.design_properties.model_copy(
        update={
            "system_defined": True,
            "system_blocks": ["propulsion", "energy", "structure", "control"],
            "system_priority": ["propulsion", "energy", "structure", "control"],
            "components": components,
        }
    )
    orch.workspace_manager.save_state(ps.model_copy(update={"design_properties": dp}))
    return orch


def _open_component_acquisition(orch: JarvisOrchestrator) -> None:
    """Open DEFINE_MISSING for propulsion components (Phase A), as after FN-011."""
    result = orch.handle_user_text("ayúdame a declarar propulsión", _RefuseLLM())
    assert result["action"] == "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert session.pending_param_definitions == ["motors", "propellers", "esc"]


def test_definir_propulsion_inside_wizard_reprompts_no_llm(tmp_path: Path):
    """Field-note case: already in DEFINE_MISSING, 'definir propulsión' is not a value."""
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)
    before = orch.state_manager.get_runtime_session()
    collected_before = dict(before.collected_params)
    pending_before = list(before.pending_param_definitions)

    result = orch.handle_user_text("definir propulsión", _RefuseLLM())

    assert result["status"] == "interactive"
    assert result["action"] == "define_missing_params"
    assert result.get("block_declaration_reprompt") is True
    assert "No reconozco" not in str(result.get("error") or "")
    assert "No reconozco" not in str(result.get("message") or "")
    assert result.get("question")
    after = orch.state_manager.get_runtime_session()
    assert after.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert after.collected_params == collected_before
    assert after.pending_param_definitions == pending_before


def test_ayudame_declarar_propulsion_inside_wizard_reprompts_no_llm(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)
    result = orch.handle_user_text("ayúdame a declarar propulsión", _RefuseLLM())
    assert result.get("block_declaration_reprompt") is True
    assert result["action"] == "define_missing_params"
    assert orch.state_manager.get_runtime_session().pending_param_definitions == [
        "motors",
        "propellers",
        "esc",
    ]


def test_collected_params_preserved_across_block_reprompt(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)
    session = orch.state_manager.get_runtime_session()
    orch.state_manager.set_runtime_session(
        session.model_copy(
            update={
                "collected_params": {"motor_count": 4.0},
                "pending_param_definitions": ["propellers"],
            }
        )
    )

    orch.handle_user_text("definir propulsión", _RefuseLLM())

    after = orch.state_manager.get_runtime_session()
    assert after.collected_params == {"motor_count": 4.0}
    assert after.pending_param_definitions == ["propellers"]


def test_definir_energia_while_propulsion_active_does_not_jump(tmp_path: Path):
    orch = _project_with_active_propulsion(tmp_path)
    _open_component_acquisition(orch)
    before = list(orch.state_manager.get_runtime_session().pending_param_definitions)

    orch.handle_user_text("definir energía", _RefuseLLM())

    after = orch.state_manager.get_runtime_session()
    assert after.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert after.pending_param_definitions == before
    assert "battery" not in " ".join(after.pending_param_definitions)


def test_numeric_value_still_accepted_in_define_missing(tmp_path: Path):
    """Regression: real values must still advance the wizard."""
    orch = _project_with_active_propulsion(tmp_path, components_done=True)
    start = orch.handle_user_text("ayúdame a declarar propulsión", _RefuseLLM())
    assert start["action"] == "define_missing_params"
    session = orch.state_manager.get_runtime_session()
    assert session.param_definition_reason == MISSING_PROPULSION_PARAMETERS
    # Phase B asks motor_count then thrust — answer first numeric pending.
    first = session.pending_param_definitions[0]
    result = orch.handle_user_text("4", _RefuseLLM())
    after = orch.state_manager.get_runtime_session()
    if after.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS:
        assert first not in after.pending_param_definitions or after.collected_params.get(
            first
        ) == 4.0
    else:
        # Wizard may complete if only one param remained.
        assert result.get("status") in {"ok", "interactive"}
