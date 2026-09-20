"""Fase C · C3 — `SimulatedImuHal`: deterministic synthetic IMU samples.

Python scaffold / sim only — production flight_control runtime is C++
(future IC). No real MCU / I2C / SPI / UART drivers, no network sockets,
no claim that hardware is present, and no presentation of this class as
"product-ready" — this is the only HAL shipped in C3, and it never
touches a physical bus or a real control loop. Given the same `seed`,
`read_imu()` produces the exact same sequence of samples every run
(`random.Random(seed)` is deterministic by construction), which is what
the C3 IC's T2 checks.
"""

from __future__ import annotations

import random

from jarvis.flight_software.flight_control.types import ImuSample

_DT_S = 0.01
_GRAVITY_MPS2 = 9.81
_NOISE_STD_ACCEL = 0.01
_NOISE_STD_GYRO = 0.001


class SimulatedImuHal:
    def __init__(self, seed: int = 0) -> None:
        self._seed = seed
        self._rng = random.Random(seed)
        self._t_s = 0.0

    def read_imu(self) -> ImuSample:
        sample = ImuSample(
            t_s=self._t_s,
            accel_mps2=(
                self._rng.gauss(0.0, _NOISE_STD_ACCEL),
                self._rng.gauss(0.0, _NOISE_STD_ACCEL),
                -_GRAVITY_MPS2 + self._rng.gauss(0.0, _NOISE_STD_ACCEL),
            ),
            gyro_rad_s=(
                self._rng.gauss(0.0, _NOISE_STD_GYRO),
                self._rng.gauss(0.0, _NOISE_STD_GYRO),
                self._rng.gauss(0.0, _NOISE_STD_GYRO),
            ),
        )
        self._t_s += _DT_S
        return sample

    def reset(self) -> None:
        self._rng = random.Random(self._seed)
        self._t_s = 0.0
