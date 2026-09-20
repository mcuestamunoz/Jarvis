"""Fase C · C9 — `QuadXMixer`: the fifth `flight_control` rung (motor
allocation, after C3 sampling, C6 filtering, C7 estimation, and C8
control).

Python scaffold / sim only — production flight_control runtime is C++
(future IC). Consumes a **collective thrust** number (how hard to push
"up") and a C8 `BodyRateCommand` (how to roll/pitch/yaw) and emits a
`MotorForceCommand` — **four normalized force numbers**, nothing else.
Given "reparte el empuje entre las 4 hélices," this rung answers "estas
son las cuatro fuerzas de motor que lo harían" — it does not answer
"así es como enciendo un ESC."

**Hard cut (C9 IC §0 decision 7) — all of the following are explicitly
out of scope and absent from this module:**
- no PWM microseconds, no DShot, no ESC UART, no GPIO
- no claim that hardware is armed or that motors spin

**Exactly one airframe layout — quadrotor X** (C9 IC §0 decision 4). A
`+`/H/Y6/octo mixing matrix "to compare" is forbidden in this Buy.

**Motor order and geometry (locked, documented here per §0 decision 5):**
motors are indexed `0..3` around a symmetric X frame, 45° off the body
X/Y axes:

```text
        body +X (forward)
             │
  m1 (FL) \  │  / m0 (FR)
           \ │ /
  ───────────┼───────────  body +Y (right)
           / │ \
  m2 (RL) /  │  \ m3 (RR)
             │
```

- `m0` = Front-Right (FR)
- `m1` = Front-Left (FL)
- `m2` = Rear-Left (RL)
- `m3` = Rear-Right (RR)

**Allocation (per §0 decision 6, honesty-critical):** `BodyRateCommand`
(C8) outputs **body rates**, not true body torques — a production stack
usually inserts a rate→torque loop (a rate controller/ESC current model)
between them. This B1 mixer treats `omega_body_rad_s` directly as
`(roll, pitch, yaw)` **mix channels** (torque-like inputs) purely to
teach allocation geometry. It does **not** claim rate is physically
equivalent to torque, and it does **not** invent a second controller to
bridge that gap — that bridge is a later, separate IC.

```text
m0 (FR) = collective - roll_scale*roll + pitch_scale*pitch - yaw_scale*yaw
m1 (FL) = collective + roll_scale*roll + pitch_scale*pitch + yaw_scale*yaw
m2 (RL) = collective + roll_scale*roll - pitch_scale*pitch - yaw_scale*yaw
m3 (RR) = collective - roll_scale*roll - pitch_scale*pitch + yaw_scale*yaw
```

each then clamped to `[0, 1]` (per §0 decision 8 — dimensionless,
normalized motor force commands; `collective` is likewise clamped to
`[0, 1]` before mixing, not rejected).

No `set_pwm`/`write_dshot`/`arm`/`disarm`/`command_esc`/`open_serial`
anywhere in this module — this is allocation arithmetic only, never
actuation.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from jarvis.flight_software.flight_control.controller import BodyRateCommand

_DEFAULT_ROLL_SCALE = 0.05
_DEFAULT_PITCH_SCALE = 0.05
_DEFAULT_YAW_SCALE = 0.05

MotorForces = tuple[float, float, float, float]


class MotorForceCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    t_s: float
    motor_forces: MotorForces
    layout: Literal["quad_x"] = "quad_x"
    notes: str | None = None

    @field_validator("motor_forces")
    @classmethod
    def _finite_forces(cls, value: MotorForces) -> MotorForces:
        if len(value) != 4:
            raise ValueError("motor_forces must have exactly 4 entries")
        if not all(math.isfinite(component) for component in value):
            raise ValueError("motor_forces must be finite")
        return value


class QuadXMixer:
    """Fixed linear allocation for a quadrotor X frame — see this
    module's own docstring for motor order and the mix formula. `roll_scale`,
    `pitch_scale`, `yaw_scale` must each be finite and `>= 0`; a `0`
    disables that channel's contribution."""

    def __init__(
        self,
        roll_scale: float = _DEFAULT_ROLL_SCALE,
        pitch_scale: float = _DEFAULT_PITCH_SCALE,
        yaw_scale: float = _DEFAULT_YAW_SCALE,
    ) -> None:
        for name, value in (
            ("roll_scale", roll_scale),
            ("pitch_scale", pitch_scale),
            ("yaw_scale", yaw_scale),
        ):
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and >= 0")
        self._roll_scale = roll_scale
        self._pitch_scale = pitch_scale
        self._yaw_scale = yaw_scale

    def mix(self, collective: float, rates: BodyRateCommand) -> MotorForceCommand:
        collective_clamped = _clamp01(collective)
        roll, pitch, yaw = rates.omega_body_rad_s

        raw = (
            collective_clamped - self._roll_scale * roll + self._pitch_scale * pitch - self._yaw_scale * yaw,
            collective_clamped + self._roll_scale * roll + self._pitch_scale * pitch + self._yaw_scale * yaw,
            collective_clamped + self._roll_scale * roll - self._pitch_scale * pitch - self._yaw_scale * yaw,
            collective_clamped - self._roll_scale * roll - self._pitch_scale * pitch + self._yaw_scale * yaw,
        )
        forces = tuple(_clamp01(value) for value in raw)

        return MotorForceCommand(t_s=rates.t_s, motor_forces=forces, layout="quad_x")


def hover_collective(default: float = 0.5) -> float:
    """For tests/smoke only — a symbolic mid-range collective value, not a
    claim about real hover thrust for any vehicle."""
    return default


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
