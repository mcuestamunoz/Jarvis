"""Fase C · C8 — `PdAttitudeController`: the fourth `flight_control` rung
(attitude control, after C3 sampling, C6 filtering, and C7 estimation).

Python scaffold / sim only — production flight_control runtime is C++
(future IC). Consumes an `AttitudeSetpoint` (desired orientation) and a
C7 `AttitudeState` (estimated orientation + body rate) and emits a
`BodyRateCommand` — a **single PD controller**, nothing else. Given
"quiero estar nivelado / inclinado así," this rung answers "estas son
las velocidades de giro en el cuerpo que lo lograrían" — it does not
answer "así es como muevo los motores."

**Hard cut (C8 IC §0 decision 5) — all of the following are explicitly
out of scope and absent from this module:**
- no motor thrusts, no mixer matrix, no PWM/ESC output
- no collective-thrust channel (hover thrust is a mixer-stage concern,
  not this rung's)
- no position or velocity control loop

**Exactly one controller** — a proportional-derivative (PD) law on the
small-angle orientation error, damped by the estimated body rate. A
cascaded rate PID, LQR, MPC, INDI, or a second controller "to compare"
are all forbidden in this Buy (C8 IC §0 decision 4).

**Frame convention (C8 IC §0 decision 7):** `AttitudeSetpoint` and
`AttitudeState` share the same `"enu"` world frame as C7.
`BodyRateCommand.omega_body_rad_s` is expressed in the **body** frame,
matching `AttitudeState.omega_body_rad_s`'s own convention.

**Not wired to C4 autonomy:** `AutonomyVerb.HOLD` is never auto-routed
into this controller — C4 stays Safety-gated and non-executing, and
this rung never calls `submit_command`. Computing a rate command is
sensing/state math, not actuation: no Safety `allow` is required, and
there is no actuator to write to.

No `mix`/`allocate`/`set_pwm`/`write_motor`/`command_esc`/
`compute_thrusts`, anywhere in this module.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from jarvis.flight_software.flight_control.attitude import AttitudeState, Quat
from jarvis.flight_software.flight_control.types import Vec3

_DEFAULT_KP = 6.0
_DEFAULT_KD = 0.6
_IDENTITY_QUAT: Quat = (1.0, 0.0, 0.0, 0.0)


class AttitudeSetpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    t_s: float
    q_body_to_world_desired: Quat
    frame: Literal["enu"] = "enu"


class BodyRateCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    t_s: float
    omega_body_rad_s: Vec3
    notes: str | None = None

    @field_validator("omega_body_rad_s")
    @classmethod
    def _finite_rate(cls, value: Vec3) -> Vec3:
        if not all(math.isfinite(component) for component in value):
            raise ValueError("omega_body_rad_s must be finite")
        return value


class PdAttitudeController:
    """`omega_cmd = kp * e_rot - kd * omega_measured`, where `e_rot` is the
    body-frame small-angle rotation vector from the estimated orientation
    toward the desired one (twice the vector part of the shortest-path
    error quaternion `conj(q_estimated) ⊗ q_desired`), and
    `omega_measured` is `AttitudeState.omega_body_rad_s`. `kp` must be
    `> 0`; `kd` must be `>= 0`; both must be finite. No internal D-filter
    state is kept (per IC §2.3's "prefer none") — `reset()` is a no-op
    kept only for API symmetry with the other `flight_control` rungs."""

    def __init__(self, kp: float = _DEFAULT_KP, kd: float = _DEFAULT_KD) -> None:
        if not math.isfinite(kp) or kp <= 0.0:
            raise ValueError("kp must be finite and > 0")
        if not math.isfinite(kd) or kd < 0.0:
            raise ValueError("kd must be finite and >= 0")
        self._kp = kp
        self._kd = kd

    def reset(self) -> None:
        """No-op — this controller carries no internal state to clear."""
        return None

    def compute(self, setpoint: AttitudeSetpoint, state: AttitudeState) -> BodyRateCommand:
        q_err = _shortest_error_quat(
            _quat_multiply(_quat_conjugate(state.q_body_to_world), setpoint.q_body_to_world_desired)
        )
        e_rot = (2.0 * q_err[1], 2.0 * q_err[2], 2.0 * q_err[3])
        omega_measured = state.omega_body_rad_s
        omega_cmd = (
            self._kp * e_rot[0] - self._kd * omega_measured[0],
            self._kp * e_rot[1] - self._kd * omega_measured[1],
            self._kp * e_rot[2] - self._kd * omega_measured[2],
        )
        return BodyRateCommand(t_s=state.t_s, omega_body_rad_s=omega_cmd)


def level_setpoint(t_s: float) -> AttitudeSetpoint:
    """Identity quaternion — level hover attitude in `enu`. For tests and
    smoke only; not a claim about hover thrust or any physical setpoint."""
    return AttitudeSetpoint(t_s=t_s, q_body_to_world_desired=_IDENTITY_QUAT)


def _quat_multiply(a: Quat, b: Quat) -> Quat:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    )


def _quat_conjugate(q: Quat) -> Quat:
    w, x, y, z = q
    return (w, -x, -y, -z)


def _shortest_error_quat(q_err: Quat) -> Quat:
    """Unit quaternions `q` and `-q` represent the same rotation; picking
    the sign with `w >= 0` always yields the shorter-path rotation vector
    when extracting the small-angle error below."""
    if q_err[0] < 0.0:
        return (-q_err[0], -q_err[1], -q_err[2], -q_err[3])
    return q_err
