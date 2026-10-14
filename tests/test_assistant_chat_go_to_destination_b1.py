"""Tests T1-T5 for `B1-assistant-chat-go-to-destination` (T32).

Closes **SD-GO_TO**: a resolver seam
(`JarvisOrchestrator._resolve_go_to_destination`) owns chat GO_TO's
destination, ordered (1) metadata connect plug `go_to_x_m`/`go_to_y_m`
(for later GPS/world/voice), (2) finite prove-now parse
(`jarvis.intelligence.assistant_task.parse_go_to_destination`) on
`go to|goto|ir a|ve a <x> <y>`, (3) else `None` — never inventing a
default. When present, the existing T20 sim tick gets real
coordinates; when absent, the existing honest "sin destino" note is
unchanged.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from jarvis.capabilities.intent import TerminalIntentAdapter
from jarvis.capabilities.skills_runtime import run_skill
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.intelligence.assistant_task import (
    parse_go_to_destination,
    try_request_charge_task,
    try_request_follow_task,
    try_request_patrol_task,
    try_request_return_home_task,
    try_request_takeoff_task,
)


class _ExplodingLLMInterface:
    def interpret(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def complete(self, *args, **kwargs):
        raise AssertionError("llm must not be called")


def test_t1_armar_then_bare_go_to_still_sin_destino(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    orch.handle_user_text("armar", exploding)
    result = orch.handle_user_text("go to", exploding)
    assert result["action"] == "vehicle_go_to"
    assert "allow" in result["message"]
    assert "Simulación" in result["message"]
    assert "sin destino" in result["message"].lower()
    assert "tick en t=" not in result["message"]


def test_t2_armar_then_go_to_with_coords_ticks_real_sim(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    orch.handle_user_text("armar", exploding)
    result = orch.handle_user_text("go to 1.0 2.0", exploding)
    assert result["action"] == "vehicle_go_to"
    assert "allow" in result["message"]
    assert "Simulación" in result["message"]
    assert "tick en t=" in result["message"]
    assert "sin destino" not in result["message"].lower()

    # Other locked prove-now forms behave the same.
    for raw in ("goto -3.5 4", "ir a 10 -2.25", "ve a 0.5 0.5"):
        other = orch.handle_user_text(raw, exploding)
        assert other["action"] == "vehicle_go_to"
        assert "tick en t=" in other["message"]


def test_t3_metadata_connect_plug_resolves_destination():
    """Unit coverage of the resolver seam itself — the metadata plug
    (source 1) is for future GPS/world/voice providers; chat today
    never populates it (`TerminalIntentAdapter.parse` always starts
    with empty metadata), so this proves the seam directly rather than
    via `handle_user_text`."""
    orch = JarvisOrchestrator()

    intent = TerminalIntentAdapter.parse("go to")
    intent.metadata["go_to_x_m"] = "5.5"
    intent.metadata["go_to_y_m"] = "-1.25"
    assert orch._resolve_go_to_destination(intent) == (5.5, -1.25)

    bare_intent = TerminalIntentAdapter.parse("go to")
    assert orch._resolve_go_to_destination(bare_intent) is None

    prove_now_intent = TerminalIntentAdapter.parse("go to 7 8")
    assert orch._resolve_go_to_destination(prove_now_intent) == (7.0, 8.0)

    non_finite_intent = TerminalIntentAdapter.parse("go to")
    non_finite_intent.metadata["go_to_x_m"] = "inf"
    non_finite_intent.metadata["go_to_y_m"] = "2"
    assert orch._resolve_go_to_destination(non_finite_intent) is None

    # Direct classify-layer parse, same pattern, used by try_request_go_to_task.
    assert parse_go_to_destination("go to 1.0 2.0") == (1.0, 2.0)
    assert parse_go_to_destination("ve a comprar pan") is None


def test_t4_hold_land_still_tick_patrol_no_tick_disarmed_go_to_no_tick_skill_first_still_ok(
    tmp_path: Path,
):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()

    disarmed = orch.handle_user_text("go to 1.0 2.0", exploding)
    assert disarmed["action"] == "vehicle_go_to"
    assert "disarmed" in disarmed["message"]
    assert "tick en t=" not in disarmed["message"]

    orch.handle_user_text("armar", exploding)
    hold = orch.handle_user_text("hold", exploding)
    assert "Simulación" in hold["message"]
    land = orch.handle_user_text("land", exploding)
    assert "Simulación" in land["message"]
    patrol = orch.handle_user_text("patrol", exploding)
    assert "Simulación" not in patrol["message"]

    with patch(
        "jarvis.capabilities.skills_runtime.run_skill",
        wraps=run_skill,
    ) as spy:
        skill_first_result = orch.handle_user_text("go to 3 4", exploding)
    assert any(c.args[0] == "skill.request_go_to" for c in spy.call_args_list)
    assert skill_first_result["action"] == "vehicle_go_to"
    assert "tick en t=" in skill_first_result["message"]


def test_t5_no_tip_pins_esc_fence_and_siblings_refuse_destination_pattern():
    from tests.test_fase_c_esc_pwm_stub_rung_b1 import _esc_fence_violations
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()

    from pathlib import Path as _Path

    repo_root = _Path(__file__).resolve().parents[1]
    orchestrator_source = (repo_root / "src" / "jarvis" / "core" / "orchestrator.py").read_text(
        encoding="utf-8"
    )
    violations = _esc_fence_violations(orchestrator_source)
    assert not violations, f"orchestrator.py forbidden ESC coupling: {violations}"

    destination_text = "go to 1.0 2.0"
    intent = TerminalIntentAdapter.parse(destination_text)
    assert try_request_takeoff_task(intent) is None
    assert try_request_return_home_task(TerminalIntentAdapter.parse(destination_text)) is None
    assert try_request_follow_task(TerminalIntentAdapter.parse(destination_text)) is None
    assert try_request_patrol_task(TerminalIntentAdapter.parse(destination_text)) is None
    assert try_request_charge_task(TerminalIntentAdapter.parse(destination_text)) is None

    # Payload/mission lines still unaffected.
    assert try_request_charge_task(TerminalIntentAdapter.parse("carga util")) is None
