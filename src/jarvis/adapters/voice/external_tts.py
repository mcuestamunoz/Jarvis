"""Skill-first phase C — V4 (`B1-assistant-voice-tts-external`, T38).

External TTS **process seam** — speaks (or writes audio for) a plain
`str` egress (the exact string `render_response` already produces) by
invoking an external command, never by synthesizing audio inside this
repo. No speech package is added to `pyproject.toml` and no TTS
happens in `capabilities/`, `intelligence/`, or `core/` — this
module's only job is: run a configured external command, feed it the
egress text on **stdin** (never argv — Skill messages have spaces/
quotes that would need unsafe shell-escaping as a command-line
argument), and treat exit `0` as success.

**Vendor choice is explicitly out of this Buy.** The product brief
(`.jes/artifacts/engineer_note_voice_tts_product_brief.md`) recommends
a free, local Piper voice as the default demo setup — grave, short, no
theater, **not** a Marvel clone — Spanish `es_ES-davefx-medium` by
default since T49 (`en_GB-alan-medium` stays supported as a documented
legacy value) — but installing Piper and pointing `JARVIS_TTS_CMD` at
a real binary is operator/demo setup, never hardcoded here; this
module never names Piper (or any other vendor) in code.

Honesty lock: missing/empty config, a non-zero exit, or the command
itself failing to run at all (missing binary) are each surfaced as the
same typed `TtsProcessError`/`TtsConfigError` — never a silent no-op
"success."

T50 (`B1-assistant-voice-speak-sanitize`): every call runs `text`
through `speak_sanitize.sanitize_for_speech` first — the single seam
every spoken egress passes through (`--chat --voice-speak` via
`_chat_speak_fn`, `--voice`/`--voice-fixture`/`--voice-audio` via
`_voice_speak_fn`), so wiring it here covers both without touching
`adapters/cli/main.py`. Layer 1 (everything `print`ed) is never
touched — only what travels on to the external TTS command. When the
sanitized text is empty, this function returns immediately without
invoking any external command — no filler speech, and no config/process
error either (there is nothing to speak, so a missing `JARVIS_TTS_CMD`
is not this call's problem).
"""

from __future__ import annotations

import os
import shlex
import subprocess
from typing import Callable

from jarvis.adapters.voice.speak_sanitize import sanitize_for_speech


class TtsError(Exception):
    """Base for every external-TTS seam failure — never a silent
    no-op success."""


class TtsConfigError(TtsError):
    """The TTS command template (env var or explicit argument) is
    missing or empty."""


class TtsProcessError(TtsError):
    """The external TTS command exited with a non-zero status, or
    could not be run at all (missing binary)."""


JARVIS_TTS_CMD_ENV = "JARVIS_TTS_CMD"


def speak_egress(
    text: str,
    *,
    command_template: str | None = None,
    env_var: str = JARVIS_TTS_CMD_ENV,
) -> None:
    """Invoke the external TTS command configured by `command_template`
    (or, if omitted, the `env_var` environment variable — default
    `JARVIS_TTS_CMD`), feeding it `text` on stdin. Raises
    `TtsConfigError` when no command is configured, `TtsProcessError`
    on a non-zero exit or when the command cannot be run at all
    (missing binary). `command_template` is split via `shlex.split`
    directly — unlike T37's `{audio}` placeholder, there is nothing to
    substitute here: the egress text always travels on stdin, never
    as an argv token.

    `text` is first run through `sanitize_for_speech` (T50) — decoration
    stripped, the locked glossary applied. If nothing is left to say,
    this returns immediately: no external command is invoked, no error
    is raised, no filler speech is produced."""
    sanitized = sanitize_for_speech(text)
    if not sanitized:
        return

    template = command_template if command_template is not None else os.environ.get(env_var)
    if not template:
        raise TtsConfigError(
            f"no external TTS command configured (set {env_var} or pass command_template)"
        )

    argv = shlex.split(template)
    try:
        completed = subprocess.run(argv, input=sanitized, capture_output=True, text=True)
    except OSError as error:
        raise TtsProcessError(f"could not run external TTS command {argv!r}: {error}") from error

    if completed.returncode != 0:
        raise TtsProcessError(
            f"external TTS command exited {completed.returncode}: {completed.stderr.strip()}"
        )


def make_speak_callable(
    *,
    command_template: str | None = None,
    env_var: str = JARVIS_TTS_CMD_ENV,
) -> Callable[[str], None]:
    """Build a `speak(text: str) -> None` callable with
    `command_template`/`env_var` pre-bound — the exact shape
    `jarvis.adapters.voice.run_voice(..., speak=...)` (T36) expects.
    `speak_egress` itself already matches that shape when called with
    its defaults (env-configured); this factory is for passing an
    explicit `command_template` without relying on the environment
    (e.g. tests, or a CLI flag with its own override)."""

    def speak(text: str) -> None:
        speak_egress(text, command_template=command_template, env_var=env_var)

    return speak
