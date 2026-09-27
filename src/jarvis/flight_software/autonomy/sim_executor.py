"""Fase C · C40 (`B1-fase-c-autonomy-executor`) — `SimAutonomyExecutor`:
a **separate, sim-only** driver that maps `AutonomyVerb.HOLD`/`GO_TO`/
`LAND` into the existing C38/C39 setpoint chain so verbs actually drive
`ToyQuad6DofPlant` via `FlightControlLoop.step`.

Python scaffold / sim only — production flight_control runtime is C++
(future IC). This is **not** the C4 command surface
(`jarvis.flight_software.autonomy.surface`): `propose_command`/
`submit_command` and `RejectAllSafetyGate` are completely untouched by
this module, and `AutonomySubmissionResult.execution` is never set or
imported here. This executor is a deliberately **separate** API —
`SimAutonomyExecutor.tick(...)` — that a caller runs *outside* Safety
entirely, exactly the way every prior smoke in this ladder ran its own
loop outside `step`.

**Reuse, not reinvention (IC §0 decision 6, locked):** this module does
not implement any PD law of its own. Every tick calls, unmodified,
`PositionController.compute` (C39) and `AltitudeController.compute`
(C38), then `FlightControlLoop.step` (C24), then `plant.step` (C36) —
the exact same four-call chain `run_position_loop_smoke` already used,
now wrapped as a stateful per-verb driver instead of a fixed-setpoint
smoke.

**Verb map (IC §0 decision 5, locked):**

- **`HOLD`** — freezes a `PositionSetpoint` at the current xy (or a
  caller-supplied `x_m`/`y_m`) and a `z_des_m` at the current z (or a
  caller-supplied `z_m`) **the first tick `HOLD` is ticked**, then holds
  that same frozen point every subsequent tick regardless of drift —
  not "chase wherever I already am" (which would be a zero-error
  no-op), but "stay where I was told to stay."
- **`GO_TO`** — requires finite `x_m`/`y_m` params; every tick, a fresh
  `PositionSetpoint(x_m, y_m)` is built straight from those params (not
  frozen — a caller may retarget mid-flight by calling `tick` again with
  different params under the same verb... though in practice this
  executor's own `_active_verb` tracking only resets frozen state on a
  *verb* change, so a same-tick param change on `GO_TO` **does** apply
  immediately, unlike `HOLD`/`LAND`'s frozen anchors). `z_m` is optional;
  when absent, the altitude target is frozen at the **current** z the
  first tick `GO_TO` is ticked (documented default — "keep whatever
  height you were at unless told otherwise"), not a new invented
  cruise-altitude constant.
- **`LAND`** — freezes xy the same way `HOLD` does, and ratchets a
  descending `z_des_m` target downward by `land_rate_mps * dt_s` each
  tick (default `0.5 m/s`), clamped at a documented floor `z_land_m`
  (default `0.0`) or a caller-supplied `z_m` floor. This is a toy
  descent-rate schedule, **not** a claim of touchdown gear, ground
  contact, or motor cutoff — it only ever asserts `true_position_m[2]`
  decreases toward the floor, never that anything "lands."
- **Any other verb** (`TAKEOFF`/`FOLLOW`/`RETURN_HOME`/`PATROL`) —
  `tick(...)` raises `ValueError` naming the unsupported verb. This Buy
  implements exactly three verbs; the other four enum members remain
  valid to `propose_command` (C4) but this sim executor does not drive
  them.

**Coupling is expected, not a bug (IC §0 decision 7 / C39 N2):** while
aggressively chasing an xy setpoint, `true_position_m[2]` may droop
below `z_des_m` — the position controller's tilt and the altitude
controller's collective are two independent laws feeding the same
plant, not a cascaded/coupled controller. This module does not correct
for that coupling and does not claim glued altitude during `GO_TO`.

**Params (IC §0 decision 8):** a typed `SimAutonomyParams(x_m, y_m,
z_m)` — all optional floats — rather than parsing
`AutonomyCommand.params: dict[str, str]`. This executor does not accept
or construct an `AutonomyCommand` at all; a caller wanting to bridge
from `propose_command`'s own typed command into this executor's params
would do that translation itself, outside this module (not needed for
this Buy's own tests/smokes).

verb -> setpoints in RAM != execute on copper. Sim HOLD/LAND/GO_TO !=
flying != Safety allow. `plant.step` still happens **outside**
`FlightControlLoop.step`, exactly as every prior Buy in this ladder.
This module never imports `AutonomySubmissionResult` and never writes
the word "executed" into any field anywhere in this file.
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict

from jarvis.flight_software.autonomy.types import AutonomyVerb
from jarvis.flight_software.flight_control.altitude_controller import AltitudeController
from jarvis.flight_software.flight_control.controller import AttitudeSetpoint
from jarvis.flight_software.flight_control.loop import ControlTickResult, FlightControlLoop
from jarvis.flight_software.flight_control.plant import ToyQuad6DofPlant
from jarvis.flight_software.flight_control.position_controller import PositionController, PositionSetpoint
from jarvis.flight_software.flight_control.sim_altitude_hal import SimulatedAltitudeHal
from jarvis.flight_software.flight_control.sim_position_hal import SimulatedPositionHal

_DEFAULT_Z_LAND_M = 0.0
_DEFAULT_LAND_RATE_MPS = 0.5

_SUPPORTED_VERBS = (AutonomyVerb.HOLD, AutonomyVerb.GO_TO, AutonomyVerb.LAND)


class SimAutonomyParams(BaseModel):
    """All fields optional floats — a typed alternative to parsing
    `AutonomyCommand.params: dict[str, str]` (IC §0 decision 8)."""

    model_config = ConfigDict(extra="forbid")

    x_m: float | None = None
    y_m: float | None = None
    z_m: float | None = None


class SimAutonomyTickResult(BaseModel):
    """Everything one `SimAutonomyExecutor.tick()` call produced — for
    introspection/tests only, never an actuator record."""

    model_config = ConfigDict(extra="forbid")

    t_s: float
    verb: AutonomyVerb
    xy_setpoint: PositionSetpoint
    z_des_m: float
    setpoint: AttitudeSetpoint
    collective: float
    tick: ControlTickResult


class SimAutonomyExecutor:
    """Holds one `ToyQuad6DofPlant` (caller-owned, passed in) plus one
    instance each of `FlightControlLoop`/`SimulatedPositionHal`/
    `PositionController`/`SimulatedAltitudeHal`/`AltitudeController` —
    injected, or default-constructed with each rung's own existing
    defaults, matching `run_position_loop_smoke`'s own construction.
    Stateful: tracks the current `ImuSample` (advanced by `plant.step`
    every tick) and, per active verb, a frozen anchor point (`HOLD`/
    `LAND` xy, `GO_TO`/`HOLD` z) that resets whenever the verb changes."""

    def __init__(
        self,
        plant: ToyQuad6DofPlant,
        loop: FlightControlLoop | None = None,
        pos_hal: SimulatedPositionHal | None = None,
        pos_controller: PositionController | None = None,
        alt_hal: SimulatedAltitudeHal | None = None,
        alt_controller: AltitudeController | None = None,
        z_land_m: float = _DEFAULT_Z_LAND_M,
        land_rate_mps: float = _DEFAULT_LAND_RATE_MPS,
    ) -> None:
        if not math.isfinite(z_land_m):
            raise ValueError("z_land_m must be finite")
        if not math.isfinite(land_rate_mps) or land_rate_mps <= 0.0:
            raise ValueError("land_rate_mps must be finite and > 0")

        self._plant = plant
        self._loop = loop if loop is not None else FlightControlLoop()
        self._pos_hal = pos_hal if pos_hal is not None else SimulatedPositionHal()
        self._pos_controller = pos_controller if pos_controller is not None else PositionController()
        self._alt_hal = alt_hal if alt_hal is not None else SimulatedAltitudeHal()
        self._alt_controller = alt_controller if alt_controller is not None else AltitudeController()
        self._z_land_m = z_land_m
        self._land_rate_mps = land_rate_mps

        self._sample = plant.sense()
        self._active_verb: AutonomyVerb | None = None
        self._hold_setpoint: PositionSetpoint | None = None
        self._hold_z_des: float | None = None
        self._goto_z_des: float | None = None
        self._land_setpoint: PositionSetpoint | None = None
        self._land_z_des: float | None = None

    def tick(self, verb: AutonomyVerb, params: SimAutonomyParams | None, dt_s: float) -> SimAutonomyTickResult:
        """`sense -> HALs -> pos.compute -> alt.compute -> loop.step ->
        plant.step`, once, for the given verb. Raises `ValueError` for
        any verb other than `HOLD`/`GO_TO`/`LAND`, for non-finite
        `dt_s`/params, or for a `GO_TO` missing `x_m`/`y_m`."""
        if verb not in _SUPPORTED_VERBS:
            raise ValueError(f"unsupported verb for sim executor: {verb.value}")
        if not math.isfinite(dt_s) or dt_s <= 0.0:
            raise ValueError("dt_s must be finite and > 0")

        params = params if params is not None else SimAutonomyParams()
        for name, value in (("x_m", params.x_m), ("y_m", params.y_m), ("z_m", params.z_m)):
            if value is not None and not math.isfinite(value):
                raise ValueError(f"{name} must be finite")

        if verb != self._active_verb:
            self._hold_setpoint = None
            self._hold_z_des = None
            self._goto_z_des = None
            self._land_setpoint = None
            self._land_z_des = None
            self._active_verb = verb

        true_x, true_y, true_z = self._plant.true_position_m
        vx_mps, vy_mps, vz_mps = self._plant.true_velocity_mps

        if verb == AutonomyVerb.HOLD:
            if self._hold_setpoint is None:
                x_des = params.x_m if params.x_m is not None else true_x
                y_des = params.y_m if params.y_m is not None else true_y
                self._hold_setpoint = PositionSetpoint(x_m=x_des, y_m=y_des)
            if self._hold_z_des is None:
                self._hold_z_des = params.z_m if params.z_m is not None else true_z
            xy_setpoint = self._hold_setpoint
            z_des_m = self._hold_z_des
        elif verb == AutonomyVerb.GO_TO:
            if params.x_m is None or params.y_m is None:
                raise ValueError("GO_TO requires x_m and y_m params")
            xy_setpoint = PositionSetpoint(x_m=params.x_m, y_m=params.y_m)
            if self._goto_z_des is None:
                self._goto_z_des = params.z_m if params.z_m is not None else true_z
            z_des_m = params.z_m if params.z_m is not None else self._goto_z_des
        else:  # AutonomyVerb.LAND
            if self._land_setpoint is None:
                x_des = params.x_m if params.x_m is not None else true_x
                y_des = params.y_m if params.y_m is not None else true_y
                self._land_setpoint = PositionSetpoint(x_m=x_des, y_m=y_des)
            if self._land_z_des is None:
                self._land_z_des = true_z
            floor = params.z_m if params.z_m is not None else self._z_land_m
            self._land_z_des = max(floor, self._land_z_des - self._land_rate_mps * dt_s)
            xy_setpoint = self._land_setpoint
            z_des_m = self._land_z_des

        position = self._pos_hal.read_position(true_x, true_y, self._sample.t_s)
        altitude = self._alt_hal.read_altitude(true_z, self._sample.t_s)
        setpoint = self._pos_controller.compute(xy_setpoint, position, vx_mps, vy_mps, self._sample.t_s)
        collective = self._alt_controller.compute(z_des_m, altitude, vz_mps)
        tick_result = self._loop.step(self._sample, setpoint, collective)
        self._sample = self._plant.step(tick_result.forces, dt_s=dt_s)

        return SimAutonomyTickResult(
            t_s=self._sample.t_s,
            verb=verb,
            xy_setpoint=xy_setpoint,
            z_des_m=z_des_m,
            setpoint=setpoint,
            collective=collective,
            tick=tick_result,
        )
