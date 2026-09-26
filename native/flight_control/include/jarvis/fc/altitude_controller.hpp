// Fase C · C38 (`B1-fase-c-altitude-loop`) — `AltitudeController`, C++
// twin of the Python `flight_control/altitude_controller.py`.
//
// Host scaffold only. A z -> collective law, run OUTSIDE
// `ControlLoop::step` — see the Python twin's own module docstring for
// the full derivation and disclosed defaults (hover_bias, kp/kd, vz
// source, naming/setpoint-type choices). Mirrors that file exactly.
//
// One law only: collective = clip(hover_bias + kp*(z_des_m - altitude_m)
// - kd*vz_mps, 0, 1). Stateless, no dt.
//
// z -> collective in RAM != altitude hold in air.
#pragma once

#include "jarvis/fc/sim_altitude_hal.hpp"

namespace jarvis::fc {

// `kp` (finite, > 0), `kd` (finite, >= 0), `hover_bias` (finite, in
// [0, 1]) are all documented toy tuning constants. Defaults match
// ToyQuad6DofPlant's own default constants (mass_kg=1.0,
// thrust_gain=20.0) — see the Python twin's own disclosed-deviation
// note for why this replaces a naive hover_collective()-style default.
class AltitudeController {
public:
    explicit AltitudeController(double kp = 0.2, double kd = 0.3, double hover_bias = 9.81 / (4.0 * 20.0));

    double compute(double z_des_m, const AltitudeSample& altitude, double vz_mps) const;

private:
    double kp_;
    double kd_;
    double hover_bias_;
};

}  // namespace jarvis::fc
