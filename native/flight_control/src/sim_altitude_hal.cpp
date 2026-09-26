// Fase C · C38 — implementation of `jarvis::fc::SimulatedAltitudeHal`.
//
// Host scaffold only. See include/jarvis/fc/sim_altitude_hal.hpp for the
// full honesty statement. No real sensor bus anywhere in this file.
#include "jarvis/fc/sim_altitude_hal.hpp"

#include <cmath>
#include <stdexcept>

namespace jarvis::fc {

AltitudeSample SimulatedAltitudeHal::read_altitude(double true_z_m, double t_s) const {
    if (!std::isfinite(true_z_m)) {
        throw std::invalid_argument("true_z_m must be finite");
    }
    return AltitudeSample{t_s, true_z_m};
}

}  // namespace jarvis::fc
