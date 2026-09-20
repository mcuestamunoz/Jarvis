"""Fase C · C3+C6+C7+C8+C9 — `vehicle_profiles`: which physical/hardware
configuration a system needs (see `docs/PLATFORM_CAPABILITY_VISION.md`
§4).

Python scaffold / sim only — production flight_control runtime is C++
(future IC). C3 ships exactly one profile, a pytest smoke fixture
(`smoke_quad_hal_imu`) declaring it expects the `hal_imu` rung only — not a
real vehicle, not flight-capable, and not bound to any craft
workspace/BOM/catalog SKU. C6 adds `run_hal_imu_filter_smoke`, the same
smoke path piped through `ImuLowPassFilter` — still sensing, never
estimation. C7 adds `run_hal_imu_attitude_smoke`, the same profile piped
through the C6 filter and then a `ComplementaryAttitudeEstimator` — state
estimation, still not control/actuation. C8 adds
`run_attitude_controller_smoke`, chaining a `PdAttitudeController` on top
— a body-rate command only, never a motor command. C9 adds
`run_mixer_smoke`, chaining a `QuadXMixer` on top — four normalized
motor force numbers only, never PWM/DShot/ESC signaling; no new profile
field/JSON for any of C6/C7/C8/C9. See
`.jes/artifacts/implementation_contract_fase_c_first_fc_rung_b1.md`,
`.jes/artifacts/implementation_contract_fase_c_imu_filtering_rung_b1.md`,
`.jes/artifacts/implementation_contract_fase_c_attitude_estimation_rung_b1.md`,
`.jes/artifacts/implementation_contract_fase_c_attitude_controller_rung_b1.md`,
and
`.jes/artifacts/implementation_contract_fase_c_mixer_rung_b1.md`.
"""

from jarvis.vehicle_profiles.loader import load_profile, load_smoke_profile
from jarvis.vehicle_profiles.schemas import VehicleProfile
from jarvis.vehicle_profiles.smoke import (
    run_attitude_controller_smoke,
    run_hal_imu_attitude_smoke,
    run_hal_imu_filter_smoke,
    run_hal_imu_smoke,
    run_mixer_smoke,
)

__all__ = [
    "VehicleProfile",
    "load_profile",
    "load_smoke_profile",
    "run_attitude_controller_smoke",
    "run_hal_imu_attitude_smoke",
    "run_hal_imu_filter_smoke",
    "run_hal_imu_smoke",
    "run_mixer_smoke",
]
