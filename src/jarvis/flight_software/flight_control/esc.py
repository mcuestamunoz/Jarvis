"""Fase C · C10 — ESC/PWM command encoding stub: the sixth `flight_control`
rung (after C3 sampling, C6 filtering, C7 estimation, C8 control, and C9
mixing).

Python scaffold / sim only — production flight_control runtime is C++
(future IC). Consumes a C9 `MotorForceCommand` (4× `[0,1]`) and produces
an `EscPwmCommand` — **4 PWM pulse widths in microseconds**, encoded with
one documented linear map. `SimulatedEscSink.apply(...)` records that
command **in memory only**. Given "traduce fuerza de motor a la señal
típica que un ESC esperaría," this rung answers "estos son los anchos de
pulso" — it does not answer "y aquí está el pin GPIO que los emite."

**Hard cut (C10 IC §0 decisions 5–7) — all of the following are
explicitly out of scope and absent from this module:**
- no `RPi.GPIO`, no `pigpio`, no `/dev/mem`, no serial/USB opens, no
  sockets — `SimulatedEscSink` only ever mutates its own in-memory state
- no DShot/Oneshot/Multishot bit-banging as a shipped product encoding
  (classic PWM-in-µs is the **only** encoding in this Buy)
- no claim that arming powers anything physical — `armed` is a plain
  in-memory flag on the simulated sink, nothing more

**Encoding (locked, C10 IC §0 decision 4):** `encode_motor_forces` maps
each (clamped) motor force linearly onto `[min_us, max_us]`, default
`1000`–`2000` µs — `force=0 → min_us`, `force=1 → max_us`. `min_us` and
`max_us` must be finite with `min_us < max_us`, else `ValueError`.

**Arming behavior (locked, C10 IC §0 decision 6):** `SimulatedEscSink`
starts `armed=False`. `apply(cmd)` **always records** `cmd` as the sink's
last command (useful for tests/introspection), but only reports
`EscApplyResult.applied=True` when the sink is armed at the moment of the
call — while disarmed, `applied=False` with `reason="disarmed"`. Neither
branch ever claims a physical write happened: there is no actuator here
to write to.

No `write_gpio`/`open_serial`/`send_dshot`/`pigpio_*`/`export_pwm`
anywhere in this module — this is command encoding and in-memory
bookkeeping only, never actuation.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from jarvis.flight_software.flight_control.mixer import MotorForceCommand

_DEFAULT_MIN_US = 1000.0
_DEFAULT_MAX_US = 2000.0

PulseWidths = tuple[float, float, float, float]


class EscPwmCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    t_s: float
    pulse_us: PulseWidths
    protocol: Literal["pwm_us"] = "pwm_us"
    notes: str | None = None

    @field_validator("pulse_us")
    @classmethod
    def _finite_pulses(cls, value: PulseWidths) -> PulseWidths:
        if len(value) != 4:
            raise ValueError("pulse_us must have exactly 4 entries")
        if not all(math.isfinite(component) for component in value):
            raise ValueError("pulse_us must be finite")
        return value


class EscApplyResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    applied: bool
    reason: str | None = None
    pulse_us: PulseWidths | None = None


def encode_motor_forces(
    forces: MotorForceCommand, *, min_us: float = _DEFAULT_MIN_US, max_us: float = _DEFAULT_MAX_US
) -> EscPwmCommand:
    """Linear map: `force=0 -> min_us`, `force=1 -> max_us`. Each force is
    defensively clamped to `[0, 1]` before mixing in — `MotorForceCommand`
    is normally already clamped by `QuadXMixer`, but this function does
    not assume its input came from there."""
    if not math.isfinite(min_us) or not math.isfinite(max_us) or min_us >= max_us:
        raise ValueError("min_us and max_us must be finite with min_us < max_us")

    span = max_us - min_us
    pulses = tuple(min_us + _clamp01(force) * span for force in forces.motor_forces)
    return EscPwmCommand(t_s=forces.t_s, pulse_us=pulses)


class SimulatedEscSink:
    """In-memory only — never opens a pin, a port, or a socket. `armed`
    defaults to `False`; `apply(cmd)` always records `cmd` as the last
    command but only marks `applied=True` while armed."""

    def __init__(self) -> None:
        self._armed = False
        self._last_command: EscPwmCommand | None = None

    @property
    def armed(self) -> bool:
        return self._armed

    def arm(self) -> None:
        """Flips an in-memory flag only — never claims physical power."""
        self._armed = True

    def disarm(self) -> None:
        self._armed = False

    def apply(self, cmd: EscPwmCommand) -> EscApplyResult:
        self._last_command = cmd
        if not self._armed:
            return EscApplyResult(applied=False, reason="disarmed", pulse_us=cmd.pulse_us)
        return EscApplyResult(applied=True, reason=None, pulse_us=cmd.pulse_us)

    def last_command(self) -> EscPwmCommand | None:
        return self._last_command


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
