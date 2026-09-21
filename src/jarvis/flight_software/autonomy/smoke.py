"""Fase C · C4 — pytest smoke path only (not Engineer Board smoke).
Extended in C17 with a second smoke for the real Safety policy gate.

Python scaffold / sim only — production flight_control runtime is C++
(future IC). `smoke_hold_and_land` proposes `HOLD` then `LAND` and
submits each through `default_safety_gate()` (`RejectAllSafetyGate`)
unless a gate is explicitly given, and asserts both results are
`reject` / `not_attempted` — it exists to prove the always-reject
chain, not to fly anything.

`smoke_policy_gate_hold_and_land` (C17) does the same for an armed
`ArmedAllowlistSafetyGate`: both verbs are asserted `allow`, but
`execution` still asserts `"not_implemented"` — allow is not execute,
there is no actuator here, no ESC sink touched, and this helper does not
arm anything but its own Safety-policy latch.
"""

from __future__ import annotations

from jarvis.capabilities.safety import ArmedAllowlistSafetyGate, SafetyGate, default_safety_gate
from jarvis.flight_software.autonomy.surface import propose_command, submit_command
from jarvis.flight_software.autonomy.types import AutonomySubmissionResult, AutonomyVerb


def smoke_hold_and_land(gate: SafetyGate | None = None) -> list[AutonomySubmissionResult]:
    active_gate = gate or default_safety_gate()
    results: list[AutonomySubmissionResult] = []
    for verb in (AutonomyVerb.HOLD, AutonomyVerb.LAND):
        command = propose_command(verb)
        result = submit_command(command, active_gate)
        assert result.safety.outcome == "reject"
        assert result.execution == "not_attempted"
        results.append(result)
    return results


def smoke_policy_gate_hold_and_land() -> list[AutonomySubmissionResult]:
    """Arms a fresh `ArmedAllowlistSafetyGate` and submits `HOLD` then
    `LAND` through it — both allowed by the policy's locked allow-list,
    yet `execution` stays `"not_implemented"` on both: allow is a Safety
    verdict, not a dispatch to any actuator."""
    policy_gate = ArmedAllowlistSafetyGate()
    policy_gate.arm()
    results: list[AutonomySubmissionResult] = []
    for verb in (AutonomyVerb.HOLD, AutonomyVerb.LAND):
        command = propose_command(verb)
        result = submit_command(command, policy_gate)
        assert result.safety.outcome == "allow"
        assert result.execution == "not_implemented"
        results.append(result)
    return results
