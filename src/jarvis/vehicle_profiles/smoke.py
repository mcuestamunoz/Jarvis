"""Fase C · C3+C6+C7+C8+C9+C10+C11+C12 — pytest smoke path only (not
Engineer Board smoke).

Python scaffold / sim only — production flight_control runtime is C++
(future IC). `run_hal_imu_smoke` loads a vehicle profile, builds a
`SimulatedImuHal` from it, and reads samples. `run_hal_imu_filter_smoke`
(C6) does the same but pipes each raw sample through an
`ImuLowPassFilter` — still sensing post-process, not estimation.
`run_hal_imu_attitude_smoke` (C7) pipes each raw sample through the C6
filter and then through a `ComplementaryAttitudeEstimator` — state
estimation, still not control/actuation. `run_attitude_controller_smoke`
(C8) takes ≥1 `AttitudeState` (from a synthetic sequence, not requiring
live HAL) and a level `AttitudeSetpoint`, and runs them through a
`PdAttitudeController` to produce `BodyRateCommand`s — still not
actuation, there is no motor to command. `run_mixer_smoke` (C9) chains
the full C3→C9 pipeline, converts each `BodyRateCommand` to a
`BodyTorqueCommand` via the C12 `LinearRateTorqueBridge`, and finishes by
piping that through a `QuadXMixer` with a hover-range collective — still
not actuation, there is no ESC to write to. `run_esc_pwm_smoke` (C10)
chains the full C3→C10 pipeline (through the same C12 bridge), encoding
each `MotorForceCommand` to PWM µs and applying it to a
`SimulatedEscSink` (disarmed by default) — still not actuation, there is
no pin/port/socket anywhere in this package. `run_controlled_flight_sim_smoke`
(C11, updated for C12; refactored for C24) closes the C0 §7 wooden-ladder
tip: a `ToyQuadAttitudePlant` seeded at a documented tilt feeds
`ImuSample`s through a `FlightControlLoop.step` call (C24's own named
tick — filter→estimate→PD→bridge→mix, unchanged order/math, now called
by name instead of inlined), whose `MotorForceCommand` output is fed back
into the plant — still not actuation, the plant is a toy attitude-only
sim, never hardware, and `step` itself never calls the plant.
`run_open_loop_baseline_smoke` runs the same plant with a constant,
uncorrected mix (zero commanded body torque, via the bridge on a
zero-rate command) for comparison — with zero initial rate and zero
corrective torque, this plant's tilt error stays exactly constant,
showing the closed loop above is doing real work, not just numerical
decay. None of these call `SafetyGate.evaluate` for an `allow` outcome
and none touch any actuator — there is none to touch. Reuses the
existing `smoke_quad_hal_imu` profile id — no new `VehicleProfile`
field, no new profile JSON, no schema change for C7 through C12.
"""

from __future__ import annotations

import math

from jarvis.flight_software.flight_control.attitude import (
    AttitudeState,
    ComplementaryAttitudeEstimator,
)
from jarvis.flight_software.flight_control.controller import (
    BodyRateCommand,
    PdAttitudeController,
    level_setpoint,
)
from jarvis.flight_software.flight_control.esc import (
    EscApplyResult,
    SimulatedEscSink,
    encode_motor_forces,
)
from jarvis.flight_software.flight_control.filter import ImuLowPassFilter
from jarvis.flight_software.flight_control.loop import FlightControlLoop
from jarvis.flight_software.flight_control.mixer import (
    MotorForceCommand,
    QuadXMixer,
    hover_collective,
)
from jarvis.flight_software.flight_control.altitude_controller import AltitudeController
from jarvis.flight_software.flight_control.plant import (
    ToyQuad6DofPlant,
    ToyQuadAttitudePlant,
    tilt_angle_rad,
)
from jarvis.flight_software.flight_control.position_controller import PositionController, PositionSetpoint
from jarvis.flight_software.flight_control.sim_altitude_hal import SimulatedAltitudeHal
from jarvis.flight_software.flight_control.sim_position_hal import SimulatedPositionHal
from jarvis.flight_software.flight_control.rate_torque import LinearRateTorqueBridge
from jarvis.flight_software.flight_control.sim_imu_hal import SimulatedImuHal
from jarvis.flight_software.flight_control.types import ImuSample
from jarvis.vehicle_profiles.loader import load_profile


