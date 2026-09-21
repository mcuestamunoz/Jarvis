"""Fase C · C11 — `ToyQuadAttitudePlant`: the C0 §7 wooden-ladder **tip**
(closing the sim loop, after C3 sampling, C6 filtering, C7 estimation, C8
control, C9 mixing, and C10 PWM encoding).

Python scaffold / sim only — production flight_control runtime is C++
(future IC). This module lets the existing C3→C10 pipeline run as a
**closed loop**: the plant advances a toy attitude from `MotorForceCommand`
(C9 forces), and emits the next `ImuSample` **consistent with its own true
attitude** — fixing, for this closed-loop tip only, C7's documented
"`SimulatedImuHal` is not attitude-aware" limitation. `SimulatedImuHal`
itself is untouched; C3's existing tests and smoke stay exactly as they
were.

**This is a toy, explicitly not product flight physics (C11 IC §0 decision
5):** `ToyQuadAttitudePlant` tracks **attitude only** — quaternion + body
angular rate — no position, no velocity, no real aerodynamics, no motor
thrust curve, no vehicle mass/inertia sourced from any real hardware. Its
"torque" response to motor forces is a single toy linear map
(`torque_gain`) plus toy passive angular damping (`angular_damping`),
chosen only to make the closed loop demonstrably converge — never
presented as a CFD/aero solver or as truth about any real vehicle.

**Rate ≠ torque — this honesty gap remains open (C11 IC §0 decision 7):**
C9's `QuadXMixer` still treats `BodyRateCommand.omega_body_rad_s` (a rate)
directly as its roll/pitch/yaw mix channels, without claiming rate is
physically equivalent to torque. This plant does **not** silently insert
a rate→torque controller to "fix" that for realism — its own toy
force→angular-acceleration map is a separate, equally-toy simplification,
documented here, not a physics correction. A real rate→torque bridge
remains a future, separate Buy if ever prioritized.

**Motor→torque-proxy signs (documented, matches C9's own X-geometry):**
given `MotorForceCommand.motor_forces = (m0, m1, m2, m3)` = `(FR, FL, RL,
RR)` per `mixer.py`'s own docstring, this plant computes:

```text
roll_proxy  = (m1 + m2) - (m0 + m3)   # (FL+RL) - (FR+RR)
pitch_proxy = (m0 + m1) - (m2 + m3)   # (FR+FL) - (RL+RR)
yaw_proxy   = (m1 + m3) - (m0 + m2)   # (FL+RR) - (FR+RL)
```

These are the algebraic inverse of `QuadXMixer.mix`'s own forward
formulas (by construction of that linear system) — not a new physics
claim, just the geometric counterpart of the same documented X layout.

No `write_gpio`/`open_serial`/`send_dshot`/`fly`/`arm_motors_hardware`
anywhere in this module — this is toy attitude-only integration, never
actuation, and never a claim that any real vehicle is airborne.
"""

from __future__ import annotations

import math

from jarvis.flight_software.flight_control.attitude import AttitudeState, Quat
from jarvis.flight_software.flight_control.mixer import MotorForceCommand
from jarvis.flight_software.flight_control.types import ImuSample, Vec3

_DEFAULT_TORQUE_GAIN = 40.0
_DEFAULT_ANGULAR_DAMPING = 0.5
_GRAVITY_MPS2 = 9.81
_IDENTITY_QUAT: Quat = (1.0, 0.0, 0.0, 0.0)
_ZERO_VEC3: Vec3 = (0.0, 0.0, 0.0)
_WORLD_GRAVITY_ENU: Vec3 = (0.0, 0.0, -_GRAVITY_MPS2)


