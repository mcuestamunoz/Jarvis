#include "jarvis/fc/rate_torque.hpp"

#include <cmath>
#include <stdexcept>

namespace jarvis::fc {

namespace {
void validate_gains(const Vec3& gains) {
    for (double value : gains) {
        if (!std::isfinite(value) || value <= 0.0) {
            throw std::invalid_argument("gains must each be finite and > 0");
        }
    }
}
}  // namespace

LinearRateTorqueBridge::LinearRateTorqueBridge(Vec3 gains) : gains_(gains) {
    validate_gains(gains_);
}

LinearRateTorqueBridge::LinearRateTorqueBridge(double gain) : gains_{gain, gain, gain} {
    validate_gains(gains_);
}

BodyTorqueCommand LinearRateTorqueBridge::convert(const BodyRateCommand& rates) const {
    return BodyTorqueCommand{
        rates.t_s,
        Vec3{
            gains_[0] * rates.omega_body_rad_s[0],
            gains_[1] * rates.omega_body_rad_s[1],
            gains_[2] * rates.omega_body_rad_s[2],
        },
    };
}

}  // namespace jarvis::fc
