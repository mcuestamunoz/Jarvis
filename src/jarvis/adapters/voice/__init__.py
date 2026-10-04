"""Voice adapter package — Skill-first phase C (voz). Fixture-driven
loop (`B1-assistant-voice-fixture-loop`, T36) + external STT process
seam (`B1-assistant-voice-stt-external`, T37) + external TTS process
seam (`B1-assistant-voice-tts-external`, T38). No mic/speaker driver
in this package, no vendor SDK — see `fixture_loop.py`/
`external_stt.py`/`external_tts.py`'s own docstrings for the honesty
lock. T38's default demo setup (operator-installed, never hardcoded
here) is a free, local Piper `en_GB` voice — see
`.jes/artifacts/engineer_note_voice_tts_product_brief.md`."""

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
    TtsConfigError,
    TtsError,
    TtsProcessError,
    make_speak_callable,
    speak_egress,
)
from jarvis.adapters.voice.fixture_loop import FixtureSttSource, run_voice, run_voice_turn

__all__ = [
    "FixtureSttSource",
    "JARVIS_STT_CMD_ENV",
    "JARVIS_TTS_CMD_ENV",
    "SttConfigError",
    "SttEmptyTranscriptError",
    "SttError",
    "SttProcessError",
    "TtsConfigError",
    "TtsError",
    "TtsProcessError",
    "make_speak_callable",
    "run_voice",
    "run_voice_turn",
    "run_voice_turn_from_audio",
    "speak_egress",
    "transcribe_audio_file",
]
