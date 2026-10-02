"""Tests T1-T5 for `B1-assistant-chat-skill-first-vehicle-takeoff` (T26).

Fourth vehicle Skill-first — TAKEOFF via shared `run_skill` vehicle
gate, then existing orch `_handle_vehicle_takeoff`. HOLD/LAND/GO_TO
stay Skill-first. TAKEOFF is explicitly NOT in the T20 sim-copper tick
set (only HOLD/LAND/GO_TO) — this Buy never adds one, and SD-GO_TO
stays untouched/OPEN.
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


def test_t1_chat_takeoff_skill_gate_and_vehicle_takeoff_shape(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    with patch(
        "jarvis.capabilities.skills_runtime.run_skill",
        wraps=run_skill,
    ) as spy:
        result = orch.handle_user_text("takeoff", exploding)
    assert spy.called
    assert any(c.args[0] == "skill.request_takeoff" for c in spy.call_args_list)
    assert result["action"] == "vehicle_takeoff"
    assert "disarmed" in result["message"].lower() or "reject" in result["message"].lower()


def test_t1b_armed_chat_takeoff_allow_not_implemented_no_sim_tick(tmp_path: Path):
    """Gate passes when armed, Safety allows, but no sim tick is ever
    added — TAKEOFF is not in T20's HOLD/LAND/GO_TO tick set."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    orch.handle_user_text("armar", exploding)
    result = orch.handle_user_text("takeoff", exploding)
    assert result["action"] == "vehicle_takeoff"
    assert "allow" in result["message"]
    assert "not_implemented" in result["message"]
    assert "Simulación" not in result["message"]
    assert "executed" not in result["message"].lower()


def test_t2_direct_run_skill_takeoff_ok_flight_takeoff_not_implemented():
    result = run_skill("skill.request_takeoff")
    assert result.outcome == "ok"
    assert result.reason is None
    registry = CapabilityRegistry.load_default()
    takeoff = next(s for s in registry.skills() if s.id == "skill.request_takeoff")
    assert takeoff.availability == CapabilityAvailability.AVAILABLE
    flight_takeoff = registry.get_capability("flight.takeoff")
    assert flight_takeoff is not None
    assert flight_takeoff.availability == CapabilityAvailability.NOT_IMPLEMENTED


def test_t3_hold_land_go_to_still_ok_return_home_still_stub():
    """T27 (`B1-assistant-chat-skill-first-vehicle-return-home`) later
    flips `skill.request_return_home` too — this test's own "still
    stub" sibling probe moves to FOLLOW. See
    `tests/test_assistant_chat_skill_first_vehicle_return_home_b1.py`
    for RETURN_HOME's own coverage."""
    for skill_id in ("skill.request_hold", "skill.request_land", "skill.request_go_to"):
        result = run_skill(skill_id)
        assert result.outcome == "ok", f"{skill_id} should still be ok"
    follow = run_skill("skill.request_follow")
    assert follow.outcome == "reject"
    assert follow.reason == "skill_stub"


def test_t4_chat_hold_land_go_to_still_skill_first_vehicle(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    for raw, skill_id, action in (
        ("hold", "skill.request_hold", "vehicle_hold"),
        ("land", "skill.request_land", "vehicle_land"),
        ("go to", "skill.request_go_to", "vehicle_go_to"),
    ):
        with patch(
            "jarvis.capabilities.skills_runtime.run_skill",
            wraps=run_skill,
        ) as spy:
            result = orch.handle_user_text(raw, exploding)
        assert any(c.args[0] == skill_id for c in spy.call_args_list)
        assert result["action"] == action


def test_t4b_go_to_sin_destino_honesty_untouched(tmp_path: Path):
    """SD-GO_TO stays OPEN — regression check that T26 never touched it."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    orch.handle_user_text("armar", exploding)
    result = orch.handle_user_text("go to", exploding)
    assert "sin destino" in result["message"].lower() or "no disponible" in result["message"].lower()


def test_t5_no_tip_version_pins_in_new_suite():
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()
