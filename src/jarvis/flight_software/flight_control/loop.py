"""Fase C · C24 — `FlightControlLoop.step`: the named one-cycle control tick
(`B1-fase-c-control-loop-tick`).

Python scaffold / sim only — production flight_control runtime is C++ (see
`loop.hpp`/`loop.cpp` in `native/flight_control/`, this Buy's own C++ twin;
a real MCU ISR is a later, separate Buy). This module extracts the body
that C11's `run_controlled_flight_sim_smoke` and C13's `fc_closed_loop_smoke`
already ran **inlined**, giving it one name: `FlightControlLoop.step`. It
does not add any new math — `filter.py` … `mixer.py` are called, never
reimplemented, in exactly the order those two smokes already used:

```text
filter_sample -> estimator.update -> controller.compute -> bridge.convert -> mixer.mix
```

**Named control tick != flying != MCU ISR != motors != RC sticks.**

**Exists:** one named cycle — IMU sample + attitude setpoint + collective
in, four motor forces out — reusing C6-C12's own rungs verbatim, callable
from a smoke loop today and, unmodified, from a future MCU timer tick.
**Impossible:** a running FC on a board; sticks flying the craft; an ESC
on a wire. Nothing in this module is any of those.

**Split tick vs world (C24 IC §0 decision 4, locked):** `step` does
**not** call the plant, does not read a real IMU, and does not write a
pin. The caller supplies an `ImuSample` (from `ToyQuadAttitudePlant.sense`/
`.step` in the smokes, from any HAL in a future Buy) and consumes the
returned `MotorForceCommand` itself — `plant.step(out.forces, dt)` stays
outside `step`, in the caller's own loop, exactly as before extraction.

**No timer (C24 IC §0 decision 9):** `dt` is **not** an argument of
`step`. The estimator/controller still derive their own timing from
`ImuSample.t_s`, unchanged from C7/C8. A hardware 1 kHz ISR calling this
tick on a fixed schedule is a later Buy.

**No RC (C24 IC §0 decision 10):** `AttitudeSetpoint` and `collective`
are plain arguments — the caller decides them (the smokes still use
`level_setpoint` and a hover-range collective). Mapping RC sticks to
those arguments is C25, not this Buy.

**No PWM actuation (C24 IC §0 decision 8):** `ControlTickResult.pwm` is
populated via C10's own `encode_motor_forces(forces)` for visibility
only — plain PWM-microsecond numbers, nothing written anywhere.
`SimulatedEscSink.apply` is never called inside `step`; arming/applying a
PWM command stays the caller's own choice, same as every earlier Buy.

**Safety / autonomy untouched (C24 IC §0 decision 12):** `step` never
calls `SafetyGate.evaluate` or `submit_command` — this is sensing/control
math, not actuation, matching every rung it wires together.

**Constructing before calling is not optional (C24 IC §2 "typed error or
documented impossible"):** `step` is a bound instance method of
`FlightControlLoop` — Python's own method-binding rules make calling it
without first constructing a `FlightControlLoop` instance a `TypeError`
("missing 1 required positional argument: 'self'") at the language level,
not a case this module adds special-case code to check. No public
free-function `step(...)` exists here for that reason.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from jarvis.flight_software.flight_control.attitude import (
    AttitudeState,
    ComplementaryAttitudeEstimator,
)
from jarvis.flight_software.flight_control.controller import (
    AttitudeSetpoint,
    BodyRateCommand,
    PdAttitudeController,
)
from jarvis.flight_software.flight_control.esc import EscPwmCommand, encode_motor_forces
from jarvis.flight_software.flight_control.filter import ImuLowPassFilter
from jarvis.flight_software.flight_control.mixer import MotorForceCommand, QuadXMixer
from jarvis.flight_software.flight_control.rate_torque import (
    BodyTorqueCommand,
    LinearRateTorqueBridge,
)
from jarvis.flight_software.flight_control.types import ImuSample


class ControlTickResult(BaseModel):
    """Everything one `step()` call produced, in pipeline order — nothing
    here is an actuator; `pwm` is PWM-microsecond numbers only, never
    written anywhere."""

    model_config = ConfigDict(extra="forbid")

    t_s: float
    filtered: ImuSample
    state: AttitudeState
    rate_cmd: BodyRateCommand
    torque_cmd: BodyTorqueCommand
    forces: MotorForceCommand
    pwm: EscPwmCommand


class FlightControlLoop:
    """Holds one instance of each existing rung (filter, estimator,
    controller, bridge, mixer) — injected, or default-constructed with
    that rung's own existing defaults, matching every prior smoke's own
    construction. `step()` runs them in the locked order and returns a
    `ControlTickResult`; it never touches a plant, a real HAL, a pin, or
    Safety."""

    def __init__(
        self,
        filt: ImuLowPassFilter | None = None,
        estimator: ComplementaryAttitudeEstimator | None = None,
        controller: PdAttitudeController | None = None,
        bridge: LinearRateTorqueBridge | None = None,
        mixer: QuadXMixer | None = None,
    ) -> None:
        self._filt = filt if filt is not None else ImuLowPassFilter()
        self._estimator = estimator if estimator is not None else ComplementaryAttitudeEstimator()
        self._controller = controller if controller is not None else PdAttitudeController()
        self._bridge = bridge if bridge is not None else LinearRateTorqueBridge()
        self._mixer = mixer if mixer is not None else QuadXMixer()

    def step(
        self, sample: ImuSample, setpoint: AttitudeSetpoint, collective: float
    ) -> ControlTickResult:
        """`filter_sample -> estimator.update -> controller.compute ->
        bridge.convert -> mixer.mix` — exactly the C11/C13 order, calling
        each existing rung's own unmodified method. Does not call
        `plant.step`, does not read a HAL, does not write a pin."""
        filtered = self._filt.filter_sample(sample)
        state = self._estimator.update(filtered)
        rate_cmd = self._controller.compute(setpoint, state)
        torque_cmd = self._bridge.convert(rate_cmd)
        forces = self._mixer.mix(collective, torque_cmd)
        pwm = encode_motor_forces(forces)
        return ControlTickResult(
            t_s=forces.t_s,
            filtered=filtered,
            state=state,
            rate_cmd=rate_cmd,
            torque_cmd=torque_cmd,
            forces=forces,
            pwm=pwm,
        )
