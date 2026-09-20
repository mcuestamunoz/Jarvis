"""Fase C · C3 — `flight_software`: the vehicle-class CONTROL SPINE.

**Python scaffold / sim only — production flight_control runtime is C++
(future IC).** Engineer amendment on top of the C3 IC: everything under
this package is a platform scaffold written in Python — typed contracts,
`SimulatedImuHal`, a profile smoke helper. It is **not** the production
flight controller. The real flight_control runtime/firmware will be C++,
built in later Buys with its own IC (path/build TBD there) — this Buy
creates no C++ tree and no CMake anywhere in the repo.

**Naming split (honesty-critical — do not conflate):**
- craft catalog `flight_controller` (`library/flight_controller/`, bound via
  `jarvis.core.catalog_bind`) is a **BOM identity record** — a physical part
  the Engineer declares/mounts on a project, with mass/envelope like any
  other component.
- `flight_software.flight_control` (this package) is the **vehicle-class
  control spine** — HAL, sensors, estimation, control, mixer, actuators.
  These are different systems of record and must never be treated as the
  same thing by any reader of this codebase.

This package currently ships exactly **one rung**: HAL + simulated IMU
sample acquisition (`flight_control/`). No filtering, no state estimation,
no attitude/rate/position controller, no mixer, no ESC/PWM, no autonomy
verbs (`TAKEOFF`/`HOLD`/`GO_TO`/...). Nothing here is wired to
`orchestrator.py`, the Board, `library/`, or any `jarvis.capabilities`
Intent adapter — see
`.jes/artifacts/implementation_contract_fase_c_first_fc_rung_b1.md` §0/§3.

This is a sensing-only stub. It does not make any vehicle flyable and must
never be described as such, and this Python code must never be presented
as production-ready flight_control, MCU drivers, or a real control loop —
see `.jes/artifacts/implementation_report_fase_c_first_fc_rung_b1.md`.
"""

from jarvis.flight_software.flight_control.hal import ImuHal
from jarvis.flight_software.flight_control.sim_imu_hal import SimulatedImuHal
from jarvis.flight_software.flight_control.types import ImuSample

__all__ = ["ImuHal", "ImuSample", "SimulatedImuHal"]
