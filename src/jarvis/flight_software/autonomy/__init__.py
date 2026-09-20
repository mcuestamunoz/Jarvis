"""Fase C · C4 — `flight_software.autonomy`: typed autonomy command SURFACE.

Python scaffold / sim only — production flight_control runtime is C++
(future IC). Every submission goes through `SafetyGate.evaluate(...)`
before any hypothetical execution step; with the only shipped gate
(`RejectAllSafetyGate`), that step is always absent — `execution` is
never `"executed"` on any path shipped in `src/`. This package proposes
commands, it does not fly, arm, hold, or land anything.

Vocabulary matches C0 §8's starter set (`TAKEOFF`/`HOLD`/`GO_TO`/`FOLLOW`/
`RETURN_HOME`/`LAND`/`PATROL`). `HOLD` and `LAND` are exercised
end-to-end through Safety in tests, per the C4 IC's lock — the other
verbs are equally valid enum members and may be proposed the same way.

This is an orchestration surface, not a control loop — it does not call
`flight_control`'s HAL/IMU, does not read sensors as a substitute for
"holding," and does not touch Continuity, the orchestrator, the Board,
or `library/`. See
`.jes/artifacts/implementation_contract_fase_c_autonomy_surface_b1.md`.
"""

from jarvis.flight_software.autonomy.smoke import smoke_hold_and_land
from jarvis.flight_software.autonomy.surface import propose_command, submit_command
from jarvis.flight_software.autonomy.types import (
    AutonomyCommand,
    AutonomySubmissionResult,
    AutonomyVerb,
)

__all__ = [
    "AutonomyCommand",
    "AutonomySubmissionResult",
    "AutonomyVerb",
    "propose_command",
    "smoke_hold_and_land",
    "submit_command",
]
