"""Fase C · C4 — pytest smoke path only (not Engineer Board smoke).

Python scaffold / sim only — production flight_control runtime is C++
(future IC). `smoke_hold_and_land` proposes `HOLD` then `LAND` and
submits each through `default_safety_gate()` (`RejectAllSafetyGate`)
unless a gate is explicitly given, and asserts both results are
`reject` / `not_attempted` — it exists to prove the always-reject
chain, not to fly anything.
"""

from __future__ import annotations

from jarvis.capabilities.safety import SafetyGate, default_safety_gate
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
