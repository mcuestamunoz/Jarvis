// Fase C · C39 (`B1-fase-c-position-loop`) — `PositionSetpoint` +
// `PositionController`, C++ twin of the Python
// `flight_control/position_controller.py`.
//
// Host scaffold only. An xy -> roll/pitch tilt law, run OUTSIDE
// `ControlLoop::step` — see the Python twin's own module docstring for
// the full sign derivation/proof and disclosed defaults (naming, setpoint
// type, max_tilt_rad reuse, yaw-held-at-0). Mirrors that file exactly.
//
// One law only:
//   pitch_rad = clip(kp*(x_des - x) - kd*vx_mps, -max_tilt_rad, max_tilt_rad)
//   roll_rad  = clip(-(kp*(y_des - y) - kd*vy_mps), -max_tilt_rad, max_tilt_rad)
//   q = roll_pitch_yaw_to_quat(roll_rad, pitch_rad, 0.0)
//
// Signs (derived + proven, same as the Python twin): a positive pitch
// rotates body +Z thrust onto positive world X (East) — no sign flip on
// the pitch term. A positive roll rotates body +Z thrust onto negative
// world Y (South) — hence the sign flip on the roll term. Yaw is always
// held at 0 by this controller's own output.
//
// Not `AutonomyVerb::kGoTo` — this header never includes anything under
// an autonomy/executor path and does not implement that verb (C40, a
// separate, future Buy).
//
// xy -> tilt in RAM != position hold in air != GO_TO executed.
#pragma once

#include "jarvis/fc/controller.hpp"
#include "jarvis/fc/sim_position_hal.hpp"

namespace jarvis::fc {

struct PositionSetpoint {
    double x_m = 0.0;
    double y_m = 0.0;
};

// `kp` (finite, > 0), `kd` (finite, >= 0), `max_tilt_rad` (finite, > 0)
// are all documented toy tuning constants. Default `max_tilt_rad` reuses
// `kRcMaxTiltRad` (rc_setpoint.hpp, C25 — pi/6, 30 degrees). Deterministic
// — no internal state, no noise.
class PositionController {
public:
    explicit PositionController(double kp = 0.15, double kd = 0.3, double max_tilt_rad = 3.14159265358979323846 / 6.0);

    AttitudeSetpoint compute(
        const PositionSetpoint& setpoint, const PositionSample& position, double vx_mps, double vy_mps,
        double t_s) const;

private:
    double kp_;
    double kd_;
    double max_tilt_rad_;
};

}  // namespace jarvis::fc
