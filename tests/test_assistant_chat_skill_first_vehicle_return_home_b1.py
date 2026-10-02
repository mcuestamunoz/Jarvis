"""Tests T1-T5 for `B1-assistant-chat-skill-first-vehicle-return-home` (T27).

Fifth vehicle Skill-first — RETURN_HOME via shared `run_skill` vehicle
gate, then existing orch `_handle_vehicle_return_home`. HOLD/LAND/
GO_TO/TAKEOFF stay Skill-first. RETURN_HOME is explicitly NOT in the
T20 sim-copper tick set. FN-016's wizard nav-back cancel must still run
before this intercept — unreordered (regression).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from jarvis.capabilities.registry import CapabilityRegistry
from jarvis.capabilities.schemas import CapabilityAvailability
from jarvis.capabilities.skills_runtime import run_skill
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.core.parameter_requirements import MISSING_PROPULSION_PARAMETERS
from tests.test_fn016_navigation_parse_safety import _project_with_active_propulsion


class _ExplodingLLMInterface:
    def interpret(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def complete(self, *args, **kwargs):
        raise AssertionError("llm must not be called")


def test_t1_chat_rtl_skill_gate_and_vehicle_return_home_shape(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    with patch(
        "jarvis.capabilities.skills_runtime.run_skill",
        wraps=run_skill,
    ) as spy:
        result = orch.handle_user_text("rtl", exploding)
    assert spy.called
    assert any(c.args[0] == "skill.request_return_home" for c in spy.call_args_list)
    assert result["action"] == "vehicle_return_home"
    assert "disarmed" in result["message"].lower() or "reject" in result["message"].lower()


def test_t1b_armed_chat_return_home_allow_not_implemented_no_sim_tick(tmp_path: Path):
    """Gate passes when armed, Safety allows, but no sim tick is ever
    added — RETURN_HOME is not in T20's HOLD/LAND/GO_TO tick set."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    orch.handle_user_text("armar", exploding)
    result = orch.handle_user_text("return home", exploding)
    assert result["action"] == "vehicle_return_home"
    assert "allow" in result["message"]
    assert "not_implemented" in result["message"]
    assert "Simulación" not in result["message"]
    assert "executed" not in result["message"].lower()


def test_t2_direct_run_skill_return_home_ok_flight_return_home_not_implemented():
    result = run_skill("skill.request_return_home")
    assert result.outcome == "ok"
    assert result.reason is None
    registry = CapabilityRegistry.load_default()
    return_home = next(s for s in registry.skills() if s.id == "skill.request_return_home")
    assert return_home.availability == CapabilityAvailability.AVAILABLE
    flight_return_home = registry.get_capability("flight.return_home")
    assert flight_return_home is not None
    assert flight_return_home.availability == CapabilityAvailability.NOT_IMPLEMENTED


def test_t3_hold_land_go_to_takeoff_still_ok_follow_still_stub():
    for skill_id in (
        "skill.request_hold",
        "skill.request_land",
        "skill.request_go_to",
        "skill.request_takeoff",
    ):
        result = run_skill(skill_id)
        assert result.outcome == "ok", f"{skill_id} should still be ok"
    charge = run_skill("skill.request_charge")
    assert charge.outcome == "reject"
    assert charge.reason == "skill_stub"


def test_t4_chat_hold_land_go_to_takeoff_still_skill_first_vehicle(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    for raw, skill_id, action in (
        ("hold", "skill.request_hold", "vehicle_hold"),
        ("land", "skill.request_land", "vehicle_land"),
        ("go to", "skill.request_go_to", "vehicle_go_to"),
        ("takeoff", "skill.request_takeoff", "vehicle_takeoff"),
    ):
        with patch(
            "jarvis.capabilities.skills_runtime.run_skill",
            wraps=run_skill,
        ) as spy:
            result = orch.handle_user_text(raw, exploding)
        assert any(c.args[0] == skill_id for c in spy.call_args_list)
        assert result["action"] == action


def test_t4b_fn016_wizard_nav_back_still_wins_over_return_home(tmp_path: Path):
    """FN-016 (T15) precedence regression: inside an active
    DEFINE_MISSING_PARAMETERS wizard, "volver"/"vuelve" must still
    cancel the wizard — never reach the RETURN_HOME Skill-first gate at
    all. This Buy must not reorder that check."""
    orch = _project_with_active_propulsion(tmp_path, components_done=True)
    orch.start_define_missing_params(
        ["per_motor_max_thrust_n"], reason=MISSING_PROPULSION_PARAMETERS
    )
    result = orch.handle_user_text("volver", _ExplodingLLMInterface())
    assert result["status"] == "cancelled"
    assert result["action"] == "define_missing_params"


def test_t4c_idle_volver_still_vehicle_return_home_skill_first(tmp_path: Path):
    """Outside a wizard, "volver" still classifies as RETURN_HOME and
    now goes through the Skill-first gate too."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    with patch(
        "jarvis.capabilities.skills_runtime.run_skill",
        wraps=run_skill,
    ) as spy:
        result = orch.handle_user_text("volver", exploding)
    assert any(c.args[0] == "skill.request_return_home" for c in spy.call_args_list)
    assert result["action"] == "vehicle_return_home"


def test_t5_no_tip_version_pins_in_new_suite():
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()
