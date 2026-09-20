"""Fase C · C3 — `ImuHal`: a sensing-only interface.

Python scaffold / sim only — production flight_control runtime is C++
(future IC). No `write_motor`, `set_pwm`, `arm`, `disarm`, or any
actuation method exists anywhere under `flight_software/` in C3 — locked
by the Implementation Contract §2.2 and audited directly by
`tests/test_fase_c_first_fc_rung_b1.py::test_t3_no_actuator_shaped_methods`.
"""

from __future__ import annotations

from typing import Protocol

from jarvis.flight_software.flight_control.types import ImuSample


class ImuHal(Protocol):
    def read_imu(self) -> ImuSample: ...
