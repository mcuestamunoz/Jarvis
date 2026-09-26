"""Fase C · C11 — `ToyQuadAttitudePlant`: the C0 §7 wooden-ladder **tip**
(closing the sim loop, after C3 sampling, C6 filtering, C7 estimation, C8
control, C9 mixing, and C10 PWM encoding).

Python scaffold / sim only — production flight_control runtime is C++
(future IC). This module lets the existing C3→C10 pipeline run as a
**closed loop**: the plant advances a toy attitude from `MotorForceCommand`
(C9 forces), and emits the next `ImuSample` **consistent with its own true
attitude** — fixing, for this closed-loop tip only, C7's documented
"`SimulatedImuHal` is not attitude-aware" limitation. `SimulatedImuHal`
itself is untouched; C3's existing tests and smoke stay exactly as they
were.

**This is a toy, explicitly not product flight physics (C11 IC §0 decision
5):** `ToyQuadAttitudePlant` tracks **attitude only** — quaternion + body
angular rate — no position, no velocity, no real aerodynamics, no motor
thrust curve, no vehicle mass/inertia sourced from any real hardware. Its
"torque" response to motor forces is a single toy linear map
(`torque_gain`) plus toy passive angular damping (`angular_damping`),
chosen only to make the closed loop demonstrably converge — never
presented as a CFD/aero solver or as truth about any real vehicle.

**Rate ≠ torque — this honesty gap remains open (C11 IC §0 decision 7):**
C9's `QuadXMixer` still treats `BodyRateCommand.omega_body_rad_s` (a rate)
directly as its roll/pitch/yaw mix channels, without claiming rate is
physically equivalent to torque. This plant does **not** silently insert
a rate→torque controller to "fix" that for realism — its own toy
force→angular-acceleration map is a separate, equally-toy simplification,
documented here, not a physics correction. A real rate→torque bridge
remains a future, separate Buy if ever prioritized.

**Motor→torque-proxy signs (documented, matches C9's own X-geometry):**
given `MotorForceCommand.motor_forces = (m0, m1, m2, m3)` = `(FR, FL, RL,
RR)` per `mixer.py`'s own docstring, this plant computes:

```text
roll_proxy  = (m1 + m2) - (m0 + m3)   # (FL+RL) - (FR+RR)
pitch_proxy = (m0 + m1) - (m2 + m3)   # (FR+FL) - (RL+RR)
yaw_proxy   = (m1 + m3) - (m0 + m2)   # (FL+RR) - (FR+RL)
```

These are the algebraic inverse of `QuadXMixer.mix`'s own forward
formulas (by construction of that linear system) — not a new physics
claim, just the geometric counterpart of the same documented X layout.

No `write_gpio`/`open_serial`/`send_dshot`/`fly`/`arm_motors_hardware`
anywhere in this module — this is toy attitude-only integration, never
actuation, and never a claim that any real vehicle is airborne.

**Fase C · C36 (`B1-fase-c-sim-6dof-plant`) adds `ToyQuad6DofPlant`** —
`ToyQuadAttitudePlant` above is unchanged, byte-for-byte, and stays the
only plant C11/C13's own closed-loop tilt-recovery smoke uses.
`ToyQuad6DofPlant` is a **second, separate** toy plant: same toy
attitude dynamics (identical motor->torque-proxy formulas, identical
`torque_gain`/`angular_damping` integration) **plus** a toy translation
law that lets the mixer's forces move a body through ENU space, not
just tilt it in place.

**Translation law (C36 IC §0 decision 7, exactly one toy map):**
`thrust_body = (0, 0, thrust_gain * sum(motor_forces))` — a single toy
scalar (`thrust_gain`, finite, `> 0`) turns the four normalized mixer
force numbers into a body-frame `+Z` thrust; `mass_kg` (finite, `> 0`)
is likewise a toy scalar, never sourced from any real hardware/catalog
(MY5 or otherwise). `a_world = R(q) * (thrust_body / mass_kg) +
g_world`, with `g_world = (0, 0, -9.81)` (ENU, matching C7/C11).
Integration is **semi-implicit ("symplectic") Euler**: velocity
advances first (`v += a * dt`), then position advances using that
*already-updated* velocity (`p += v_new * dt`) — a standard, simple,
stable choice for a toy integrator, not a claim of any particular
numerical-methods rigor. The thrust direction for a given `step()` call
uses the attitude **at the start of that step** (before this same
call's attitude integration), not the just-integrated end-of-step
attitude — i.e. attitude and translation are advanced from the same
starting state each step, kept simple and documented rather than
inventing a sub-stepped coupling.

**IMU honesty (C36 IC §0 decision 8, locked):** `ImuSample` from
`ToyQuad6DofPlant` stays **exactly as attitude-shaped as C11's own** —
`gyro_rad_s = omega`, `accel_mps2 = R^T(q) * g_world` (gravity rotated
into body frame from the plant's own **true** attitude). The plant's
own linear acceleration (thrust minus gravity) is **not** folded into
`ImuSample` this Buy — pose truth lives only on the plant's own
`true_position_m`/`true_velocity_mps` getters. This is deliberate: C7's
complementary filter expects "down" from the accelerometer reading;
injecting hover specific-force into that channel would fight the
filter's own gravity-referencing assumption. A specific-force-aware
IMU, if ever wanted, is an explicitly separate, future IC — not
something this Buy quietly slips in.

**`FlightControlLoop.step` stays byte-unchanged in role:** it still
never calls any plant, `ToyQuad6DofPlant` included. The caller pattern
is unchanged from C11/C24: `sample = plant.step(loop.step(sample,
setpoint, collective).forces, dt_s=dt_s)`, entirely outside `step`
itself.

**Non-goals (C36 IC §2, explicitly out of this Buy):** no magnetometer/
yaw reference (C37), no altitude or position **controller** (C38/C39
— this Buy provides truth for those loops to later sense, not a loop
that closes on it), no autonomy executor (C40), no Safety policy change
(C41), no ICM/gyro client wiring (C42), no craft/`library/`/Board
coupling (C43), no GPIO/DShot/serial, no MY5 mass/inertia cited as this
plant's default, no `fly()`/product CFD/aero solver.
"""

