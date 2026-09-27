// Fase C · C40 (`B1-fase-c-autonomy-executor`) — `SimAutonomyExecutor`,
// C++ twin of the Python `flight_software/autonomy/sim_executor.py`.
//
// Host scaffold only. A **separate, sim-only** driver — this tree has no
// C++ port of the C4 command surface (`propose_command`/`submit_command`/
// `AutonomySubmissionResult`, Python-only orchestration types), and this
// header does not add one. `SimAutonomyVerb` below is a small, LOCAL
// enum scoped to this executor only (HOLD/GO_TO/LAND) — it is not, and
// does not attempt to be, a C++ twin of the Python `AutonomyVerb` (which
// has four more members this executor does not drive: TAKEOFF/FOLLOW/
// RETURN_HOME/PATROL).
//
// Reuse, not reinvention: every tick calls, unmodified,
// `PositionController::compute` (C39) and `AltitudeController::compute`
// (C38), then `ControlLoop::step` (C24), then `plant.step` (C36) — see
// the Python twin's own module docstring for the full verb-map
// derivation, the frozen-anchor semantics (HOLD/LAND freeze xy the tick
// they begin; GO_TO's z is frozen only when `z_m` is absent), and the
// disclosed C39 N2 z-droop-under-tilt coupling.
//
// verb -> setpoints in RAM != execute on copper. Sim HOLD/LAND/GO_TO !=
// flying != Safety allow.
#pragma once

#include <optional>

#include "jarvis/fc/altitude_controller.hpp"
#include "jarvis/fc/controller.hpp"
#include "jarvis/fc/loop.hpp"
#include "jarvis/fc/plant.hpp"
#include "jarvis/fc/position_controller.hpp"
#include "jarvis/fc/sim_altitude_hal.hpp"
#include "jarvis/fc/sim_position_hal.hpp"

namespace jarvis::fc {

enum class SimAutonomyVerb {
    kHold,
    kGoTo,
    kLand,
};

struct SimAutonomyParams {
    std::optional<double> x_m{};
    std::optional<double> y_m{};
    std::optional<double> z_m{};
};

struct SimAutonomyTickResult {
    double t_s = 0.0;
    SimAutonomyVerb verb = SimAutonomyVerb::kHold;
    PositionSetpoint xy_setpoint{};
    double z_des_m = 0.0;
    AttitudeSetpoint setpoint{};
    double collective = 0.0;
    ControlTickResult tick{};
};

// Holds a REFERENCE to a caller-owned `ToyQuad6DofPlant` — never
// constructs or owns a plant itself, matching the Python twin. Stateful:
// tracks the current `ImuSample` (advanced by `plant.step` every tick)
// and, per active verb, a frozen anchor point that resets whenever the
// verb changes. `z_land_m` (finite, default `0.0`) and `land_rate_mps`
// (finite, `> 0`, default `0.5`) are documented toy LAND constants.
class SimAutonomyExecutor {
public:
    explicit SimAutonomyExecutor(ToyQuad6DofPlant& plant, double z_land_m = 0.0, double land_rate_mps = 0.5);

    // `sense -> HALs -> pos.compute -> alt.compute -> loop.step ->
    // plant.step`, once, for the given verb. Throws
    // `std::invalid_argument` for non-finite `dt_s`/params or a `kGoTo`
    // missing `x_m`/`y_m`.
    SimAutonomyTickResult tick(SimAutonomyVerb verb, const SimAutonomyParams& params, double dt_s);

private:
    ToyQuad6DofPlant& plant_;
    ControlLoop loop_{};
    SimulatedPositionHal pos_hal_{};
    PositionController pos_controller_{};
    SimulatedAltitudeHal alt_hal_{};
    AltitudeController alt_controller_{};
    double z_land_m_;
    double land_rate_mps_;

    ImuSample sample_;
    std::optional<SimAutonomyVerb> active_verb_{};
    std::optional<PositionSetpoint> hold_setpoint_{};
    std::optional<double> hold_z_des_{};
    std::optional<double> goto_z_des_{};
    std::optional<PositionSetpoint> land_setpoint_{};
    std::optional<double> land_z_des_{};
};

}  // namespace jarvis::fc
