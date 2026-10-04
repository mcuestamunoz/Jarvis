"""Skill-first phase C — V3 (`B1-assistant-voice-stt-external`, T37).

External STT **process seam** — turns an audio file path into a
transcript `str` by invoking an external command, never by decoding
audio inside this repo. No speech package is added to `pyproject.toml`
and no audio decode happens in `capabilities/`, `intelligence/`, or
`core/` — this module's only job is: run a configured external
command, read its stdout, and hand the result to the exact same
`run_voice_turn` seam T36 already proved (`source=IntentSource.VOICE`).

**Vendor choice is explicitly out of this Buy.** `JARVIS_STT_CMD` (or
whatever the caller passes as `command_template`) names *some*
external command — real Whisper/Vosk/cloud-SDK integration is a
separate, later Engineer ★ that only has to point this same env var at
a real binary; this seam never hardcodes a vendor and never tip-pins a
speech dependency.

Honesty lock: missing/empty config, a non-zero exit, or an empty
transcript are each a distinct typed `SttError` subclass — never a
silent fallback to an invented Skill phrase.
"""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path


class SttError(Exception):
    """Base for every external-STT seam failure — never a silent
    fixture fallback or an invented transcript."""


class SttConfigError(SttError):
    """The STT command template (env var or explicit argument) is
    missing or empty."""


class SttProcessError(SttError):
    """The external STT command exited with a non-zero status."""


class SttEmptyTranscriptError(SttError):
    """The external STT command exited `0` but produced no non-blank
    stdout — never treated as a successful, empty transcript."""


JARVIS_STT_CMD_ENV = "JARVIS_STT_CMD"


def transcribe_audio_file(
    audio_path: str | Path,
    *,
    command_template: str | None = None,
    env_var: str = JARVIS_STT_CMD_ENV,
) -> str:
    """Invoke the external STT command configured by `command_template`
    (or, if omitted, the `env_var` environment variable — default
    `JARVIS_STT_CMD`) on `audio_path`, returning its stripped stdout as
    the transcript.

    `command_template` must contain the literal `{audio}` placeholder,
    substituted with `str(audio_path)` before the resulting string is
    split into argv via `shlex.split` (so a template like
    `"path/to/fake_stt.sh {audio}"` becomes a real argv list — no
    shell is spawned). Raises `SttConfigError` when no template is
    configured, `SttProcessError` on a non-zero exit, and
    `SttEmptyTranscriptError` when stdout is empty/whitespace-only
    despite a `0` exit.
    """
    template = command_template if command_template is not None else os.environ.get(env_var)
    if not template:
        raise SttConfigError(
            f"no external STT command configured (set {env_var} or pass command_template)"
        )

    argv = shlex.split(template.format(audio=str(audio_path)))
    try:
        completed = subprocess.run(argv, capture_output=True, text=True)
    except OSError as error:
        raise SttProcessError(f"could not run external STT command {argv!r}: {error}") from error

    if completed.returncode != 0:
        raise SttProcessError(
            f"external STT command exited {completed.returncode}: {completed.stderr.strip()}"
        )

    transcript = completed.stdout.strip()
    if not transcript:
        raise SttEmptyTranscriptError("external STT command produced an empty transcript")

    return transcript


def run_voice_turn_from_audio(
    orchestrator,
    llm_interface,
    audio_path: str | Path,
    *,
    command_template: str | None = None,
    env_var: str = JARVIS_STT_CMD_ENV,
) -> tuple[dict, str]:
    """One coherent voice turn from an audio file: `transcribe_audio_file`
    → the exact same `run_voice_turn` T36 already proved (`source=
    IntentSource.VOICE` → `render_response` egress, no fulfill fork).
    Raises `SttError` (never falls back to a fixture or an invented
    phrase) if transcription fails."""
    from jarvis.adapters.voice.fixture_loop import run_voice_turn

    transcript = transcribe_audio_file(
        audio_path, command_template=command_template, env_var=env_var
    )
    return run_voice_turn(orchestrator, llm_interface, transcript)
