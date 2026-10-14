"""Tests T1-T6 for `B1-assistant-voice-session-key` (T58 / V12).

T56 made Ctrl-C cancel speech honestly. T58 adds in-session keys for
`--voice-only`: **Esc** or **Space** while Jarvis speaks, **Esc** while
it settles/records — each acting exactly like Ctrl-C at that moment. A
`SessionKeyWatcher` (cbreak terminal + short-lived `select` thread)
watches stdin only during those windows and, on a matching key, sends
the same SIGINT a terminal Ctrl-C sends to the foreground group, so the
T56 TTS-group stop + `TtsCancelled` and the T53/T57 take-cancel paths
are reused unchanged. No global hotkey, no new dependency, nothing
during the brain/LLM wait, nothing in `--chat`.

T1/T2 run the production `SessionKeyWatcher.for_terminal()` path inside
a real pseudo-terminal (`pty.fork`): the child owns the terminal and is
its foreground group, the test types Esc/Space into the master side.
T3/T4 inject a pipe-backed watcher (interrupt = SIGINT to this process)
into the real `--voice-only` loop with the T53 fakes. No speaker/mic.
"""

from __future__ import annotations

import os
import pty
import select
import signal
import sys
import textwrap
import time
import typing
from pathlib import Path

import pytest

import jarvis.adapters.cli.main as main_module
import jarvis.workspace.workspace_manager as workspace_manager_module
from jarvis.adapters.voice.session_keys import (
    SPEAK_CANCEL_KEYS,
    TAKE_CANCEL_KEYS,
    SessionKeyWatcher,
)
from jarvis.capabilities.safety import AuthoritySource
from tests.test_assistant_voice_cancel_mid_tts_b1 import _blocking_tts, _gone, _pids

REPO_ROOT = Path(__file__).resolve().parents[1]
GUIDE = REPO_ROOT / "docs" / "USER_GUIDE_VOICE.md"


@pytest.fixture(autouse=True)
def _default_sigint_handler():
    previous = signal.signal(signal.SIGINT, signal.default_int_handler)
    yield
    signal.signal(signal.SIGINT, previous)


_PTY_CHILD = textwrap.dedent(
    """
    import termios
    from jarvis.adapters.voice import TtsCancelled, TtsProcessError, speak_egress
    from jarvis.adapters.voice.session_keys import SPEAK_CANCEL_KEYS, SessionKeyWatcher

    watcher = SessionKeyWatcher.for_terminal()
    print("WATCHER", watcher is not None, flush=True)
    window = None
    try:
        with watcher.watching(SPEAK_CANCEL_KEYS) as window:
            speak_egress("Una respuesta larga.", command_template={tts!r})
        print("RESULT finished", flush=True)
    except TtsCancelled:
        print("RESULT cancelled", window.fired, flush=True)
    except TtsProcessError as error:
        print("RESULT process-error", error, flush=True)
    print("ICANON", bool(termios.tcgetattr(0)[3] & termios.ICANON), flush=True)
    """
)


