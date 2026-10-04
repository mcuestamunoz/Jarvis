"""Tests T1-T5 for `B1-assistant-chat-voice-speak` (T43).

The Engineer tried T42's `--voice` (Skill-first only) and wanted the real
`jarvis --chat` instead — projects, Continuity, craft, LLM fallthrough —
with each reply also *spoken*. `run_chat(speak_tts=True)` wires that in
without a second renderer and without forcing `source=VOICE`: the chat
brain stays exactly `--chat` as before, only now every `Jarvis > …` print
also reaches `speak_egress`/`JARVIS_TTS_CMD` (T38's seam), never through
`_voice_speak_fn` (which would double-print).

Isolation note: `run_chat()` takes no `workspace_root` — unlike T42's
`run_voice_interactive` — so these tests isolate the same way any other
caller of the real CLI entry point would have to: monkeypatching the
module-level `DEFAULT_WORKSPACE_ROOT` that `WorkspaceManager.__init__`
reads, pointing it at `tmp_path`. No real on-disk workspace is ever
touched. Fake stdin is driven by monkeypatching `builtins.input`; the
fake TTS is a tiny shell script that records what it received —
mirroring `test_assistant_voice_demo_ready_b1.py`'s and
`test_assistant_voice_interactive_cli_b1.py`'s own pattern. No Piper/
whisper/speaker/mic is ever required.
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


def test_t1_chat_with_voice_speak_reaches_fake_tts(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    from jarvis.adapters.cli.main import run_chat

    received = tmp_path / "received.log"
    script = _write_fake_tts_script(tmp_path, received)
    monkeypatch.setenv("JARVIS_TTS_CMD", str(script))
    _feed_lines(monkeypatch, ["armar", "exit"])

    run_chat(speak_tts=True)

    out = capsys.readouterr().out
    assert "vehicle_arm_policy" in out

    assert received.exists(), "speak_tts=True must reach the external TTS command"
    captures = [chunk for chunk in received.read_text(encoding="utf-8").split("---\n") if chunk.strip()]
    assert len(captures) >= 1
    assert any("vehicle_arm_policy" in c or "ARMADA" in c for c in captures)


def test_t2_bare_chat_default_never_invokes_tts(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    from jarvis.adapters.cli.main import run_chat

    received = tmp_path / "received.log"
    script = _write_fake_tts_script(tmp_path, received)
    # Even with a working TTS command configured, bare run_chat() must
    # never call it — speak is opt-in only via speak_tts=True.
    monkeypatch.setenv("JARVIS_TTS_CMD", str(script))
    _feed_lines(monkeypatch, ["armar", "exit"])

    run_chat()  # bare default — byte-identical to pre-T43 behavior

    out = capsys.readouterr().out
    assert "vehicle_arm_policy" in out
    assert not received.exists(), "bare --chat must never invoke JARVIS_TTS_CMD"


def test_t3_missing_tts_config_is_honest_and_loop_survives(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)
    from jarvis.adapters.cli.main import run_chat

    _feed_lines(monkeypatch, ["armar", "hold", "exit"])

    run_chat(speak_tts=True)

    out = capsys.readouterr().out
    assert out.count("TTS no disponible") >= 2
    # The loop kept going past each TTS failure to the next turn and exit.
    assert "vehicle_arm_policy" in out
    assert "vehicle_hold" in out
    assert "Sesión cerrada" in out


def test_t4_voice_interactive_path_unaffected():
    """`--voice` (T42) must stay importable/runnable — this Buy touches
    `run_chat`/`main()` only, never `run_voice_interactive` itself. The
    full T42 suite (`test_assistant_voice_interactive_cli_b1.py`) is
    re-run alongside this file in CI/the implementation report as the
    authoritative regression check; this is a lightweight import smoke."""
    from jarvis.adapters.cli.main import run_voice_interactive

    assert callable(run_voice_interactive)


def test_t5_no_tip_pins_no_speech_deps_esc_fence_green_guide_mentions_chat_voice_speak():
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
    assert "--chat --voice-speak" in guide, "guide never documents --chat --voice-speak"
