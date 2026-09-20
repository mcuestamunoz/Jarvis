"""Fase C · C2 — Safety/Authority gate stub (`B1-fase-c-intent-safety-stub`).

`default_safety_gate()` is the ONLY shipped gate factory and it always
returns `RejectAllSafetyGate` — nothing in `src/` can accidentally
`allow` a proposed resolution in C2. There is no `AllowAllSafetyGate`
under `src/`; if a test needs one to exercise the `allow` branch of a
caller, it must define a local fake inside the test file itself (IC
§2.2 lock). `run_intent_through_safety` never calls an actuator, a
Skill's `execute`, or the Capability Registry's "run" anything — it is
a pure function from `Intent` to `SafetyDecision`.
"""

from __future__ import annotations

import uuid
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from jarvis.capabilities.intent import Intent

AuthoritySource = Literal["radio", "api", "operator"]
AuthorityKind = Literal["override", "kill", "mode", "unknown"]
SafetyOutcome = Literal["allow", "reject", "defer"]


class AuthoritySignal(BaseModel):
    """Data only — never decoded RC channels, never ELRS/CRSF."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: AuthoritySource
    kind: AuthorityKind
    payload: str | None = None


class SafetyRequest(BaseModel):
    """Input to a `SafetyGate`. No actuator command blob — a request
    references an intent and/or a proposed-action id string only.

    `authority_signal_id` (Fase C · C5) is optional traceability only — an
    id pointing at an `AuthoritySignal` that motivated this request (e.g.
    a simulated radio `kill`/`override`). Setting it does **not** change
    gate behavior: `RejectAllSafetyGate` still always rejects regardless
    of this field, and no shipped gate lets "authority" imply `allow`."""

    model_config = ConfigDict(extra="forbid")

    intent_id: str | None = None
    action_id: str | None = None
    authority_signal_id: str | None = None


class SafetyDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: SafetyOutcome
    reason: str = ""
    gate_id: str

    @model_validator(mode="after")
    def _reason_required_on_reject(self) -> "SafetyDecision":
        if self.outcome == "reject" and not self.reason:
            raise ValueError("reason is required when outcome is 'reject'")
        return self


class SafetyGate(Protocol):
    def evaluate(self, request: SafetyRequest) -> SafetyDecision: ...


class RejectAllSafetyGate:
    """C2 default implementation — always rejects. See IC §0.5: nothing
    can accidentally 'pass' Safety in C2."""

    gate_id = "reject_all"

    def evaluate(self, request: SafetyRequest) -> SafetyDecision:
        return SafetyDecision(
            outcome="reject",
            reason="not_implemented",
            gate_id=self.gate_id,
        )


def default_safety_gate() -> SafetyGate:
    """The only shipped gate factory. Always returns `RejectAllSafetyGate`."""
    return RejectAllSafetyGate()


def run_intent_through_safety(intent: Intent, gate: SafetyGate) -> SafetyDecision:
    """Builds a `SafetyRequest` from `intent` and returns `gate.evaluate(...)`.
    Never calls an actuator, a Skill's `execute`, or the Capability
    Registry's "run" anything — there is no step after this one in C2."""
    request = SafetyRequest(intent_id=intent.id)
    return gate.evaluate(request)
