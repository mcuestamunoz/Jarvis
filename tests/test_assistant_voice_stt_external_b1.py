"""Tests T1-T5 for `B1-assistant-voice-stt-external` (T37).

Skill-first phase C — **V3**: an external STT **process seam** —
invoke a configured external command on an audio file path, feed its
stdout transcript into the exact same `run_voice_turn` (T36) →
`handle_user_text(..., source=VOICE)` (T35) chain. No speech package
in `pyproject.toml`, no audio decode anywhere in this repo, no vendor
hardcoded — tests use a tiny fake STT script, never a mic or a real
vendor binary.
"""

from __future__ import annotations

import stat
import typing
from pathlib import Path
from unittest.mock import patch

import pytest

from jarvis.adapters.voice import (
    FixtureSttSource,
    SttConfigError,
    SttEmptyTranscriptError,
    SttError,
    SttProcessError,
    run_voice,
    run_voice_turn_from_audio,
    transcribe_audio_file,
)
from jarvis.capabilities.intent import VoiceIntentAdapter
from jarvis.capabilities.safety import AuthoritySource
from jarvis.core.orchestrator import JarvisOrchestrator


def _write_fake_stt_script(tmp_path: Path, transcript: str = "hold") -> Path:
    script = tmp_path / "fake_stt.sh"
    script.write_text(f"#!/bin/sh\necho '{transcript}'\n", encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script


class _ExplodingLLMInterface:
    def interpret(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def complete(self, *args, **kwargs):
        raise AssertionError("llm must not be called")


def test_t1_fake_stt_cmd_returns_expected_transcript(tmp_path: Path):
    script = _write_fake_stt_script(tmp_path, "hold")
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(b"")

    transcript = transcribe_audio_file(
        audio_path, command_template=f"{script} {{audio}}"
    )
    assert transcript == "hold"


def test_t2_missing_or_empty_config_is_typed_failure(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("JARVIS_STT_CMD", raising=False)
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(b"")

    with pytest.raises(SttConfigError):
        transcribe_audio_file(audio_path)

    with pytest.raises(SttConfigError):
        transcribe_audio_file(audio_path, command_template="")


def test_t3_nonzero_exit_or_empty_stdout_is_typed_failure(tmp_path: Path):
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(b"")

    failing_script = tmp_path / "failing_stt.sh"
    failing_script.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    failing_script.chmod(failing_script.stat().st_mode | stat.S_IEXEC)
    with pytest.raises(SttProcessError):
        transcribe_audio_file(audio_path, command_template=f"{failing_script} {{audio}}")

    empty_script = tmp_path / "empty_stt.sh"
    empty_script.write_text("#!/bin/sh\nprintf ''\n", encoding="utf-8")
    empty_script.chmod(empty_script.stat().st_mode | stat.S_IEXEC)
    with pytest.raises(SttEmptyTranscriptError):
        transcribe_audio_file(audio_path, command_template=f"{empty_script} {{audio}}")

    with pytest.raises(SttProcessError):
        transcribe_audio_file(
            audio_path, command_template="this_binary_does_not_exist_xyz {audio}"
        )


def test_t4_fake_stt_wired_to_voice_turn_source_voice_honest_result(tmp_path: Path):
    script = _write_fake_stt_script(tmp_path, "hold")
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(b"")

    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    with patch.object(VoiceIntentAdapter, "parse", wraps=VoiceIntentAdapter.parse) as voice_spy:
        result, egress = run_voice_turn_from_audio(
            orch, exploding, audio_path, command_template=f"{script} {{audio}}"
        )

    assert result["action"] == "vehicle_hold"
    assert "disarmed" in result["message"]
    assert egress
    assert voice_spy.called
    for call in voice_spy.call_args_list:
        assert call.args[0] == "hold"


def test_t5_no_tip_pins_esc_fence_no_speech_deps_no_voice_authority_chat_unaffected(
    tmp_path: Path, monkeypatch
):
    from tests.test_fase_c_esc_pwm_stub_rung_b1 import _esc_fence_violations
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()

    repo_root = Path(__file__).resolve().parents[1]
    pyproject_text = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    for forbidden in ("whisper", "vosk", "speechrecognition", "pyttsx", "elevenlabs", "pyaudio"):
        assert forbidden not in pyproject_text.lower()

    for rel_path in (
        "src/jarvis/adapters/voice/fixture_loop.py",
        "src/jarvis/adapters/voice/external_stt.py",
        "src/jarvis/adapters/cli/main.py",
    ):
        source = (repo_root / rel_path).read_text(encoding="utf-8")
        violations = _esc_fence_violations(source)
        assert not violations, f"{rel_path} forbidden ESC coupling: {violations}"

    assert "voice" not in typing.get_args(AuthoritySource)

    # --chat still works with zero STT env configured.
    monkeypatch.delenv("JARVIS_STT_CMD", raising=False)
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    result = orch.handle_user_text("hold", exploding)
    assert result["action"] == "vehicle_hold"

    # --voice-fixture (T36) still works untouched by this Buy.
    fixture = FixtureSttSource.from_lines(["armar", "hold"])
    turns = run_voice(orch, exploding, fixture)
    assert len(turns) == 2
    assert turns[1][1]["action"] == "vehicle_hold"


def test_stt_error_is_base_of_typed_failures():
    assert issubclass(SttConfigError, SttError)
    assert issubclass(SttProcessError, SttError)
    assert issubclass(SttEmptyTranscriptError, SttError)
