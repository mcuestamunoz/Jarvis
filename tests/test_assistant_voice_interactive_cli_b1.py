"""Tests T1-T5 for `B1-assistant-voice-interactive-cli` (T42).

Skill-first phase C — interactive **use**, not a fixture/batch demo:
`run_voice_interactive()` is a REPL the Engineer sits in — type a turn,
see AND hear the reply. Reuses T35-T38's seams unchanged (`run_voice_turn`
tags `source=VOICE`; `_voice_speak_fn` speaks via `JARVIS_TTS_CMD`, same
honest-failure shape T38/T41 already proved). `--chat` stays text-only
by default — nothing here touches it.

Fake stdin is driven by monkeypatching `builtins.input`; the fake TTS
is a tiny shell script that records what it received, mirroring
`test_assistant_voice_demo_ready_b1.py`'s own pattern. No Piper/whisper/
speaker/mic is ever required.
"""

from __future__ import annotations

import stat
import typing
from pathlib import Path
from unittest.mock import patch

from jarvis.capabilities.intent import VoiceIntentAdapter
from jarvis.capabilities.safety import AuthoritySource


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
    it runs out, which is exactly what a REPL must survive."""
    queue = list(lines)

    def fake_input(prompt: str = "") -> str:
        if not queue:
            raise EOFError
        return queue.pop(0)

    monkeypatch.setattr("builtins.input", fake_input)


def test_t1_two_typed_turns_then_quit_speaks_both_egresses(tmp_path, monkeypatch, capsys):
    from jarvis.adapters.cli.main import run_voice_interactive

    received = tmp_path / "received.log"
    script = _write_fake_tts_script(tmp_path, received)
    monkeypatch.setenv("JARVIS_TTS_CMD", str(script))
    _feed_lines(monkeypatch, ["armar", "hold", "salir"])

    run_voice_interactive(workspace_root=tmp_path)

    out = capsys.readouterr().out
    assert "vehicle_arm_policy" in out
    assert "vehicle_hold" in out
    assert "Sesión de voz cerrada" in out

    captures = [chunk for chunk in received.read_text(encoding="utf-8").split("---\n") if chunk.strip()]
    assert len(captures) == 2
    assert "vehicle_arm_policy" in captures[0] or "ARMADA" in captures[0]
    assert "vehicle_hold" in captures[1] or "HOLD solicitado" in captures[1]


def test_t2_missing_tts_config_is_honest_and_loop_survives(tmp_path, monkeypatch, capsys):
    from jarvis.adapters.cli.main import run_voice_interactive

    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)
    _feed_lines(monkeypatch, ["hold", "estado", "salir"])

    run_voice_interactive(workspace_root=tmp_path)

    out = capsys.readouterr().out
    assert out.count("TTS no disponible") == 2
    # The loop kept going past the first TTS failure to the second turn.
    assert "vehicle_hold" in out
    assert "project_status" in out or "Proyecto" in out or "No hay proyecto" in out
    assert "Sesión de voz cerrada" in out


def test_t3_voice_source_used_for_every_typed_turn(tmp_path, monkeypatch):
    from jarvis.adapters.cli.main import run_voice_interactive

    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)
    _feed_lines(monkeypatch, ["armar", "hold", "salir"])

    with patch.object(VoiceIntentAdapter, "parse", wraps=VoiceIntentAdapter.parse) as voice_spy:
        run_voice_interactive(workspace_root=tmp_path)

    assert voice_spy.call_count >= 2
    for call in voice_spy.call_args_list:
        assert call.args[0] in ("armar", "hold")


def test_t4_chat_flag_alone_never_invokes_tts(tmp_path, monkeypatch):
    """`--chat` is a separate, deliberately untouched entry point —
    confirm it has no code path to `speak_egress`/`JARVIS_TTS_CMD` even
    when that env var is set, by checking `run_chat`'s own source for
    any reference to the TTS seam."""
    import inspect

    from jarvis.adapters.cli.main import run_chat

    source = inspect.getsource(run_chat)
    for forbidden in ("speak_egress", "JARVIS_TTS_CMD", "_voice_speak_fn", "TtsError"):
        assert forbidden not in source, f"run_chat must never reference {forbidden!r}"


def test_t5_no_tip_pins_no_speech_deps_esc_fence_green_guide_leads_with_voice():
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
    # Bare "--voice" (the interactive flag) must appear, and strictly
    # before the first "--voice-fixture" mention — "--voice" is itself a
    # substring of "--voice-fixture", so this needs a boundary match
    # rather than a plain .find().
    bare_voice_match = re.search(r"--voice(?![-\w])", guide)
    assert bare_voice_match is not None, "guide never mentions the bare --voice flag"
    fixture_pos = guide.find("--voice-fixture")
    assert fixture_pos == -1 or bare_voice_match.start() < fixture_pos, (
        "guide must lead with interactive --voice before --voice-fixture"
    )
