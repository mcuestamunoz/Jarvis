"""Tests T1-T6 for `B1-assistant-voice-cancel-mid-tts` (T56 / V12).

`speak_egress` used a blocking `subprocess.run`: Ctrl-C while Jarvis was
talking neither reliably stopped the external player nor left the
`--voice-only` session alive. T56 starts the TTS command in its own
session (process group), stops that whole group on `KeyboardInterrupt`
(SIGTERM, SIGKILL after a grace), and raises `TtsCancelled` — a
`KeyboardInterrupt` subclass, deliberately not a `TtsError`.
`--voice-only` catches it, prints `Jarvis > Habla cancelada.` (never
spoken) and goes straight back to the mic. Mid-record Ctrl-C and the
double-Ctrl-C exit (T53) are unchanged.

Ctrl-C is simulated with a real SIGINT to this test process, sent from
a watcher thread once the fake TTS has signalled that it started — the
same signal path a terminal Ctrl-C takes. Fake TTS scripts spawn a
child (standing in for `afplay`) and record both pids so the tests can
prove nothing is left talking. No speaker, no mic.
"""

from __future__ import annotations

import os
import signal
import stat
import threading
import time
import typing
from pathlib import Path

import pytest

import jarvis.workspace.workspace_manager as workspace_manager_module
from jarvis.adapters.voice import (
    TtsCancelled,
    TtsConfigError,
    TtsError,
    TtsProcessError,
    speak_egress,
)
from jarvis.capabilities.safety import AuthoritySource

REPO_ROOT = Path(__file__).resolve().parents[1]
GUIDE = REPO_ROOT / "docs" / "USER_GUIDE_VOICE.md"
LIVING_MAP = REPO_ROOT / ".jes" / "artifacts" / "engineer_note_chat_spoken_continuity_map.md"


@pytest.fixture(autouse=True)
def _default_sigint_handler():
    previous = signal.signal(signal.SIGINT, signal.default_int_handler)
    yield
    signal.signal(signal.SIGINT, previous)


