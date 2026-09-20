"""Python scaffold / sim only — production flight_control runtime is C++
(future IC). See `jarvis.flight_software`'s package docstring."""

from jarvis.flight_software.flight_control.attitude import (
    AttitudeState,
    ComplementaryAttitudeEstimator,
    read_attitude,
)
from jarvis.flight_software.flight_control.filter import ImuLowPassFilter, read_filtered
from jarvis.flight_software.flight_control.hal import ImuHal
from jarvis.flight_software.flight_control.sim_imu_hal import SimulatedImuHal
from jarvis.flight_software.flight_control.types import ImuSample

__all__ = [
    "AttitudeState",
    "ComplementaryAttitudeEstimator",
    "ImuHal",
    "ImuLowPassFilter",
    "ImuSample",
    "SimulatedImuHal",
    "read_attitude",
    "read_filtered",
]
