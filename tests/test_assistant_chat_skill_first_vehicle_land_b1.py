"""Tests T1-T5 for `B1-assistant-chat-skill-first-vehicle-land` (T24).

Second vehicle Skill-first — LAND via shared `run_skill` vehicle gate,
then existing orch `_handle_vehicle_land`. HOLD stays Skill-first.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from jarvis.capabilities.registry import CapabilityRegistry
from jarvis.capabilities.schemas import CapabilityAvailability
from jarvis.capabilities.skills_runtime import run_skill
from jarvis.core.orchestrator import JarvisOrchestrator


class _ExplodingLLMInterface:
    def interpret(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def complete(self, *args, **kwargs):
        raise AssertionError("llm must not be called")


def test_t1_chat_land_skill_gate_and_vehicle_land_shape(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    with patch(
        "jarvis.capabilities.skills_runtime.run_skill",
        wraps=run_skill,
    ) as spy:
        result = orch.handle_user_text("land", exploding)
    assert spy.called
    assert any(c.args[0] == "skill.request_land" for c in spy.call_args_list)
    assert result["action"] == "vehicle_land"
    assert "disarmed" in result["message"].lower() or "reject" in result["message"].lower()


def test_t2_direct_run_skill_land_ok_flight_land_not_implemented():
    result = run_skill("skill.request_land")
    assert result.outcome == "ok"
    assert result.reason is None
    registry = CapabilityRegistry.load_default()
    land = next(s for s in registry.skills() if s.id == "skill.request_land")
    assert land.availability == CapabilityAvailability.AVAILABLE
    flight_land = registry.get_capability("flight.land")
    assert flight_land is not None
    assert flight_land.availability == CapabilityAvailability.NOT_IMPLEMENTED


def test_t3_hold_still_ok_takeoff_still_stub():
    """T25 (`B1-assistant-chat-skill-first-vehicle-go-to`) later flips
    `skill.request_go_to` to `available` too, and T26 flips TAKEOFF —
    this test's own "still stub" sibling probe moves to RETURN_HOME,
    which stays stub. See `tests/test_assistant_chat_skill_first_vehicle_go_to_b1.py`
    / `tests/test_assistant_chat_skill_first_vehicle_takeoff_b1.py` for
    GO_TO's/TAKEOFF's own coverage."""
    hold = run_skill("skill.request_hold")
    assert hold.outcome == "ok"
    return_home = run_skill("skill.request_return_home")
    assert return_home.outcome == "reject"
    assert return_home.reason == "skill_stub"


def test_t4_chat_hold_still_skill_first_vehicle(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    with patch(
        "jarvis.capabilities.skills_runtime.run_skill",
        wraps=run_skill,
    ) as spy:
        result = orch.handle_user_text("hold", exploding)
    assert any(c.args[0] == "skill.request_hold" for c in spy.call_args_list)
    assert result["action"] == "vehicle_hold"


def test_t5_no_tip_version_pins_in_new_suite():
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()
