"""Fase C · C5 — Radio dual-role ingress stub (`B1-fase-c-radio-dual-role`).

Python platform scaffold. A production radio/ELRS stack (which may end up
native/C++) is a **future IC** — this module never decodes CRSF/ELRS/SBUS
or opens a serial/USB/SPI port; it only builds typed `Intent`/
`AuthoritySignal` objects from a typed stub frame that stands in for "what
came off the link."

A radio event is modeled as **dual-role** per C0 §3: it may carry an
`Intent` only, an `AuthoritySignal` only, or both as separate typed
objects in one `RadioDualRoleResult`. Radio and Authority are never
collapsed into an Assistant "skill" or into autonomy `execute` — see
`jarvis.flight_software.autonomy`, which this module never calls.

The **live/unclassified** radio path stays exactly what C2 shipped:
`jarvis.capabilities.intent.RadioIntentAdapter.parse(...)` still always
raises `NotImplementedError`. `SimulatedRadioIngress` is a **separate**,
explicitly-simulated API — it does not make `RadioIntentAdapter` "work."
"""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from jarvis.capabilities.intent import Intent, IntentSource
from jarvis.capabilities.safety import AuthorityKind, AuthoritySignal

RadioFrameRole = Literal["intent", "authority", "both"]


class RadioStubFrame(BaseModel):
    """Typed stand-in for "what came off the link" — never a decoded
    protocol. No `channels: list[int]` RC raw map pretending to be ELRS."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: RadioFrameRole
    intent_text: str = ""
    authority_kind: AuthorityKind | None = None
    authority_payload: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _validate_role_shape(self) -> "RadioStubFrame":
        needs_intent = self.role in ("intent", "both")
        needs_authority = self.role in ("authority", "both")

        if needs_intent and not self.intent_text.strip():
            raise ValueError("intent_text is required when role is 'intent' or 'both'")
        if not needs_intent and self.intent_text:
            raise ValueError("intent_text must be empty when role is 'authority'")

        if needs_authority and self.authority_kind is None:
            raise ValueError("authority_kind is required when role is 'authority' or 'both'")
        if not needs_authority and self.authority_kind is not None:
            raise ValueError("authority_kind must be unset when role is 'intent'")

        return self


class RadioDualRoleResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    frame_id: str
    intent: Intent | None = None
    authority: AuthoritySignal | None = None

    @model_validator(mode="after")
    def _at_least_one_role_present(self) -> "RadioDualRoleResult":
        if self.intent is None and self.authority is None:
            raise ValueError("RadioDualRoleResult must carry an intent, an authority, or both")
        return self


class SimulatedRadioIngress:
    """Builds a `RadioDualRoleResult` from a `RadioStubFrame`. Never opens
    a socket, a serial/USB/SPI port, or a file for RF — pure object
    construction only."""

    def ingest(self, frame: RadioStubFrame) -> RadioDualRoleResult:
        intent = None
        if frame.role in ("intent", "both"):
            intent = Intent(source=IntentSource.RADIO, raw_text=frame.intent_text)

        authority = None
        if frame.role in ("authority", "both"):
            authority = AuthoritySignal(
                source="radio",
                kind=frame.authority_kind,
                payload=frame.authority_payload,
            )

        return RadioDualRoleResult(frame_id=frame.id, intent=intent, authority=authority)


def describe_dual_role(result: RadioDualRoleResult) -> str:
    """Short debug string — no Safety call required."""
    parts = [f"frame_id={result.frame_id}"]
    if result.intent is not None:
        parts.append(f"intent(source={result.intent.source.value}, raw_text={result.intent.raw_text!r})")
    if result.authority is not None:
        parts.append(f"authority(kind={result.authority.kind}, payload={result.authority.payload!r})")
    return " ".join(parts)