from __future__ import annotations

import math

from jarvis.flight_software.flight_control.attitude import AttitudeState, Quat
from jarvis.flight_software.flight_control.mixer import MotorForceCommand
from jarvis.flight_software.flight_control.types import ImuSample, Vec3

_DEFAULT_TORQUE_GAIN = 40.0
_DEFAULT_ANGULAR_DAMPING = 0.5
_GRAVITY_MPS2 = 9.81
_IDENTITY_QUAT: Quat = (1.0, 0.0, 0.0, 0.0)
_ZERO_VEC3: Vec3 = (0.0, 0.0, 0.0)
_WORLD_GRAVITY_ENU: Vec3 = (0.0, 0.0, -_GRAVITY_MPS2)

# C36 — toy 6-DoF translation defaults. Both arbitrary, documented toy
# tuning constants (same status as _DEFAULT_TORQUE_GAIN above) — never
# sourced from any real hardware/catalog mass or thrust curve.
_DEFAULT_MASS_KG = 1.0
_DEFAULT_6DOF_THRUST_GAIN = 20.0


class ToyQuadAttitudePlant:
    """Toy, attitude-only rigid-body-ish dynamics. `torque_gain` (must be
    finite and `> 0`) scales the motor-force differential proxies into a
    toy angular acceleration; `angular_damping` (must be finite and `>= 0`)
    is a toy passive damping term. Deterministic — no noise added, unlike
    `SimulatedImuHal` (C3), which is intentional: this tip's pass
    criterion is about closed-loop convergence, not sensor realism."""

    def __init__(
        self,
        torque_gain: float = _DEFAULT_TORQUE_GAIN,
        angular_damping: float = _DEFAULT_ANGULAR_DAMPING,
    ) -> None:
        if not math.isfinite(torque_gain) or torque_gain <= 0.0:
            raise ValueError("torque_gain must be finite and > 0")
        if not math.isfinite(angular_damping) or angular_damping < 0.0:
            raise ValueError("angular_damping must be finite and >= 0")
        self._torque_gain = torque_gain
        self._angular_damping = angular_damping
        self._q: Quat = _IDENTITY_QUAT
        self._omega: Vec3 = _ZERO_VEC3
        self._t_s = 0.0

    def reset(self, initial_q: Quat = _IDENTITY_QUAT, initial_omega: Vec3 = _ZERO_VEC3) -> None:
        self._q = _quat_normalize(initial_q)
        self._omega = initial_omega
        self._t_s = 0.0

    @property
    def true_attitude(self) -> AttitudeState:
        """The plant's own true state — never an estimate. Tests use this
        to check closed-loop convergence honestly, independent of
        whatever C7's estimator currently believes."""
        return AttitudeState(
            t_s=self._t_s, q_body_to_world=self._q, omega_body_rad_s=self._omega, frame="enu"
        )

    def sense(self) -> ImuSample:
        """Reads the current true state as an `ImuSample` **without**
        advancing dynamics — used to seed a closed loop before any forces
        have been computed yet."""
        return ImuSample(
            t_s=self._t_s,
            accel_mps2=_rotate_vector(_quat_conjugate(self._q), _WORLD_GRAVITY_ENU),
            gyro_rad_s=self._omega,
        )

    def step(self, forces: MotorForceCommand, *, dt_s: float) -> ImuSample:
        if not math.isfinite(dt_s) or dt_s <= 0.0:
            raise ValueError("dt_s must be finite and > 0")

        fr, fl, rl, rr = forces.motor_forces
        roll_proxy = (fl + rl) - (fr + rr)
        pitch_proxy = (fr + fl) - (rl + rr)
        yaw_proxy = (fl + rr) - (fr + rl)

        angular_accel = (
            self._torque_gain * roll_proxy - self._angular_damping * self._omega[0],
            self._torque_gain * pitch_proxy - self._angular_damping * self._omega[1],
            self._torque_gain * yaw_proxy - self._angular_damping * self._omega[2],
        )

        new_omega = (
            self._omega[0] + angular_accel[0] * dt_s,
            self._omega[1] + angular_accel[1] * dt_s,
            self._omega[2] + angular_accel[2] * dt_s,
        )
        axis_angle = (new_omega[0] * dt_s, new_omega[1] * dt_s, new_omega[2] * dt_s)
        new_q = _quat_normalize(_quat_multiply(self._q, _quat_from_small_angle(axis_angle)))

        self._omega = new_omega
        self._q = new_q
        self._t_s += dt_s

        return ImuSample(
            t_s=self._t_s,
            accel_mps2=_rotate_vector(_quat_conjugate(new_q), _WORLD_GRAVITY_ENU),
            gyro_rad_s=new_omega,
        )


