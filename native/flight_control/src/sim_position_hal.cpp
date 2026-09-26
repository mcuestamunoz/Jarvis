// Fase C · C39 — implementation of `jarvis::fc::SimulatedPositionHal`.
//
// Host scaffold only. See include/jarvis/fc/sim_position_hal.hpp for the
// full honesty statement. No real sensor bus anywhere in this file.
#include "jarvis/fc/sim_position_hal.hpp"

#include <cmath>
#include <stdexcept>

namespace jarvis::fc {

PositionSample SimulatedPositionHal::read_position(
    double true_x_m, double true_y_m, double t_s, std::optional<double> true_z_m) const {
    if (!std::isfinite(true_x_m)) {
        throw std::invalid_argument("true_x_m must be finite");
    }
    if (!std::isfinite(true_y_m)) {
        throw std::invalid_argument("true_y_m must be finite");
    }
    if (true_z_m.has_value() && !std::isfinite(*true_z_m)) {
        throw std::invalid_argument("true_z_m must be finite");
    }
    PositionSample sample;
    sample.t_s = t_s;
    sample.x_m = true_x_m;
    sample.y_m = true_y_m;
    sample.z_m = true_z_m;
    return sample;
}

}  // namespace jarvis::fc
