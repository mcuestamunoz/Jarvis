"""Fase C · C38 (`B1-fase-c-altitude-loop`) — `AltitudeSample` +
`SimulatedAltitudeHal`: a deterministic, caller-attitude-driven simulated
altitude sensor.

Python scaffold / sim only — production flight_control runtime is C++
(future IC). No real MCU/I2C/SPI baro or ToF driver, no claim that a
height sensor chip is present anywhere in this repo. `read_altitude(...)`
never touches a bus, a socket, or any hardware.

**Direct altitude port, not a meteorology model (IC §0 decision 4):**
this HAL emits `altitude_m` **directly** from the caller-supplied true
height — it does not model barometric pressure, an ISA lapse-rate
table, or a ToF beam. This is a *shape*-only stand-in for "some sensor
eventually reports height" — a real baro/ToF driver, whichever this
desk ends up with, is a separate, future, explicitly-scoped Buy.

**Not plant-owning (same pattern as `SimulatedMagHal`, C37) — read
before using this class:** `read_altitude` takes the **true** `z` (ENU
Up, metres) as a required, caller-supplied argument — this HAL never
owns or secretly consults a plant. Tests and smokes pass in whatever
height they want (a plant's own `true_position_m[2]`, or a synthetic
value built by hand).

**Noise:** off by default, matching this Buy's own sibling sensors
(`SimulatedImuHal` aside — C3's own noise is a documented exception;
`SimulatedMagHal`, C37, is noise-off by default and this HAL follows
that, more recent convention). Deterministic — same true `z` in, same
`AltitudeSample` out, every call.

Sim altitude != live baro/ToF chip. Nothing in this module reads a real
sensor.
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict


class AltitudeSample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    t_s: float
    altitude_m: float


class SimulatedAltitudeHal:
    """Stateless — `read_altitude` is a pure pass-through of the
    caller-supplied true height, never a claim about any real sensor's
    own noise/bias/lag characteristics."""

    def read_altitude(self, true_z_m: float, t_s: float = 0.0) -> AltitudeSample:
        if not math.isfinite(true_z_m):
            raise ValueError("true_z_m must be finite")
        return AltitudeSample(t_s=t_s, altitude_m=true_z_m)
