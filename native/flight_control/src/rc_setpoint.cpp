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

double stick_deflection_rad(int channel_value) {
    double frac;
    if (channel_value >= kRcChMid) {
        double span = static_cast<double>(kRcChMax - kRcChMid);
        frac = (channel_value - kRcChMid) / span;
    } else {
        double span = static_cast<double>(kRcChMid - kRcChMin);
        frac = (channel_value - kRcChMid) / span;
    }
    double frac_clipped = std::max(-1.0, std::min(1.0, frac));
    return frac_clipped * kRcMaxTiltRad;
}

double throttle_to_collective(int channel_value) {
    double span = static_cast<double>(kRcChMax - kRcChMin);
    double frac = (channel_value - kRcChMin) / span;
    return std::max(0.0, std::min(1.0, frac));
}

// Body 3-2-1 (yaw-pitch-roll) Euler-to-quaternion composition with yaw
// fixed at 0 — yaw stick is out of scope this Buy (no mag).
Quat roll_pitch_to_quat(double roll_rad, double pitch_rad) {
    double half_roll = roll_rad / 2.0;
    double half_pitch = pitch_rad / 2.0;
    double cr = std::cos(half_roll);
    double sr = std::sin(half_roll);
    double cp = std::cos(half_pitch);
    double sp = std::sin(half_pitch);
    return Quat{cp * cr, cp * sr, sp * cr, -sp * sr};
}

}  // namespace

RcLoopInputs map_rc_to_loop_inputs(const std::vector<int>& channels, double t_s) {
    if (static_cast<int>(channels.size()) < kMinChannels) {
        throw std::invalid_argument("channels must have at least 4 entries (AETR-shaped)");
    }

    double roll_rad = stick_deflection_rad(channels[kRcChRoll]);
    double pitch_rad = stick_deflection_rad(channels[kRcChPitch]);
    double collective = throttle_to_collective(channels[kRcChThrottle]);

    RcLoopInputs result;
    result.setpoint.t_s = t_s;
    result.setpoint.q_body_to_world_desired = roll_pitch_to_quat(roll_rad, pitch_rad);
    result.collective = collective;
    return result;
}

}  // namespace jarvis::fc
