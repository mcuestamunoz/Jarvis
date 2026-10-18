"""Tests T1-T5 for `B1-assistant-voice-blank-stt-take` (T59).

T58 live smoke: when nobody speaks, whisper.cpp returns `[BLANK_AUDIO]`
(or `[Music]`, `[Silence]`, …) instead of an empty string, so
`--voice-only` echoed `User > [voz] [BLANK_AUDIO]`, sent it to the brain
and printed "No se pudo interpretar la intención" in a loop. T59 adds
`is_blank_stt_transcript` (closed marker set, case-insensitive, any
number of markers, whitespace/edge punctuation around) next to the STT
seam; the mic reader treats such a take as empty — no echo, nothing to
the brain, listen again. Real speech, including wrong-but-real words,
is unchanged.

Mic-free: the T53 `_FakeVoice` RECORD/STT/TTS fakes.
"""

from __future__ import annotations

import typing
from pathlib import Path

import jarvis.workspace.workspace_manager as workspace_manager_module
from jarvis.adapters.voice import BLANK_STT_MARKERS, is_blank_stt_transcript
from jarvis.capabilities.safety import AuthoritySource

REPO_ROOT = Path(__file__).resolve().parents[1]
GUIDE = REPO_ROOT / "docs" / "USER_GUIDE_VOICE.md"


def test_t1_markers_and_whitespace_are_blank():
    for raw in (
        "[BLANK_AUDIO]",
        "[blank_audio]",
        "  [BLANK_AUDIO]  ",
        "[Music]",
        "[MUSIC]",
        "(music)",
        "[Silence]",
        "[Silence].",
        "(silence)",
        "[BLANK_AUDIO] [BLANK_AUDIO]",
        "[BLANK_AUDIO]\n[Music]",
        "",
        "   ",
    ):
        assert is_blank_stt_transcript(raw), repr(raw)
    assert {"[blank_audio]", "[music]", "[silence]"} <= BLANK_STT_MARKERS


def test_t2_real_speech_is_not_blank():
    for raw in (
        "estado",
        "salir",
        "Completo.",
        "armar",
        "See you in the next step",  # wrong-but-real words still reach the brain
        "Hola [Music]",
        "[BLANK]",
        "BLANK_AUDIO",
        "music",
    ):
        assert not is_blank_stt_transcript(raw), repr(raw)


def _voice_only(tmp_path: Path, monkeypatch, transcripts: list[str], *, tts: bool = False):
    from jarvis.adapters.cli.main import run_voice_only
    from tests.test_assistant_voice_only_loop_b1 import _FakeVoice

    monkeypatch.setattr(workspace_manager_module, "DEFAULT_WORKSPACE_ROOT", tmp_path / "workspace")

    def no_keyboard(prompt: str = "") -> str:
        raise AssertionError("voice-only must not read the keyboard without projects")

    monkeypatch.setattr("builtins.input", no_keyboard)
    fake = _FakeVoice(tmp_path, monkeypatch, transcripts, tts=tts)
    return fake, run_voice_only


def test_t3_blank_take_no_echo_no_intent_error_mic_reopens(tmp_path, monkeypatch, capsys):
    fake, run_voice_only = _voice_only(tmp_path, monkeypatch, ["[BLANK_AUDIO]", "[Music]", "salir"])
    run_voice_only()

    out = capsys.readouterr().out
    assert "[BLANK_AUDIO]" not in out and "[Music]" not in out
    assert "No se pudo interpretar" not in out
    assert "STT no disponible" not in out, "a blank take is not an STT failure"
    assert out.count("User > [voz]") == 1 and "User > [voz] salir" in out
    assert fake.record_count() == 3, "mic reopens after each blank take"
    assert out.count("Jarvis > Grabando") == 3
    assert out.count("Sesión cerrada") == 1

    # A blank take counts as a completed take: it resets the double-cancel
    # counter (cancel, blank, cancel ≠ two consecutive cancels).
    import jarvis.adapters.voice as voice_module

    sub = tmp_path / "counter"
    sub.mkdir()
    fake, run_voice_only = _voice_only(sub, monkeypatch, ["[BLANK_AUDIO]", "salir"])
    real_record = voice_module.record_audio_file
    calls = {"n": 0}

    def cancel_first_and_third(output_path, **kwargs):
        calls["n"] += 1
        if calls["n"] in (1, 3):
            raise KeyboardInterrupt
        return real_record(output_path, **kwargs)

    monkeypatch.setattr(voice_module, "record_audio_file", cancel_first_and_third)
    run_voice_only()
    out = capsys.readouterr().out
    assert out.count("Grabación cancelada") == 2
    assert "User > [voz] salir" in out, "session must survive cancel → blank → cancel"


def test_t4_real_speech_still_echoes_and_reaches_the_brain(tmp_path, monkeypatch, capsys):
    _, run_voice_only = _voice_only(tmp_path, monkeypatch, ["armar", "estado", "salir"], tts=True)
    run_voice_only()
    out = capsys.readouterr().out
    assert "User > [voz] armar" in out and "vehicle_arm_policy" in out
    assert "User > [voz] estado" in out
    assert "User > [voz] salir" in out and out.count("Sesión cerrada") == 1


def test_t5_guide_deps_tip_pin_esc():
    guide = GUIDE.read_text(encoding="utf-8")
    assert "[BLANK_AUDIO]" in guide
    assert "T59" in guide
    assert 'JARVIS_WHISPER_ARGS="-l es"' in guide

    from tests.test_fase_c_esc_pwm_stub_rung_b1 import _esc_fence_violations
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
    for forbidden in (
        "piper", "whisper", "vosk", "speechrecognition", "pyttsx", "elevenlabs",
        "pyaudio", "sounddevice", "langdetect", "langid", "fasttext",
    ):
        assert forbidden not in pyproject_text, f"{forbidden!r} leaked into pyproject deps"
    for rel_path in ("src/jarvis/adapters/voice/external_stt.py", "src/jarvis/adapters/cli/main.py"):
        source = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        assert not _esc_fence_violations(source), f"{rel_path} forbidden ESC coupling"
    assert "voice" not in typing.get_args(AuthoritySource)
