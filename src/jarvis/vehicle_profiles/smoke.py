"""Fase C · C3+C6+C7+C8+C9+C10 — pytest smoke path only (not Engineer
Board smoke).

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
the full C3→C9 pipeline and finishes by piping each `BodyRateCommand`
through a `QuadXMixer` with a hover-range collective — still not
actuation, there is no ESC to write to. `run_esc_pwm_smoke` (C10) chains
the full C3→C10 pipeline, encoding each `MotorForceCommand` to PWM µs
and applying it to a `SimulatedEscSink` (disarmed by default) — still
not actuation, there is no pin/port/socket anywhere in this package.
None of these call `SafetyGate.evaluate` for an `allow` outcome and none
touch any actuator — there is none to touch. Reuses the existing
`smoke_quad_hal_imu` profile id — no new `VehicleProfile` field, no new
profile JSON, no schema change for C7, C8, C9, or C10.
"""

from __future__ import annotations

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
from jarvis.flight_software.flight_control.mixer import (
    MotorForceCommand,
    QuadXMixer,
    hover_collective,
)
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
    mixer = QuadXMixer()
    results: list[MotorForceCommand] = []
    for _ in range(max(1, samples)):
        filtered = filt.filter_sample(hal.read_imu())
        state = estimator.update(filtered)
        setpoint = level_setpoint(state.t_s)
        rate_cmd = controller.compute(setpoint, state)
        results.append(mixer.mix(collective, rate_cmd))
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
        forces = mixer.mix(collective, rate_cmd)
        pwm_cmd = encode_motor_forces(forces)
        results.append(sink.apply(pwm_cmd))
    return results