def run_hal_imu_smoke(
    profile_id: str = "smoke_quad_hal_imu", samples: int = 1
) -> list[ImuSample]:
    profile = load_profile(profile_id)
    assert profile.rung == "hal_imu"
    hal = SimulatedImuHal(seed=0)
    return [hal.read_imu() for _ in range(max(1, samples))]


def run_hal_imu_filter_smoke(
    profile_id: str = "smoke_quad_hal_imu", samples: int = 1, alpha: float = 0.2
) -> list[ImuSample]:
    profile = load_profile(profile_id)
    assert profile.rung == "hal_imu"
    hal = SimulatedImuHal(seed=0)
    filt = ImuLowPassFilter(alpha=alpha)
    return [filt.filter_sample(hal.read_imu()) for _ in range(max(1, samples))]


def run_hal_imu_attitude_smoke(
    profile_id: str = "smoke_quad_hal_imu",
    samples: int = 1,
    alpha: float = 0.2,
    gain: float = 0.02,
) -> list[AttitudeState]:
    profile = load_profile(profile_id)
    assert profile.rung == "hal_imu"
    hal = SimulatedImuHal(seed=0)
    filt = ImuLowPassFilter(alpha=alpha)
    estimator = ComplementaryAttitudeEstimator(gain=gain)
    results: list[AttitudeState] = []
    for _ in range(max(1, samples)):
        filtered = filt.filter_sample(hal.read_imu())
        results.append(estimator.update(filtered))
    return results


def run_attitude_controller_smoke(
    profile_id: str = "smoke_quad_hal_imu",
    samples: int = 1,
    alpha: float = 0.2,
    gain: float = 0.02,
    kp: float = 6.0,
    kd: float = 0.6,
) -> list[BodyRateCommand]:
    profile = load_profile(profile_id)
    assert profile.rung == "hal_imu"
    hal = SimulatedImuHal(seed=0)
    filt = ImuLowPassFilter(alpha=alpha)
    estimator = ComplementaryAttitudeEstimator(gain=gain)
    controller = PdAttitudeController(kp=kp, kd=kd)
    results: list[BodyRateCommand] = []
    for _ in range(max(1, samples)):
        filtered = filt.filter_sample(hal.read_imu())
        state = estimator.update(filtered)
        setpoint = level_setpoint(state.t_s)
        results.append(controller.compute(setpoint, state))
    return results


def run_mixer_smoke(
    profile_id: str = "smoke_quad_hal_imu",
    samples: int = 1,
    alpha: float = 0.2,
    gain: float = 0.02,
    kp: float = 6.0,
    kd: float = 0.6,
    collective: float = hover_collective(),
) -> list[MotorForceCommand]:
    profile = load_profile(profile_id)
    assert profile.rung == "hal_imu"
    hal = SimulatedImuHal(seed=0)
    filt = ImuLowPassFilter(alpha=alpha)
    estimator = ComplementaryAttitudeEstimator(gain=gain)
    controller = PdAttitudeController(kp=kp, kd=kd)
    bridge = LinearRateTorqueBridge()
    mixer = QuadXMixer()
    results: list[MotorForceCommand] = []
    for _ in range(max(1, samples)):
        filtered = filt.filter_sample(hal.read_imu())
        state = estimator.update(filtered)
        setpoint = level_setpoint(state.t_s)
        rate_cmd = controller.compute(setpoint, state)
        torque_cmd = bridge.convert(rate_cmd)
        results.append(mixer.mix(collective, torque_cmd))
    return results


