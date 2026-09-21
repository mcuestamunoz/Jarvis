#include "jarvis/fc/controller.hpp"

#include <cmath>
#include <stdexcept>

#include "jarvis/fc/quat_math.hpp"

namespace jarvis::fc {

namespace {
// Unit quaternions `q` and `-q` represent the same rotation; picking the
// sign with `w >= 0` always yields the shorter-path rotation vector when
// extracting the small-angle error below.
Quat shortest_error_quat(const Quat& q_err) {
    if (q_err.w < 0.0) {
        return Quat{-q_err.w, -q_err.x, -q_err.y, -q_err.z};
    }
    return q_err;
}
}  // namespace

PdAttitudeController::PdAttitudeController(double kp, double kd) : kp_(kp), kd_(kd) {
    if (!std::isfinite(kp) || kp <= 0.0) {
        throw std::invalid_argument("kp must be finite and > 0");
    }
    if (!std::isfinite(kd) || kd < 0.0) {
        throw std::invalid_argument("kd must be finite and >= 0");
    }
}

void PdAttitudeController::reset() {}

BodyRateCommand PdAttitudeController::compute(const AttitudeSetpoint& setpoint,
                                               const AttitudeState& state) const {
    Quat q_err = shortest_error_quat(
        quat::multiply(quat::conjugate(state.q_body_to_world), setpoint.q_body_to_world_desired));
    Vec3 e_rot{2.0 * q_err.x, 2.0 * q_err.y, 2.0 * q_err.z};
    const Vec3& omega_measured = state.omega_body_rad_s;
    Vec3 omega_cmd{
        kp_ * e_rot[0] - kd_ * omega_measured[0],
        kp_ * e_rot[1] - kd_ * omega_measured[1],
        kp_ * e_rot[2] - kd_ * omega_measured[2],
    };
    return BodyRateCommand{state.t_s, omega_cmd};
}

AttitudeSetpoint level_setpoint(double t_s) {
    return AttitudeSetpoint{t_s, Quat{1.0, 0.0, 0.0, 0.0}};
}

}  // namespace jarvis::fc
