"""Fase C · C2 — Safety/Authority gate stub (`B1-fase-c-intent-safety-stub`),
extended in C17 (`B1-fase-c-safety-real-policy`) with the first real
(non-RejectAll) Safety policy.

`default_safety_gate()` is the ONLY shipped gate **factory** and it still
always returns `RejectAllSafetyGate` — nothing in `src/` can accidentally
`allow` a proposed resolution by using the default. There is no
`AllowAllSafetyGate` under `src/`; if a test needs one to exercise the
`allow` branch of a caller in isolation, it must define a local fake
inside the test file itself (IC §2.2 lock, unchanged since C2).
`run_intent_through_safety` never calls an actuator, a Skill's `execute`,
or the Capability Registry's "run" anything — it is a pure function from
`Intent` to `SafetyDecision`.

**C17 — `ArmedAllowlistSafetyGate`:** a real, opt-in policy gate. It
starts **disarmed** and, while disarmed, always rejects (reason
`"disarmed"`, never the historical `"not_implemented"` RejectAll uses —
IC §0 decision 8 locks these reason strings apart so callers can tell a
policy rejection from RejectAll's blanket one). Once explicitly `arm()`ed,
it `allow`s only the two verbs on its locked allow-list — `HOLD` and
`LAND` — parsed from the `autonomy:{verb}:{id}` shape `submit_command`
already builds; any other verb, or a request whose `action_id` does not
match that shape, is rejected too (reason `"verb_not_allowed"` /
`"unparseable_action_id"`). It never reads `authority_signal_id` at
all — Authority is trace-only (C5) and cannot imply `allow` through this
gate or any other shipped one. **Allow still never means execute**:
`submit_command`'s `allow` branch (see `flight_software.autonomy.surface`)
resolves to `execution="not_implemented"`, exactly as it already did for
C4's unreachable-in-shipped-code `allow` branch — this Buy does not add
an executor, does not touch `SimulatedEscSink`/GPIO/PWM, and
`default_safety_gate()` is unchanged.
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


class ArmedAllowlistSafetyGate:
    """C17 — first real Safety policy: an opt-in armed allow-list.

    Starts **disarmed**. While disarmed, `evaluate(...)` always rejects
    with reason `"disarmed"`. Once `arm()`ed, it allows only `HOLD` and
    `LAND` (this Buy's locked minimum allow-list — not configurable here;
    extending it is a future Buy's decision, not this one's) parsed from
    `request.action_id`'s `autonomy:{verb}:{id}` shape; any other verb, or
    an `action_id` that does not match that shape, is rejected with reason
    `"verb_not_allowed"` / `"unparseable_action_id"` respectively.
    `request.authority_signal_id` is never read by this gate — Authority
    stays trace-only and cannot flip a decision here.

    This is a Safety **policy** latch, unrelated to and never coupled
    with `SimulatedEscSink.arm()` (C10) or any hardware arm state — the
    two `arm()`s are separate, independent software switches."""

    gate_id = "armed_allowlist"
    _ALLOWED_VERBS: frozenset[str] = frozenset({"HOLD", "LAND"})

    def __init__(self) -> None:
        self._armed = False

    @property
    def armed(self) -> bool:
        return self._armed

    def arm(self) -> None:
        self._armed = True

    def disarm(self) -> None:
        self._armed = False

    def evaluate(self, request: SafetyRequest) -> SafetyDecision:
        if not self._armed:
            return SafetyDecision(outcome="reject", reason="disarmed", gate_id=self.gate_id)

        verb = _parse_autonomy_verb(request.action_id)
        if verb is None:
            return SafetyDecision(
                outcome="reject", reason="unparseable_action_id", gate_id=self.gate_id
            )
        if verb not in self._ALLOWED_VERBS:
            return SafetyDecision(outcome="reject", reason="verb_not_allowed", gate_id=self.gate_id)
        return SafetyDecision(outcome="allow", gate_id=self.gate_id)


def _parse_autonomy_verb(action_id: str | None) -> str | None:
    """Parses `"autonomy:{verb}:{id}"` -> `verb`, or `None` if `action_id`
    is absent or does not match that shape. Robust to an id segment that
    itself is absent (e.g. a bare `"autonomy:HOLD"`)."""
    if action_id is None:
        return None
    parts = action_id.split(":", 2)
    if len(parts) < 2 or parts[0] != "autonomy" or not parts[1]:
        return None
    return parts[1]


def default_safety_gate() -> SafetyGate:
    """The only shipped gate factory. Always returns `RejectAllSafetyGate`."""
    return RejectAllSafetyGate()


def run_intent_through_safety(intent: Intent, gate: SafetyGate) -> SafetyDecision:
    """Builds a `SafetyRequest` from `intent` and returns `gate.evaluate(...)`.
    Never calls an actuator, a Skill's `execute`, or the Capability
    Registry's "run" anything — there is no step after this one in C2."""
    request = SafetyRequest(intent_id=intent.id)
    return gate.evaluate(request)
