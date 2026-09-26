// Fase C · C25 — implementation of `jarvis::fc::map_rc_to_loop_inputs`.
//
// Host scaffold only. See `include/jarvis/fc/rc_setpoint.hpp` for the
// full honesty statement. No radio-link parsing, no plant, no GPIO/PWM/DShot,
// no Safety call anywhere in this file.
#include "jarvis/fc/rc_setpoint.hpp"

#include <cmath>
#include <stdexcept>

namespace jarvis::fc {

namespace {

constexpr int kMinChannels = 4;

double stick_deflection_rad(int channel_value, double max_rad = kRcMaxTiltRad) {
    double frac;
    if (channel_value >= kRcChMid) {
        double span = static_cast<double>(kRcChMax - kRcChMid);
        frac = (channel_value - kRcChMid) / span;
    } else {
        double span = static_cast<double>(kRcChMid - kRcChMin);
        frac = (channel_value - kRcChMid) / span;
    }
    double frac_clipped = std::max(-1.0, std::min(1.0, frac));
    return frac_clipped * max_rad;
}

double throttle_to_collective(int channel_value) {
    double span = static_cast<double>(kRcChMax - kRcChMin);
    double frac = (channel_value - kRcChMin) / span;
    return std::max(0.0, std::min(1.0, frac));
}

// Body 3-2-1 (yaw-pitch-roll) Euler-to-quaternion composition
// (`q = q_yaw * q_pitch * q_roll`). C37 adds the `yaw_rad` term —
// verified to reduce to the exact pre-C37 formula
// (`{cp*cr, cp*sr, sp*cr, -sp*sr}`) when `yaw_rad == 0.0`.
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

RcLoopInputs map_rc_to_loop_inputs(const std::vector<int>& channels, double t_s) {
    if (static_cast<int>(channels.size()) < kMinChannels) {
        throw std::invalid_argument("channels must have at least 4 entries (AETR-shaped)");
    }

    double roll_rad = stick_deflection_rad(channels[kRcChRoll]);
    double pitch_rad = stick_deflection_rad(channels[kRcChPitch]);
    double yaw_rad = stick_deflection_rad(channels[kRcChYaw], kRcMaxYawRad);
    double collective = throttle_to_collective(channels[kRcChThrottle]);

    RcLoopInputs result;
    result.setpoint.t_s = t_s;
    result.setpoint.q_body_to_world_desired = roll_pitch_yaw_to_quat(roll_rad, pitch_rad, yaw_rad);
    result.collective = collective;
    return result;
}

}  // namespace jarvis::fc