class ToyQuad6DofPlant:
    """Toy rigid-body-ish dynamics with attitude **and** translation —
    see this module's own docstring (C36) for the full honesty
    statement. `mass_kg`/`thrust_gain` (both finite, `> 0`) are toy
    translation tuning constants; `torque_gain`/`angular_damping` are
    the same C11 attitude constants, unchanged in meaning. Deterministic
    — no noise, same as `ToyQuadAttitudePlant`."""

    def __init__(
        self,
        mass_kg: float = _DEFAULT_MASS_KG,
        thrust_gain: float = _DEFAULT_6DOF_THRUST_GAIN,
        torque_gain: float = _DEFAULT_TORQUE_GAIN,
        angular_damping: float = _DEFAULT_ANGULAR_DAMPING,
    ) -> None:
        if not math.isfinite(mass_kg) or mass_kg <= 0.0:
            raise ValueError("mass_kg must be finite and > 0")
        if not math.isfinite(thrust_gain) or thrust_gain <= 0.0:
            raise ValueError("thrust_gain must be finite and > 0")
        if not math.isfinite(torque_gain) or torque_gain <= 0.0:
            raise ValueError("torque_gain must be finite and > 0")
        if not math.isfinite(angular_damping) or angular_damping < 0.0:
            raise ValueError("angular_damping must be finite and >= 0")
        self._mass_kg = mass_kg
        self._thrust_gain = thrust_gain
        self._torque_gain = torque_gain
        self._angular_damping = angular_damping
        self._q: Quat = _IDENTITY_QUAT
        self._omega: Vec3 = _ZERO_VEC3
        self._position_m: Vec3 = _ZERO_VEC3
        self._velocity_mps: Vec3 = _ZERO_VEC3
        self._t_s = 0.0

    def reset(
        self,
        position_m: Vec3 = _ZERO_VEC3,
        velocity_mps: Vec3 = _ZERO_VEC3,
        initial_q: Quat = _IDENTITY_QUAT,
        initial_omega: Vec3 = _ZERO_VEC3,
    ) -> None:
        self._position_m = position_m
        self._velocity_mps = velocity_mps
        self._q = _quat_normalize(initial_q)
        self._omega = initial_omega
        self._t_s = 0.0

    @property
    def true_attitude(self) -> AttitudeState:
        """The plant's own true attitude — never an estimate."""
        return AttitudeState(
            t_s=self._t_s, q_body_to_world=self._q, omega_body_rad_s=self._omega, frame="enu"
        )

    @property
    def true_position_m(self) -> Vec3:
        """The plant's own true ENU position — never an estimate. No
        estimator in this ladder currently consumes this; tests assert
        against it directly, matching `true_attitude`'s own role."""
        return self._position_m

    @property
    def true_velocity_mps(self) -> Vec3:
        """The plant's own true ENU velocity — never an estimate."""
        return self._velocity_mps

    def sense(self) -> ImuSample:
        """Reads the current true state as a C11-shaped `ImuSample`
        (gravity in body frame + gyro) **without** advancing dynamics.
        No specific-force/linear-acceleration term — see this module's
        own C36 honesty note."""
        return ImuSample(
            t_s=self._t_s,
            accel_mps2=_rotate_vector(_quat_conjugate(self._q), _WORLD_GRAVITY_ENU),
            gyro_rad_s=self._omega,
        )

    def step(self, forces: MotorForceCommand, *, dt_s: float) -> ImuSample:
        if not math.isfinite(dt_s) or dt_s <= 0.0:
            raise ValueError("dt_s must be finite and > 0")

        fr, fl, rl, rr = forces.motor_forces

        # Attitude integration — identical formulas to ToyQuadAttitudePlant.
        roll_proxy = (fl + rl) - (fr + rr)
        pitch_proxy = (fr + fl) - (rl + rr)
        yaw_proxy = (fl + rr) - (fr + rl)

        angular_accel = (
            self._torque_gain * roll_proxy - self._angular_damping * self._omega[0],
            self._torque_gain * pitch_proxy - self._angular_damping * self._omega[1],
            self._torque_gain * yaw_proxy - self._angular_damping * self._omega[2],
        )
        new_omega = (
            self._omega[0] + angular_accel[0] * dt_s,
            self._omega[1] + angular_accel[1] * dt_s,
            self._omega[2] + angular_accel[2] * dt_s,
        )
        axis_angle = (new_omega[0] * dt_s, new_omega[1] * dt_s, new_omega[2] * dt_s)
        new_q = _quat_normalize(_quat_multiply(self._q, _quat_from_small_angle(axis_angle)))

        # Translation integration — the one new toy map this Buy adds.
        # Thrust direction uses self._q (the attitude at the START of
        # this step), not new_q — documented in this module's own C36
        # note above.
        thrust_sum = fr + fl + rl + rr
        thrust_body: Vec3 = (0.0, 0.0, self._thrust_gain * thrust_sum)
        thrust_world = _rotate_vector(self._q, thrust_body)
        accel_world = (
            thrust_world[0] / self._mass_kg + _WORLD_GRAVITY_ENU[0],
            thrust_world[1] / self._mass_kg + _WORLD_GRAVITY_ENU[1],
            thrust_world[2] / self._mass_kg + _WORLD_GRAVITY_ENU[2],
        )
        new_velocity = (
            self._velocity_mps[0] + accel_world[0] * dt_s,
            self._velocity_mps[1] + accel_world[1] * dt_s,
            self._velocity_mps[2] + accel_world[2] * dt_s,
        )
        # Semi-implicit Euler: position uses the just-updated velocity.
        new_position = (
            self._position_m[0] + new_velocity[0] * dt_s,
            self._position_m[1] + new_velocity[1] * dt_s,
            self._position_m[2] + new_velocity[2] * dt_s,
        )

        self._omega = new_omega
        self._q = new_q
        self._velocity_mps = new_velocity
        self._position_m = new_position
        self._t_s += dt_s

        return ImuSample(
            t_s=self._t_s,
            accel_mps2=_rotate_vector(_quat_conjugate(new_q), _WORLD_GRAVITY_ENU),
            gyro_rad_s=new_omega,
        )


