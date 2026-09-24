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

**Fase C · C26 — `EscOutput`: naming the port (`B1-fase-c-esc-output-hal`).**
The mixer speaks **forces** only — it has never known PWM, DShot, or any
wire protocol, and still does not (C26 IC §0 decision 4). Whoever "emits"
toward an ESC speaks a named **port**: `EscOutput.apply_forces(forces) ->
EscApplyResult`. Today the only device plugged into that port is
`SimulatedEscSink` (in-memory only, exactly as C10/C14 shipped it); a
future pin driver would implement the same port and encode **inside its
own** `apply_forces`, never inside the mixer. `apply_forces` on
`SimulatedEscSink` is a thin wrapper — `encode_motor_forces(forces)` then
`self.apply(cmd)` — so the C10 `apply(EscPwmCommand)` path, its arming
semantics, and every existing C10/C14 test stay byte-for-byte unchanged.

**`EscOutput` is `abc.ABC`, not `typing.Protocol` (disclosed per IC §1):**
`SimulatedEscSink` is a plain class already, not a Pydantic model, so an
ABC does not fight anything here — no deviation was needed.

**Only one implementation ships this Buy (C26 IC §0 decision 7):**
`SimulatedEscSink`. No GPIO sink, no dummy pin class, no
`NotImplementedError`-only stub offered as product surface — a second
`EscOutput` implementation is a later, separate Buy if ever prioritized.

**`EscOutput HAL != pin != motors != DShot`.** **Exists:** a named port;
the simulated sink implements it; the mixer still does not know the wire
protocol. **Impossible:** a motor on a wire; a DShot stream; `step`
actuating anything — C24's `FlightControlLoop.step` still never calls
`apply`/`apply_forces` (unchanged, verified in this Buy's own tests).
"""

from __future__ import annotations

import abc
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


class EscOutput(abc.ABC):
    """The named ESC output port (C26). Same contract for today's
    in-memory `SimulatedEscSink` and any future pin driver — the mixer
    never sees this type, it only ever produces `MotorForceCommand`.
    `apply_forces` is where encoding into a wire-shaped command belongs;
    a future implementation encodes DShot/Oneshot/whatever **inside its
    own** `apply_forces`, never in `mixer.py`."""

    @abc.abstractmethod
    def apply_forces(self, forces: MotorForceCommand) -> EscApplyResult:
        """Encode `forces` however this port's device expects, then
        apply it. Must never claim a physical write happened — there is
        no actuator behind any implementation that ships in this repo."""
        raise NotImplementedError

    @abc.abstractmethod
    def arm(self) -> None:
        """Flips an in-memory flag only — never claims physical power."""
        raise NotImplementedError

    @abc.abstractmethod
    def disarm(self) -> None:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def armed(self) -> bool:
        raise NotImplementedError


class SimulatedEscSink(EscOutput):
    """In-memory only — never opens a pin, a port, or a socket. `armed`
    defaults to `False`; `apply(cmd)` always records `cmd` as the last
    command but only marks `applied=True` while armed. `apply_forces`
    (C26) is a thin wrapper: `encode_motor_forces(forces)` then
    `self.apply(cmd)` — the C10 `apply(EscPwmCommand)` path and its
    arming semantics are unchanged."""

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

    def apply_forces(self, forces: MotorForceCommand) -> EscApplyResult:
        cmd = encode_motor_forces(forces)
        return self.apply(cmd)

    def last_command(self) -> EscPwmCommand | None:
        return self._last_command


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
