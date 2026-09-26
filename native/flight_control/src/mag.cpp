// Fase C · C37 — implementation of `jarvis::fc::SimulatedMagHal`.
//
// Host scaffold only. See include/jarvis/fc/mag.hpp for the full
// honesty statement. No real sensor bus anywhere in this file.
#include "jarvis/fc/mag.hpp"

#include <cmath>
#include <stdexcept>

#include "jarvis/fc/quat_math.hpp"

namespace jarvis::fc {

SimulatedMagHal::SimulatedMagHal(Vec3 world_field_enu) : world_field_enu_(world_field_enu) {
    for (double c : world_field_enu) {
        if (!std::isfinite(c)) {
            throw std::invalid_argument("world_field_enu must be finite");
        }
    }
    double norm = std::sqrt(world_field_enu[0] * world_field_enu[0] + world_field_enu[1] * world_field_enu[1] +
                             world_field_enu[2] * world_field_enu[2]);
    if (norm < 1e-9) {
        throw std::invalid_argument("world_field_enu must be nonzero");
    }
}

MagSample SimulatedMagHal::read_mag(const Quat& true_q_body_to_world, double t_s) const {
    Vec3 body_field = quat::rotate_vector(quat::conjugate(true_q_body_to_world), world_field_enu_);
    return MagSample{t_s, body_field};
}

}  // namespace jarvis::fc
