import pytest

from jarvis.llm.response_parser import LLMResponseParser, LLMResponseValidationError
from jarvis.schemas.action_schema import (
    InteractiveSessionState,
    LLMRequestMode,
    OrchestratorMode,
    ProjectDraft,
)
from jarvis.schemas.state_schema import RuntimeState


# Helper used by ActionPolicy variable tests
def _idle_rt() -> RuntimeState:
    return RuntimeState()


def test_parser_accepts_valid_idle_request():
    parser = LLMResponseParser()

    request = parser.parse(
        {
            "action": "create_project",
            "project_id": None,
            "parameters": {},
        }
    )

    validated = parser.validate_for_runtime(request, RuntimeState())

    assert validated.action.value == "create_project"
    assert validated.parameters == {}


def test_parser_accepts_simulate_in_idle_without_project_id():
    parser = LLMResponseParser()
    request = parser.parse(
        {
            "action": "simulate",
            "parameters": {},
        }
    )

    validated = parser.validate_for_runtime(request, RuntimeState())

    assert validated.action.value == "simulate"


def test_parser_accepts_iterate_in_idle_without_project_id():
    parser = LLMResponseParser()
    request = parser.parse(
        {
            "action": "iterate",
            "parameters": {},
        }
    )

    validated = parser.validate_for_runtime(request, RuntimeState())

    assert validated.action.value == "iterate"


def test_parser_rejects_extra_fields():
    parser = LLMResponseParser()

    with pytest.raises(LLMResponseValidationError):
        parser.parse(
            {
                "action": "create_project",
                "parameters": {},
                "unexpected": "boom",
            }
        )


def test_parser_rejects_new_action_when_session_is_active():
    parser = LLMResponseParser()
    request = parser.parse(
        {
            "action": "simulate",
            "parameters": {},
            "mode": "interactive",
            "raw_user_input": "quiero simular ahora",
        }
    )
    runtime = RuntimeState(
        session=InteractiveSessionState(
            mode=OrchestratorMode.CREATE_PROJECT_INTERACTIVE,
            step=2,
            project_draft=ProjectDraft(vehicle_type="dron"),
        )
    )

    with pytest.raises(LLMResponseValidationError):
        parser.validate_for_runtime(request, runtime)


def test_parser_requires_interactive_mode_when_session_is_active():
    parser = LLMResponseParser()
    request = parser.parse(
        {
            "action": "iterate",
            "parameters": {"answer": "sí"},
        }
    )
    runtime = RuntimeState(
        session=InteractiveSessionState(
            mode=OrchestratorMode.ITERATE_INTERACTIVE,
            step=1,
        )
    )

    with pytest.raises(LLMResponseValidationError):
        parser.validate_for_runtime(request, runtime)


def test_parser_accepts_interactive_response_inside_active_session():
    parser = LLMResponseParser()
    request = parser.parse(
        {
            "action": "iterate",
            "project_id": "abc123",
            "parameters": {},
            "mode": "interactive",
            "raw_user_input": "material",
        }
    )
    runtime = RuntimeState(
        session=InteractiveSessionState(
            mode=OrchestratorMode.ITERATE_INTERACTIVE,
            step=1,
        )
    )

    validated = parser.validate_for_runtime(request, runtime)
    action_request = parser.to_action_request(validated)

    assert validated.mode == LLMRequestMode.INTERACTIVE
    assert action_request["action"] == "iterate"
    assert action_request["parameters"]["project_id"] == "abc123"
    assert action_request["raw_user_input"] == "material"


def test_parser_rejects_simulate_in_interactive_mode_when_iterate_session_is_active():
    parser = LLMResponseParser()
    request = parser.parse(
        {
            "action": "simulate",
            "project_id": "abc123",
            "parameters": {},
            "mode": "interactive",
            "raw_user_input": "simula ahora",
        }
    )
    runtime = RuntimeState(
        session=InteractiveSessionState(
            mode=OrchestratorMode.ITERATE_INTERACTIVE,
            step=2,
        )
    )

    with pytest.raises(LLMResponseValidationError):
        parser.validate_for_runtime(request, runtime)


# ---------------------------------------------------------------------------
# ActionPolicy — variable validation against registry (FASE_LLM)
# ---------------------------------------------------------------------------

def test_policy_accepts_iterate_with_known_variable():
    parser = LLMResponseParser()
    request = parser.parse(
        {
            "action": "iterate",
            "parameters": {"variable": "battery_capacity_wh", "operacion": "increase", "confidence": 0.9},
        }
    )
    validated = parser.validate_for_runtime(request, _idle_rt())
    assert validated.parameters["variable"] == "battery_capacity_wh"


def test_policy_accepts_iterate_without_variable():
    """No variable field → policy allows it; wizard will ask."""
    parser = LLMResponseParser()
    request = parser.parse({"action": "iterate", "parameters": {}})
    validated = parser.validate_for_runtime(request, _idle_rt())
    assert validated.action.value == "iterate"


def test_policy_rejects_iterate_with_unknown_variable():
    """LLM invents 'turbocompresor' → policy raises before reaching the wizard."""
    parser = LLMResponseParser()
    request = parser.parse(
        {
            "action": "iterate",
            "parameters": {"variable": "turbocompresor", "confidence": 0.9},
        }
    )
    with pytest.raises(LLMResponseValidationError, match="turbocompresor"):
        parser.validate_for_runtime(request, _idle_rt())


def test_policy_accepts_iterate_with_derived_variable():
    """Derived variables pass ActionPolicy — SemanticIntentAdapter handles the redirect."""
    parser = LLMResponseParser()
    request = parser.parse(
        {
            "action": "iterate",
            "parameters": {"variable": "autonomia", "confidence": 0.9},
        }
    )
    # Should NOT raise — derived variable rejection is the adapter's responsibility
    validated = parser.validate_for_runtime(request, _idle_rt())
    assert validated.parameters["variable"] == "autonomia"


def test_policy_does_not_check_variable_for_other_actions():
    """variable field in parameters of a non-iterate action is ignored."""
    parser = LLMResponseParser()
    request = parser.parse(
        {
            "action": "calculate",
            "parameters": {"variable": "invented_variable"},
        }
    )
    validated = parser.validate_for_runtime(request, _idle_rt())
    assert validated.action.value == "calculate"
