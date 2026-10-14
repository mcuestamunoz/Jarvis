"""Skill-first phase C — V8 (`B1-assistant-chat-voice-ptt`, T47).

External **record** process seam — captures a fixed-duration audio file
by invoking an external command, never by touching a microphone or
decoding/encoding audio inside this repo. No speech/audio package is
added to `pyproject.toml` and no audio capture happens in
`capabilities/`, `intelligence/`, or `core/` — this module's only job
is: run a configured external command that writes a wav to a given
path, and treat exit `0` **plus** a non-empty output file as success.

**Vendor choice is explicitly out of this Buy.** `JARVIS_RECORD_CMD`
names some external command (the shipped `scripts/voice/record_turn.sh`
wraps ffmpeg/arecord) — this seam never hardcodes a recorder and never
tip-pins an audio dependency.

Honesty lock: missing/malformed config, a non-zero exit, or a command
that exits `0` but produces no (or an empty) output file are each
surfaced as a typed `RecordError` subclass — never a silent "recorded
nothing" success.

T53 made this seam the default mic input of `--voice-only`; T55 removed
the retired typed push-to-talk trigger (`is_ptt_trigger` /
`PTT_TRIGGER_PHRASES`) that used to live here.
"""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

JARVIS_RECORD_CMD_ENV = "JARVIS_RECORD_CMD"
JARVIS_RECORD_SECONDS_ENV = "JARVIS_RECORD_SECONDS"
DEFAULT_RECORD_SECONDS = 7
# T54 (`B1-assistant-voice-silence-cut`, V10): the silence cut itself
# lives in the external recorder (`scripts/voice/record_turn.sh` reads
# this same env var); Python only resolves it to print an honest cue.
JARVIS_RECORD_SILENCE_SECONDS_ENV = "JARVIS_RECORD_SILENCE_SECONDS"
DEFAULT_RECORD_SILENCE_SECONDS = 1.0


class RecordError(Exception):
    """Base for every external-record seam failure — never a silent
    "recorded nothing" success."""


class RecordConfigError(RecordError):
    """The record command template (env var or explicit argument) is
    missing, empty, or missing the required `{output}` placeholder."""


class RecordProcessError(RecordError):
    """The external record command exited with a non-zero status,
    could not be run at all (missing binary), or exited `0` but
    produced no (or an empty) output file."""


def resolve_record_seconds(env_var: str = JARVIS_RECORD_SECONDS_ENV) -> int:
    """Capture duration: `env_var` (default `JARVIS_RECORD_SECONDS`) if
    set and a valid positive integer, else `DEFAULT_RECORD_SECONDS`
    (7). An unparseable value falls back to the default rather than
    crashing the chat loop over a malformed env var."""
    raw = os.environ.get(env_var)
    if not raw:
        return DEFAULT_RECORD_SECONDS
    try:
        seconds = int(raw)
    except ValueError:
        return DEFAULT_RECORD_SECONDS
    return seconds if seconds > 0 else DEFAULT_RECORD_SECONDS


def resolve_record_silence_seconds(env_var: str = JARVIS_RECORD_SILENCE_SECONDS_ENV) -> float:
    """Silence-cut window the external recorder applies (T54): unset →
    `DEFAULT_RECORD_SILENCE_SECONDS` (1.0); set but empty, or `0` →
    `0.0` (fixed-duration capture, T53 behavior); a negative or
    unparseable value → the default. Must stay in step with
    `scripts/voice/record_turn.sh`, which applies the same rules."""
    raw = os.environ.get(env_var)
    if raw is None:
        return DEFAULT_RECORD_SILENCE_SECONDS
    if not raw.strip():
        return 0.0
    try:
        seconds = float(raw)
    except ValueError:
        return DEFAULT_RECORD_SILENCE_SECONDS
    return seconds if seconds >= 0 else DEFAULT_RECORD_SILENCE_SECONDS


def record_audio_file(
    output_path: str | Path,
    *,
    seconds: int | None = None,
    command_template: str | None = None,
    env_var: str = JARVIS_RECORD_CMD_ENV,
) -> None:
    """Invoke the external record command configured by
    `command_template` (or, if omitted, the `env_var` environment
    variable — default `JARVIS_RECORD_CMD`), capturing to
    `output_path`. `seconds` defaults to `resolve_record_seconds()`
    when omitted.

    `command_template` must contain the literal `{output}` placeholder
    (substituted with `str(output_path)`) and may optionally contain
    `{seconds}` (substituted with the resolved duration) before the
    resulting string is split into argv via `shlex.split` — no shell is
    spawned. Raises `RecordConfigError` when no template is configured
    or `{output}` is missing from it, `RecordProcessError` on a
    non-zero exit, a command that cannot be run at all (missing
    binary), or a `0` exit that produced no (or an empty) output file.
    """
    template = command_template if command_template is not None else os.environ.get(env_var)
    if not template:
        raise RecordConfigError(
            f"no external record command configured (set {env_var} or pass command_template)"
        )
    if "{output}" not in template:
        raise RecordConfigError(
            f"{env_var} template must contain the literal {{output}} placeholder"
        )

    resolved_seconds = seconds if seconds is not None else resolve_record_seconds()
    argv = shlex.split(template.format(output=str(output_path), seconds=resolved_seconds))
    try:
        completed = subprocess.run(argv, capture_output=True, text=True)
    except OSError as error:
        raise RecordProcessError(
            f"could not run external record command {argv!r}: {error}"
        ) from error

    if completed.returncode != 0:
        raise RecordProcessError(
            f"external record command exited {completed.returncode}: {completed.stderr.strip()}"
        )

    out = Path(output_path)
    if not out.exists() or out.stat().st_size == 0:
        raise RecordProcessError(
            f"external record command exited 0 but produced no audio at {output_path}"
        )