def run_esc_pwm_smoke(
    profile_id: str = "smoke_quad_hal_imu",
    samples: int = 1,
    alpha: float = 0.2,
    gain: float = 0.02,
    kp: float = 6.0,
    kd: float = 0.6,
    collective: float = hover_collective(),
    armed: bool = False,
) -> list[EscApplyResult]:
    profile = load_profile(profile_id)
    assert profile.rung == "hal_imu"
    hal = SimulatedImuHal(seed=0)
    filt = ImuLowPassFilter(alpha=alpha)
    estimator = ComplementaryAttitudeEstimator(gain=gain)
    controller = PdAttitudeController(kp=kp, kd=kd)
    bridge = LinearRateTorqueBridge()
    mixer = QuadXMixer()
    sink = SimulatedEscSink()
    if armed:
        sink.arm()
    results: list[EscApplyResult] = []
    for _ in range(max(1, samples)):
        filtered = filt.filter_sample(hal.read_imu())
        state = estimator.update(filtered)
        setpoint = level_setpoint(state.t_s)
        rate_cmd = controller.compute(setpoint, state)
        torque_cmd = bridge.convert(rate_cmd)
        forces = mixer.mix(collective, torque_cmd)
        pwm_cmd = encode_motor_forces(forces)
        results.append(sink.apply(pwm_cmd))
    return results


def _tilted_initial_quat(tilt_rad: float) -> tuple[float, float, float, float]:
    half = tilt_rad / 2.0
    return (math.cos(half), math.sin(half), 0.0, 0.0)


def run_controlled_flight_sim_smoke(
    steps: int = 200,
    dt_s: float = 0.01,
    initial_tilt_rad: float = math.radians(15.0),
    alpha: float = 0.2,
    gain: float = 0.05,
    kp: float = 6.0,
    kd: float = 0.6,
    collective: float = hover_collective(),
    torque_gain: float = 40.0,
    angular_damping: float = 0.5,
) -> list[float]:
    """Closes the C0 §7 wooden-ladder tip: `FlightControlLoop.step`
    (C24's named tick: filter -> estimate -> PD -> bridge -> mix) then
    `plant.step`, in a loop — the tick itself never calls the plant.
    Returns the **true** tilt-error series (radians, plant's own true
    attitude vs level — never the estimator's belief), one entry per step
    plus the initial value."""
    plant = ToyQuadAttitudePlant(torque_gain=torque_gain, angular_damping=angular_damping)
    plant.reset(initial_q=_tilted_initial_quat(initial_tilt_rad))

    filt = ImuLowPassFilter(alpha=alpha)
    estimator = ComplementaryAttitudeEstimator(gain=gain)
    controller = PdAttitudeController(kp=kp, kd=kd)
    bridge = LinearRateTorqueBridge()
    mixer = QuadXMixer()
    loop = FlightControlLoop(
        filt=filt, estimator=estimator, controller=controller, bridge=bridge, mixer=mixer
    )

    tilt_errors_rad = [tilt_angle_rad(plant.true_attitude.q_body_to_world)]
    sample = plant.sense()
    for _ in range(max(1, steps)):
        setpoint = level_setpoint(sample.t_s)
        tick = loop.step(sample, setpoint, collective)
        sample = plant.step(tick.forces, dt_s=dt_s)
        tilt_errors_rad.append(tilt_angle_rad(plant.true_attitude.q_body_to_world))
    return tilt_errors_rad