def tilt_angle_rad(q: Quat) -> float:
    """Angle (radians, always `>= 0`) between `q` and the identity/level
    orientation — `2 * acos(|w|)`. Used to measure closed-loop
    convergence against the plant's own **true** attitude, never against
    the estimator's belief (which may still be settling)."""
    w = max(-1.0, min(1.0, q[0]))
    return 2.0 * math.acos(abs(w))


def _quat_normalize(q: Quat) -> Quat:
    w, x, y, z = q
    norm = math.sqrt(w * w + x * x + y * y + z * z)
    if norm < 1e-12:
        return _IDENTITY_QUAT
    return (w / norm, x / norm, y / norm, z / norm)


def _quat_multiply(a: Quat, b: Quat) -> Quat:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    )


def _quat_conjugate(q: Quat) -> Quat:
    w, x, y, z = q
    return (w, -x, -y, -z)


def _quat_from_small_angle(axis_angle: Vec3) -> Quat:
    x, y, z = axis_angle
    return _quat_normalize((1.0, x / 2.0, y / 2.0, z / 2.0))


def _rotate_vector(q: Quat, v: Vec3) -> Vec3:
    qv: Quat = (0.0, v[0], v[1], v[2])
    result = _quat_multiply(_quat_multiply(q, qv), _quat_conjugate(q))
    return (result[1], result[2], result[3])