class ToyQuadAttitudePlant:
    """Toy, attitude-only rigid-body-ish dynamics. `torque_gain` (must be
    finite and `> 0`) scales the motor-force differential proxies into a
    toy angular acceleration; `angular_damping` (must be finite and `>= 0`)
    is a toy passive damping term. Deterministic — no noise added, unlike
    `SimulatedImuHal` (C3), which is intentional: this tip's pass
    criterion is about closed-loop convergence, not sensor realism."""

    def __init__(
        self,
        torque_gain: float = _DEFAULT_TORQUE_GAIN,
        angular_damping: float = _DEFAULT_ANGULAR_DAMPING,
    ) -> None:
        if not math.isfinite(torque_gain) or torque_gain <= 0.0:
            raise ValueError("torque_gain must be finite and > 0")
        if not math.isfinite(angular_damping) or angular_damping < 0.0:
            raise ValueError("angular_damping must be finite and >= 0")
        self._torque_gain = torque_gain
        self._angular_damping = angular_damping
        self._q: Quat = _IDENTITY_QUAT
        self._omega: Vec3 = _ZERO_VEC3
        self._t_s = 0.0

    def reset(self, initial_q: Quat = _IDENTITY_QUAT, initial_omega: Vec3 = _ZERO_VEC3) -> None:
        self._q = _quat_normalize(initial_q)
        self._omega = initial_omega
        self._t_s = 0.0

    @property
    def true_attitude(self) -> AttitudeState:
        """The plant's own true state — never an estimate. Tests use this
        to check closed-loop convergence honestly, independent of
        whatever C7's estimator currently believes."""
        return AttitudeState(
            t_s=self._t_s, q_body_to_world=self._q, omega_body_rad_s=self._omega, frame="enu"
        )

    def sense(self) -> ImuSample:
        """Reads the current true state as an `ImuSample` **without**
        advancing dynamics — used to seed a closed loop before any forces
        have been computed yet."""
        return ImuSample(
            t_s=self._t_s,
            accel_mps2=_rotate_vector(_quat_conjugate(self._q), _WORLD_GRAVITY_ENU),
            gyro_rad_s=self._omega,
        )

    def step(self, forces: MotorForceCommand, *, dt_s: float) -> ImuSample:
        if not math.isfinite(dt_s) or dt_s <= 0.0:
            raise ValueError("dt_s must be finite and > 0")

        fr, fl, rl, rr = forces.motor_forces
        roll_proxy = (fl + rl) - (fr + rr)
        pitch_proxy = (fr + fl) - (rl + rr)
        yaw_proxy = (fl + rr) - (fr + rl)

        angular_accel = (
            self._torque_gain * roll_proxy - self._angular_damping * self._omega[0],
            self._torque_gain * pitch_proxy - self._angular_damping * self._omega[1],
            self._torque_gain * yaw_proxy - self._angular_damping * self._omega[2],
        )

        new_omega = (
            self._omega[0] + angular_accel[0] * dt_s,
            self._omega[1] + angular_accel[1] * dt_s,
            self._omega[2] + angular_accel[2] * dt_s,
        )
        axis_angle = (new_omega[0] * dt_s, new_omega[1] * dt_s, new_omega[2] * dt_s)
        new_q = _quat_normalize(_quat_multiply(self._q, _quat_from_small_angle(axis_angle)))

        self._omega = new_omega
        self._q = new_q
        self._t_s += dt_s

        return ImuSample(
            t_s=self._t_s,
            accel_mps2=_rotate_vector(_quat_conjugate(new_q), _WORLD_GRAVITY_ENU),
            gyro_rad_s=new_omega,
        )


def tilt_angle_rad(q: Quat) -> float:
    """Angle (radians, always `>= 0`) between `q` and the identity/level
    orientation — `2 * acos(|w|)`. Used to measure closed-loop
    convergence against the plant's own **true** attitude, never against
    the estimator's belief (which may still be settling)."""
    w = max(-1.0, min(1.0, q[0]))
    return 2.0 * math.acos(abs(w))


def _quat_normalize(q: Quat) -> Quat:
    w, x, y, z = q
    norm = math.sqrt(w * w + x * x + y * y + z * z)
    if norm < 1e-12:
        return _IDENTITY_QUAT
    return (w / norm, x / norm, y / norm, z / norm)


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


def _quat_from_small_angle(axis_angle: Vec3) -> Quat:
    x, y, z = axis_angle
    return _quat_normalize((1.0, x / 2.0, y / 2.0, z / 2.0))


def _rotate_vector(q: Quat, v: Vec3) -> Vec3:
    qv: Quat = (0.0, v[0], v[1], v[2])
    result = _quat_multiply(_quat_multiply(q, qv), _quat_conjugate(q))
    return (result[1], result[2], result[3])
