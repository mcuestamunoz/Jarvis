// Fase C · C38 — implementation of `jarvis::fc::AltitudeController`.
//
// Host scaffold only. See include/jarvis/fc/altitude_controller.hpp and
// the Python twin's own module docstring for the full honesty
// statement. No GPIO/PWM/DShot, no Safety call anywhere in this file.
#include "jarvis/fc/altitude_controller.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace jarvis::fc {

AltitudeController::AltitudeController(double kp, double kd, double hover_bias)
    : kp_(kp), kd_(kd), hover_bias_(hover_bias) {
    if (!std::isfinite(kp) || kp <= 0.0) {
        throw std::invalid_argument("kp must be finite and > 0");
    }
    if (!std::isfinite(kd) || kd < 0.0) {
        throw std::invalid_argument("kd must be finite and >= 0");
    }
    if (!std::isfinite(hover_bias) || hover_bias < 0.0 || hover_bias > 1.0) {
        throw std::invalid_argument("hover_bias must be finite and in [0, 1]");
    }
}

double AltitudeController::compute(double z_des_m, const AltitudeSample& altitude, double vz_mps) const {
    if (!std::isfinite(z_des_m)) {
        throw std::invalid_argument("z_des_m must be finite");
    }
    if (!std::isfinite(vz_mps)) {
        throw std::invalid_argument("vz_mps must be finite");
    }
    double error = z_des_m - altitude.altitude_m;
    double raw = hover_bias_ + kp_ * error - kd_ * vz_mps;
    return std::max(0.0, std::min(1.0, raw));
}

}  // namespace jarvis::fc