def run_sim_6dof_smoke(
    steps: int = 50,
    dt_s: float = 0.01,
    initial_tilt_rad: float = math.radians(5.0),
    collective: float = hover_collective(),
    mass_kg: float = 1.0,
    thrust_gain: float = 20.0,
    torque_gain: float = 40.0,
    angular_damping: float = 0.5,
) -> list[tuple[float, float, float]]:
    """C36 (`B1-fase-c-sim-6dof-plant`) — a thin smoke chaining
    `FlightControlLoop.step` (C24's own named tick, still never calling
    any plant) with `ToyQuad6DofPlant.step`, seeded at a small documented
    tilt (default 5 degrees about the pitch axis) plus a hover-range
    collective, showing the resulting ENU pose actually moves — both
    climbing (net thrust vs gravity) and drifting horizontally (the
    tilt). Returns the true-position series, one entry per step plus the
    initial value. Not a controller and not proof any loop drives this
    plant anywhere in particular — `level_setpoint` still targets level,
    the plant simply has somewhere to go now."""
    plant = ToyQuad6DofPlant(
        mass_kg=mass_kg, thrust_gain=thrust_gain, torque_gain=torque_gain, angular_damping=angular_damping
    )
    plant.reset(initial_q=_tilted_initial_quat(initial_tilt_rad))

    filt = ImuLowPassFilter()
    estimator = ComplementaryAttitudeEstimator()
    controller = PdAttitudeController()
    bridge = LinearRateTorqueBridge()
    mixer = QuadXMixer()
    loop = FlightControlLoop(
        filt=filt, estimator=estimator, controller=controller, bridge=bridge, mixer=mixer
    )

    positions = [plant.true_position_m]
    sample = plant.sense()
    for _ in range(max(1, steps)):
        setpoint = level_setpoint(sample.t_s)
        tick = loop.step(sample, setpoint, collective)
        sample = plant.step(tick.forces, dt_s=dt_s)
        positions.append(plant.true_position_m)
    return positions


def run_altitude_loop_smoke(
    steps: int = 500,
    dt_s: float = 0.01,
    z_des_m: float = 2.0,
    mass_kg: float = 1.0,
    thrust_gain: float = 20.0,
    torque_gain: float = 40.0,
    angular_damping: float = 0.5,
    kp: float = 0.2,
    kd: float = 0.3,
    hover_bias: float = 9.81 / (4.0 * 20.0),
) -> list[float]:
    """C38 (`B1-fase-c-altitude-loop`) — a thin smoke chaining
    `AltitudeController.compute` -> `FlightControlLoop.step` (C24's own
    named tick, still never calling any plant) -> `ToyQuad6DofPlant.step`,
    starting at `z=0` with a documented `z_des_m`, showing the resulting
    true altitude climbs and `|z - z_des_m|` shrinks over `steps`. The
    attitude setpoint passed to `step` stays `level_setpoint` throughout
    — this Buy does not touch RC/mag, only the `collective` argument.
    Returns the true-altitude series, one entry per step plus the
    initial value. `hover_bias` defaults to the toy hover point matching
    this smoke's own `mass_kg`/`thrust_gain` (see `altitude_controller.py`'s
    own disclosed-deviation note for why, not `hover_collective()`)."""
    plant = ToyQuad6DofPlant(
        mass_kg=mass_kg, thrust_gain=thrust_gain, torque_gain=torque_gain, angular_damping=angular_damping
    )
    loop = FlightControlLoop()
    hal = SimulatedAltitudeHal()
    alt_controller = AltitudeController(kp=kp, kd=kd, hover_bias=hover_bias)

    altitudes = [plant.true_position_m[2]]
    sample = plant.sense()
    for _ in range(max(1, steps)):
        altitude = hal.read_altitude(plant.true_position_m[2], sample.t_s)
        vz_mps = plant.true_velocity_mps[2]
        collective = alt_controller.compute(z_des_m, altitude, vz_mps)
        setpoint = level_setpoint(sample.t_s)
        tick = loop.step(sample, setpoint, collective)
        sample = plant.step(tick.forces, dt_s=dt_s)
        altitudes.append(plant.true_position_m[2])
    return altitudes


