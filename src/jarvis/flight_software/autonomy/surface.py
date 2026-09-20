"""Fase C · C4 — autonomy command surface API.

Python scaffold / sim only — production flight_control runtime is C++
(future IC). `submit_command` MUST call `SafetyGate.evaluate(...)` before
any hypothetical execution step. With the only shipped gate
(`RejectAllSafetyGate`), the outcome is always `reject`, so the execution
step is absent — `execution` resolves to `"not_attempted"`. Even in the
unreachable-in-C4 branch where a caller supplies a test-local fake gate
that returns `allow`, this module still does not actuate: `execution`
resolves to `"not_implemented"`, never `"executed"`. There is no function
here named like `execute_hold`/`run_land`/`dispatch_autonomy` that skips
Safety.
"""

from __future__ import annotations

from jarvis.capabilities.safety import SafetyGate, SafetyRequest
from jarvis.flight_software.autonomy.types import (
    AutonomyCommand,
    AutonomySubmissionResult,
    AutonomyVerb,
)


def propose_command(
    verb: AutonomyVerb,
    *,
    intent_id: str | None = None,
    params: dict[str, str] | None = None,
) -> AutonomyCommand:
    """Pure constructor helper — does not call Safety."""
    return AutonomyCommand(verb=verb, intent_id=intent_id, params=params or {})


def submit_command(command: AutonomyCommand, gate: SafetyGate) -> AutonomySubmissionResult:
    request = SafetyRequest(
        intent_id=command.intent_id,
        action_id=f"autonomy:{command.verb.value}:{command.id}",
    )
    decision = gate.evaluate(request)

    if decision.outcome != "allow":
        return AutonomySubmissionResult(
            command_id=command.id,
            verb=command.verb,
            safety=decision,
            execution="not_attempted",
        )

    # Only reachable with a test-local fake gate — no gate shipped in
    # src/ ever returns "allow" in C4 (see RejectAllSafetyGate). Even
    # here there is no actuator to call.
    return AutonomySubmissionResult(
        command_id=command.id,
        verb=command.verb,
        safety=decision,
        execution="not_implemented",
    )
