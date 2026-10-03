"""Tests T1-T5 for `B1-assistant-chat-skill-first-ops-charge` (T31).

Last chat Skill stub — ops CHARGE Skill-first. Device gate
(`_device_skill_gate` + `_DEVICE_GATE_SKILL_IDS`) — deliberately NOT
the vehicle gate, NOT the policy gate, and NOT
`SoftwareCapabilitySafetyGate` (that gate would reject `ops.charge`'s
`not_implemented`+`device` shape outright). Closes chat Skill-first for
all twelve declared Skills. Seven vehicle Skill-first (HOLD…PATROL) and
both policy Skills (ARM/DISARM) stay green.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from jarvis.capabilities.registry import CapabilityRegistry
from jarvis.capabilities.schemas import CapabilityAvailability
from jarvis.capabilities.skills_runtime import (
    _POLICY_GATE_SKILL_IDS,
    _VEHICLE_GATE_SKILL_IDS,
    run_skill,
)
from jarvis.core.orchestrator import JarvisOrchestrator


class _ExplodingLLMInterface:
    def interpret(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def complete(self, *args, **kwargs):
        raise AssertionError("llm must not be called")


def test_t1_chat_charge_skill_gate_and_honest_not_implemented(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    with patch(
        "jarvis.capabilities.skills_runtime.run_skill",
        wraps=run_skill,
    ) as spy:
        result = orch.handle_user_text("charge", exploding)
    assert spy.called
    assert any(c.args[0] == "skill.request_charge" for c in spy.call_args_list)
    assert result["action"] == "ops_charge"
    assert "no está implementada" in result["message"]
    assert "no se inicia ninguna carga real" in result["message"]
    assert "AutonomyVerb" in result["message"]


def test_t2_direct_run_skill_charge_ok_ops_charge_not_implemented_not_other_gates():
    result = run_skill("skill.request_charge")
    assert result.outcome == "ok"
    assert result.reason is None

    registry = CapabilityRegistry.load_default()
    charge = next(s for s in registry.skills() if s.id == "skill.request_charge")
    assert charge.availability == CapabilityAvailability.AVAILABLE
    ops_charge = registry.get_capability("ops.charge")
    assert ops_charge is not None
    assert ops_charge.availability == CapabilityAvailability.NOT_IMPLEMENTED

    assert "skill.request_charge" not in _VEHICLE_GATE_SKILL_IDS
    assert "skill.request_charge" not in _POLICY_GATE_SKILL_IDS


def test_t3_seven_vehicle_and_both_policy_skills_still_ok():
    for skill_id in (
        "skill.request_hold",
        "skill.request_land",
        "skill.request_go_to",
        "skill.request_takeoff",
        "skill.request_return_home",
        "skill.request_follow",
        "skill.request_patrol",
        "skill.request_arm_policy",
        "skill.request_disarm_policy",
    ):
        result = run_skill(skill_id)
        assert result.outcome == "ok", f"{skill_id} should still be ok"


def test_t4_chat_hold_armar_desarmar_still_skill_first(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    for raw, skill_id, action in (
        ("hold", "skill.request_hold", "vehicle_hold"),
        ("armar", "skill.request_arm_policy", "vehicle_arm_policy"),
        ("desarmar", "skill.request_disarm_policy", "vehicle_disarm_policy"),
    ):
        with patch(
            "jarvis.capabilities.skills_runtime.run_skill",
            wraps=run_skill,
        ) as spy:
            result = orch.handle_user_text(raw, exploding)
        assert any(c.args[0] == skill_id for c in spy.call_args_list)
        assert result["action"] == action


def test_t5_no_tip_pins_and_payload_phrase_still_not_charge(tmp_path: Path):
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()

    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    with patch(
        "jarvis.capabilities.skills_runtime.run_skill",
        wraps=run_skill,
    ) as spy:
        result = orch.handle_user_text("carga util", exploding)
    assert not any(c.args[0] == "skill.request_charge" for c in spy.call_args_list)
    assert result["action"] != "ops_charge"
