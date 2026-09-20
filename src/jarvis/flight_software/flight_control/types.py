"""Fase C · C3 — the only data type in the first `flight_control` rung.

`ImuSample` is a pure sensing record. There is no actuator field here, and
none may be added to this rung — filtering, state estimation, attitude/
rate/position control, mixer, and ESC/PWM are all out of scope until their
own future Implementation Contracts (see the C3 IC §0 decision 3).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

Vec3 = tuple[float, float, float]


class ImuSample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    t_s: float
    accel_mps2: Vec3
    gyro_rad_s: Vec3
