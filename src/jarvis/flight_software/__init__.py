"""Fase C · C3 — `flight_software`: the vehicle-class CONTROL SPINE.

**Python scaffold / sim only — production flight_control runtime is C++
(future IC).** Engineer amendment on top of the C3 IC: everything under
this package is a platform scaffold written in Python — typed contracts,
`SimulatedImuHal`, a profile smoke helper. It is **not** the production
flight controller. The real flight_control runtime/firmware will be C++,
built in later Buys with its own IC (path/build TBD there) — this Buy
creates no C++ tree and no CMake anywhere in the repo.

**Naming split (honesty-critical — do not conflate):**
- craft catalog `flight_controller` (`library/flight_controller/`, bound via
  `jarvis.core.catalog_bind`) is a **BOM identity record** — a physical part
  the Engineer declares/mounts on a project, with mass/envelope like any
  other component.
- `flight_software.flight_control` (this package) is the **vehicle-class
  control spine** — HAL, sensors, estimation, control, mixer, actuators.
  These are different systems of record and must never be treated as the
  same thing by any reader of this codebase.

`flight_control/` ships exactly **two rungs**: HAL + simulated IMU sample
acquisition (C3), and a deterministic EMA/low-pass `ImuLowPassFilter`
(C6) that consumes those samples — sensing post-process only, never
estimation (no quaternion/Euler/Madgwick/Mahony/EKF output). No state
estimation, no attitude/rate/position controller, no mixer, no ESC/PWM.
`autonomy/` (C4) ships a typed command
**surface** — `TAKEOFF`/`HOLD`/`GO_TO`/`FOLLOW`/`RETURN_HOME`/`LAND`/
`PATROL` as proposable, non-operational commands that must pass through
`SafetyGate.evaluate(...)` before any hypothetical execution step; with
the only shipped gate (`RejectAllSafetyGate`), that step is always absent
— see `jarvis.flight_software.autonomy`'s own docstring. Nothing in this
package is wired to `orchestrator.py`, the Board, `library/`, or any
`jarvis.capabilities` Intent adapter — see
`.jes/artifacts/implementation_contract_fase_c_first_fc_rung_b1.md` §0/§3
and `.jes/artifacts/implementation_contract_fase_c_autonomy_surface_b1.md`.

This is a sensing + command-surface stub. It does not make any vehicle
flyable, holdable, or landable, and must never be described as such, and
this Python code must never be presented as production-ready
flight_control, MCU drivers, or a real control loop — see
`.jes/artifacts/implementation_report_fase_c_first_fc_rung_b1.md`,
`.jes/artifacts/implementation_report_fase_c_autonomy_surface_b1.md`, and
`.jes/artifacts/implementation_report_fase_c_imu_filtering_rung_b1.md`.
"""

from jarvis.flight_software.flight_control.filter import ImuLowPassFilter, read_filtered
from jarvis.flight_software.flight_control.hal import ImuHal
from jarvis.flight_software.flight_control.sim_imu_hal import SimulatedImuHal
from jarvis.flight_software.flight_control.types import ImuSample

__all__ = ["ImuHal", "ImuLowPassFilter", "ImuSample", "SimulatedImuHal", "read_filtered"]
