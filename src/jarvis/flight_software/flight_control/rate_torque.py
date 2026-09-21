"""Fase C · C12 — rate→torque honesty bridge (`B1-fase-c-rate-torque-bridge`).

Python scaffold / sim only — production flight_control runtime is C++
(future IC). Closes the C9 honesty gap documented since `v0.5.7`:
`QuadXMixer` no longer consumes a C8 `BodyRateCommand` (rad/s) directly
as if it were a torque. This module names that conversion explicitly —
`LinearRateTorqueBridge.convert(rates) -> BodyTorqueCommand` — a single
feedforward map, `tau_i = gain_i * omega_cmd_i` per axis.

**Exactly one bridge law (locked, C12 IC §0 decision 4):** feedforward
only. This is **not** a cascaded rate PID — there is no
`kp * (omega_cmd - omega_measured)` term, no integral or derivative
state, no measured-rate feedback anywhere in this module. (C8's
`PdAttitudeController` already accounts for measured rate via its own
`kd` term, upstream of this bridge.) Not LQR, not INDI, not a second
attitude controller.

**Units honesty (locked, C12 IC §0 decision 5):**
`BodyTorqueCommand.tau_body` is a **normalized, dimensionless,
torque-like mix command** for this Buy — it is **not** claimed as
Newton-metres of any real vehicle, and no inertia model or unit
conversion exists anywhere in this module.

No `rate_pid_step`, no `compute_inertia_torque_nm` presented as product
truth, no `write_gpio`, no cascaded "inner rate loop" class — this is a
single linear feedforward map, never actuation.
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, field_validator

from jarvis.flight_software.flight_control.controller import BodyRateCommand
from jarvis.flight_software.flight_control.types import Vec3

_DEFAULT_GAIN = 1.0


class BodyTorqueCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    t_s: float
    tau_body: Vec3
    notes: str | None = None

    @field_validator("tau_body")
    @classmethod
    def _finite_tau(cls, value: Vec3) -> Vec3:
        if not all(math.isfinite(component) for component in value):
            raise ValueError("tau_body must be finite")
        return value


class LinearRateTorqueBridge:
    """`tau_i = gain_i * omega_cmd_i` per axis. Pass either a single
    scalar `gain` (applied to all three axes) or a per-axis `gains`
    3-tuple — not both. Every resolved gain must be finite and `> 0`."""

    def __init__(
        self,
        gain: float | None = None,
        gains: Vec3 | None = None,
    ) -> None:
        if gain is not None and gains is not None:
            raise ValueError("pass either gain or gains, not both")
        if gains is not None:
            resolved: Vec3 = gains
        else:
            scalar = gain if gain is not None else _DEFAULT_GAIN
            resolved = (scalar, scalar, scalar)
        for value in resolved:
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError("gains must each be finite and > 0")
        self._gains = resolved

    def convert(self, rates: BodyRateCommand) -> BodyTorqueCommand:
        gx, gy, gz = self._gains
        wx, wy, wz = rates.omega_body_rad_s
        return BodyTorqueCommand(t_s=rates.t_s, tau_body=(gx * wx, gy * wy, gz * wz))
