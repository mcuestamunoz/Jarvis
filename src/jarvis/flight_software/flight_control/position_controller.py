"""Fase C · C39 (`B1-fase-c-position-loop`) — `PositionController`: an
xy -> roll/pitch tilt law, run **outside** `FlightControlLoop.step`.

Python scaffold / sim only — production flight_control runtime is C++
(future IC). Horizontal motion stops being only open-loop tilt or luck:
this controller derives an `AttitudeSetpoint` from a simulated
horizontal position measurement, so `ToyQuad6DofPlant` can move toward a
documented ENU point.

**Setpoint type (IC §0 decision 8, locked):** `PositionSetpoint(x_m,
y_m)` — deliberately does **not** collide with `AttitudeSetpoint`
(`controller.py`, C8) or the disclosed plain-`float` choice
`altitude_controller.py` (C38) made for the same reason. Unlike
`z_des_m` (a single scalar, easily confused with nothing else nearby),
`(x_des, y_des)` is a pair that benefits from a named type, and
`PositionSetpoint` has no existing near-homograph in this codebase to
collide with — so the IC's own "typed preferred" is followed here
without reservation.

**Not `AutonomyVerb.GO_TO` (IC §0 decision 8, locked):** this module
never imports `autonomy/`, never calls `propose_command`/`submit_command`,
and does not implement the GO_TO verb's own executor (C40, a separate,
future Buy). A `PositionSetpoint` is a plain xy target for this
controller's own law — not an autonomy command.

**One law only (IC §0 decision 6, locked) — not cascaded PID, not
LQR, not velocity-loop-only:**

```text
pitch_rad = clip(kp * (x_des - x) - kd * vx_mps, -max_tilt_rad, max_tilt_rad)
roll_rad  = clip(-(kp * (y_des - y) - kd * vy_mps), -max_tilt_rad, max_tilt_rad)
q = roll_pitch_yaw_to_quat(roll_rad, pitch_rad, 0.0)   # yaw held at 0
```

**Signs, derived and verified (IC §0 decision 6, "document and prove"):**
rotating the body `+Z` thrust vector by a *positive pitch* (rotation
about the body/world `Y` axis) lands the thrust's horizontal component
on **positive world `X`** (East) — `(sin(pitch)*T, 0, cos(pitch)*T)`,
hand-derived the same way `plant.py`'s own C36 translation law was
verified, and cross-checked numerically before writing any test. So a
positive East position error (`x_des > x`) must produce a **positive**
pitch command — no sign flip on the pitch term. A *positive roll*
(rotation about body/world `X`) lands the thrust's horizontal component
on **negative world `Y`** (South) — `(0, -sin(roll)*T, cos(roll)*T)` —
so a positive North error (`y_des > y`) needs a **negative** roll
command, hence the sign flip on the roll term above. `test_t3_...` in
this Buy's own test module asserts both signs directly against the
closed-loop plant, not just the controller's own output in isolation.

**`vx_mps`/`vy_mps` source (same pattern as C38's own `vz_mps`):**
caller-supplied arguments, not internally integrated or
finite-differenced — the shipped smoke passes
`ToyQuad6DofPlant.true_velocity_mps[0:2]` directly.

**`max_tilt_rad` default:** reuses `RC_MAX_TILT_RAD` (`rc_setpoint.py`,
C25 — `pi/6`, 30 degrees) rather than duplicating that numeric literal,
per the IC's own "prefer <= RC_MAX_TILT_RAD if that constant is reused"
suggestion.

**Yaw held at 0:** the `AttitudeSetpoint` this controller produces
always has yaw `0` — this Buy does not touch RC yaw (C37) or invent a
heading-following behavior; a caller wanting to combine position hold
with a non-zero commanded yaw would need a separate, explicitly-scoped
Buy to compose the two.

**Integration with `step` (IC §0 decision 7, locked):** this controller
runs **outside** `FlightControlLoop.step` — its own output is the
`setpoint` argument callers already pass to `step`. Collective still
comes from C38's own `AltitudeController`, unchanged, un-reimplemented
here.

Sim position != live GPS/flow chip. xy -> tilt in RAM != position hold
in air != GO_TO executed. An ENU point in RAM != a house map. Nothing
here reads a real sensor or claims any real vehicle holds position.
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict

from jarvis.flight_software.flight_control.controller import AttitudeSetpoint
from jarvis.flight_software.flight_control.rc_setpoint import RC_MAX_TILT_RAD
from jarvis.flight_software.flight_control.sim_position_hal import PositionSample

Quat = tuple[float, float, float, float]

_DEFAULT_KP = 0.15
_DEFAULT_KD = 0.3


class PositionSetpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x_m: float
    y_m: float


class PositionController:
    """`kp` (finite, `> 0`), `kd` (finite, `>= 0`), `max_tilt_rad`
    (finite, `> 0`) are all documented toy tuning constants.
    Deterministic — no internal state, no noise."""

    def __init__(
        self,
        kp: float = _DEFAULT_KP,
        kd: float = _DEFAULT_KD,
        max_tilt_rad: float = RC_MAX_TILT_RAD,
    ) -> None:
        if not math.isfinite(kp) or kp <= 0.0:
            raise ValueError("kp must be finite and > 0")
        if not math.isfinite(kd) or kd < 0.0:
            raise ValueError("kd must be finite and >= 0")
        if not math.isfinite(max_tilt_rad) or max_tilt_rad <= 0.0:
            raise ValueError("max_tilt_rad must be finite and > 0")
        self._kp = kp
        self._kd = kd
        self._max_tilt_rad = max_tilt_rad

    def compute(
        self,
        setpoint: PositionSetpoint,
        position: PositionSample,
        vx_mps: float,
        vy_mps: float,
        t_s: float,
    ) -> AttitudeSetpoint:
        if not math.isfinite(vx_mps):
            raise ValueError("vx_mps must be finite")
        if not math.isfinite(vy_mps):
            raise ValueError("vy_mps must be finite")

        error_x = setpoint.x_m - position.x_m
        error_y = setpoint.y_m - position.y_m
        pitch_raw = self._kp * error_x - self._kd * vx_mps
        roll_raw = -(self._kp * error_y - self._kd * vy_mps)
        pitch_rad = max(-self._max_tilt_rad, min(self._max_tilt_rad, pitch_raw))
        roll_rad = max(-self._max_tilt_rad, min(self._max_tilt_rad, roll_raw))

        quat = _roll_pitch_yaw_to_quat(roll_rad, pitch_rad, 0.0)
        return AttitudeSetpoint(t_s=t_s, q_body_to_world_desired=quat)


def _roll_pitch_yaw_to_quat(roll_rad: float, pitch_rad: float, yaw_rad: float) -> Quat:
    """Body 3-2-1 (yaw-pitch-roll) Euler-to-quaternion composition —
    same formula `rc_setpoint.py` uses, kept as this module's own private
    copy per this project's established per-module-private-helper style
    (see `native/flight_control/include/jarvis/fc/quat_math.hpp`'s own
    header comment for the documented C++-side deviation from this same
    convention)."""
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
