"""Fase C · C2 — Safety/Authority gate stub (`B1-fase-c-intent-safety-stub`),
extended in C17 (`B1-fase-c-safety-real-policy`) with the first real
(non-RejectAll) Safety policy, and again in C41
(`B1-fase-c-safety-sim-policy`) to widen that policy's own allow-list to
match what `SimAutonomyExecutor` (C40) can drive in sim.

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
it `allow`s only the verbs on its allow-list — originally `HOLD` and
`LAND` only, **widened in C41 to also include `GO_TO`** (IC §0 decision
4: "aligned to what C40 can command in sim") — parsed from the
`autonomy:{verb}:{id}` shape `submit_command` already builds; any other
verb, or a request whose `action_id` does not match that shape, is
rejected too (reason `"verb_not_allowed"` / `"unparseable_action_id"`).
It never reads `authority_signal_id` at all — Authority is trace-only
(C5) and cannot imply `allow` through this gate or any other shipped
one. **Allow still never means execute**: `submit_command`'s `allow`
branch (see `flight_software.autonomy.surface`) resolves to
`execution="not_implemented"`, exactly as it already did for C4's
unreachable-in-shipped-code `allow` branch — this gate is never called
from `SimAutonomyExecutor.tick`, and `SimAutonomyExecutor` is never
called from `submit_command` or from this module; the two stay entirely
separate call paths, same as C40 left them. This Buy does not add an
executor, does not touch `SimulatedEscSink`/GPIO/PWM, and
`default_safety_gate()` is unchanged.

**One gate story, not two (C41 IC §0 decision 8):** the C40 verb-alignment
this Buy adds lives on `ArmedAllowlistSafetyGate` itself — extending its
existing allow-list — rather than as a second, parallel
`SimAutonomyAllowlistSafetyGate` class. C17's own gate already existed
specifically as "an opt-in armed allow-list for autonomy verbs"; adding a
second gate class with an overlapping `HOLD`/`LAND` allow-list would be
two competing answers to "which gate do I use for an autonomy verb,"
not one. `gate_id` stays `"armed_allowlist"` — callers checking that
string are unaffected by this widening.

**T4 (`B1-assistant-software-safety-bridge`) adds `SoftwareCapabilitySafetyGate`**
— the first Safety link for the Assistant's **software-only** Tasks
(`jarvis.intelligence.assistant_task`), sitting between T3's registry
membership soft-check and a Task's `task_kind` write. `allow` iff every
capability id encoded in `request.action_id` (`"capability:<id>[,<id>...]"`,
parsed by `_parse_capability_action_id`) is a known row in
`CapabilityRegistry.load_default()`, that row's `availability ==
CapabilityAvailability.AVAILABLE`, and its bound provider (via
`capability.provider_id` -> `registry.get_provider`) has `kind ==
ProviderKind.SOFTWARE` — otherwise `reject` with one of a finite set of
reason strings (`unparseable_action_id`, `empty_capabilities`,
`capability_unknown`, `capability_unavailable`, `provider_not_software`).
`default_safety_gate()` is **unchanged** (still always `RejectAllSafetyGate`)
and this gate is never routed through it — the Assistant constructs
`SoftwareCapabilitySafetyGate` explicitly. `ArmedAllowlistSafetyGate`'s
own allow-list and arm state are untouched; this is a separate gate for a
separate, non-autonomy request shape (`capability:...`, never
`autonomy:{verb}:{id}`). Like every gate here, `evaluate(...)` never
calls an actuator, a Skill's `execute`, or the registry's "run" anything
— it only reads `CapabilityRecord`/`ProviderRecord` fields.

**T14 (`B1-assistant-vehicle-allowlist-widen`) widens
`ArmedAllowlistSafetyGate._ALLOWED_VERBS`** a third time — from
`{HOLD, LAND, GO_TO}` to all seven `AutonomyVerb` values that have a
chat Task by this point (`TAKEOFF`/`RETURN_HOME`/`FOLLOW`/`PATROL` join
the three C41 already allowed). Same policy, same `gate_id`, same latch
API (`arm`/`disarm`/`armed`/`evaluate`) — only the set literal changes.
`allow` still never means execute: `SimAutonomyExecutor` stays
HOLD/LAND/GO_TO-only in sim (C40), so this gate's allow-list is now
deliberately **wider** than what anything in this codebase actually
executes — a chat `armar` followed by `takeoff`/`rtl`/`follow`/`patrol`
yields Safety `allow` and `execution="not_implemented"`, never
`"executed"`. No new Task kind, phrase table, capability, or skill.
"""

from __future__ import annotations

