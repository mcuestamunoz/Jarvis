"""Fase C · C37 (`B1-fase-c-mag-yaw-rung`) — `SimulatedMagHal`: a
deterministic, caller-attitude-driven simulated magnetometer.

Python scaffold / sim only — production flight_control runtime is C++
(future IC). No real MCU/I2C/SPI driver, no claim that a magnetometer
chip is present anywhere in this repo. `read_mag(...)` never touches a
bus, a socket, or any hardware.

**Not attitude-owning (IC §0 decision 5, locked) — read before using
this class:** unlike `SimulatedImuHal` (C3), which is deliberately NOT
attitude-aware (see `attitude.py`'s own honesty note — it always emits a
fixed-direction reading regardless of any "true" orientation), this
class *is* attitude-aware, but it never owns or secretly consults a
plant to get that attitude. `read_mag` takes the **true**
`q_body_to_world` as a required, caller-supplied argument — tests and
smokes pass in whatever attitude they want (a plant's own
`true_attitude.q_body_to_world`, or a synthetic quaternion built by
hand). This HAL is a pure rotation of a fixed world field into body
frame, nothing else.

**World field (documented toy default, decision 4/5 — not a datasheet
claim):** `WORLD_MAG_FIELD_ENU = (0.0, 1.0, 0.0)` — East `0`, North
`1.0` (a toy unit magnitude, not µT-calibrated to any real location),
Up `0.0`. Real Earth field has significant vertical inclination at most
latitudes; this Buy's own yaw correction only ever needs the horizontal
component (see `attitude.py`'s own C37 extension), so a nonzero Up
component would add nothing here and would invite a false precision
claim — deliberately omitted, not an oversight.

**Noise (decision 5):** off by default, matching the IC's own
"Optional noise = off by default." Deterministic — same true attitude
in, same `MagSample` out, every call.

Sim mag != live mag chip != ICM SPI mag. Nothing in this module reads a
real sensor.
"""

from __future__ import annotations

import math

from jarvis.flight_software.flight_control.mag import MagSample
from jarvis.flight_software.flight_control.types import Vec3

Quat = tuple[float, float, float, float]

WORLD_MAG_FIELD_ENU: Vec3 = (0.0, 1.0, 0.0)


class SimulatedMagHal:
    """`world_field_enu` (finite, nonzero) is the fixed toy world field —
    `read_mag` rotates it into the body frame using the caller-supplied
    true `q_body_to_world`, via the inverse (conjugate) rotation, same
    convention `ToyQuadAttitudePlant.sense()` already uses for gravity."""

    def __init__(self, world_field_enu: Vec3 = WORLD_MAG_FIELD_ENU) -> None:
        if not all(math.isfinite(c) for c in world_field_enu):
            raise ValueError("world_field_enu must be finite")
        norm = math.sqrt(sum(c * c for c in world_field_enu))
        if norm < 1e-9:
            raise ValueError("world_field_enu must be nonzero")
        self._world_field_enu = world_field_enu

    def read_mag(self, true_q_body_to_world: Quat, t_s: float = 0.0) -> MagSample:
        body_field = _rotate_vector(_quat_conjugate(true_q_body_to_world), self._world_field_enu)
        return MagSample(t_s=t_s, mag_body_uT=body_field)


def _quat_conjugate(q: Quat) -> Quat:
    w, x, y, z = q
    return (w, -x, -y, -z)


def _quat_multiply(a: Quat, b: Quat) -> Quat:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    )


def _rotate_vector(q: Quat, v: Vec3) -> Vec3:
    qv: Quat = (0.0, v[0], v[1], v[2])
    result = _quat_multiply(_quat_multiply(q, qv), _quat_conjugate(q))
    return (result[1], result[2], result[3])
