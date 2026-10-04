"""Tests T1-T5 for `B1-assistant-voice-intent-ingress` (T35).

Skill-first phase C — **V1**: fill `VoiceIntentAdapter.parse(raw_text: str)
-> Intent(source=VOICE)` (mirrors `TerminalIntentAdapter`, stops
`NotImplementedError` for Voice only) and thread an optional `source`
through `handle_user_text` -> `_handle_global_commands` -> the twelve
classify sites, via one shared helper (`_parse_intent`) rather than a
hardcoded `TerminalIntentAdapter.parse` at each site. Default `source`
stays `TERMINAL` — CLI/MCP callers are byte-identical without passing
the new keyword. No STT/TTS, no voice loop, no craft/world — those are
later phases (T36+).
"""

from __future__ import annotations

import typing
from pathlib import Path
from unittest.mock import patch

from jarvis.capabilities.intent import (
    ApiIntentAdapter,
    Intent,
    IntentSource,
    RadioIntentAdapter,
    TerminalIntentAdapter,
    VoiceIntentAdapter,
)
from jarvis.capabilities.safety import AuthoritySource
from jarvis.core.orchestrator import JarvisOrchestrator

import pytest


class _ExplodingLLMInterface:
    def interpret(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def complete(self, *args, **kwargs):
        raise AssertionError("llm must not be called")


def test_t1_voice_adapter_parses_without_not_implemented():
    result = VoiceIntentAdapter.parse("hold")
    assert isinstance(result, Intent)
    assert result.source == IntentSource.VOICE
    assert result.raw_text == "hold"
    assert result.id
    assert result.metadata == {}


def test_t2_default_source_stays_terminal_regression(tmp_path: Path):
    """No `source` kwarg (every existing CLI/MCP call shape) must still
    resolve to TERMINAL and behave exactly as before T35."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    with (
        patch.object(TerminalIntentAdapter, "parse", wraps=TerminalIntentAdapter.parse) as terminal_spy,
        patch.object(VoiceIntentAdapter, "parse", wraps=VoiceIntentAdapter.parse) as voice_spy,
    ):
        result = orch.handle_user_text("hold", exploding)
    assert result["action"] == "vehicle_hold"
    assert "disarmed" in result["message"]
    assert "reject" in result["message"]
    assert terminal_spy.called
    assert not voice_spy.called

    orch.handle_user_text("armar", exploding)
    result2 = orch.handle_user_text("hold", exploding)
    assert result2["action"] == "vehicle_hold"
    assert "allow" in result2["message"]


def test_t3_voice_source_reaches_classify_on_skill_phrase(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    orch.handle_user_text("armar", exploding)

    with (
        patch.object(TerminalIntentAdapter, "parse", wraps=TerminalIntentAdapter.parse) as terminal_spy,
        patch.object(VoiceIntentAdapter, "parse", wraps=VoiceIntentAdapter.parse) as voice_spy,
    ):
        result = orch.handle_user_text("hold", exploding, source=IntentSource.VOICE)

    assert result["action"] == "vehicle_hold"
    assert "allow" in result["message"]
    assert voice_spy.called
    assert not terminal_spy.called
    for call in voice_spy.call_args_list:
        assert call.args[0] == "hold"


def test_t4_radio_api_still_not_implemented_no_mandatory_new_args(tmp_path: Path):
    for adapter in (RadioIntentAdapter, ApiIntentAdapter):
        with pytest.raises(NotImplementedError, match="not_implemented"):
            adapter.parse("anything")

    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    # Old call shape (no `source`) must still work with zero new required args.
    result = orch.handle_user_text("estado", exploding)
    assert result["status"] == "ok"


def test_t5_no_tip_pins_esc_fence_and_no_voice_authority_member():
    from tests.test_fase_c_esc_pwm_stub_rung_b1 import _esc_fence_violations
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()

    repo_root = Path(__file__).resolve().parents[1]
    orchestrator_source = (repo_root / "src" / "jarvis" / "core" / "orchestrator.py").read_text(
        encoding="utf-8"
    )
    violations = _esc_fence_violations(orchestrator_source)
    assert not violations, f"orchestrator.py forbidden ESC coupling: {violations}"

    assert "voice" not in typing.get_args(AuthoritySource)
