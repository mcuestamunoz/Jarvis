"""T42 (`B1-assistant-voice-interactive-cli`) tests, re-homed by T53 (V9).

T42 shipped `--voice`, a keyboard REPL over the Skills-only voice brain
(`run_voice_turn`, `source=VOICE`) that also spoke each reply. T53
(`B1-assistant-voice-only-loop`) retired it from the product: personal
Jarvis has one voice entry, `--voice-only` (full chat brain). `--voice`
now prints a one-line pointer to `--voice-only` and exits 2, and
`run_voice_interactive` is gone. The `run_voice_turn` seam itself stays
for batch/CI (`--voice-fixture`/`--voice-audio`) — T3 keeps proving it
tags every turn `source=VOICE`. REPL tests T1/T2 are retired.
"""

from __future__ import annotations

import sys
import typing
from pathlib import Path
from unittest.mock import patch

import pytest

from jarvis.capabilities.intent import VoiceIntentAdapter
from jarvis.capabilities.safety import AuthoritySource


def test_t1_voice_flag_redirects_to_voice_only_and_opens_nothing(monkeypatch, capsys):
    from jarvis.adapters.cli import main as main_module

    def no_session(*_args, **_kwargs):
        raise AssertionError("--voice must not open any session")

    for name in ("run_chat", "run_voice_only", "run_demo"):
        monkeypatch.setattr(main_module, name, no_session)
    monkeypatch.setattr(sys, "argv", ["jarvis", "--voice"])
    with pytest.raises(SystemExit) as exit_info:
        main_module.main()

    assert exit_info.value.code == 2
    assert "--voice-only" in capsys.readouterr().err
    assert not hasattr(main_module, "run_voice_interactive")


def test_t3_run_voice_turn_seam_still_tags_voice_source(tmp_path):
    from jarvis.adapters.voice import run_voice_turn
    from jarvis.core.orchestrator import JarvisOrchestrator
    from jarvis.llm.llm_client import JarvisLLMInterface
    from jarvis.llm.ollama_client import OllamaClient

    orchestrator = JarvisOrchestrator(workspace_root=tmp_path)
    llm_interface = JarvisLLMInterface(client=OllamaClient())
    with patch.object(VoiceIntentAdapter, "parse", wraps=VoiceIntentAdapter.parse) as voice_spy:
        for line in ("armar", "hold"):
            run_voice_turn(orchestrator, llm_interface, line)

    assert voice_spy.call_count >= 2
    for call in voice_spy.call_args_list:
        assert call.args[0] in ("armar", "hold")


def test_t4_chat_flag_alone_never_invokes_tts(tmp_path, monkeypatch):
    """`--chat` is the silent product mode — confirm it has no code path
    to `speak_egress`/`JARVIS_TTS_CMD` even when that env var is set, by
    checking `run_chat`'s own source for any reference to the TTS seam."""
    import inspect

    from jarvis.adapters.cli.main import run_chat

    source = inspect.getsource(run_chat)
    for forbidden in ("speak_egress", "JARVIS_TTS_CMD", "_voice_speak_fn", "TtsError"):
        assert forbidden not in source, f"run_chat must never reference {forbidden!r}"


def test_t5_no_tip_pins_no_speech_deps_esc_fence_green_guide_drops_interactive_voice():
    from tests.test_fase_c_esc_pwm_stub_rung_b1 import _esc_fence_violations
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()

    repo_root = Path(__file__).resolve().parents[1]
    pyproject_text = (repo_root / "pyproject.toml").read_text(encoding="utf-8").lower()
    for forbidden in ("piper", "whisper", "vosk", "speechrecognition", "pyttsx", "elevenlabs", "pyaudio"):
        assert forbidden not in pyproject_text, f"{forbidden!r} leaked into pyproject deps"

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

    assert "voice" not in typing.get_args(AuthoritySource)

    import re

    guide = (repo_root / "docs" / "USER_GUIDE_VOICE.md").read_text(encoding="utf-8")
    # Bare "--voice" (the retired interactive flag) must no longer be
    # taught — "--voice" is a substring of "--voice-only"/"--voice-fixture",
    # so this needs a boundary match rather than a plain `in`.
    assert re.search(r"--voice(?![-\w])", guide) is None, "guide still teaches interactive --voice"
    assert "--voice-only" in guide
