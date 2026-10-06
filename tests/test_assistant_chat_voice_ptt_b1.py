"""Tests T1-T7 for `B1-assistant-chat-voice-ptt` (T47).

T43 gave `--chat --voice-speak` spoken replies; T45 kept Continuity
walls honest (brief by default). The remaining gap the Engineer named:
*speaking into the air* inside that same session, not the Skills-only
`--voice` REPL and not the one-shot `--voice-audio` path. T46-DC locked
push-to-talk (not always-on): typing the finite trigger `hablar`/
`habla` at `User > ` records a timed clip via a new external
`JARVIS_RECORD_CMD` seam, transcribes it via the existing T37
`JARVIS_STT_CMD` seam, echoes `User > [voz] {transcript}`, and lets
that transcript fall through the exact same `run_chat` loop — same
`TERMINAL` brain, same Continuity, same T45 wall rules. No
`source=VOICE`, no `run_voice_turn`, no new orchestrator.

Isolation note: same pattern as `test_assistant_chat_voice_speak_b1.py`
/ `test_assistant_chat_spoken_continuity_b1.py` — `run_chat()` takes no
`workspace_root`, so these tests monkeypatch the module-level
`DEFAULT_WORKSPACE_ROOT`. Fake RECORD/STT/TTS are tiny shell scripts —
no real mic, no Piper/whisper binary required anywhere in this file.
"""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import jarvis.workspace.workspace_manager as workspace_manager_module

REPO_ROOT = Path(__file__).resolve().parents[1]
RECORD_WRAPPER = REPO_ROOT / "scripts" / "voice" / "record_turn.sh"


