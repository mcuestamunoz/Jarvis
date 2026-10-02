"""Tests T1-T5 for `B1-assistant-chat-skill-first-vehicle-hold` (T23).

First vehicle Skill-first — HOLD only via `run_skill` gate, then existing
orch `_handle_vehicle_hold`. Other vehicle Skills stay stub.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from jarvis.capabilities.registry import CapabilityRegistry
from jarvis.capabilities.schemas import CapabilityAvailability
from jarvis.capabilities.skills_runtime import run_skill
from jarvis.core.orchestrator import JarvisOrchestrator

REPO_ROOT = Path(__file__).resolve().parents[1]


class _ExplodingLLMInterface:
    def interpret(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def complete(self, *args, **kwargs):
        raise AssertionError("llm must not be called")


def test_t1_chat_hold_skill_gate_and_vehicle_hold_shape(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    with patch(
        "jarvis.capabilities.skills_runtime.run_skill",
        wraps=run_skill,
    ) as spy:
        result = orch.handle_user_text("hold", exploding)
    assert spy.called
    assert any(c.args[0] == "skill.request_hold" for c in spy.call_args_list)
    assert result["action"] == "vehicle_hold"
    # Disarmed ArmedAllowlist honesty — never a claim of executed flight.
    assert "disarmed" in result["message"].lower() or "reject" in result["message"].lower()


def test_t2_direct_run_skill_hold_ok_gate_not_software_safety():
    result = run_skill("skill.request_hold")
    assert result.outcome == "ok"
    assert result.reason is None
    # Gate only — no UX message from skills_runtime for vehicle HOLD.
    # Software Safety would reject vehicle/not_implemented; we must not.
    registry = CapabilityRegistry.load_default()
    hold = next(s for s in registry.skills() if s.id == "skill.request_hold")
    assert hold.availability == CapabilityAvailability.AVAILABLE
    flight_hold = registry.get_capability("flight.hold")
    assert flight_hold is not None
    assert flight_hold.availability == CapabilityAvailability.NOT_IMPLEMENTED


def test_t3_other_vehicle_skill_still_stub():
    """T23: LAND was stub. T24 flips LAND to available — see
    `test_assistant_chat_skill_first_vehicle_land_b1`. CHARGE stays stub."""
    charge = run_skill("skill.request_charge")
    assert charge.outcome == "reject"
    assert charge.reason == "skill_stub"
    go_to = run_skill("skill.request_go_to")
    assert go_to.outcome == "reject"
    assert go_to.reason == "skill_stub"


def test_t4_software_skill_first_still_green(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    explain = orch.handle_user_text("explain c-rate-de-bateria", exploding)
    assert explain["status"] == "ok"
    assert "DEFINICION" in explain["message"]
    with patch(
        "jarvis.capabilities.skills_runtime.run_skill",
        wraps=run_skill,
    ) as spy:
        status = orch.handle_user_text("estado", exploding)
    assert any(c.args[0] == "skill.project_status" for c in spy.call_args_list)
    assert status["action"] == "project_status"
    assert "startup_context" in status


def test_t5_no_tip_version_pins_in_new_suite():
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()
