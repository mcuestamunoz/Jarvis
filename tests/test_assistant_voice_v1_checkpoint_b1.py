"""Tests T1-T5 for `B1-assistant-voice-v1-checkpoint` (T39).

Skill-first phase C — **V5, product milestone**: no new voice seam.
This file only *proves* T35-T38's existing surface already delivers
"speak → Skill-first brain → spoken reply" for all twelve declared
Skills, end-to-end, without a real mic/speaker/vendor — reusing
`VoiceIntentAdapter`, `run_voice`/`run_voice_turn`/
`run_voice_turn_from_audio`, `speak_egress`/`make_speak_callable`
exactly as T35-T38 shipped them.
"""

from __future__ import annotations

import stat
import typing
from pathlib import Path
from unittest.mock import patch

import pytest

from jarvis.adapters.voice import (
    FixtureSttSource,
    make_speak_callable,
    run_voice,
    run_voice_turn_from_audio,
)
from jarvis.capabilities.intent import ApiIntentAdapter, RadioIntentAdapter, VoiceIntentAdapter
from jarvis.capabilities.safety import AuthoritySource
from jarvis.core.orchestrator import JarvisOrchestrator

# One phrase per declared Skill — reuses the exact chat Skill-first
# vocabulary, same order the IC itself suggests. "armar" before the
# seven vehicle verbs so each gets an honest allow/not_implemented
# turn rather than a disarmed reject — either is a valid non-empty
# egress, this order just demos the richer path.
TWELVE_SKILL_PHRASES: tuple[str, ...] = (
    "armar",
    "hold",
    "land",
    "go to",
    "takeoff",
    "return home",
    "follow",
    "patrol",
    "charge",
    "desarmar",
    "explain c-rate-de-bateria",
    "estado",
)

EXPECTED_ACTIONS: frozenset[str] = frozenset(
    {
        "vehicle_arm_policy",
        "vehicle_hold",
        "vehicle_land",
        "vehicle_go_to",
        "vehicle_takeoff",
        "vehicle_return_home",
        "vehicle_follow",
        "vehicle_patrol",
        "ops_charge",
        "vehicle_disarm_policy",
        "global_command",  # explain
        "project_status",  # estado
    }
)


class _ExplodingLLMInterface:
    """Craft/LLM fallthrough must never be required for the twelve
    Skill-first phrases — any call here fails the test loudly."""

    def interpret(self, *args, **kwargs):
        raise AssertionError("llm must not be called for a Skill-first voice phrase")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm must not be called for a Skill-first voice phrase")

    def complete(self, *args, **kwargs):
        raise AssertionError("llm must not be called for a Skill-first voice phrase")


def _write_fake_tts_script(tmp_path: Path, received_path: Path) -> Path:
    script = tmp_path / "fake_tts.sh"
    script.write_text(
        f"#!/bin/sh\ncat >> {received_path}\nprintf '\\n---\\n' >> {received_path}\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script


def _write_fake_stt_script(tmp_path: Path, transcript: str) -> Path:
    script = tmp_path / "fake_stt.sh"
    script.write_text(f"#!/bin/sh\necho '{transcript}'\n", encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script


def test_t1_twelve_skills_via_fixture_voice_loop_no_craft_fallthrough(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    fixture = FixtureSttSource.from_lines(TWELVE_SKILL_PHRASES)

    with patch.object(VoiceIntentAdapter, "parse", wraps=VoiceIntentAdapter.parse) as voice_spy:
        turns = run_voice(orch, exploding, fixture)

    assert len(turns) == len(TWELVE_SKILL_PHRASES)
    seen_actions = {result["action"] for _text, result, _egress in turns}
    assert seen_actions == EXPECTED_ACTIONS
    for text, result, egress in turns:
        assert egress, f"{text!r} ({result['action']}) produced empty egress"
    assert voice_spy.called
    for call in voice_spy.call_args_list:
        assert call.args[0] in TWELVE_SKILL_PHRASES


def test_t2_twelve_skills_speak_wired_fake_tts_records_every_egress(tmp_path: Path):
    received_path = tmp_path / "received.log"
    script = _write_fake_tts_script(tmp_path, received_path)
    speak = make_speak_callable(command_template=str(script))

    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    fixture = FixtureSttSource.from_lines(TWELVE_SKILL_PHRASES)
    turns = run_voice(orch, exploding, fixture, speak=speak)

    assert len(turns) == 12
    received = received_path.read_text(encoding="utf-8")
    captures = [chunk for chunk in received.split("---\n") if chunk.strip()]
    assert len(captures) == 12
    for _text, _result, egress in turns:
        assert egress in received


def test_t3_stt_to_skill_to_tts_combined_seam(tmp_path: Path):
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(b"")
    stt_script = _write_fake_stt_script(tmp_path, "hold")
    received_path = tmp_path / "received.log"
    tts_script = _write_fake_tts_script(tmp_path, received_path)
    speak = make_speak_callable(command_template=str(tts_script))

    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    with patch.object(VoiceIntentAdapter, "parse", wraps=VoiceIntentAdapter.parse) as voice_spy:
        result, egress = run_voice_turn_from_audio(
            orch, exploding, audio_path, command_template=f"{stt_script} {{audio}}"
        )
        speak(egress)

    assert result["action"] == "vehicle_hold"
    assert egress
    assert received_path.read_text(encoding="utf-8").startswith(egress)
    assert voice_spy.called
    for call in voice_spy.call_args_list:
        assert call.args[0] == "hold"


def test_t4_radio_api_still_not_implemented_no_voice_authority_member():
    for adapter in (RadioIntentAdapter, ApiIntentAdapter):
        with pytest.raises(NotImplementedError, match="not_implemented"):
            adapter.parse("anything")
    assert "voice" not in typing.get_args(AuthoritySource)


def test_t5_pyproject_0_7_0_no_speech_deps_no_tip_pins_esc_fence_chat_unaffected(
    tmp_path: Path, monkeypatch
):
    from tests.test_fase_c_esc_pwm_stub_rung_b1 import _esc_fence_violations
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()

    repo_root = Path(__file__).resolve().parents[1]
    pyproject_text = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    for forbidden in (
        "whisper",
        "vosk",
        "speechrecognition",
        "pyttsx",
        "elevenlabs",
        "pyaudio",
        "piper",
    ):
        assert forbidden not in pyproject_text.lower()

    for rel_path in (
        "src/jarvis/core/orchestrator.py",
        "src/jarvis/adapters/voice/fixture_loop.py",
        "src/jarvis/adapters/voice/external_stt.py",
        "src/jarvis/adapters/voice/external_tts.py",
        "src/jarvis/adapters/cli/main.py",
    ):
        source = (repo_root / rel_path).read_text(encoding="utf-8")
        violations = _esc_fence_violations(source)
        assert not violations, f"{rel_path} forbidden ESC coupling: {violations}"

    # --chat / --voice-fixture still work with zero STT/TTS env configured.
    monkeypatch.delenv("JARVIS_STT_CMD", raising=False)
    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    result = orch.handle_user_text("hold", exploding)
    assert result["action"] == "vehicle_hold"

    fixture = FixtureSttSource.from_lines(["armar", "hold"])
    turns = run_voice(orch, exploding, fixture)
    assert len(turns) == 2
    assert turns[1][1]["action"] == "vehicle_hold"
