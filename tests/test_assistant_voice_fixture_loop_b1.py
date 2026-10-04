"""Tests T1-T5 for `B1-assistant-voice-fixture-loop` (T36).

Skill-first phase C — **V2**: a fixture-driven voice loop proving
ingress (T35's `VoiceIntentAdapter`/`source=IntentSource.VOICE`) →
Skill-first brain (`run_skill`/`_handle_*`, unchanged) → egress
(existing `render_response`, unchanged) end-to-end, without any real
microphone/speaker or STT/TTS vendor. No craft/`world/` here.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from jarvis.adapters.voice import FixtureSttSource, run_voice, run_voice_turn
from jarvis.capabilities.intent import (
    ApiIntentAdapter,
    IntentSource,
    RadioIntentAdapter,
    TerminalIntentAdapter,
    VoiceIntentAdapter,
)
from jarvis.capabilities.safety import AuthoritySource
from jarvis.core.orchestrator import JarvisOrchestrator

import pytest
import typing


class _ExplodingLLMInterface:
    def interpret(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def complete(self, *args, **kwargs):
        raise AssertionError("llm must not be called")


def test_t1_fixture_stt_yields_provided_text_unchanged(tmp_path: Path):
    lines = ["armar", "hold", "estado"]
    source = FixtureSttSource.from_lines(lines)
    assert list(source) == lines

    fixture_path = tmp_path / "fixture.txt"
    fixture_path.write_text("armar\n\nhold\n  \nestado\n", encoding="utf-8")
    from_path_source = FixtureSttSource.from_path(fixture_path)
    assert list(from_path_source) == lines


def test_t2_single_skill_turn_voice_source_and_non_empty_egress(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    with (
        patch.object(VoiceIntentAdapter, "parse", wraps=VoiceIntentAdapter.parse) as voice_spy,
        patch.object(TerminalIntentAdapter, "parse", wraps=TerminalIntentAdapter.parse) as terminal_spy,
    ):
        result, egress = run_voice_turn(orch, exploding, "hold")

    assert result["action"] == "vehicle_hold"
    assert "disarmed" in result["message"]
    assert "reject" in result["message"]
    assert isinstance(egress, str)
    assert egress
    assert "vehicle_hold" in egress
    assert voice_spy.called
    assert not terminal_spy.called


def test_t3_multiline_fixture_armar_then_hold_sees_armed_latch(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    fixture = FixtureSttSource.from_lines(["armar", "hold"])

    with patch.object(VoiceIntentAdapter, "parse", wraps=VoiceIntentAdapter.parse) as voice_spy:
        turns = run_voice(orch, exploding, fixture)

    assert len(turns) == 2
    arm_text, arm_result, arm_egress = turns[0]
    hold_text, hold_result, hold_egress = turns[1]
    assert arm_text == "armar"
    assert arm_result["action"] == "vehicle_arm_policy"
    assert arm_egress
    assert hold_text == "hold"
    assert hold_result["action"] == "vehicle_hold"
    assert "allow" in hold_result["message"]
    assert "Simulación" in hold_egress
    assert voice_spy.call_count >= 2
    for call in voice_spy.call_args_list:
        assert call.args[0] in ("armar", "hold")


def test_t3b_speak_callback_receives_each_egress(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    fixture = FixtureSttSource.from_lines(["armar", "hold"])
    spoken: list[str] = []
    run_voice(orch, exploding, fixture, speak=spoken.append)
    assert len(spoken) == 2
    assert all(isinstance(s, str) and s for s in spoken)


def test_t4_chat_mcp_path_unchanged_radio_api_still_not_implemented(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    # Old call shape (no `source`) still works with zero new required args.
    result = orch.handle_user_text("hold", exploding)
    assert result["action"] == "vehicle_hold"

    for adapter in (RadioIntentAdapter, ApiIntentAdapter):
        with pytest.raises(NotImplementedError, match="not_implemented"):
            adapter.parse("anything")


def test_t5_no_tip_pins_esc_fence_and_no_voice_authority_member():
    from tests.test_fase_c_esc_pwm_stub_rung_b1 import _esc_fence_violations
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()

    repo_root = Path(__file__).resolve().parents[1]
    for rel_path in (
        "src/jarvis/core/orchestrator.py",
        "src/jarvis/adapters/voice/fixture_loop.py",
        "src/jarvis/adapters/cli/main.py",
    ):
        source = (repo_root / rel_path).read_text(encoding="utf-8")
        violations = _esc_fence_violations(source)
        assert not violations, f"{rel_path} forbidden ESC coupling: {violations}"

    assert "voice" not in typing.get_args(AuthoritySource)
