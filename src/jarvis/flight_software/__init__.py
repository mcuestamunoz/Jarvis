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

`flight_control/` ships exactly **six rungs plus one closed-loop sim
tip**: HAL + simulated IMU
sample acquisition (C3); a deterministic EMA/low-pass `ImuLowPassFilter`
(C6) that consumes those samples — sensing post-process only; a single
minimal `ComplementaryAttitudeEstimator` (C7) that consumes filtered
samples and emits `AttitudeState` (quaternion + body rate) — NOT
Mahony/Madgwick/EKF/UKF by name (no bias learning, no gradient descent,
no covariance), no magnetometer/GPS/baro fusion, and never
flight-verified; a single `PdAttitudeController` (C8) that consumes an
`AttitudeSetpoint` + `AttitudeState` and emits a `BodyRateCommand` — a
body-rate number only, never a motor command; a single `QuadXMixer`
(C9) that consumes a collective thrust + `BodyRateCommand` and emits a
`MotorForceCommand` — four normalized `[0, 1]` motor force numbers for
one documented quad-X layout; an ESC/PWM encoding stub (C10) —
`encode_motor_forces` maps those four forces linearly onto PWM pulse
widths in microseconds (default `1000`–`2000` µs), and `SimulatedEscSink`
records the resulting `EscPwmCommand` **in memory only**, starting
`armed=False` — no `RPi.GPIO`/`pigpio`/serial/socket I/O, no DShot as a
shipped product, and no claim that arming powers anything physical or
that any motor spins; and, closing the C0 §7 wooden-ladder tip, a single
`ToyQuadAttitudePlant` (C11) that advances a toy, attitude-only, sim-only
dynamics from `MotorForceCommand` and emits the next `ImuSample`
**consistent with its own true attitude** — letting the whole C3→C10
chain run as a closed loop that measurably recovers toward level, still
never touching real hardware and never claiming any vehicle flies. No
position/velocity control loop anywhere in this package. `autonomy/`
(C4) ships a typed command
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
`.jes/artifacts/implementation_report_fase_c_autonomy_surface_b1.md`,
`.jes/artifacts/implementation_report_fase_c_imu_filtering_rung_b1.md`,
`.jes/artifacts/implementation_report_fase_c_attitude_estimation_rung_b1.md`,
`.jes/artifacts/implementation_report_fase_c_attitude_controller_rung_b1.md`,
`.jes/artifacts/implementation_report_fase_c_mixer_rung_b1.md`,
`.jes/artifacts/implementation_report_fase_c_esc_pwm_stub_rung_b1.md`,
and
`.jes/artifacts/implementation_report_fase_c_controlled_flight_sim_tip_b1.md`.
"""

from jarvis.flight_software.flight_control.attitude import (
    AttitudeState,
    ComplementaryAttitudeEstimator,
    read_attitude,
)
from jarvis.flight_software.flight_control.controller import (
    AttitudeSetpoint,
    BodyRateCommand,
    PdAttitudeController,
    level_setpoint,
)
from jarvis.flight_software.flight_control.esc import (
    EscApplyResult,
    EscPwmCommand,
    SimulatedEscSink,
    encode_motor_forces,
)
from jarvis.flight_software.flight_control.filter import ImuLowPassFilter, read_filtered
from jarvis.flight_software.flight_control.hal import ImuHal
from jarvis.flight_software.flight_control.mixer import (
    MotorForceCommand,
    QuadXMixer,
    hover_collective,
)
from jarvis.flight_software.flight_control.plant import ToyQuadAttitudePlant, tilt_angle_rad
from jarvis.flight_software.flight_control.sim_imu_hal import SimulatedImuHal
from jarvis.flight_software.flight_control.types import ImuSample

__all__ = [
    "AttitudeSetpoint",
    "AttitudeState",
    "BodyRateCommand",
    "ComplementaryAttitudeEstimator",
    "EscApplyResult",
    "EscPwmCommand",
    "ImuHal",
    "ImuLowPassFilter",
    "ImuSample",
    "MotorForceCommand",
    "PdAttitudeController",
    "QuadXMixer",
    "SimulatedEscSink",
    "SimulatedImuHal",
    "ToyQuadAttitudePlant",
    "encode_motor_forces",
    "hover_collective",
    "level_setpoint",
    "read_attitude",
    "read_filtered",
    "tilt_angle_rad",
]
