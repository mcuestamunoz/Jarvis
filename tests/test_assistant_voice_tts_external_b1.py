"""Tests T1-T5 for `B1-assistant-voice-tts-external` (T38).

Skill-first phase C — **V4**: an external TTS **process seam** —
invoke a configured external command, feeding it the `render_response`
egress string on **stdin** (never argv — Skill messages have spaces/
quotes), and treat exit `0` as success. Wires into T36's `run_voice(...,
speak=...)` seam unchanged. No speech package in `pyproject.toml`, no
vendor hardcoded (the product brief recommends a free, local Piper
`en_GB` voice as the *demo* setup, installed outside the package —
never named in this module's code) — tests use a tiny fake TTS script
that reads stdin and records it, never a speaker or a real vendor
binary.
"""

from __future__ import annotations

import stat
import typing
from pathlib import Path

import pytest

from jarvis.adapters.voice import (
    FixtureSttSource,
    TtsConfigError,
    TtsError,
    TtsProcessError,
    make_speak_callable,
    run_voice,
    run_voice_turn,
    speak_egress,
)
from jarvis.capabilities.safety import AuthoritySource
from jarvis.core.orchestrator import JarvisOrchestrator


def _write_fake_tts_script(tmp_path: Path, received_path: Path) -> Path:
    script = tmp_path / "fake_tts.sh"
    script.write_text(
        f"#!/bin/sh\ncat >> {received_path}\nprintf '\\n---\\n' >> {received_path}\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script


class _ExplodingLLMInterface:
    def interpret(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def complete(self, *args, **kwargs):
        raise AssertionError("llm must not be called")


def test_t1_fake_tts_cmd_receives_egress_on_stdin(tmp_path: Path):
    received_path = tmp_path / "received.log"
    script = _write_fake_tts_script(tmp_path, received_path)

    text = 'hello there, this has spaces and "quotes" — no theater'
    speak_egress(text, command_template=str(script))

    assert received_path.read_text(encoding="utf-8").startswith(text)


def test_t2_missing_or_empty_config_is_typed_failure(monkeypatch):
    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)

    with pytest.raises(TtsConfigError):
        speak_egress("hola")

    with pytest.raises(TtsConfigError):
        speak_egress("hola", command_template="")


def test_t3_nonzero_exit_or_missing_binary_is_typed_failure(tmp_path: Path):
    failing_script = tmp_path / "failing_tts.sh"
    failing_script.write_text("#!/bin/sh\ncat >/dev/null\nexit 1\n", encoding="utf-8")
    failing_script.chmod(failing_script.stat().st_mode | stat.S_IEXEC)
    with pytest.raises(TtsProcessError):
        speak_egress("hola", command_template=str(failing_script))

    with pytest.raises(TtsProcessError):
        speak_egress("hola", command_template="this_binary_does_not_exist_xyz")


def test_t4_skill_turn_via_run_voice_speak_wired_to_fake_tts(tmp_path: Path):
    received_path = tmp_path / "received.log"
    script = _write_fake_tts_script(tmp_path, received_path)
    speak = make_speak_callable(command_template=str(script))

    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    result, egress = run_voice_turn(orch, exploding, "hold")
    speak(egress)

    assert result["action"] == "vehicle_hold"
    received = received_path.read_text(encoding="utf-8")
    assert egress in received

    # Also prove it end-to-end through run_voice's own speak= wiring (T36 seam).
    fixture = FixtureSttSource.from_lines(["armar", "hold"])
    turns = run_voice(orch, exploding, fixture, speak=speak)
    assert len(turns) == 2
    received_after_loop = received_path.read_text(encoding="utf-8")
    assert turns[0][2] in received_after_loop
    assert turns[1][2] in received_after_loop


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
        "src/jarvis/adapters/voice/fixture_loop.py",
        "src/jarvis/adapters/voice/external_stt.py",
        "src/jarvis/adapters/voice/external_tts.py",
        "src/jarvis/adapters/cli/main.py",
    ):
        source = (repo_root / rel_path).read_text(encoding="utf-8")
        violations = _esc_fence_violations(source)
        assert not violations, f"{rel_path} forbidden ESC coupling: {violations}"

    assert "voice" not in typing.get_args(AuthoritySource)

    # --chat still works with zero TTS/STT env configured.
    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)
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


def test_tts_error_is_base_of_typed_failures():
    assert issubclass(TtsConfigError, TtsError)
    assert issubclass(TtsProcessError, TtsError)