def _isolate_workspace(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(workspace_manager_module, "DEFAULT_WORKSPACE_ROOT", tmp_path / "workspace")


def _write_script(tmp_path: Path, name: str, body: str) -> Path:
    script = tmp_path / name
    script.write_text(body, encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script


def _write_fake_record_script(tmp_path: Path, *, marker: Path | None = None) -> Path:
    """Writes a placeholder wav to the `{output}` path (argv[1]).
    Optionally also touches `marker` so a test can prove this script
    was (or was not) invoked."""
    touch_line = f'touch "{marker}"\n' if marker is not None else ""
    return _write_script(
        tmp_path,
        "fake_record.sh",
        f'#!/bin/sh\n{touch_line}printf \'RIFF....WAVEfake\' > "$1"\n',
    )


def _write_fake_stt_script(tmp_path: Path, transcript: str, *, name: str = "fake_stt.sh") -> Path:
    return _write_script(tmp_path, name, f"#!/bin/sh\nprintf '{transcript}\\n'\n")


def _write_failing_script(tmp_path: Path, name: str, message: str = "boom") -> Path:
    return _write_script(tmp_path, name, f"#!/bin/sh\necho '{message}' >&2\nexit 1\n")


def _feed_lines(monkeypatch, lines: list[str]):
    queue = list(lines)

    def fake_input(prompt: str = "") -> str:
        if not queue:
            raise EOFError
        return queue.pop(0)

    monkeypatch.setattr("builtins.input", fake_input)


def test_t1_hablar_records_transcribes_and_falls_through_same_chat(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    record_script = _write_fake_record_script(tmp_path)
    stt_script = _write_fake_stt_script(tmp_path, "armar")
    monkeypatch.setenv("JARVIS_RECORD_CMD", f"{record_script} {{output}}")
    monkeypatch.setenv("JARVIS_STT_CMD", f"{stt_script} {{audio}}")
    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)
    from jarvis.adapters.cli.main import run_chat

    _feed_lines(monkeypatch, ["hablar", "exit"])
    run_chat(speak_tts=True)

    out = capsys.readouterr().out
    assert out.count("Grabando") == 1
    assert "Grabando 7 s" in out
    assert "User > [voz] armar" in out
    assert "vehicle_arm_policy" in out or "ARMADA" in out
    # "hablar" itself never reached the chat brain as a phrase to interpret.
    assert "No he entendido" not in out


def test_t2_typed_skill_never_triggers_record(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    marker = tmp_path / "record_was_called.marker"
    record_script = _write_fake_record_script(tmp_path, marker=marker)
    monkeypatch.setenv("JARVIS_RECORD_CMD", f"{record_script} {{output}}")
    monkeypatch.delenv("JARVIS_STT_CMD", raising=False)
    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)
    from jarvis.adapters.cli.main import run_chat

    _feed_lines(monkeypatch, ["armar", "exit"])
    run_chat(speak_tts=True)

    out = capsys.readouterr().out
    assert "vehicle_arm_policy" in out
    assert "Grabando" not in out
    assert not marker.exists(), "typing a Skill phrase must never invoke the record seam"


def test_t3_bare_chat_hablar_never_records(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    marker = tmp_path / "record_was_called2.marker"
    record_script = _write_fake_record_script(tmp_path, marker=marker)
    monkeypatch.setenv("JARVIS_RECORD_CMD", f"{record_script} {{output}}")
    from jarvis.adapters.cli.main import run_chat

    _feed_lines(monkeypatch, ["hablar", "exit"])
    run_chat()  # bare --chat, speak_tts=False default

    out = capsys.readouterr().out
    assert "Grabando" not in out
    assert not marker.exists(), "bare --chat must never invoke the record seam on 'hablar'"


def test_t4_missing_record_config_is_honest_and_loop_survives(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    monkeypatch.delenv("JARVIS_RECORD_CMD", raising=False)
    monkeypatch.delenv("JARVIS_STT_CMD", raising=False)
    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)
    from jarvis.adapters.cli.main import run_chat

    _feed_lines(monkeypatch, ["hablar", "armar", "exit"])
    run_chat(speak_tts=True)

    out = capsys.readouterr().out
    assert "Grabación no disponible" in out
    assert "vehicle_arm_policy" in out  # loop survived to the next typed turn
    assert "Sesión cerrada" in out


def test_t4b_record_ok_but_missing_stt_config_is_honest(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    record_script = _write_fake_record_script(tmp_path)
    monkeypatch.setenv("JARVIS_RECORD_CMD", f"{record_script} {{output}}")
    monkeypatch.delenv("JARVIS_STT_CMD", raising=False)
    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)
    from jarvis.adapters.cli.main import run_chat

    _feed_lines(monkeypatch, ["hablar", "exit"])
    run_chat(speak_tts=True)

    out = capsys.readouterr().out
    assert "STT no disponible" in out
    assert "Sesión cerrada" in out


def test_t5_record_process_failure_is_honest_and_loop_survives(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    failing_record = _write_failing_script(tmp_path, "failing_record.sh")
    monkeypatch.setenv("JARVIS_RECORD_CMD", f"{failing_record} {{output}}")
    monkeypatch.delenv("JARVIS_STT_CMD", raising=False)
    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)
    from jarvis.adapters.cli.main import run_chat

    _feed_lines(monkeypatch, ["hablar", "armar", "exit"])
    run_chat(speak_tts=True)

    out = capsys.readouterr().out
    assert "Grabación no disponible" in out
    assert "vehicle_arm_policy" in out


def test_t5b_empty_transcript_is_honest_and_loop_survives(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    record_script = _write_fake_record_script(tmp_path)
    empty_stt = _write_script(tmp_path, "empty_stt.sh", "#!/bin/sh\nprintf ''\n")
    monkeypatch.setenv("JARVIS_RECORD_CMD", f"{record_script} {{output}}")
    monkeypatch.setenv("JARVIS_STT_CMD", f"{empty_stt} {{audio}}")
    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)
    from jarvis.adapters.cli.main import run_chat

    _feed_lines(monkeypatch, ["hablar", "armar", "exit"])
    run_chat(speak_tts=True)

    out = capsys.readouterr().out
    assert "STT no disponible" in out
    assert "vehicle_arm_policy" in out


def test_t5c_transcript_literally_hablar_does_not_re_record(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    marker = tmp_path / "record_call_count"
    record_script = _write_script(
        tmp_path,
        "counting_record.sh",
        f'#!/bin/sh\nprintf "x" >> "{marker}"\nprintf \'RIFF....WAVEfake\' > "$1"\n',
    )
    stt_script = _write_fake_stt_script(tmp_path, "hablar")
    monkeypatch.setenv("JARVIS_RECORD_CMD", f"{record_script} {{output}}")
    monkeypatch.setenv("JARVIS_STT_CMD", f"{stt_script} {{audio}}")
    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)
    from jarvis.adapters.cli.main import run_chat

    _feed_lines(monkeypatch, ["hablar", "exit"])
    run_chat(speak_tts=True)

    out = capsys.readouterr().out
    assert out.count("Grabando") == 1, "a transcript that says 'hablar' must not trigger a second recording"
    assert "User > [voz] hablar" in out
    assert marker.read_text(encoding="utf-8") == "x"


def test_t6_run_chat_source_guard_and_voice_interactive_unaffected():
    import inspect

    from jarvis.adapters.cli.main import run_chat, run_voice_interactive

    source = inspect.getsource(run_chat)
    for forbidden in ("speak_egress", "JARVIS_TTS_CMD", "_voice_speak_fn", "TtsError"):
        assert forbidden not in source, f"run_chat must never reference {forbidden!r}"
    assert callable(run_voice_interactive)


def test_t7_no_tip_pins_no_speech_deps_esc_fence_green_guide_map_and_wrapper():
    from tests.test_fase_c_esc_pwm_stub_rung_b1 import _esc_fence_violations
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()

    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
    for forbidden in (
        "piper", "whisper", "vosk", "speechrecognition", "pyttsx", "elevenlabs", "pyaudio",
        "ffmpeg-python", "pyaudio", "sounddevice",
    ):
        assert forbidden not in pyproject_text, f"{forbidden!r} leaked into pyproject deps"

    for rel_path in (
        "src/jarvis/core/orchestrator.py",
        "src/jarvis/adapters/voice/fixture_loop.py",
        "src/jarvis/adapters/voice/external_stt.py",
        "src/jarvis/adapters/voice/external_tts.py",
        "src/jarvis/adapters/voice/external_record.py",
        "src/jarvis/adapters/voice/spoken_continuity.py",
        "src/jarvis/adapters/cli/main.py",
    ):
        source = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        violations = _esc_fence_violations(source)
        assert not violations, f"{rel_path} forbidden ESC coupling: {violations}"

    guide = (REPO_ROOT / "docs" / "USER_GUIDE_VOICE.md").read_text(encoding="utf-8")
    assert "hablar" in guide
    assert "habla" in guide

    living_map = (REPO_ROOT / ".jes" / "artifacts" / "engineer_note_chat_spoken_continuity_map.md").read_text(
        encoding="utf-8"
    )
    assert "Grabando" in living_map
    assert "[voz]" in living_map

    assert RECORD_WRAPPER.exists() and RECORD_WRAPPER.stat().st_size > 0
    assert (RECORD_WRAPPER.stat().st_mode & stat.S_IXUSR), "record_turn.sh must be executable"

    # Honesty path: with no recorder on PATH at all, --check must fail loudly,
    # regardless of whether this host happens to have ffmpeg/arecord installed.
    stripped_env = {"PATH": "/nonexistent-ptt-test-path"}
    done = subprocess.run(
        [str(RECORD_WRAPPER), "--check"],
        capture_output=True,
        text=True,
        env=stripped_env,
    )
    assert done.returncode != 0
    assert "no recorder found" in done.stderr
