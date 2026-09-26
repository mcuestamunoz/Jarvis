"""Fase C · C38 (`B1-fase-c-altitude-loop`) — `AltitudeController`: a
z -> collective law, run **outside** `FlightControlLoop.step`.

Python scaffold / sim only — production flight_control runtime is C++
(future IC). Collective stops being only the RC stick or a fixed
constant: this controller derives it from a simulated height
measurement, so `ToyQuad6DofPlant` can climb toward, or hold near, a
documented `z_des_m`.

**Naming note (disclosed):** deliberately named `altitude_controller.py`,
not `altitude.py` — this codebase already ships `attitude.py` (the C7
estimator) and `AttitudeSetpoint` (`controller.py`, C8); "altitude" and
"attitude" differ by one letter, and this Buy avoids adding a second,
easily-confused near-homograph on top of an existing one.

**Setpoint type (disclosed, IC §0 decision 8 — "AltitudeSetpoint(z_m)
or plain z_des float, typed preferred"):** this module uses a **plain
`float` `z_des_m`**, not a typed `AltitudeSetpoint` wrapper — for the
same reason as the module name above: a class named `AltitudeSetpoint`
sitting next to the existing `AttitudeSetpoint` would be a standing
readability hazard (a one-letter typo silently passes the wrong type to
the wrong function, since both would carry unrelated float payloads).
The IC's own "typed preferred" is satisfied by `AltitudeController`
itself and by `AltitudeSample` (`sim_altitude_hal.py`); `z_des_m` alone
does not need its own wrapper type to stay unambiguous.

**One law only (IC §0 decision 6, locked) — not cascaded PID, not
LQR:**

```text
collective = clip(hover_bias + kp * (z_des_m - altitude_m) - kd * vz_mps, 0, 1)
```

`hover_bias` is the baseline collective at zero error and zero vertical
speed. `kp` (finite, `> 0`) and `kd` (finite, `>= 0`) are toy tuning
constants, same status as every other gain in this ladder
(`torque_gain`, `mag_gain`, ...) — never sourced from any real
autopilot's tuning.

**`hover_bias` default (disclosed deviation from the IC's own suggested
default):** the IC's own §0 decision 6 suggests reusing `hover_collective()`
(C9's symbolic mid-range collective, `0.5`) as the default bias. Verified
empirically before locking this default: `hover_collective()` is a
generic placeholder never tuned to any specific thrust curve, and it is
badly mismatched with `ToyQuad6DofPlant`'s own default toy physics
(`mass_kg=1.0`, `thrust_gain=20.0`) — at `collective=0.5` this plant's
own thrust law produces roughly 4x the force needed to counter gravity,
so a controller defaulting to it never settles near `z_des_m`, it
perpetually overshoots to a new (wrong) equilibrium several metres
above the setpoint. This module instead defaults `hover_bias` to
`mass_kg * GRAVITY_MPS2 / (4 * thrust_gain)` evaluated at
`ToyQuad6DofPlant`'s own default constants — the toy collective that
actually balances gravity for the plant this Buy's own smoke and tests
are built around, verified to converge monotonically (no overshoot)
toward a documented `z_des_m` over a documented step count. A caller
driving a differently-configured plant should pass its own computed
`hover_bias` explicitly — this module does not import `plant.py` or
reach into any plant instance to compute it automatically, keeping this
controller as plant-agnostic as `SimulatedMagHal`/`SimulatedAltitudeHal`
already are.

**`vz_mps` source (disclosed, IC §0 decision 6 — "pick one, document"):**
this controller takes `vz_mps` as a **caller-supplied argument**, not an
internally-integrated or finite-differenced state. The shipped smoke
passes `ToyQuad6DofPlant.true_velocity_mps[2]` directly — that truth
already exists on the plant, so inventing a second, independent
finite-difference estimate of the same quantity here would be a needless
duplication, not a meaningfully different design.

**Stateless, no `dt`:** `compute(...)` is a pure function of its
arguments — no internal time integration, no rate limiting, nothing
that would need a `dt` to update. This is the simplest reading of "one
law only" the IC's own T2 anticipates a `dt` argument for; this design
does not have one to validate, disclosed here rather than left silent.

**Integration with `step` (IC §0 decision 7, locked):** this controller
runs **outside** `FlightControlLoop.step` — its own output is the
`collective` argument callers already pass to `step`. The attitude
setpoint passed to `step` is unrelated and unchanged (still `level_setpoint`
or an RC-derived one, exactly as before this Buy).

Sim altitude != live baro/ToF chip. z -> collective in RAM != altitude
hold in air. Nothing in this module reads a real sensor or claims a
real vehicle holds height.
"""

from __future__ import annotations

import math

from jarvis.flight_software.flight_control.sim_altitude_hal import AltitudeSample

_DEFAULT_KP = 0.2
_DEFAULT_KD = 0.3
_GRAVITY_MPS2 = 9.81
# ToyQuad6DofPlant's own default constants (mass_kg=1.0, thrust_gain=20.0)
# — see the module docstring's own disclosed-deviation note for why this
# replaces the IC's suggested hover_collective() (0.5) default.
_DEFAULT_HOVER_BIAS = _GRAVITY_MPS2 / (4.0 * 20.0)


class AltitudeController:
    """`kp` (finite, `> 0`), `kd` (finite, `>= 0`), `hover_bias` (finite,
    in `[0, 1]`) are all documented toy tuning constants. Deterministic —
    no internal state, no noise."""

    def __init__(
        self,
        kp: float = _DEFAULT_KP,
        kd: float = _DEFAULT_KD,
        hover_bias: float = _DEFAULT_HOVER_BIAS,
    ) -> None:
        if not math.isfinite(kp) or kp <= 0.0:
            raise ValueError("kp must be finite and > 0")
        if not math.isfinite(kd) or kd < 0.0:
            raise ValueError("kd must be finite and >= 0")
        if not math.isfinite(hover_bias) or not (0.0 <= hover_bias <= 1.0):
            raise ValueError("hover_bias must be finite and in [0, 1]")
        self._kp = kp
        self._kd = kd
        self._hover_bias = hover_bias

    def compute(self, z_des_m: float, altitude: AltitudeSample, vz_mps: float) -> float:
        if not math.isfinite(z_des_m):
            raise ValueError("z_des_m must be finite")
        if not math.isfinite(vz_mps):
            raise ValueError("vz_mps must be finite")
        error = z_des_m - altitude.altitude_m
        raw = self._hover_bias + self._kp * error - self._kd * vz_mps
        return max(0.0, min(1.0, raw))
