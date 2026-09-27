"""Fase C · C3+C6+C7+C8+C9+C10+C11 — `vehicle_profiles`: which physical/
hardware configuration a system needs (see
`docs/PLATFORM_CAPABILITY_VISION.md` §4).

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
motor force numbers only, never PWM/DShot/ESC signaling. C10 adds
`run_esc_pwm_smoke`, encoding each force to PWM µs and applying it to a
`SimulatedEscSink` (disarmed by default) — in-memory bookkeeping only,
no pin/port/socket. C11 closes the C0 §7 wooden-ladder tip:
`run_controlled_flight_sim_smoke` feeds a `ToyQuadAttitudePlant`'s own
`ImuSample`s through the C6→C10 chain in a loop, and
`run_open_loop_baseline_smoke` runs the same plant with no correction for
comparison — both toy, attitude-only, sim-only, never hardware; no new
profile field/JSON for any of C6–C11. See
`.jes/artifacts/implementation_contract_fase_c_first_fc_rung_b1.md`,
`.jes/artifacts/implementation_contract_fase_c_imu_filtering_rung_b1.md`,
`.jes/artifacts/implementation_contract_fase_c_attitude_estimation_rung_b1.md`,
`.jes/artifacts/implementation_contract_fase_c_attitude_controller_rung_b1.md`,
`.jes/artifacts/implementation_contract_fase_c_mixer_rung_b1.md`,
`.jes/artifacts/implementation_contract_fase_c_esc_pwm_stub_rung_b1.md`,
and
`.jes/artifacts/implementation_contract_fase_c_controlled_flight_sim_tip_b1.md`.

C43 (`B1-fase-c-craft-fs-bind`) adds a one-way, READ-ONLY bind from a
`VehicleProfile` to craft identity: `bind_profile_to_craft_identity`
(`bind.py`) looks up a catalog SKU via `ComponentLibrary`
(`jarvis.knowledge.library`) and returns a `BoundVehicleProfile` —
identity fields only (sku/manufacturer/model/size_class_inch), never
geometry/mass, never a write to `library/` or any workspace. Direction
is locked: `vehicle_profiles` may read craft identity; craft packages
(`core`/`adapters`/Continuity/CLI/Board) still never import
`jarvis.flight_software`/`jarvis.vehicle_profiles`. See
`.jes/artifacts/implementation_contract_fase_c_craft_fs_bind_b1.md`.
"""

from jarvis.vehicle_profiles.bind import BoundVehicleProfile, bind_profile_to_craft_identity
from jarvis.vehicle_profiles.loader import load_profile, load_smoke_profile, load_this_quad_profile
from jarvis.vehicle_profiles.schemas import VehicleProfile
from jarvis.vehicle_profiles.smoke import (
    run_altitude_loop_smoke,
    run_attitude_controller_smoke,
    run_controlled_flight_sim_smoke,
    run_esc_pwm_smoke,
    run_hal_imu_attitude_smoke,
    run_hal_imu_filter_smoke,
    run_hal_imu_smoke,
    run_mixer_smoke,
    run_open_loop_baseline_smoke,
    run_position_loop_smoke,
    run_sim_6dof_smoke,
)

__all__ = [
    "BoundVehicleProfile",
    "VehicleProfile",
    "bind_profile_to_craft_identity",
    "load_profile",
    "load_smoke_profile",
    "load_this_quad_profile",
    "run_altitude_loop_smoke",
    "run_attitude_controller_smoke",
    "run_controlled_flight_sim_smoke",
    "run_esc_pwm_smoke",
    "run_hal_imu_attitude_smoke",
    "run_hal_imu_filter_smoke",
    "run_hal_imu_smoke",
    "run_mixer_smoke",
    "run_open_loop_baseline_smoke",
    "run_position_loop_smoke",
    "run_sim_6dof_smoke",
]
