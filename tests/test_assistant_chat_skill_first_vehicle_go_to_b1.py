"""Tests T1-T5 for `B1-assistant-chat-skill-first-vehicle-go-to` (T25).

Third vehicle Skill-first — GO_TO via shared `run_skill` vehicle gate,
then existing orch `_handle_vehicle_go_to`. HOLD/LAND stay Skill-first.
SD-GO_TO (chat GO_TO never parses a destination, while the T20 sim
executor requires one) stays explicitly OPEN — this Buy is gate-only,
never a destination parse/invent.
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


def test_t1_chat_go_to_skill_gate_and_vehicle_go_to_shape(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    with patch(
        "jarvis.capabilities.skills_runtime.run_skill",
        wraps=run_skill,
    ) as spy:
        result = orch.handle_user_text("go to", exploding)
    assert spy.called
    assert any(c.args[0] == "skill.request_go_to" for c in spy.call_args_list)
    assert result["action"] == "vehicle_go_to"
    assert "disarmed" in result["message"].lower() or "reject" in result["message"].lower()


def test_t1b_armed_chat_go_to_still_honest_sin_destino(tmp_path: Path):
    """Gate passes when armed, but SD-GO_TO stays OPEN — the existing
    T20 sim-copper honesty note (empty params, no coordinates) must
    still fire unchanged, never an invented destination."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    orch.handle_user_text("armar", exploding)
    result = orch.handle_user_text("go to", exploding)
    assert result["action"] == "vehicle_go_to"
    assert "allow" in result["message"]
    assert "Simulación" in result["message"]
    assert "sin destino" in result["message"].lower() or "no disponible" in result["message"].lower()


def test_t2_direct_run_skill_go_to_ok_flight_go_to_not_implemented():
    result = run_skill("skill.request_go_to")
    assert result.outcome == "ok"
    assert result.reason is None
    registry = CapabilityRegistry.load_default()
    go_to = next(s for s in registry.skills() if s.id == "skill.request_go_to")
    assert go_to.availability == CapabilityAvailability.AVAILABLE
    flight_go_to = registry.get_capability("flight.go_to")
    assert flight_go_to is not None
    assert flight_go_to.availability == CapabilityAvailability.NOT_IMPLEMENTED


def test_t3_hold_land_still_ok_takeoff_still_stub():
    """T26/T27 later flip TAKEOFF/RETURN_HOME too — this test's own
    "still stub" sibling probe moves to FOLLOW. See
    `tests/test_assistant_chat_skill_first_vehicle_takeoff_b1.py` /
    `..._return_home_b1.py` for their own coverage."""
    hold = run_skill("skill.request_hold")
    assert hold.outcome == "ok"
    land = run_skill("skill.request_land")
    assert land.outcome == "ok"
    charge = run_skill("skill.request_charge")
    assert charge.outcome == "reject"
    assert charge.reason == "skill_stub"


def test_t4_chat_hold_and_land_still_skill_first_vehicle(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    for raw, skill_id, action in (
        ("hold", "skill.request_hold", "vehicle_hold"),
        ("land", "skill.request_land", "vehicle_land"),
    ):
        with patch(
            "jarvis.capabilities.skills_runtime.run_skill",
            wraps=run_skill,
        ) as spy:
            result = orch.handle_user_text(raw, exploding)
        assert any(c.args[0] == skill_id for c in spy.call_args_list)
        assert result["action"] == action


def test_t5_no_tip_version_pins_in_new_suite():
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()
