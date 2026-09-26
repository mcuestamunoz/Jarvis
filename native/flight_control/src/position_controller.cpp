// Fase C · C39 — implementation of `jarvis::fc::PositionController`.
//
// Host scaffold only. See include/jarvis/fc/position_controller.hpp and
// the Python twin's own module docstring for the full honesty statement
// and sign derivation. No GPIO/PWM/DShot, no Safety call, no autonomy
// executor anywhere in this file.
#include "jarvis/fc/position_controller.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace jarvis::fc {

namespace {

// Body 3-2-1 (yaw-pitch-roll) Euler-to-quaternion composition — same
// formula rc_setpoint.cpp uses, kept as this file's own private copy per
// this project's established per-module-private-helper style (quat_math.hpp
// is the one deliberate exception, for GENERIC quaternion primitives only).
Quat roll_pitch_yaw_to_quat(double roll_rad, double pitch_rad, double yaw_rad) {
    double half_roll = roll_rad / 2.0;
    double half_pitch = pitch_rad / 2.0;
    double half_yaw = yaw_rad / 2.0;
    double cr = std::cos(half_roll);
    double sr = std::sin(half_roll);
    double cp = std::cos(half_pitch);
    double sp = std::sin(half_pitch);
    double cy = std::cos(half_yaw);
    double sy = std::sin(half_yaw);
    return Quat{
        cy * cp * cr + sy * sp * sr,
        cy * cp * sr - sy * sp * cr,
        cy * sp * cr + sy * cp * sr,
        sy * cp * cr - cy * sp * sr,
    };
}

}  // namespace

PositionController::PositionController(double kp, double kd, double max_tilt_rad)
    : kp_(kp), kd_(kd), max_tilt_rad_(max_tilt_rad) {
    if (!std::isfinite(kp) || kp <= 0.0) {
        throw std::invalid_argument("kp must be finite and > 0");
    }
    if (!std::isfinite(kd) || kd < 0.0) {
        throw std::invalid_argument("kd must be finite and >= 0");
    }
    if (!std::isfinite(max_tilt_rad) || max_tilt_rad <= 0.0) {
        throw std::invalid_argument("max_tilt_rad must be finite and > 0");
    }
}

AttitudeSetpoint PositionController::compute(
    const PositionSetpoint& setpoint, const PositionSample& position, double vx_mps, double vy_mps,
    double t_s) const {
    if (!std::isfinite(vx_mps)) {
        throw std::invalid_argument("vx_mps must be finite");
    }
    if (!std::isfinite(vy_mps)) {
        throw std::invalid_argument("vy_mps must be finite");
    }

    double error_x = setpoint.x_m - position.x_m;
    double error_y = setpoint.y_m - position.y_m;
    double pitch_raw = kp_ * error_x - kd_ * vx_mps;
    double roll_raw = -(kp_ * error_y - kd_ * vy_mps);
    double pitch_rad = std::max(-max_tilt_rad_, std::min(max_tilt_rad_, pitch_raw));
    double roll_rad = std::max(-max_tilt_rad_, std::min(max_tilt_rad_, roll_raw));

    AttitudeSetpoint result;
    result.t_s = t_s;
    result.q_body_to_world_desired = roll_pitch_yaw_to_quat(roll_rad, pitch_rad, 0.0);
    return result;
}

}  // namespace jarvis::fc