def _run_in_pty(tmp_path: Path, key: bytes) -> str:
    script = _blocking_tts(tmp_path)
    pid, master = pty.fork()
    if pid == 0:  # child: owns the pty, is its foreground process group
        os.execve(
            sys.executable,
            [sys.executable, "-c", _PTY_CHILD.format(tts=str(script))],
            dict(os.environ),
        )
    output = b""
    deadline = time.monotonic() + 20
    sent = False
    try:
        while time.monotonic() < deadline:
            if not sent and (tmp_path / "tts_started").exists():
                time.sleep(0.2)
                os.write(master, key)
                sent = True
            ready, _, _ = select.select([master], [], [], 0.05)
            if ready:
                try:
                    chunk = os.read(master, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                output += chunk
                if b"ICANON" in output and output.rstrip().endswith((b"True", b"False")):
                    break
    finally:
        os.waitpid(pid, 0)
        os.close(master)
    return output.decode("utf-8", "replace")


@pytest.mark.parametrize("key,label", [(b"\x1b", "Esc"), (b" ", "Space")])
def test_t1_t2_real_terminal_key_mid_speech_cancels_like_ctrl_c(tmp_path, key, label):
    output = _run_in_pty(tmp_path, key)
    assert "WATCHER True" in output, f"{label}: no watcher on a real terminal: {output!r}"
    assert "RESULT cancelled True" in output, f"{label}: {output!r}"
    assert "process-error" not in output
    assert "ICANON True" in output, f"{label}: terminal not restored to canonical mode: {output!r}"
    for pid in _pids(tmp_path):
        assert _gone(pid), f"{label}: pid {pid} still running after cancel"


def test_t1b_watcher_absent_without_owned_terminal():
    # pytest's stdin is not an interactive terminal owned by this process.
    assert SessionKeyWatcher.for_terminal() is None
    assert SPEAK_CANCEL_KEYS == {b"\x1b", b" "}
    assert TAKE_CANCEL_KEYS == {b"\x1b"}


def _pipe_watcher(monkeypatch, *, refill: int = 0):
    """Pipe-backed watcher injected as the session's terminal watcher.
    `refill` extra Esc keys are queued, one after each firing, so the
    next key window sees one too (deterministic multi-window tests)."""
    read_fd, write_fd = os.pipe()
    remaining = {"n": refill}

    def interrupt():
        if remaining["n"] > 0:
            remaining["n"] -= 1
            os.write(write_fd, b"\x1b")
        os.kill(os.getpid(), signal.SIGINT)

    watcher = SessionKeyWatcher(read_fd, interrupt, set_cbreak=False)
    monkeypatch.setattr(SessionKeyWatcher, "for_terminal", classmethod(lambda cls: watcher))
    return watcher, write_fd


def _voice_only_setup(tmp_path: Path, monkeypatch, transcripts, *, tts: bool = True):
    from tests.test_assistant_voice_only_loop_b1 import _FakeVoice

    monkeypatch.setattr(workspace_manager_module, "DEFAULT_WORKSPACE_ROOT", tmp_path / "workspace")

    def no_keyboard(prompt: str = "") -> str:
        raise AssertionError("voice-only must not read the keyboard without projects")

    monkeypatch.setattr("builtins.input", no_keyboard)
    return _FakeVoice(tmp_path, monkeypatch, transcripts, tts=tts)


def test_t3_voice_only_esc_mid_speech_habla_cancelada_then_settle_and_mic(tmp_path, monkeypatch, capsys):
    fake = _voice_only_setup(tmp_path, monkeypatch, ["armar", "salir"])
    monkeypatch.setenv("JARVIS_TTS_CMD", str(_blocking_tts(tmp_path, block_once=True)))
    monkeypatch.setenv("JARVIS_VOICE_SETTLE_SECONDS", "0.1")
    _, write_fd = _pipe_watcher(monkeypatch)

    import threading

    def press_esc_when_speaking():
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and not (tmp_path / "tts_started").exists():
            time.sleep(0.02)
        time.sleep(0.2)
        os.write(write_fd, b"\x1b")

    threading.Thread(target=press_esc_when_speaking, daemon=True).start()
    main_module.run_voice_only()

    out = capsys.readouterr().out
    assert "Esc o Espacio cortan el habla" in out
    assert "Jarvis > Habla cancelada." in out
    assert out.count("Sesión cerrada") == 1
    assert out.index("Habla cancelada") < out.index("User > [voz] salir") < out.index("Sesión cerrada")
    events = [line.split()[0] for line in fake.event_lines()]
    assert "REC" in events[events.index("TTS") + 1 :], "mic must reopen after the Esc cancel"
    for pid in _pids(tmp_path):
        assert _gone(pid)


def test_t4_esc_during_settle_cancels_take_twice_ends_session(tmp_path, monkeypatch, capsys):
    # One Esc during the settle → take cancelled, session continues.
    fake = _voice_only_setup(tmp_path, monkeypatch, ["armar", "salir"], tts=False)
    monkeypatch.setenv("JARVIS_VOICE_SETTLE_SECONDS", "1.0")
    _, write_fd = _pipe_watcher(monkeypatch)
    os.write(write_fd, b"\x1b")
    main_module.run_voice_only()
    out = capsys.readouterr().out
    assert "Grabación cancelada" in out
    assert "Habla cancelada" not in out
    assert "User > [voz] armar" in out and out.count("Sesión cerrada") == 1
    assert fake.record_count() == 2, "cancelled take never reached the recorder"

    # Space is ignored while settling/recording (never throws a take away).
    sub = tmp_path / "space"
    sub.mkdir()
    _voice_only_setup(sub, monkeypatch, ["salir"], tts=False)
    monkeypatch.setenv("JARVIS_VOICE_SETTLE_SECONDS", "0.3")
    _, write_fd = _pipe_watcher(monkeypatch)
    os.write(write_fd, b" ")
    main_module.run_voice_only()
    out = capsys.readouterr().out
    assert "Grabación cancelada" not in out and "User > [voz] salir" in out

    # Esc in two consecutive takes → session ends (same rule as Ctrl-C).
    sub = tmp_path / "double"
    sub.mkdir()
    fake = _voice_only_setup(sub, monkeypatch, ["armar"], tts=False)
    monkeypatch.setenv("JARVIS_VOICE_SETTLE_SECONDS", "1.0")
    _, write_fd = _pipe_watcher(monkeypatch, refill=1)
    os.write(write_fd, b"\x1b")
    main_module.run_voice_only()
    out = capsys.readouterr().out
    assert out.count("Grabación cancelada") == 1
    assert "Sesión cerrada" in out and "[voz]" not in out
    assert fake.record_count() == 0


def test_t5_bare_chat_never_installs_watcher_and_ctrl_c_mid_tts_still_works(tmp_path, monkeypatch, capsys):
    def no_watcher(cls):
        raise AssertionError("--chat must never install the session key watcher")

    monkeypatch.setattr(SessionKeyWatcher, "for_terminal", classmethod(no_watcher))
    import jarvis.adapters.voice as voice_module

    def forbidden(*_args, **_kwargs):
        raise AssertionError("bare --chat must never record or speak")

    for name in ("record_audio_file", "transcribe_audio_file", "speak_egress"):
        monkeypatch.setattr(voice_module, name, forbidden)
    monkeypatch.setattr(workspace_manager_module, "DEFAULT_WORKSPACE_ROOT", tmp_path / "chat_ws")
    queue = ["armar", "exit"]
    monkeypatch.setattr("builtins.input", lambda prompt="": queue.pop(0) if queue else "exit")
    main_module.run_chat()
    assert "vehicle_arm_policy" in capsys.readouterr().out
    monkeypatch.undo()

    # Regression: no terminal watcher (None) → plain Ctrl-C mid-TTS still cancels (T56).
    from tests.test_assistant_voice_cancel_mid_tts_b1 import _ctrl_c_when

    sub = tmp_path / "ctrlc"
    sub.mkdir()
    _voice_only_setup(sub, monkeypatch, ["armar", "salir"])
    monkeypatch.setenv("JARVIS_TTS_CMD", str(_blocking_tts(sub, block_once=True)))
    monkeypatch.setattr(SessionKeyWatcher, "for_terminal", classmethod(lambda cls: None))
    _ctrl_c_when(sub / "tts_started")
    main_module.run_voice_only()
    out = capsys.readouterr().out
    assert "Jarvis > Habla cancelada." in out and out.count("Sesión cerrada") == 1
    assert "Esc o Espacio" not in out, "no key banner without a key watcher"


def test_t6_guide_deps_tip_pin_esc_fences():
    guide = GUIDE.read_text(encoding="utf-8")
    assert "Esc" in guide and "Espacio" in guide

    from tests.test_fase_c_esc_pwm_stub_rung_b1 import _esc_fence_violations
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
    for forbidden in (
        "piper", "whisper", "vosk", "speechrecognition", "pyttsx", "elevenlabs",
        "pyaudio", "sounddevice", "pynput", "keyboard", "readchar", "getch", "pyobjc",
    ):
        assert forbidden not in pyproject_text, f"{forbidden!r} leaked into pyproject deps"
    for rel_path in (
        "src/jarvis/adapters/voice/session_keys.py",
        "src/jarvis/adapters/voice/external_tts.py",
        "src/jarvis/adapters/cli/main.py",
    ):
        source = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        assert not _esc_fence_violations(source), f"{rel_path} forbidden ESC coupling"
    assert "voice" not in typing.get_args(AuthoritySource)

    # No global hotkey machinery: stdin/termios only.
    source = (REPO_ROOT / "src/jarvis/adapters/voice/session_keys.py").read_text(encoding="utf-8")
    for forbidden in ("Quartz", "AppKit", "CGEvent", "IOKit", "evdev", "/dev/input", "LaunchAgent"):
        assert forbidden not in source
