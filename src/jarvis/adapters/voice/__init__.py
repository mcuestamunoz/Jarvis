"""Voice adapter package — Skill-first phase C (voz), fixture-driven
**V2 only** (`B1-assistant-voice-fixture-loop`, T36). No real STT/TTS,
no mic/speaker I/O, no vendor SDK — see `fixture_loop.py`'s own
docstring for the honesty lock and the later phases (T37 real STT,
T38 real TTS) that replace only the fixture, never this shape."""

from jarvis.adapters.voice.fixture_loop import FixtureSttSource, run_voice, run_voice_turn

__all__ = ["FixtureSttSource", "run_voice", "run_voice_turn"]
