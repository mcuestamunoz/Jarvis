"""Voice adapter package — Skill-first phase C (voz). Fixture-driven
loop (`B1-assistant-voice-fixture-loop`, T36) + external STT process
seam (`B1-assistant-voice-stt-external`, T37). No real TTS, no mic
stream, no vendor SDK — see `fixture_loop.py`/`external_stt.py`'s own
docstrings for the honesty lock and the later phases (T38 real TTS)
that replace only the fixture/STT process, never this shape."""

from jarvis.adapters.voice.external_stt import (
    JARVIS_STT_CMD_ENV,
    SttConfigError,
    SttEmptyTranscriptError,
    SttError,
    SttProcessError,
    run_voice_turn_from_audio,
    transcribe_audio_file,
)
from jarvis.adapters.voice.fixture_loop import FixtureSttSource, run_voice, run_voice_turn

__all__ = [
    "FixtureSttSource",
    "JARVIS_STT_CMD_ENV",
    "SttConfigError",
    "SttEmptyTranscriptError",
    "SttError",
    "SttProcessError",
    "run_voice",
    "run_voice_turn",
    "run_voice_turn_from_audio",
    "transcribe_audio_file",
]