def run_position_loop_smoke(
    steps: int = 1000,
    dt_s: float = 0.01,
    x_des_m: float = 5.0,
    y_des_m: float = 0.0,
    z_des_m: float = 2.0,
    mass_kg: float = 1.0,
    thrust_gain: float = 20.0,
    torque_gain: float = 40.0,
    angular_damping: float = 0.5,
    pos_kp: float = 0.15,
    pos_kd: float = 0.3,
    alt_kp: float = 0.2,
    alt_kd: float = 0.3,
    hover_bias: float = 9.81 / (4.0 * 20.0),
) -> list[tuple[float, float, float]]:
    """C39 (`B1-fase-c-position-loop`) — a thin smoke chaining
    `PositionController.compute` (setpoint) + `AltitudeController.compute`
    (collective, C38, unchanged) -> `FlightControlLoop.step` (C24's own
    named tick, still never calling any plant) -> `ToyQuad6DofPlant.step`,
    starting at `(0, 0, 0)` with documented `x_des_m`/`y_des_m`/`z_des_m`,
    showing horizontal distance to the position setpoint shrinks while
    altitude is held near `z_des_m` by the unchanged C38 controller.
    Returns the true `(x, y, z)` series, one entry per step plus the
    initial value."""
    plant = ToyQuad6DofPlant(
        mass_kg=mass_kg, thrust_gain=thrust_gain, torque_gain=torque_gain, angular_damping=angular_damping
    )
    loop = FlightControlLoop()
    pos_hal = SimulatedPositionHal()
    pos_controller = PositionController(kp=pos_kp, kd=pos_kd)
    alt_hal = SimulatedAltitudeHal()
    alt_controller = AltitudeController(kp=alt_kp, kd=alt_kd, hover_bias=hover_bias)
    pos_setpoint = PositionSetpoint(x_m=x_des_m, y_m=y_des_m)

    positions = [plant.true_position_m]
    sample = plant.sense()
    for _ in range(max(1, steps)):
        position = pos_hal.read_position(plant.true_position_m[0], plant.true_position_m[1], sample.t_s)
        altitude = alt_hal.read_altitude(plant.true_position_m[2], sample.t_s)
        vx_mps, vy_mps, vz_mps = plant.true_velocity_mps
        setpoint = pos_controller.compute(pos_setpoint, position, vx_mps, vy_mps, sample.t_s)
        collective = alt_controller.compute(z_des_m, altitude, vz_mps)
        tick = loop.step(sample, setpoint, collective)
        sample = plant.step(tick.forces, dt_s=dt_s)
        positions.append(plant.true_position_m)
    return positions


def run_open_loop_baseline_smoke(
    steps: int = 200,
    dt_s: float = 0.01,
    initial_tilt_rad: float = math.radians(15.0),
    collective: float = hover_collective(),
    torque_gain: float = 40.0,
    angular_damping: float = 0.5,
) -> list[float]:
    """No-control baseline (for comparison against
    `run_controlled_flight_sim_smoke`): applies a constant, uncorrected
    hover mix every step (zero commanded body rate) instead of running
    filter/estimator/controller at all."""
    plant = ToyQuadAttitudePlant(torque_gain=torque_gain, angular_damping=angular_damping)
    plant.reset(initial_q=_tilted_initial_quat(initial_tilt_rad))
    bridge = LinearRateTorqueBridge()
    mixer = QuadXMixer()
    zero_rate_cmd = BodyRateCommand(t_s=0.0, omega_body_rad_s=(0.0, 0.0, 0.0))
    zero_torque_cmd = bridge.convert(zero_rate_cmd)

    tilt_errors_rad = [tilt_angle_rad(plant.true_attitude.q_body_to_world)]
    for _ in range(max(1, steps)):
        forces = mixer.mix(collective, zero_torque_cmd)
        plant.step(forces, dt_s=dt_s)
        tilt_errors_rad.append(tilt_angle_rad(plant.true_attitude.q_body_to_world))
    return tilt_errors_rad
