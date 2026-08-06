"""Tests for PromptBuilder — FASE_LLM: action_space injection."""
from jarvis.core.parameter_requirements import PARAMETER_REQUIREMENTS
from jarvis.llm.prompt_builder import PromptBuilder, _ACTION_SPACE_JSON
from jarvis.schemas.state_schema import RuntimeState


def _make_idle_runtime_state() -> RuntimeState:
    return RuntimeState()


builder = PromptBuilder()


# ---------------------------------------------------------------------------
# Action Space JSON at module level
# ---------------------------------------------------------------------------

def test_action_space_json_is_non_empty_string():
    assert isinstance(_ACTION_SPACE_JSON, str)
    assert len(_ACTION_SPACE_JSON) > 0


def test_action_space_json_contains_all_registry_keys():
    for key in PARAMETER_REQUIREMENTS:
        assert key in _ACTION_SPACE_JSON, f"Registry key '{key}' missing from _ACTION_SPACE_JSON"


# ---------------------------------------------------------------------------
# System prompt content
# ---------------------------------------------------------------------------

def test_system_prompt_contains_action_space_json():
    rt = _make_idle_runtime_state()
    prompt = builder._system_prompt(rt)
    assert _ACTION_SPACE_JSON in prompt


def test_system_prompt_contains_iterate_output_instructions():
    rt = _make_idle_runtime_state()
    prompt = builder._system_prompt(rt)
    for keyword in ("operacion", "variable", "confidence"):
        assert keyword in prompt, f"Keyword '{keyword}' missing from system prompt"


def test_system_prompt_contains_action_space_header():
    rt = _make_idle_runtime_state()
    prompt = builder._system_prompt(rt)
    assert "Action Space" in prompt


def test_system_prompt_still_contains_prompt_version():
    from jarvis.config import PROMPT_VERSION
    rt = _make_idle_runtime_state()
    prompt = builder._system_prompt(rt)
    assert str(PROMPT_VERSION) in prompt


# ---------------------------------------------------------------------------
# build_messages integration
# ---------------------------------------------------------------------------

def test_build_messages_returns_system_and_user():
    rt = _make_idle_runtime_state()
    messages = builder.build_messages("quiero más autonomía", rt)
    roles = [m["role"] for m in messages]
    assert "system" in roles
    assert "user" in roles


def test_build_messages_system_contains_action_space():
    rt = _make_idle_runtime_state()
    messages = builder.build_messages("quiero más autonomía", rt)
    system_content = next(m["content"] for m in messages if m["role"] == "system")
    assert "Action Space" in system_content
    assert "battery_capacity_wh" in system_content
