"""Fase C · C7 — `ComplementaryAttitudeEstimator`: the third `flight_control`
rung (state estimation, after C3 sampling and C6 filtering).

Python scaffold / sim only — production flight_control runtime is C++
(future IC). Consumes **filtered** `ImuSample` values (C6) and emits a
typed `AttitudeState`: orientation quaternion + body angular rate. This
is a **single, minimal, gravity-referenced complementary filter** — NOT
Mahony's published algorithm (no integral/bias state, no adaptive gain),
NOT Madgwick (no gradient-descent objective function), and NOT an
EKF/UKF/MEKF (no covariance propagation, no Kalman gain). Exactly one
algorithm ships in this Buy; a second estimator "to compare" is
forbidden (C7 IC §0 decision 4).

**Hard cut (C7 IC §0 decision 5) — all of the following were explicitly
out of scope and absent from this module as shipped in C7:**
- no magnetometer fusion (yaw was therefore only ever gyro-integrated —
  there was no absolute heading reference; this estimator did not claim
  one). **Superseded by C37, disclosed below** — this is now an
  *optional* correction, off by default (`mag=None`), never silently
  substituted for the gyro-only path C7 shipped.
- no GPS/baro fusion — **still true**, untouched by C37
- no online gyro-bias estimation/learning — **still true**, untouched by C37
- no world-frame velocity or position output — **still true**, untouched by C37

**Frame convention (C7 IC §0 decision 6, locked):** the IMU sample is in
the vehicle **body frame**. `AttitudeState.q_body_to_world` is a unit
quaternion `(w, x, y, z)` mapping body-frame vectors into a **world
frame fixed to `"enu"`** (East-North-Up; gravity is `(0, 0, -g)` in this
frame — matching `SimulatedImuHal`'s own gravity convention). `frame` is
always `"enu"` in C7.

**Known simulator limitation (honesty note):** `SimulatedImuHal` (C3) is
not attitude-aware — it always emits a fixed-direction gravity vector
regardless of any "true" vehicle orientation, since C3 never models
orientation at all. This estimator's correctness is therefore validated
directly against synthetic in-memory `ImuSample` sequences with known
tilts in this Buy's tests, not solely via the shared sim HAL (which will
always look "level" by construction — see the C7 implementation report).

No actuator field, no `write_motor`/`mix`/`set_pwm`, anywhere in this
module — this is sensing/state output only, never actuation.

**Fase C · C37 (`B1-fase-c-mag-yaw-rung`) — optional mag yaw correction
added below.** The C7 hard cut above ("no magnetometer fusion") is
**superseded, disclosed**: `update(sample, mag=None)` now accepts an
**optional** `MagSample` (see `mag.py`). When `mag is None` — the
default, and the only path C7's own tests ever exercised — behavior is
**byte-for-byte identical** to before this Buy (verified by re-running
every pre-existing C7 test unchanged). This stays **one** complementary-
style estimator, not a second AHRS "to compare" (still not Mahony,
Madgwick, or an EKF/UKF by name) — the mag path is one more small-angle
proportional correction, same shape as the existing accel-tilt
correction, just about a different axis.

**Mag yaw correction (documented, locked):** when `mag` is provided, the
tilt-corrected estimate `q_new` (from the accel branch above, computed
first and unchanged) rotates the measured body-frame mag vector into
world frame, projects it onto the horizontal plane (drops the world `Z`/
Up component — only the horizontal component carries a heading
reference), and compares that against `_WORLD_MAG_NORTH_ENU` — this
module's own documented world-north reference, `(0.0, 1.0, 0.0)` (East
`0`, North `1.0`, Up `0.0`), matching `sim_mag_hal.py`'s own default
`WORLD_MAG_FIELD_ENU` by convention (independently defined here, not
imported — same pattern this codebase already uses for the shared
gravity constant across `plant.py`/`attitude.py`/`sim_imu_hal.py`, never
via cross-module import). The correction is a **world-frame** rotation
(unlike the accel correction, which is body-frame) — it is therefore
composed on the **left** of `q_new` (`q_corrected = R * q_new`), not the
right — see the inline derivation comment in `update()` for why. Still
**no GPS/baro fusion, no online gyro-bias estimation, no world-frame
velocity/position output** — those hard cuts remain exactly as they
were.

Sim mag != live mag chip != ICM SPI mag. Nothing in this module reads a
real sensor, and nothing here claims heading-hold on real hardware.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict

from jarvis.flight_software.flight_control.filter import ImuLowPassFilter
from jarvis.flight_software.flight_control.hal import ImuHal
from jarvis.flight_software.flight_control.mag import MagSample
from jarvis.flight_software.flight_control.types import ImuSample, Vec3

Quat = tuple[float, float, float, float]

_DEFAULT_GAIN = 0.02
_DEFAULT_MAG_GAIN = 0.02
_IDENTITY_QUAT: Quat = (1.0, 0.0, 0.0, 0.0)
_WORLD_DOWN_ENU: Vec3 = (0.0, 0.0, -1.0)
# C37 — this estimator's own documented world-north reference, already
# horizontal (Up=0) by convention; matches sim_mag_hal.py's own default
# WORLD_MAG_FIELD_ENU (independently defined, not imported — see the
# module docstring above for why).
_WORLD_MAG_NORTH_ENU: Vec3 = (0.0, 1.0, 0.0)


class AttitudeState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    t_s: float
    q_body_to_world: Quat
    omega_body_rad_s: Vec3
    frame: Literal["enu"] = "enu"


class ComplementaryAttitudeEstimator:
    """Gyro integration fused with accel-derived tilt via a small-angle
    proportional correction. `gain` must be in `(0, 1]`. `update(sample)`
    should be called with a **filtered** `ImuSample` (C6) — it will still
    accept a raw one for unit tests, but the shipped smoke path always
    pipes through `ImuLowPassFilter` first."""

    def __init__(
        self,
        gain: float = _DEFAULT_GAIN,
        initial_q: Quat = _IDENTITY_QUAT,
        mag_gain: float = _DEFAULT_MAG_GAIN,
    ) -> None:
        if not (0.0 < gain <= 1.0):
            raise ValueError("gain must be in (0, 1]")
        if not (0.0 < mag_gain <= 1.0):
            raise ValueError("mag_gain must be in (0, 1]")
        self._gain = gain
        self._mag_gain = mag_gain
        self._initial_q = _quat_normalize(initial_q)
        self._q: Quat | None = None
        self._last_t_s: float | None = None

    def reset(self) -> None:
        """Clears internal state — the next sample seeds the estimator at
        `initial_q` (identity/level by default)."""
        self._q = None
        self._last_t_s = None

    def update(self, sample: ImuSample, mag: MagSample | None = None) -> AttitudeState:
        omega = sample.gyro_rad_s

        if self._q is None:
            self._q = self._initial_q
            self._last_t_s = sample.t_s
            return AttitudeState(
                t_s=sample.t_s, q_body_to_world=self._q, omega_body_rad_s=omega, frame="enu"
            )

        dt = sample.t_s - self._last_t_s
        self._last_t_s = sample.t_s
        if dt <= 0.0:
            return AttitudeState(
                t_s=sample.t_s, q_body_to_world=self._q, omega_body_rad_s=omega, frame="enu"
            )

        axis_angle = (omega[0] * dt, omega[1] * dt, omega[2] * dt)
        q_pred = _quat_normalize(_quat_multiply(self._q, _quat_from_small_angle(axis_angle)))

        accel_dir = _vec_normalize(sample.accel_mps2)
        if accel_dir is None:
            q_new = q_pred
        else:
            predicted_down_body = _rotate_vector(_quat_conjugate(q_pred), _WORLD_DOWN_ENU)
            # Cross product is anti-commutative: this argument order (measured,
            # predicted) is the one that yields a correction pulling predicted_down_body
            # toward accel_dir; the reversed order silently converges away from it.
            error = _cross(accel_dir, predicted_down_body)
            correction = (self._gain * error[0], self._gain * error[1], self._gain * error[2])
            q_new = _quat_normalize(_quat_multiply(q_pred, _quat_from_small_angle(correction)))

        if mag is not None:
            # C37 — optional yaw correction. Rotate the measured body mag
            # vector into world frame using the tilt-corrected estimate
            # (q_new above, roll/pitch already trusted), then keep only
            # the horizontal component — only that carries a heading
            # reference; the vertical component is discarded, never
            # coupled back into roll/pitch.
            world_mag = _rotate_vector(q_new, mag.mag_body_uT)
            measured_horizontal = _vec_normalize((world_mag[0], world_mag[1], 0.0))
            if measured_horizontal is not None:
                # Cross product is anti-commutative: this order (measured,
                # reference) yields a correction that rotates the measured
                # horizontal heading toward _WORLD_MAG_NORTH_ENU — mirrors
                # the accel branch's own (measured, predicted) convention
                # above. Both operands are horizontal (Up=0), so the
                # result is purely a Z-axis (yaw) rotation by construction
                # — no manual projection needed.
                yaw_error = _cross(measured_horizontal, _WORLD_MAG_NORTH_ENU)
                yaw_correction = (
                    self._mag_gain * yaw_error[0],
                    self._mag_gain * yaw_error[1],
                    self._mag_gain * yaw_error[2],
                )
                # World-frame correction: composed on the LEFT of q_new
                # (q represents body->world; rotating world-frame vectors
                # by R means q_corrected = R * q, not q * R — the reverse
                # of the accel branch's own body-frame correction above).
                q_new = _quat_normalize(_quat_multiply(_quat_from_small_angle(yaw_correction), q_new))

        self._q = q_new
        return AttitudeState(t_s=sample.t_s, q_body_to_world=q_new, omega_body_rad_s=omega, frame="enu")


def read_attitude(
    hal: ImuHal, filt: ImuLowPassFilter, estimator: ComplementaryAttitudeEstimator
) -> AttitudeState:
    """`filtered = filt.filter_sample(hal.read_imu()); return
    estimator.update(filtered)` — pure pipeline helper, no Safety call,
    no actuator touched."""
    filtered = filt.filter_sample(hal.read_imu())
    return estimator.update(filtered)


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


def _vec_normalize(v: Vec3) -> Vec3 | None:
    norm = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if norm < 1e-9:
        return None
    return (v[0] / norm, v[1] / norm, v[2] / norm)


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )
