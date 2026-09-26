"""Fase C · C37 (`B1-fase-c-mag-yaw-rung`) — `MagSample`: the one new
data type this Buy adds, mirroring `types.py`'s own `ImuSample` shape.

Python scaffold / sim only — production flight_control runtime is C++
(future IC). A body-frame magnetometer reading. `mag_body_uT` is toy µT
numbers (see `sim_mag_hal.py`'s own documented world-field default) —
never a datasheet claim about any real magnetometer chip. No actuator
field, matching every other sensing-only rung (C3's `ImuSample`
included) — this is sensing only, never actuation.

Kept in its own file rather than added to `types.py`, since that
module's own docstring locks its scope to "the only data type in the
first `flight_control` rung" (C3) — `MagSample` is a new, separate rung
concern, not an extension of C3's own boundary.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from jarvis.flight_software.flight_control.types import Vec3


class MagSample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    t_s: float
    mag_body_uT: Vec3
