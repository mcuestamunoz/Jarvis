"""Voice adapter package — Skill-first phase C (voz). Fixture-driven
loop (`B1-assistant-voice-fixture-loop`, T36) + external STT process
seam (`B1-assistant-voice-stt-external`, T37) + external TTS process
seam (`B1-assistant-voice-tts-external`, T38). No mic/speaker driver
in this package, no vendor SDK — see `fixture_loop.py`/
`external_stt.py`/`external_tts.py`'s own docstrings for the honesty
lock. T38's default demo setup (operator-installed, never hardcoded
here) is a free, local Piper voice — Spanish `es_ES-davefx-medium` by
default since T49 (the original `en_GB-alan-medium` stays supported as
a documented legacy value) — see
`.jes/artifacts/engineer_note_voice_tts_product_brief.md`."""

from jarvis.adapters.voice.external_record import (
    DEFAULT_RECORD_SECONDS,
    DEFAULT_RECORD_SILENCE_SECONDS,
    DEFAULT_VOICE_SETTLE_SECONDS,
    JARVIS_RECORD_CMD_ENV,
    JARVIS_RECORD_SECONDS_ENV,
    JARVIS_RECORD_SILENCE_SECONDS_ENV,
    JARVIS_VOICE_SETTLE_SECONDS_ENV,
    RecordConfigError,
    RecordError,
    RecordProcessError,
    record_audio_file,
    resolve_record_seconds,
    resolve_record_silence_seconds,
    resolve_voice_settle_seconds,
)
from jarvis.adapters.voice.external_stt import (
    JARVIS_STT_CMD_ENV,
    SttConfigError,
    SttEmptyTranscriptError,
    SttError,
    SttProcessError,
    run_voice_turn_from_audio,
    transcribe_audio_file,
)
from jarvis.adapters.voice.external_tts import (
    JARVIS_TTS_CMD_ENV,
    TtsCancelled,
    TtsConfigError,
    TtsError,
    TtsProcessError,
    make_speak_callable,
    speak_egress,
)
from jarvis.adapters.voice.fixture_loop import FixtureSttSource, run_voice, run_voice_turn
from jarvis.adapters.voice.speak_sanitize import sanitize_for_speech
from jarvis.adapters.voice.spoken_continuity import (
    FULL_CONTINUITY_PHRASES,
    brief_spoken_continuity,
    full_spoken_continuity,
    is_full_continuity_request,
    spoken_text_for_wall,
)

__all__ = [
    "DEFAULT_RECORD_SECONDS",
    "DEFAULT_RECORD_SILENCE_SECONDS",
    "DEFAULT_VOICE_SETTLE_SECONDS",
    "FULL_CONTINUITY_PHRASES",
    "FixtureSttSource",
    "JARVIS_RECORD_CMD_ENV",
    "JARVIS_RECORD_SECONDS_ENV",
    "JARVIS_RECORD_SILENCE_SECONDS_ENV",
    "JARVIS_VOICE_SETTLE_SECONDS_ENV",
    "JARVIS_STT_CMD_ENV",
    "JARVIS_TTS_CMD_ENV",
    "RecordConfigError",
    "RecordError",
    "RecordProcessError",
    "SttConfigError",
    "SttEmptyTranscriptError",
    "SttError",
    "SttProcessError",
    "TtsCancelled",
    "TtsConfigError",
    "TtsError",
    "TtsProcessError",
    "brief_spoken_continuity",
    "full_spoken_continuity",
    "is_full_continuity_request",
    "make_speak_callable",
    "record_audio_file",
    "resolve_record_seconds",
    "resolve_record_silence_seconds",
    "resolve_voice_settle_seconds",
    "run_voice",
    "run_voice_turn",
    "run_voice_turn_from_audio",
    "sanitize_for_speech",
    "speak_egress",
    "spoken_text_for_wall",
    "transcribe_audio_file",
]
