"""Fase C · C3+C6 — pytest smoke path only (not Engineer Board smoke).

Python scaffold / sim only — production flight_control runtime is C++
(future IC). `run_hal_imu_smoke` loads a vehicle profile, builds a
`SimulatedImuHal` from it, and reads samples. `run_hal_imu_filter_smoke`
(C6) does the same but pipes each raw sample through an
`ImuLowPassFilter` — still sensing post-process, not estimation. Neither
calls `SafetyGate.evaluate` for an `allow` outcome (reading/filtering a
sensor is not actuation) and neither touches any actuator — there is
none to touch in this package.
"""

from __future__ import annotations

from jarvis.flight_software.flight_control.filter import ImuLowPassFilter
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
