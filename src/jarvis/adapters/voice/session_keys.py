"""Skill-first phase C — V12 (`B1-assistant-voice-session-key`, T58).

In-session cancel keys for `--voice-only`: **Esc** or **Space** while
Jarvis is speaking, and **Esc** while it is settling/recording, act
exactly like pressing Ctrl-C at that moment. No global OS hotkey, no
accessibility API, no dependency — only keys typed into the terminal
that is running the session.

How: `SessionKeyWatcher.watching(keys)` wraps one blocking window (a
`speak_egress` call, or settle + record + STT). For that window it puts
the terminal in cbreak mode (single keys, no echo; Ctrl-C still works)
and runs a short-lived thread that `select`s on stdin. A matching key
triggers the configured interrupt, which for a real terminal is
`os.killpg(os.getpgrp(), SIGINT)` — the very signal the terminal sends
on Ctrl-C to the foreground group. Every existing Ctrl-C path is then
reused unchanged: during TTS, `speak_egress` stops the TTS process group
and raises `TtsCancelled` (T56); during settle/record, the mic reader's
take-cancel runs and `record_turn.sh`'s INT trap stops ffmpeg (T53/T54/
T57). Outside those windows nothing reads keys — in particular not while
the brain/LLM is thinking, and never in `--chat`.

The watcher thread blocks SIGINT for itself, so the kernel delivers the
signal to the main thread, where Python raises `KeyboardInterrupt` and a
blocked `select`/`wait` is interrupted. `for_terminal()` only returns a
watcher when stdin is a TTY **and** this process is the terminal's
foreground process group — exactly the group a real Ctrl-C would hit;
otherwise there are no keys (piped stdin, background job, CI).
"""

from __future__ import annotations

import os
import select
import signal
import sys
import threading
from contextlib import contextmanager
from typing import Callable, Iterator

ESC = b"\x1b"
SPACE = b" "
# While Jarvis speaks: Esc or Space ("cállate y escúchame").
SPEAK_CANCEL_KEYS: frozenset[bytes] = frozenset({ESC, SPACE})
# While settling/recording/transcribing: Esc only — a bumped space bar
# must never throw away a take.
TAKE_CANCEL_KEYS: frozenset[bytes] = frozenset({ESC})

_POLL_SECONDS = 0.05


class KeyWindow:
    """Handle yielded by `SessionKeyWatcher.watching`; `fired` is True
    once a cancel key triggered the interrupt in that window."""

    def __init__(self) -> None:
        self.fired = False


class SessionKeyWatcher:
    def __init__(
        self,
        fd: int,
        interrupt: Callable[[], None],
        *,
        set_cbreak: bool = True,
    ) -> None:
        self._fd = fd
        self._interrupt = interrupt
        self._set_cbreak = set_cbreak

    @classmethod
    def for_terminal(cls) -> SessionKeyWatcher | None:
        """A watcher on the real terminal, or `None` when stdin is not an
        interactive terminal this process owns (no keys then)."""
        try:
            fd = sys.stdin.fileno()
            if not os.isatty(fd) or os.tcgetpgrp(fd) != os.getpgrp():
                return None
        except (AttributeError, OSError, ValueError):
            return None
        return cls(fd, lambda: os.killpg(os.getpgrp(), signal.SIGINT), set_cbreak=True)

    @contextmanager
    def watching(self, keys: frozenset[bytes]) -> Iterator[KeyWindow]:
        window = KeyWindow()
        stop = threading.Event()
        saved_mode = self._enter_cbreak()

        def watch() -> None:
            signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
            while not stop.is_set():
                try:
                    ready, _, _ = select.select([self._fd], [], [], _POLL_SECONDS)
                except (OSError, ValueError):
                    return
                if not ready:
                    continue
                try:
                    data = os.read(self._fd, 64)
                except OSError:
                    return
                if not data:
                    return
                if any(key in data for key in keys) and not stop.is_set():
                    window.fired = True
                    self._interrupt()
                    return

        thread = threading.Thread(target=watch, name="jarvis-session-keys", daemon=True)
        thread.start()
        try:
            yield window
        finally:
            stop.set()
            try:
                thread.join()
            finally:
                # Even if the SIGINT this window triggered surfaces during
                # the join, the terminal goes back to its saved mode.
                self._restore(saved_mode)

    def _enter_cbreak(self):
        if not self._set_cbreak:
            return None
        import termios
        import tty

        try:
            saved = termios.tcgetattr(self._fd)
            tty.setcbreak(self._fd, termios.TCSANOW)
        except termios.error:
            return None
        return saved

    def _restore(self, saved_mode) -> None:
        if saved_mode is None:
            return
        import termios

        try:
            termios.tcsetattr(self._fd, termios.TCSADRAIN, saved_mode)
        except termios.error:
            pass
