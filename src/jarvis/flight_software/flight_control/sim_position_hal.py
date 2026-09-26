"""Fase C · C39 (`B1-fase-c-position-loop`) — `PositionSample` +
`SimulatedPositionHal`: a deterministic, caller-attitude-driven
simulated horizontal position sensor.

Python scaffold / sim only — production flight_control runtime is C++
(future IC). No real GPS/optical-flow driver, no claim that a
positioning chip is present anywhere in this repo. `read_position(...)`
never touches a bus, a socket, or any hardware.

**Direct ENU port, not a GNSS/flow stack (IC §0 decision 4):** this HAL
emits `x_m`/`y_m` (ENU East/North) **directly** from the caller-supplied
true horizontal position — it does not model NMEA sentences, WGS84
geodesy, satellite constellations, or optical-flow image processing.
This is a *shape*-only stand-in for "some sensor eventually reports
horizontal position" — a real GPS/flow driver, whichever this desk ends
up with, is a separate, future, explicitly-scoped Buy.

**Not plant-owning (same pattern as `SimulatedAltitudeHal`, C38, and
`SimulatedMagHal`, C37):** `read_position` takes the **true** `x`/`y`
(ENU East/North, metres) as required, caller-supplied arguments — this
HAL never owns or secretly consults a plant. Tests and smokes pass in
whatever position they want (a plant's own `true_position_m[0:2]`, or a
synthetic value built by hand).

**`z_m` is optional and unused by the controller (IC §0 decision 5):**
`PositionSample` carries an optional `z_m` field for completeness (some
real position sensors report altitude too), but `PositionController`
(`position_controller.py`) never reads it — altitude stays C38's own
`AltitudeController` concern, not duplicated here.

**Noise:** off by default, matching `SimulatedMagHal`/`SimulatedAltitudeHal`.
Deterministic — same true xy in, same `PositionSample` out, every call.

Sim position != live GPS/flow chip. Nothing in this module reads a real
sensor.
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict


class PositionSample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    t_s: float
    x_m: float
    y_m: float
    z_m: float | None = None


class SimulatedPositionHal:
    """Stateless — `read_position` is a pure pass-through of the
    caller-supplied true horizontal position, never a claim about any
    real sensor's own noise/bias/lag characteristics."""

    def read_position(
        self, true_x_m: float, true_y_m: float, t_s: float = 0.0, true_z_m: float | None = None
    ) -> PositionSample:
        if not math.isfinite(true_x_m):
            raise ValueError("true_x_m must be finite")
        if not math.isfinite(true_y_m):
            raise ValueError("true_y_m must be finite")
        if true_z_m is not None and not math.isfinite(true_z_m):
            raise ValueError("true_z_m must be finite")
        return PositionSample(t_s=t_s, x_m=true_x_m, y_m=true_y_m, z_m=true_z_m)
