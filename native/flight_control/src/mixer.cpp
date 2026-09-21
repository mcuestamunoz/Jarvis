#include "jarvis/fc/mixer.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace jarvis::fc {

namespace {
double clamp01(double value) { return std::max(0.0, std::min(1.0, value)); }
}  // namespace

QuadXMixer::QuadXMixer(double roll_scale, double pitch_scale, double yaw_scale)
    : roll_scale_(roll_scale), pitch_scale_(pitch_scale), yaw_scale_(yaw_scale) {
    for (double value : {roll_scale, pitch_scale, yaw_scale}) {
        if (!std::isfinite(value) || value < 0.0) {
            throw std::invalid_argument("scales must be finite and >= 0");
        }
    }
}

MotorForceCommand QuadXMixer::mix(double collective, const BodyTorqueCommand& torques) const {
    double collective_clamped = clamp01(collective);
    double tau_x = torques.tau_body[0];
    double tau_y = torques.tau_body[1];
    double tau_z = torques.tau_body[2];

    MotorForces raw{
        collective_clamped - roll_scale_ * tau_x + pitch_scale_ * tau_y - yaw_scale_ * tau_z,
        collective_clamped + roll_scale_ * tau_x + pitch_scale_ * tau_y + yaw_scale_ * tau_z,
        collective_clamped + roll_scale_ * tau_x - pitch_scale_ * tau_y - yaw_scale_ * tau_z,
        collective_clamped - roll_scale_ * tau_x - pitch_scale_ * tau_y + yaw_scale_ * tau_z,
    };

    MotorForces forces{clamp01(raw[0]), clamp01(raw[1]), clamp01(raw[2]), clamp01(raw[3])};
    return MotorForceCommand{torques.t_s, forces};
}

double hover_collective(double default_value) { return default_value; }

}  // namespace jarvis::fc
