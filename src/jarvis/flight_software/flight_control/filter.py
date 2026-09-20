"""Fase C · C6 — `ImuLowPassFilter`: the second `flight_control` rung.

Python scaffold / sim only — production flight_control runtime is C++
(future IC). Consumes `ImuSample` streams from C3's HAL (typically
`SimulatedImuHal`) and emits **filtered** `ImuSample` values via a
deterministic first-order low-pass / exponential moving average (EMA)
applied independently to each accel and gyro axis.

This is sensing **post-process**, not estimation: no quaternion, no
Euler angles, no Madgwick/Mahony/EKF, and no attitude output of any
kind — those belong to a later, estimation-class rung (see the C6 IC
§0 decision 4). No actuator field, no `write_motor`/`mix`/`set_pwm`,
anywhere in this module.
"""

from __future__ import annotations

from jarvis.flight_software.flight_control.hal import ImuHal
from jarvis.flight_software.flight_control.types import ImuSample, Vec3

_DEFAULT_ALPHA = 0.2


class ImuLowPassFilter:
    """EMA filter: `filtered = alpha * raw + (1 - alpha) * previous_filtered`,
    applied per axis to `accel_mps2` and `gyro_rad_s`. `t_s` is copied
    verbatim from the raw sample. The first sample after construction or
    `reset()` seeds the filter directly (no smoothing applied yet)."""

    def __init__(self, alpha: float = _DEFAULT_ALPHA) -> None:
        if not (0.0 < alpha <= 1.0):
            raise ValueError("alpha must be in (0, 1]")
        self._alpha = alpha
        self._state: ImuSample | None = None

    def reset(self) -> None:
        """Clears internal state — the next sample seeds the filter."""
        self._state = None

    def filter_sample(self, raw: ImuSample) -> ImuSample:
        if self._state is None:
            filtered = raw
        else:
            filtered = ImuSample(
                t_s=raw.t_s,
                accel_mps2=_ema(self._state.accel_mps2, raw.accel_mps2, self._alpha),
                gyro_rad_s=_ema(self._state.gyro_rad_s, raw.gyro_rad_s, self._alpha),
            )
        self._state = filtered
        return filtered


def _ema(previous: Vec3, current: Vec3, alpha: float) -> Vec3:
    blended = tuple(
        alpha * cur + (1.0 - alpha) * prev for prev, cur in zip(previous, current)
    )
    return (blended[0], blended[1], blended[2])


def read_filtered(hal: ImuHal, filt: ImuLowPassFilter) -> ImuSample:
    """`raw = hal.read_imu(); return filt.filter_sample(raw)` — pure
    pipeline helper, no Safety call, no actuator touched."""
    raw = hal.read_imu()
    return filt.filter_sample(raw)