import uuid
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from jarvis.capabilities.intent import Intent
from jarvis.capabilities.registry import CapabilityRegistry
from jarvis.capabilities.schemas import CapabilityAvailability, ProviderKind

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
    Widened in C41 (`B1-fase-c-safety-sim-policy`) to also allow `GO_TO`,
    matching the three verbs `SimAutonomyExecutor` (C40) can drive in sim.
    Widened again in T14 (`B1-assistant-vehicle-allowlist-widen`) to the
    **full chat set** — all seven `AutonomyVerb` values that have a chat
    Task (`TAKEOFF`/`RETURN_HOME`/`FOLLOW`/`PATROL` join `HOLD`/`LAND`/
    `GO_TO`). `allow` here is still never execution — `SimAutonomyExecutor`
    (C40) remains HOLD/LAND/GO_TO-only in sim; this gate's allow-list may
    be (and now is) wider than what anything actually executes.

    Starts **disarmed**. While disarmed, `evaluate(...)` always rejects
    with reason `"disarmed"`. Once `arm()`ed, it allows all seven listed
    verbs — parsed from `request.action_id`'s `autonomy:{verb}:{id}`
    shape; any other verb, or an `action_id` that does not match that
    shape, is rejected with reason `"verb_not_allowed"` /
    `"unparseable_action_id"` respectively. `request.authority_signal_id`
    is never read by this gate — Authority stays trace-only and cannot
    flip a decision here.

    This is a Safety **policy** latch, unrelated to and never coupled
    with `SimulatedEscSink.arm()` (C10) or any hardware arm state — the
    two `arm()`s are separate, independent software switches. It is also
    never coupled to `SimAutonomyExecutor.tick` (C40) — `allow` here
    never calls, constructs, or references that executor; a caller
    wanting both an `allow` decision and an executed sim tick calls the
    two APIs itself, separately."""

    gate_id = "armed_allowlist"
    _ALLOWED_VERBS: frozenset[str] = frozenset({
        "HOLD", "LAND", "GO_TO", "TAKEOFF", "RETURN_HOME", "FOLLOW", "PATROL",
    })

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


def _parse_capability_action_id(action_id: str | None) -> list[str] | None:
    """Parses `"capability:<id>[,<id>...]"` -> a list of ids, or `None`
    if `action_id` is absent, does not start with the `"capability:"`
    prefix, or has an empty/malformed id segment (e.g. a trailing comma).
    An empty-but-well-formed list (`"capability:"`, nothing after the
    prefix) is distinguished from this by the caller — it parses to `[]`
    here, not `None`, so `SoftwareCapabilitySafetyGate` can reject it
    with its own `"empty_capabilities"` reason rather than the more
    generic `"unparseable_action_id"`."""
    if action_id is None:
        return None
    prefix = "capability:"
    if not action_id.startswith(prefix):
        return None
    remainder = action_id[len(prefix):]
    if remainder == "":
        return []
    ids = remainder.split(",")
    if any(not capability_id for capability_id in ids):
        return None
    return ids


class SoftwareCapabilitySafetyGate:
    """T4 — the first Safety link for the Assistant's software-only
    Tasks. `allow` iff every capability id in `request.action_id`
    exists in `CapabilityRegistry.load_default()`, is `available`, and
    is bound to a `software`-kind provider. See this module's own
    docstring for the full contract and finite reject-reason set."""

    gate_id = "software_capability"

    def evaluate(self, request: SafetyRequest) -> SafetyDecision:
        capability_ids = _parse_capability_action_id(request.action_id)
        if capability_ids is None:
            return SafetyDecision(
                outcome="reject", reason="unparseable_action_id", gate_id=self.gate_id
            )
        if not capability_ids:
            return SafetyDecision(
                outcome="reject", reason="empty_capabilities", gate_id=self.gate_id
            )

        registry = CapabilityRegistry.load_default()
        for capability_id in capability_ids:
            capability = registry.get_capability(capability_id)
            if capability is None:
                return SafetyDecision(
                    outcome="reject", reason="capability_unknown", gate_id=self.gate_id
                )
            if capability.availability != CapabilityAvailability.AVAILABLE:
                return SafetyDecision(
                    outcome="reject", reason="capability_unavailable", gate_id=self.gate_id
                )
            provider = (
                registry.get_provider(capability.provider_id)
                if capability.provider_id is not None
                else None
            )
            if provider is None or provider.kind != ProviderKind.SOFTWARE:
                return SafetyDecision(
                    outcome="reject", reason="provider_not_software", gate_id=self.gate_id
                )
        return SafetyDecision(outcome="allow", gate_id=self.gate_id)


def default_safety_gate() -> SafetyGate:
    """The only shipped gate factory. Always returns `RejectAllSafetyGate`."""
    return RejectAllSafetyGate()


def run_intent_through_safety(intent: Intent, gate: SafetyGate) -> SafetyDecision:
    """Builds a `SafetyRequest` from `intent` and returns `gate.evaluate(...)`.
    Never calls an actuator, a Skill's `execute`, or the Capability
    Registry's "run" anything — there is no step after this one in C2."""
    request = SafetyRequest(intent_id=intent.id)
    return gate.evaluate(request)