def _write_script(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


def _blocking_tts(tmp_path: Path, *, ignore_term: bool = False, block_once: bool = False) -> Path:
    """Fake TTS: records its pid and a child "player" pid, then blocks on
    the player. `ignore_term` makes both ignore SIGTERM (forces the
    SIGKILL escalation). `block_once` blocks only on the first call —
    later calls (e.g. the goodbye) return immediately."""
    trap = "trap '' TERM\n" if ignore_term else ""
    once = (
        f'if [ -e "{tmp_path}/tts_started" ]; then cat > /dev/null; '
        f'echo TTS >> "{tmp_path}/events.log"; exit 0; fi\n'
        if block_once
        else ""
    )
    return _write_script(
        tmp_path / "blocking_tts.sh",
        "#!/bin/sh\n"
        f"{trap}{once}"
        f'echo TTS >> "{tmp_path}/events.log"\n'
        "cat > /dev/null\n"
        f'echo $$ > "{tmp_path}/tts.pid"\n'
        "sleep 30 &\n"
        f'echo $! > "{tmp_path}/player.pid"\n'
        f'touch "{tmp_path}/tts_started"\n'
        "wait\n",
    )


def _ctrl_c_when(marker: Path, timeout: float = 10.0) -> threading.Thread:
    def watch():
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if marker.exists():
                time.sleep(0.1)
                os.kill(os.getpid(), signal.SIGINT)
                return
            time.sleep(0.02)

    thread = threading.Thread(target=watch, daemon=True)
    thread.start()
    return thread


def _gone(pid: int, timeout: float = 3.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.05)
    return False


def _pids(tmp_path: Path) -> list[int]:
    return [int((tmp_path / name).read_text().strip()) for name in ("tts.pid", "player.pid")]


@pytest.mark.parametrize("ignore_term", [False, True], ids=["sigterm", "sigkill-escalation"])
def test_t1_ctrl_c_mid_speech_stops_tts_group_and_raises_cancelled(tmp_path, ignore_term):
    script = _blocking_tts(tmp_path, ignore_term=ignore_term)
    _ctrl_c_when(tmp_path / "tts_started")

    start = time.monotonic()
    with pytest.raises(TtsCancelled) as raised:
        speak_egress("Una respuesta larga que Jarvis está diciendo.", command_template=str(script))
    elapsed = time.monotonic() - start

    assert isinstance(raised.value, KeyboardInterrupt)
    assert not isinstance(raised.value, TtsError), "a cancel is not a TTS failure"
    assert not isinstance(raised.value, TtsProcessError)
    assert elapsed < 8, f"cancel must not wait for the 30 s 'player' ({elapsed:.1f}s)"
    for pid in _pids(tmp_path):
        assert _gone(pid), f"pid {pid} still running after cancel"


def _isolate_workspace(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(workspace_manager_module, "DEFAULT_WORKSPACE_ROOT", tmp_path / "workspace")


def _forbid_keyboard(monkeypatch) -> None:
    def no_keyboard(prompt: str = "") -> str:
        raise AssertionError("voice-only must not read the keyboard without projects")

    monkeypatch.setattr("builtins.input", no_keyboard)


def test_t2_voice_only_cancel_prints_habla_cancelada_and_reopens_mic(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    _forbid_keyboard(monkeypatch)
    from jarvis.adapters.cli.main import run_voice_only
    from tests.test_assistant_voice_only_loop_b1 import _FakeVoice

    fake = _FakeVoice(tmp_path, monkeypatch, ["armar", "salir"])
    monkeypatch.setenv("JARVIS_TTS_CMD", str(_blocking_tts(tmp_path, block_once=True)))
    _ctrl_c_when(tmp_path / "tts_started")

    run_voice_only()

    out = capsys.readouterr().out
    assert "Jarvis > Habla cancelada." in out
    assert out.count("Sesión cerrada") == 1, "a mid-speech Ctrl-C must not end the session"
    assert out.index("Habla cancelada") < out.index("User > [voz] salir") < out.index("Sesión cerrada")
    assert "TTS no disponible" not in out

    events = [line.split()[0] for line in fake.event_lines()]
    first_tts = events.index("TTS")
    assert "REC" in events[first_tts + 1 :], "the mic must reopen after the cancelled speech"
    for pid in _pids(tmp_path):
        assert _gone(pid), f"pid {pid} still running after cancel"


def test_t3_mid_record_ctrl_c_and_double_exit_unchanged(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    _forbid_keyboard(monkeypatch)
    import jarvis.adapters.voice as voice_module
    from jarvis.adapters.cli.main import run_voice_only
    from tests.test_assistant_voice_only_loop_b1 import _FakeVoice

    _FakeVoice(tmp_path, monkeypatch, ["armar", "salir"], tts=False)
    real_record = voice_module.record_audio_file
    calls = {"n": 0}

    def cancel_first(output_path, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise KeyboardInterrupt
        return real_record(output_path, **kwargs)

    monkeypatch.setattr(voice_module, "record_audio_file", cancel_first)
    run_voice_only()
    out = capsys.readouterr().out
    assert "Grabación cancelada" in out
    assert "Habla cancelada" not in out
    assert "User > [voz] armar" in out and out.count("Sesión cerrada") == 1

    def always_interrupt(output_path, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(voice_module, "record_audio_file", always_interrupt)
    run_voice_only()
    out = capsys.readouterr().out
    assert out.count("Grabación cancelada") == 1
    assert "Sesión cerrada" in out


def test_t4_bare_chat_never_speaks_or_records(tmp_path, monkeypatch, capsys):
    _isolate_workspace(monkeypatch, tmp_path)
    import jarvis.adapters.voice as voice_module
    from jarvis.adapters.cli.main import run_chat

    def forbidden(*_args, **_kwargs):
        raise AssertionError("bare --chat must never record or speak")

    for name in ("record_audio_file", "transcribe_audio_file", "speak_egress"):
        monkeypatch.setattr(voice_module, name, forbidden)
    queue = ["armar", "exit"]
    monkeypatch.setattr("builtins.input", lambda prompt="": queue.pop(0) if queue else "exit")
    run_chat()
    out = capsys.readouterr().out
    assert "vehicle_arm_policy" in out
    assert "Habla cancelada" not in out and "Grabando" not in out


def test_t5_empty_sanitize_no_invoke_and_missing_cmd_still_honest(tmp_path, monkeypatch):
    marker = tmp_path / "invoked"
    script = _write_script(tmp_path / "marker_tts.sh", f'#!/bin/sh\ncat > /dev/null\ntouch "{marker}"\n')

    speak_egress("────────────", command_template=str(script))
    assert not marker.exists(), "decoration-only text must not invoke TTS"
    monkeypatch.delenv("JARVIS_TTS_CMD", raising=False)
    speak_egress("────────────")  # nothing to say → no config error either

    with pytest.raises(TtsConfigError):
        speak_egress("Hola.")

    speak_egress("Hola.", command_template=str(script))
    assert marker.exists()

    failing = _write_script(tmp_path / "failing_tts.sh", "#!/bin/sh\ncat > /dev/null\necho boom >&2\nexit 3\n")
    with pytest.raises(TtsProcessError, match="boom"):
        speak_egress("Hola.", command_template=str(failing))


def test_t6_guide_map_deps_tip_pin_esc():
    guide = GUIDE.read_text(encoding="utf-8")
    assert "Habla cancelada" in guide
    assert "Grabación cancelada" in guide

    living_map = LIVING_MAP.read_text(encoding="utf-8")
    assert "Habla cancelada" in living_map
    row = next(line for line in living_map.splitlines() if "Habla cancelada" in line and line.startswith("|"))
    assert "screen-only" in row

    from tests.test_fase_c_esc_pwm_stub_rung_b1 import _esc_fence_violations
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
    for forbidden in (
        "piper", "whisper", "vosk", "speechrecognition", "pyttsx", "elevenlabs",
        "pyaudio", "sounddevice", "ffmpeg-python", "psutil", "pynput", "keyboard",
    ):
        assert forbidden not in pyproject_text, f"{forbidden!r} leaked into pyproject deps"
    for rel_path in ("src/jarvis/adapters/voice/external_tts.py", "src/jarvis/adapters/cli/main.py"):
        source = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        assert not _esc_fence_violations(source), f"{rel_path} forbidden ESC coupling"
    assert "voice" not in typing.get_args(AuthoritySource)
