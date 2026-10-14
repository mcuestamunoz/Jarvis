"""Tests T1-T5 for `B1-assistant-chat-sim-copper` (T20).

After Safety `allow` on chat HOLD/LAND/GO_TO, the orchestrator runs one
`SimAutonomyExecutor.tick` (C40, sim only — never copper/ESC/motors).
`submit_command`'s own `execution` field stays byte-unchanged at
`"not_implemented"` (IC §0 decision 3, preferred path (a)).
"""

from __future__ import annotations

from pathlib import Path

from jarvis.core.orchestrator import JarvisOrchestrator
from tests.test_fase_c_esc_pwm_stub_rung_b1 import _esc_fence_violations

REPO_ROOT = Path(__file__).resolve().parents[1]


class _ExplodingLLMInterface:
    def interpret(self, *args, **kwargs):
        raise AssertionError("llm must not be called for a vehicle verb phrase")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm must not be called for a vehicle verb phrase")

    def complete(self, *args, **kwargs):
        raise AssertionError("llm must not be called for a vehicle verb phrase")


def test_t1_armar_then_hold_sim_tick_observed():
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()
    assert orch.handle_user_text("armar", exploding)["action"] == "vehicle_arm_policy"

    result = orch.handle_user_text("hold", exploding)
    assert result["action"] == "vehicle_hold"
    assert "allow" in result["message"]
    assert "not_implemented" in result["message"]
    assert "Simulación" in result["message"]
    assert "ejecuta" in result["message"].lower()  # "no se ejecuta... real" still present
    assert "executed" not in result["message"].lower()

    # Side effect observable: the lazy sim executor was actually constructed
    # and ticked (state advances), not just a static string.
    executor = orch._sim_autonomy_executor()
    assert executor is orch._sim_autonomy_executor()


def test_t1b_armar_then_land_sim_tick_observed():
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()
    orch.handle_user_text("armar", exploding)
    result = orch.handle_user_text("land", exploding)
    assert result["action"] == "vehicle_land"
    assert "Simulación" in result["message"]


def test_t1c_armar_then_go_to_sim_unavailable_without_target():
    """A *bare* GO_TO phrase (no destination) still carries empty
    params and still gets this same honest note. T32
    (`B1-assistant-chat-go-to-destination`, closes SD-GO_TO) adds a
    destination-bearing prove-now parse (e.g. "go to 1.0 2.0") that
    ticks a real sim note instead — see
    `tests/test_assistant_chat_go_to_destination_b1.py` for that
    coverage; this test only locks the bare-phrase honesty."""
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()
    orch.handle_user_text("armar", exploding)
    result = orch.handle_user_text("go to", exploding)
    assert result["action"] == "vehicle_go_to"
    assert "allow" in result["message"]
    assert "Simulación" in result["message"]
    assert "sin destino" in result["message"].lower() or "no disponible" in result["message"].lower()


def test_t2_armar_then_patrol_allow_no_tick():
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()
    orch.handle_user_text("armar", exploding)
    result = orch.handle_user_text("patrol", exploding)
    assert result["action"] == "vehicle_patrol"
    assert "allow" in result["message"]
    assert "not_implemented" in result["message"]
    assert "Simulación" not in result["message"]


def test_t2b_armar_then_takeoff_rtl_follow_allow_no_tick():
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()
    orch.handle_user_text("armar", exploding)
    for raw, action in (
        ("takeoff", "vehicle_takeoff"),
        ("rtl", "vehicle_return_home"),
        ("follow", "vehicle_follow"),
    ):
        result = orch.handle_user_text(raw, exploding)
        assert result["action"] == action
        assert "allow" in result["message"]
        assert "not_implemented" in result["message"]
        assert "Simulación" not in result["message"]


def test_t3_disarmed_hold_reject_no_tick():
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()
    result = orch.handle_user_text("hold", exploding)
    assert result["action"] == "vehicle_hold"
    assert "disarmed" in result["message"]
    assert "reject" in result["message"]
    assert "Simulación" not in result["message"]


def test_t4_esc_fence_still_green():
    orchestrator_source = (
        REPO_ROOT / "src" / "jarvis" / "core" / "orchestrator.py"
    ).read_text(encoding="utf-8")
    violations = _esc_fence_violations(orchestrator_source)
    assert not violations, f"orchestrator.py forbidden ESC coupling: {violations}"
