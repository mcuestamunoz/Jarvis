"""T43 (`B1-assistant-chat-voice-speak`) tests, re-homed by T53 (V9).

T43 made `--chat --voice-speak` speak every full-chat reply. T53
(`B1-assistant-voice-only-loop`) retired that hybrid: `--chat` is the
silent product mode, and the spoken full chat is `--voice-only`, which
reuses T43's thin `_chat_speak_fn` helper unchanged. The tests that
asserted hybrid speak-on-chat (T1, T3) and the interactive `--voice`
import smoke (T4) are retired; T2 (bare chat never speaks) and T5
(deps/ESC/guide guards) remain. Spoken full-chat behavior is covered by
`test_assistant_voice_only_loop_b1.py`.

Isolation: `run_chat()` takes no `workspace_root`, so these tests
monkeypatch the module-level `DEFAULT_WORKSPACE_ROOT`. Fake TTS is a
tiny shell script; no Piper/whisper/speaker/mic is ever required.
"""

from __future__ import annotations

import stat
import typing
from pathlib import Path

import jarvis.workspace.workspace_manager as workspace_manager_module
from jarvis.capabilities.safety import AuthoritySource


def _isolate_workspace(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(workspace_manager_module, "DEFAULT_WORKSPACE_ROOT", tmp_path / "workspace")


def _write_fake_tts_script(tmp_path: Path, received_path: Path) -> Path:
    script = tmp_path / "fake_tts.sh"
    script.write_text(
        f"#!/bin/sh\ncat >> {received_path}\nprintf '\\n---\\n' >> {received_path}\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script


def _feed_lines(monkeypatch, lines: list[str]):
    """Monkeypatch `input()` to pop from `lines`, raising `EOFError`
    once exhausted — the same shape a real piped stdin produces when
    it runs out, which is exactly what `run_chat`'s loop must survive."""
    queue = list(lines)

    def fake_input(prompt: str = "") -> str:
        if not queue:
            raise EOFError
        return queue.pop(0)

    monkeypatch.setattr("builtins.input", fake_input)


def test_t2_bare_chat_default_never_invokes_tts(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    from jarvis.adapters.cli.main import run_chat

    received = tmp_path / "received.log"
    script = _write_fake_tts_script(tmp_path, received)
    # Even with a working TTS command configured, bare run_chat() must
    # never call it — only --voice-only speaks.
    monkeypatch.setenv("JARVIS_TTS_CMD", str(script))
    _feed_lines(monkeypatch, ["armar", "exit"])

    run_chat()  # the silent product mode

    out = capsys.readouterr().out
    assert "vehicle_arm_policy" in out
    assert not received.exists(), "bare --chat must never invoke JARVIS_TTS_CMD"


def test_t5_no_tip_pins_no_speech_deps_esc_fence_green_guide_drops_hybrid():
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

    guide = (repo_root / "docs" / "USER_GUIDE_VOICE.md").read_text(encoding="utf-8")
    assert "--chat --voice-speak" not in guide, "T53: hybrid chat+speak is no longer product UX"
    assert "--voice-only" in guide
