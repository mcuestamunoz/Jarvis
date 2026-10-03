"""Tests T1-T5 for `B1-assistant-chat-skill-first-policy-arm` (T30).

First **policy** Skill-first slice — ARM + DISARM together. Software
Safety gate-only (on `safety.chat_armed_allowlist`, available+software)
— deliberately NOT the vehicle gate, since ARM/DISARM are a software
latch, not an AutonomyVerb. Seven vehicle Skill-first (HOLD…PATROL)
stay green. CHARGE stays stub.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from jarvis.capabilities.registry import CapabilityRegistry
from jarvis.capabilities.schemas import CapabilityAvailability
from jarvis.capabilities.skills_runtime import _VEHICLE_GATE_SKILL_IDS, run_skill
from jarvis.core.orchestrator import JarvisOrchestrator


class _ExplodingLLMInterface:
    def interpret(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def complete(self, *args, **kwargs):
        raise AssertionError("llm must not be called")


def test_t1_chat_arm_skill_gate_and_latch_armed(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    with patch(
        "jarvis.capabilities.skills_runtime.run_skill",
        wraps=run_skill,
    ) as spy:
        result = orch.handle_user_text("armar", exploding)
    assert spy.called
    assert any(c.args[0] == "skill.request_arm_policy" for c in spy.call_args_list)
    assert result["action"] == "vehicle_arm_policy"
    assert "armed=True" in result["message"]
    assert "ARMADA" in result["message"]
    assert "No es armado de ESC" in result["message"]


def test_t2_chat_disarm_skill_gate_and_latch_disarmed(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    orch.handle_user_text("armar", exploding)
    with patch(
        "jarvis.capabilities.skills_runtime.run_skill",
        wraps=run_skill,
    ) as spy:
        result = orch.handle_user_text("desarmar", exploding)
    assert any(c.args[0] == "skill.request_disarm_policy" for c in spy.call_args_list)
    assert result["action"] == "vehicle_disarm_policy"
    assert "armed=False" in result["message"]
    assert "DESARMADA" in result["message"]


def test_t3_policy_skills_ok_not_vehicle_gated_charge_still_stub():
    arm = run_skill("skill.request_arm_policy")
    assert arm.outcome == "ok"
    disarm = run_skill("skill.request_disarm_policy")
    assert disarm.outcome == "ok"

    assert "skill.request_arm_policy" not in _VEHICLE_GATE_SKILL_IDS
    assert "skill.request_disarm_policy" not in _VEHICLE_GATE_SKILL_IDS

    registry = CapabilityRegistry.load_default()
    for skill_id in ("skill.request_arm_policy", "skill.request_disarm_policy"):
        skill = next(s for s in registry.skills() if s.id == skill_id)
        assert skill.availability == CapabilityAvailability.AVAILABLE

    charge = run_skill("skill.request_charge")
    assert charge.outcome == "reject"
    assert charge.reason == "skill_stub"


def test_t4_chat_seven_vehicle_verbs_still_skill_first(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    for raw, skill_id, action in (
        ("hold", "skill.request_hold", "vehicle_hold"),
        ("land", "skill.request_land", "vehicle_land"),
        ("go to", "skill.request_go_to", "vehicle_go_to"),
        ("takeoff", "skill.request_takeoff", "vehicle_takeoff"),
        ("rtl", "skill.request_return_home", "vehicle_return_home"),
        ("follow", "skill.request_follow", "vehicle_follow"),
        ("patrol", "skill.request_patrol", "vehicle_patrol"),
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
