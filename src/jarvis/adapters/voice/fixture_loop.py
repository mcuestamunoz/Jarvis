"""Skill-first phase C — V2 (`B1-assistant-voice-fixture-loop`, T36).

A thin, fixture-driven voice adapter proving the ingress → Skill-first
brain → egress chain end-to-end without any real microphone/speaker or
STT/TTS vendor. Reuses `JarvisOrchestrator.handle_user_text(...,
source=IntentSource.VOICE)` (T35, `B1-assistant-voice-intent-ingress`)
and the existing `jarvis.adapters.cli.main.render_response` renderer
unchanged — no parallel orchestrator, no Skill runtime, no fork of
fulfill logic.

`FixtureSttSource` is the typed stand-in for "what STT produced" this
Buy — same discipline as C5's own `RadioStubFrame` standing in for
"what came off the link" without decoding real RF: plain `str` lines
in, never audio bytes, no mic, no vendor SDK. Real STT (T37,
`B1-assistant-voice-stt-external`)
and real TTS (T38, `B1-assistant-voice-tts-external`) are separate,
later Buys that replace only this fixture and the `speak` callable —
the turn/loop shape here does not change.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable, Iterator


class FixtureSttSource:
    """Typed stand-in for "what STT produced" — plain text lines,
    never audio bytes. `from_lines` wraps an in-memory iterable
    (tests); `from_path` reads one line per non-blank row of a text
    file (e.g. a `--voice-fixture PATH` CLI flag)."""

    def __init__(self, lines: Iterable[str]) -> None:
        self._lines: list[str] = list(lines)

    @classmethod
    def from_lines(cls, lines: Iterable[str]) -> "FixtureSttSource":
        return cls(lines)

    @classmethod
    def from_path(cls, path: Path) -> "FixtureSttSource":
        text = Path(path).read_text(encoding="utf-8")
        return cls(line.strip() for line in text.splitlines() if line.strip())

    def __iter__(self) -> Iterator[str]:
        return iter(self._lines)


def run_voice_turn(orchestrator: Any, llm_interface: Any, text: str) -> tuple[dict, str]:
    """One coherent voice turn: fixture `text` → the same Skill-first
    brain every chat turn already uses, tagged `source=IntentSource.
    VOICE` (T35) → the existing `render_response` renderer as egress
    text (what a later real-TTS Buy would speak). No fulfill fork, no
    voice-tuned renderer — identical `dict`/`str` shapes `run_chat`
    already produces for a `TERMINAL` turn; only the `Intent.source`
    tag differs."""
    from jarvis.adapters.cli.main import render_response
    from jarvis.capabilities.intent import IntentSource

    result = orchestrator.handle_user_text(text, llm_interface, source=IntentSource.VOICE)
    egress = render_response(result)
    return result, egress


def run_voice(
    orchestrator: Any,
    llm_interface: Any,
    fixture: Iterable[str],
    *,
    speak: Callable[[str], None] | None = None,
) -> list[tuple[str, dict, str]]:
    """Fixture-driven loop, parallel in spirit to
    `jarvis.adapters.cli.main.run_chat` but never calling `input()` —
    consumes `fixture` (e.g. a `FixtureSttSource`) line by line instead
    of a microphone, calling `run_voice_turn` once per line. `speak`
    (default: no-op) receives each turn's rendered egress string — a
    later real-TTS Buy only needs to swap this callable, not the loop
    or the turn helper. Returns every `(text, result, egress)` triple
    for inspection/tests."""
    turns: list[tuple[str, dict, str]] = []
    for text in fixture:
        result, egress = run_voice_turn(orchestrator, llm_interface, text)
        if speak is not None:
            speak(egress)
        turns.append((text, result, egress))
    return turns
