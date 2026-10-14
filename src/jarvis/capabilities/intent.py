"""Fase C · C2 — Intent ingress (`B1-fase-c-intent-safety-stub`), extended
by `B1-assistant-voice-intent-ingress` (T35, Skill-first phase C — V1).

Typed records describing WHAT was asked, never HOW to fly it. In C2,
only the `terminal` channel adapter actually constructed an `Intent` —
voice, radio, and api adapters existed as typed callables that always
refused with `NotImplementedError`, so nothing could silently produce
a "successful flight intent" from an unimplemented channel.

T35 fills **only** the voice adapter: `VoiceIntentAdapter.parse(raw_text:
str) -> Intent` now mirrors `TerminalIntentAdapter.parse` exactly,
tagged `source=IntentSource.VOICE` — text in, text out, no audio bytes,
no STT/TTS inside this module. Radio and Api adapters are deliberately
**unchanged**: both still always raise `NotImplementedError`. See
`jarvis.capabilities.safety` for the mandatory gate every proposed
resolution must pass through, and the Implementation Contract for the
full honesty lock (H-rules).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class IntentSource(str, Enum):
    TERMINAL = "terminal"
    VOICE = "voice"
    RADIO = "radio"
    API = "api"
    UI = "ui"


class Intent(BaseModel):
    """What was asked — never an actuator command."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: IntentSource
    raw_text: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, str] = Field(default_factory=dict)


class Task(BaseModel):
    """Optional thin stub — no execution fields. See IC §1.3: C2 may ship
    this schema without any production code path constructing instances
    outside tests."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    intent_id: str
    required_capability_ids: list[str] = Field(default_factory=list)


class TerminalIntentAdapter:
    """The only channel that produces a real `Intent` in C2."""

    @staticmethod
    def parse(raw_text: str) -> Intent:
        return Intent(source=IntentSource.TERMINAL, raw_text=raw_text)


class VoiceIntentAdapter:
    """T35 — second channel to actually construct an `Intent`. Text-only
    seam: `raw_text` is post-STT text (STT itself happens outside this
    module, in a later phase) — same shape as `TerminalIntentAdapter`,
    tagged `VOICE` instead of `TERMINAL`."""

    @staticmethod
    def parse(raw_text: str) -> Intent:
        return Intent(source=IntentSource.VOICE, raw_text=raw_text)


class RadioIntentAdapter:
    """Live/unclassified radio ingress — stays `NotImplemented` in C5 too
    (Fase C · C5, `B1-fase-c-radio-dual-role`). For a typed, **simulated**
    stand-in that models a radio event as Intent and/or Authority, use
    `jarvis.capabilities.radio.SimulatedRadioIngress` instead — it never
    makes this adapter "work" for arbitrary payloads."""

    @staticmethod
    def parse(raw_payload: object) -> Intent:
        raise NotImplementedError("radio intent ingress is not_implemented in C2")


class ApiIntentAdapter:
    @staticmethod
    def parse(raw_payload: object) -> Intent:
        raise NotImplementedError("api intent ingress is not_implemented in C2")
