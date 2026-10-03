"""Tests T1-T5 for `B1-assistant-chat-skill-first-vehicle-patrol` (T29).

Seventh and last vehicle Skill-first — PATROL via shared `run_skill`
vehicle gate, then existing orch `_handle_vehicle_patrol`. HOLD/LAND/
GO_TO/TAKEOFF/RETURN_HOME/FOLLOW stay Skill-first. PATROL is
explicitly NOT in the T20 sim-copper tick set. This closes the full
seven-verb chat AutonomyVerb Skill-first set — remaining Skill-first
candidates (ARM/DISARM/CHARGE) are policy/ops, not further
AutonomyVerbs.
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


def test_t1_chat_patrol_skill_gate_and_vehicle_patrol_shape(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    with patch(
        "jarvis.capabilities.skills_runtime.run_skill",
        wraps=run_skill,
    ) as spy:
        result = orch.handle_user_text("patrol", exploding)
    assert spy.called
    assert any(c.args[0] == "skill.request_patrol" for c in spy.call_args_list)
    assert result["action"] == "vehicle_patrol"
    assert "disarmed" in result["message"].lower() or "reject" in result["message"].lower()


def test_t1b_armed_chat_patrol_allow_not_implemented_no_sim_tick(tmp_path: Path):
    """Gate passes when armed, Safety allows, but no sim tick is ever
    added — PATROL is not in T20's HOLD/LAND/GO_TO tick set."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    orch.handle_user_text("armar", exploding)
    result = orch.handle_user_text("patrol", exploding)
    assert result["action"] == "vehicle_patrol"
    assert "allow" in result["message"]
    assert "not_implemented" in result["message"]
    assert "Simulación" not in result["message"]
    assert "executed" not in result["message"].lower()


def test_t2_direct_run_skill_patrol_ok_flight_patrol_not_implemented():
    result = run_skill("skill.request_patrol")
    assert result.outcome == "ok"
    assert result.reason is None
    registry = CapabilityRegistry.load_default()
    patrol = next(s for s in registry.skills() if s.id == "skill.request_patrol")
    assert patrol.availability == CapabilityAvailability.AVAILABLE
    flight_patrol = registry.get_capability("flight.patrol")
    assert flight_patrol is not None
    assert flight_patrol.availability == CapabilityAvailability.NOT_IMPLEMENTED


def test_t3_six_prior_vehicle_skills_still_ok_charge_now_ok_too():
    for skill_id in (
        "skill.request_hold",
        "skill.request_land",
        "skill.request_go_to",
        "skill.request_takeoff",
        "skill.request_return_home",
        "skill.request_follow",
    ):
        result = run_skill(skill_id)
        assert result.outcome == "ok", f"{skill_id} should still be ok"
    charge = run_skill("skill.request_charge")
    assert charge.outcome == "ok"


def test_t4_chat_hold_land_go_to_takeoff_return_home_follow_still_skill_first_vehicle(
    tmp_path: Path,
):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    for raw, skill_id, action in (
        ("hold", "skill.request_hold", "vehicle_hold"),
        ("land", "skill.request_land", "vehicle_land"),
        ("go to", "skill.request_go_to", "vehicle_go_to"),
        ("takeoff", "skill.request_takeoff", "vehicle_takeoff"),
        ("rtl", "skill.request_return_home", "vehicle_return_home"),
        ("follow", "skill.request_follow", "vehicle_follow"),
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
