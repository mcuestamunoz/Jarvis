"""T47 (`B1-assistant-chat-voice-ptt`) seam tests, re-homed by T53 (V9).

T47 added the external `JARVIS_RECORD_CMD` record seam
(`record_audio_file`, `scripts/voice/record_turn.sh`) and wired it into
`--chat --voice-speak` behind a typed `hablar`/`habla` trigger. T53
(`B1-assistant-voice-only-loop`) retired that hybrid product surface:
the record seam is now the default input of `--voice-only`
(`run_voice_only`), with no typed trigger, and bare `--chat` never
records. The tests that asserted the `hablar` intercept itself (T1, T2,
T4, T5c) are retired with it; the honesty guarantees of the seam
(missing STT config, record process failure, empty transcript) are kept
and now exercised through `run_voice_only`. The full voice-only loop
contract lives in `test_assistant_voice_only_loop_b1.py`.

Isolation: `run_chat`/`run_voice_only` take no `workspace_root`, so
these tests monkeypatch the module-level `DEFAULT_WORKSPACE_ROOT`. Fake
RECORD/STT are tiny shell scripts — no real mic, no whisper binary.
"""

from __future__ import annotations

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


def _no_keyboard(monkeypatch):
    def fail(prompt: str = "") -> str:
        raise AssertionError("voice-only must not read the keyboard without projects")

    monkeypatch.setattr("builtins.input", fail)


def _write_queue_stt_script(tmp_path: Path, transcripts: list[str]) -> Path:
    """Pops one queued transcript per call (a blank queued line is an
    empty transcript); falls back to `salir` once the queue is empty."""
    queue = tmp_path / "stt_queue.txt"
    queue.write_text("".join(f"{line}\n" for line in transcripts), encoding="utf-8")
    return _write_script(
        tmp_path,
        "queue_stt.sh",
        "#!/bin/sh\n"
        f'Q="{queue}"\n'
        'if [ ! -s "$Q" ]; then echo salir; exit 0; fi\n'
        'LINE=$(head -n 1 "$Q")\n'
        'tail -n +2 "$Q" > "$Q.tmp"; mv "$Q.tmp" "$Q"\n'
        'printf "%s" "$LINE"\n',
    )


def test_t4b_record_ok_but_missing_stt_config_is_honest(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    record_script = _write_fake_record_script(tmp_path)
    monkeypatch.setenv("JARVIS_RECORD_CMD", f"{record_script} {{output}}")
    monkeypatch.delenv("JARVIS_STT_CMD", raising=False)
    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)
    _no_keyboard(monkeypatch)
    from jarvis.adapters.cli.main import run_voice_only

    run_voice_only()

    out = capsys.readouterr().out
    assert "STT no disponible" in out
    assert "[voz]" not in out
    assert "Sesión cerrada" in out


def test_t5_record_process_failure_is_honest_and_mic_reopens(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    failed_once = tmp_path / "failed_once"
    record_script = _write_script(
        tmp_path,
        "fail_once_record.sh",
        "#!/bin/sh\n"
        f'if [ ! -e "{failed_once}" ]; then touch "{failed_once}"; echo boom >&2; exit 1; fi\n'
        "printf 'RIFF....WAVEfake' > \"$1\"\n",
    )
    stt_script = _write_queue_stt_script(tmp_path, ["armar", "salir"])
    monkeypatch.setenv("JARVIS_RECORD_CMD", f"{record_script} {{output}}")
    monkeypatch.setenv("JARVIS_STT_CMD", f"{stt_script} {{audio}}")
    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)
    _no_keyboard(monkeypatch)
    from jarvis.adapters.cli.main import run_voice_only

    run_voice_only()

    out = capsys.readouterr().out
    assert "Grabación no disponible" in out and "boom" in out
    assert "User > [voz] armar" in out
    assert "vehicle_arm_policy" in out  # mic reopened and the next turn ran
    assert "Sesión cerrada" in out


def test_t5b_empty_transcript_is_honest_and_mic_reopens(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    record_script = _write_fake_record_script(tmp_path)
    stt_script = _write_queue_stt_script(tmp_path, ["", "armar", "salir"])
    monkeypatch.setenv("JARVIS_RECORD_CMD", f"{record_script} {{output}}")
    monkeypatch.setenv("JARVIS_STT_CMD", f"{stt_script} {{audio}}")
    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)
    _no_keyboard(monkeypatch)
    from jarvis.adapters.cli.main import run_voice_only

    run_voice_only()

    out = capsys.readouterr().out
    assert "STT no disponible" in out
    assert "User > [voz] armar" in out
    assert "vehicle_arm_policy" in out


def test_t6_chat_has_no_ptt_intercept_and_interactive_voice_is_gone():
    import inspect

    import jarvis.adapters.cli.main as main_module

    for fn in (main_module.run_chat, main_module._run_chat_session):
        source = inspect.getsource(fn)
        assert "is_ptt_trigger" not in source
        for forbidden in ("speak_egress", "JARVIS_TTS_CMD", "_voice_speak_fn", "TtsError"):
            assert forbidden not in source, f"chat session must never reference {forbidden!r}"
    assert not hasattr(main_module, "run_voice_interactive")


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
    assert "JARVIS_RECORD_CMD" in guide
    assert "record_turn.sh" in guide
    assert "`hablar`" not in guide, "T53: the typed PTT trigger is no longer product UX"

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
