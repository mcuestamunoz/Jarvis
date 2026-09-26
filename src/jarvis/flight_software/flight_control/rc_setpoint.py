"""Fase C · C25 — `map_rc_to_loop_inputs`: RC channel units -> C24 tick args
(`B1-fase-c-rc-setpoint`).

Python scaffold / sim only — production flight_control runtime is C++ (see
`rc_setpoint.hpp`/`rc_setpoint.cpp` in `native/flight_control/`, this Buy's
own C++ twin). Maps already-decoded RC channel units (C19's
`CrsfRcChannels`, or any equivalent sequence of ints) onto the two
arguments C24's `FlightControlLoop.step` already accepts:
`AttitudeSetpoint` and `collective`. No CRSF frame parsing happens here —
C19's `crsf_stub.py` owns that; this module only converts already-decoded
integer channel values.

**RC->setpoint != flying != sticks drive motors != Safety allow != yaw
lock.**

**Exists:** a documented, illustrative AETR (Aileron/Elevator/Throttle/
Rudder) map from CRSF 11-bit channel units to `AttitudeSetpoint` +
`collective` — the two arguments C24's `step` already accepts, unchanged.
**Impossible:** a pilot flying the craft; a motor spinning; a failsafe;
heading-hold yaw. Nothing in this module is any of those.

**Channel map (C25 IC §0 decision 5, illustrative — not a real TX
model):** `RC_CH_ROLL`/`RC_CH_PITCH`/`RC_CH_THROTTLE` = channel indices
`0`/`1`/`2`. `CRSF_CH_MIN`/`CRSF_CH_MID`/`CRSF_CH_MAX` = `172`/`992`/
`1811`, the same illustrative CRSF 11-bit endpoint convention already
used around C20's `CrsfDualRolePolicy`.

**Yaw channel unlocked (Fase C · C37, `B1-fase-c-mag-yaw-rung`) —
`RC_CH_YAW` = index `3`:** C25 originally left this channel unused,
since C7's estimator had no magnetometer and no absolute heading
reference a yaw stick could honestly command. C37 adds that reference
(`attitude.py`'s own optional mag yaw correction) — the yaw stick is
therefore unlocked into the setpoint's own yaw. Deflection is measured
from `CRSF_CH_MID`, same shape as roll/pitch, but scaled to
`RC_MAX_YAW_RAD` (`pi`, i.e. **180 degrees**) rather than roll/pitch's
own `RC_MAX_TILT_RAD` (30 degrees) — a full-range heading command is the
documented, more sensible convention for yaw than reusing a tilt limit
(picked and disclosed here, not left implicit). Increasing channel value
maps to positive yaw rotation about world/body `Z` (ENU right-hand
convention) — the same "increasing channel -> positive rotation" sign
rule roll/pitch already use, just about the vertical axis instead of a
horizontal one. Roll/pitch/throttle maps are **byte-unchanged** by this
Buy — same formulas, same constants, same fixtures.

**Throttle -> collective (locked, decision 6):** linear map
`[CRSF_CH_MIN, CRSF_CH_MAX] -> [0, 1]`, clipped. Mid-stick (`992`) maps to
approximately `0.5003`, **not** exactly `0.5` — the CRSF convention's
endpoints (`172`/`1811`) are not perfectly symmetric around `992`
(`820` below vs. `819` above), and this module does not silently round
that away.

**Roll/pitch -> `AttitudeSetpoint` (locked, decision 7):** stick
deflection is measured **from** `CRSF_CH_MID`, scaled so the maximum
deflection (`CRSF_CH_MAX` on the high side, `CRSF_CH_MIN` on the low
side) reaches exactly `RC_MAX_TILT_RAD` (`pi/6`, i.e. 30 degrees) —
values beyond either endpoint clip at that same 30 degrees, they do not
extrapolate past it. Increasing channel value maps to positive rotation
about the corresponding body axis (roll -> body X, pitch -> body Y) —
an arbitrary but documented sign convention, not sourced from any real
transmitter. The resulting Euler roll/pitch/yaw triple (yaw from
`RC_CH_YAW`, `0` if that channel is at mid-stick) is converted to
`q_body_to_world_desired` via the standard body 3-2-1 (yaw-pitch-roll)
Euler-to-quaternion composition — **verified to reduce to the exact
pre-C37 roll/pitch-only formula when yaw is `0`** (same test fixtures,
byte-identical output), matching C8's own `AttitudeSetpoint`/`"enu"`
frame convention unchanged.

**No clock invented (decision 8):** `map_rc_to_loop_inputs` takes `t_s`
as a required keyword argument — the caller's own sample time, never a
value this module generates itself.

**Optional `step_with_rc` (decision 9):** a thin convenience that maps
then calls C24's own `FlightControlLoop.step` unchanged. It never calls a
plant, an ESC sink, or `SafetyGate.evaluate` — those stay exactly as far
from this module as they already were from `loop.py`.

**C24 (`loop.py`/`loop.hpp`) math is untouched by this Buy** — this
module only produces the two argument values `step` already accepts; it
never edits `FlightControlLoop`/`ControlLoop`. **C20's `CrsfDualRolePolicy`
(aux -> Authority `kill`) is untouched too** — this module does not read
an aux channel, does not compute Authority, and does not import
`crsf_dual_role.py`.

No `write_gpio`/`open_serial`/`send_dshot`/`submit_command`/failsafe-timer
anywhere in this module — this is a pure, deterministic unit conversion,
never actuation.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Final, Union

from pydantic import BaseModel, ConfigDict, field_validator

from jarvis.capabilities.crsf_stub import CrsfRcChannels
from jarvis.flight_software.flight_control.attitude import Quat
from jarvis.flight_software.flight_control.controller import AttitudeSetpoint
from jarvis.flight_software.flight_control.loop import ControlTickResult, FlightControlLoop
from jarvis.flight_software.flight_control.types import ImuSample

RC_CH_ROLL: Final[int] = 0
RC_CH_PITCH: Final[int] = 1
RC_CH_THROTTLE: Final[int] = 2
RC_CH_YAW: Final[int] = 3

CRSF_CH_MIN: Final[int] = 172
CRSF_CH_MID: Final[int] = 992
CRSF_CH_MAX: Final[int] = 1811

RC_MAX_TILT_RAD: Final[float] = math.pi / 6.0
# C37 — full-range heading command, not the tilt limit (see the module
# docstring's own "Yaw channel unlocked" section for why this is a
# separate, documented constant rather than reusing RC_MAX_TILT_RAD).
RC_MAX_YAW_RAD: Final[float] = math.pi

_MIN_CHANNELS: Final[int] = 4

RcChannelsInput = Union[CrsfRcChannels, Sequence[int]]


class RcLoopInputs(BaseModel):
    """The two arguments C24's `FlightControlLoop.step` already accepts —
    nothing else. `collective` is defensively re-checked here even though
    `map_rc_to_loop_inputs` always clips it first."""

    model_config = ConfigDict(extra="forbid")

    setpoint: AttitudeSetpoint
    collective: float

    @field_validator("collective")
    @classmethod
    def _finite_unit_range(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("collective must be finite")
        if not (0.0 <= value <= 1.0):
            raise ValueError("collective must be in [0, 1]")
        return value


def map_rc_to_loop_inputs(channels: RcChannelsInput, *, t_s: float) -> RcLoopInputs:
    """Converts already-decoded RC channel units into `RcLoopInputs`. Does
    not parse CRSF frames, does not read a clock, does not call `step`.
    `channels` may be a `CrsfRcChannels` (C19) or any sequence of `>= 4`
    ints (AETR-shaped); indices `RC_CH_ROLL`/`RC_CH_PITCH`/
    `RC_CH_THROTTLE`/`RC_CH_YAW` are all read as of C37."""
    values = _extract_channel_values(channels)

    roll_rad = _stick_deflection_rad(values[RC_CH_ROLL])
    pitch_rad = _stick_deflection_rad(values[RC_CH_PITCH])
    yaw_rad = _stick_deflection_rad(values[RC_CH_YAW], RC_MAX_YAW_RAD)
    collective = _throttle_to_collective(values[RC_CH_THROTTLE])

    quat = _roll_pitch_yaw_to_quat(roll_rad, pitch_rad, yaw_rad)
    setpoint = AttitudeSetpoint(t_s=t_s, q_body_to_world_desired=quat)
    return RcLoopInputs(setpoint=setpoint, collective=collective)


def step_with_rc(loop: FlightControlLoop, sample: ImuSample, channels: RcChannelsInput) -> ControlTickResult:
    """`inputs = map_rc_to_loop_inputs(channels, t_s=sample.t_s); return
    loop.step(sample, inputs.setpoint, inputs.collective)` — nothing
    else. Never calls a plant, an ESC sink, or `SafetyGate.evaluate`."""
    inputs = map_rc_to_loop_inputs(channels, t_s=sample.t_s)
    return loop.step(sample, inputs.setpoint, inputs.collective)


def _extract_channel_values(channels: RcChannelsInput) -> Sequence[int]:
    if isinstance(channels, CrsfRcChannels):
        values: Sequence[int] = channels.channels
    else:
        values = tuple(channels)

    if len(values) < _MIN_CHANNELS:
        raise ValueError(
            f"channels must have at least {_MIN_CHANNELS} entries (AETR-shaped), got {len(values)}"
        )
    for idx in (RC_CH_ROLL, RC_CH_PITCH, RC_CH_THROTTLE, RC_CH_YAW):
        value = values[idx]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"channels[{idx}] must be int, got {value!r}")
    return values


def _stick_deflection_rad(channel_value: int, max_rad: float = RC_MAX_TILT_RAD) -> float:
    if channel_value >= CRSF_CH_MID:
        span = CRSF_CH_MAX - CRSF_CH_MID
        frac = (channel_value - CRSF_CH_MID) / span
    else:
        span = CRSF_CH_MID - CRSF_CH_MIN
        frac = (channel_value - CRSF_CH_MID) / span
    frac_clipped = max(-1.0, min(1.0, frac))
    return frac_clipped * max_rad


def _throttle_to_collective(channel_value: int) -> float:
    span = CRSF_CH_MAX - CRSF_CH_MIN
    frac = (channel_value - CRSF_CH_MIN) / span
    return max(0.0, min(1.0, frac))


def _roll_pitch_yaw_to_quat(roll_rad: float, pitch_rad: float, yaw_rad: float) -> Quat:
    """Body 3-2-1 (yaw-pitch-roll) Euler-to-quaternion composition:
    `q = q_yaw (x) q_pitch (x) q_roll`. C37 adds the `yaw_rad` term —
    verified to reduce to the exact pre-C37 formula (`(cp*cr, cp*sr,
    sp*cr, -sp*sr)`) when `yaw_rad == 0.0`, since `cos(0)=1`/`sin(0)=0`
    zero out every `sy`-weighted term below."""
    half_roll = roll_rad / 2.0
    half_pitch = pitch_rad / 2.0
    half_yaw = yaw_rad / 2.0
    cr, sr = math.cos(half_roll), math.sin(half_roll)
    cp, sp = math.cos(half_pitch), math.sin(half_pitch)
    cy, sy = math.cos(half_yaw), math.sin(half_yaw)
    return (
        cy * cp * cr + sy * sp * sr,
        cy * cp * sr - sy * sp * cr,
        cy * sp * cr + sy * cp * sr,
        sy * cp * cr - cy * sp * sr,
    )
