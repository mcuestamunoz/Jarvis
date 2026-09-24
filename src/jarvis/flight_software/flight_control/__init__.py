"""Python scaffold / sim only — production flight_control runtime is C++
(future IC). See `jarvis.flight_software`'s package docstring."""

from jarvis.flight_software.flight_control.attitude import (
    AttitudeState,
    ComplementaryAttitudeEstimator,
    read_attitude,
)
from jarvis.flight_software.flight_control.controller import (
    AttitudeSetpoint,
    BodyRateCommand,
    PdAttitudeController,
    level_setpoint,
)
from jarvis.flight_software.flight_control.esc import (
    EscApplyResult,
    EscOutput,
    EscPwmCommand,
    SimulatedEscSink,
    encode_motor_forces,
)
from jarvis.flight_software.flight_control.filter import ImuLowPassFilter, read_filtered
from jarvis.flight_software.flight_control.hal import ImuHal
from jarvis.flight_software.flight_control.loop import ControlTickResult, FlightControlLoop
from jarvis.flight_software.flight_control.mixer import (
    MotorForceCommand,
    QuadXMixer,
    hover_collective,
)
from jarvis.flight_software.flight_control.plant import ToyQuadAttitudePlant, tilt_angle_rad
from jarvis.flight_software.flight_control.rate_torque import (
    BodyTorqueCommand,
    LinearRateTorqueBridge,
)
from jarvis.flight_software.flight_control.sim_imu_hal import SimulatedImuHal
from jarvis.flight_software.flight_control.types import ImuSample

__all__ = [
    "AttitudeSetpoint",
    "AttitudeState",
    "BodyRateCommand",
    "BodyTorqueCommand",
    "ComplementaryAttitudeEstimator",
    "ControlTickResult",
    "EscApplyResult",
    "EscOutput",
    "EscPwmCommand",
    "FlightControlLoop",
    "ImuHal",
    "ImuLowPassFilter",
    "ImuSample",
    "LinearRateTorqueBridge",
    "MotorForceCommand",
    "PdAttitudeController",
    "QuadXMixer",
    "SimulatedEscSink",
    "SimulatedImuHal",
    "ToyQuadAttitudePlant",
    "encode_motor_forces",
    "hover_collective",
    "level_setpoint",
    "read_attitude",
    "read_filtered",
    "tilt_angle_rad",
]
