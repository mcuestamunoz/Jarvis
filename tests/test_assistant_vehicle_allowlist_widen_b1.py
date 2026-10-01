"""Tests T1-T8 for `B1-assistant-vehicle-allowlist-widen` (T14).

Safety-policy widen of `ArmedAllowlistSafetyGate._ALLOWED_VERBS` to all
seven chat `AutonomyVerb` values. No new Task kind — allow ≠ execute.
"""

from __future__ import annotations

from pathlib import Path

from jarvis.capabilities.registry import CapabilityRegistry
from jarvis.capabilities.safety import (
    ArmedAllowlistSafetyGate,
    RejectAllSafetyGate,
    SafetyRequest,
    default_safety_gate,
)
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command

REPO_ROOT = Path(__file__).resolve().parents[1]


class _ExplodingLLMInterface:
    def interpret(self, *args, **kwargs):
        raise AssertionError("llm must not be called for a vehicle verb phrase")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm must not be called for a vehicle verb phrase")

    def complete(self, *args, **kwargs):
        raise AssertionError("llm must not be called for a vehicle verb phrase")


_SEVEN_VERBS = (
    AutonomyVerb.HOLD,
    AutonomyVerb.LAND,
    AutonomyVerb.GO_TO,
    AutonomyVerb.TAKEOFF,
    AutonomyVerb.RETURN_HOME,
    AutonomyVerb.FOLLOW,
    AutonomyVerb.PATROL,
)


def test_t1_allowed_verbs_is_the_seven_verb_chat_set():
    assert ArmedAllowlistSafetyGate._ALLOWED_VERBS == frozenset(
        {"HOLD", "LAND", "GO_TO", "TAKEOFF", "RETURN_HOME", "FOLLOW", "PATROL"}
    )
    for verb in _SEVEN_VERBS:
        assert verb.value in ArmedAllowlistSafetyGate._ALLOWED_VERBS


def test_t2_disarmed_gate_rejects_all_seven_as_disarmed():
    gate = ArmedAllowlistSafetyGate()
    assert gate.armed is False
    for verb in (AutonomyVerb.TAKEOFF, AutonomyVerb.FOLLOW, AutonomyVerb.PATROL, AutonomyVerb.RETURN_HOME):
        command = propose_command(verb, params={})
        result = submit_command(command, gate)
        assert result.safety.outcome == "reject"
        assert result.safety.reason == "disarmed"
        assert result.execution == "not_attempted"


def test_t3_armed_gate_allows_all_seven_never_executed():
    gate = ArmedAllowlistSafetyGate()
    gate.arm()
    for verb in (AutonomyVerb.TAKEOFF, AutonomyVerb.FOLLOW, AutonomyVerb.PATROL, AutonomyVerb.RETURN_HOME):
        command = propose_command(verb, params={})
        result = submit_command(command, gate)
        assert result.safety.outcome == "allow"
        assert result.execution == "not_implemented"
        assert result.execution != "executed"


def test_t4_orchestrator_armar_then_each_verb_allow_not_implemented():
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()
    assert orch.handle_user_text("armar", exploding)["action"] == "vehicle_arm_policy"

    for raw, action in (
        ("takeoff", "vehicle_takeoff"),
        ("rtl", "vehicle_return_home"),
        ("follow", "vehicle_follow"),
        ("patrol", "vehicle_patrol"),
        ("hold", "vehicle_hold"),
    ):
        result = orch.handle_user_text(raw, exploding)
        assert result["action"] == action
        assert "allow" in result["message"]
        assert "not_implemented" in result["message"]
        assert "verb_not_allowed" not in result["message"]
        assert "executed" not in result["message"].lower()


def test_t5_armar_desarmar_patrol_back_to_disarmed():
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()
    assert orch.handle_user_text("armar", exploding)["action"] == "vehicle_arm_policy"
    armed_patrol = orch.handle_user_text("patrol", exploding)
    assert "allow" in armed_patrol["message"]
    assert orch.handle_user_text("desarmar", exploding)["action"] == "vehicle_disarm_policy"
    disarmed_patrol = orch.handle_user_text("patrol", exploding)
    assert "disarmed" in disarmed_patrol["message"]
    assert "reject" in disarmed_patrol["message"]


def test_t6_seed_cascade_unchanged_and_default_gate_still_reject_all():
    registry = CapabilityRegistry.load_default()
    cap_ids = {c.id for c in registry.capabilities()}
    assert len(cap_ids) == 10
    skill_ids = {s.id for s in registry.skills()}
    assert len(skill_ids) == 11
    assert isinstance(default_safety_gate(), RejectAllSafetyGate)
    assert default_safety_gate().evaluate(SafetyRequest()).outcome == "reject"


def test_t7_no_sim_autonomy_executor_wired_from_chat():
    forbidden = ("SimAutonomyExecutor", "sim_executor")
    orchestrator_source = (
        REPO_ROOT / "src" / "jarvis" / "core" / "orchestrator.py"
    ).read_text(encoding="utf-8")
    for token in forbidden:
        assert token not in orchestrator_source, (
            f"orchestrator.py references {token!r} — chat must never drive the sim executor"
        )

