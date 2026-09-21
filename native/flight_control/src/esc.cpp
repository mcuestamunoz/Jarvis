#include "jarvis/fc/esc.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace jarvis::fc {

namespace {
double clamp01(double value) { return std::max(0.0, std::min(1.0, value)); }
}  // namespace

EscPwmCommand encode_motor_forces(const MotorForceCommand& forces, double min_us, double max_us) {
    if (!std::isfinite(min_us) || !std::isfinite(max_us) || min_us >= max_us) {
        throw std::invalid_argument("min_us and max_us must be finite with min_us < max_us");
    }

    double span = max_us - min_us;
    PulseWidths pulses{};
    for (std::size_t i = 0; i < pulses.size(); ++i) {
        pulses[i] = min_us + clamp01(forces.motor_forces[i]) * span;
    }

    EscPwmCommand cmd;
    cmd.t_s = forces.t_s;
    cmd.pulse_us = pulses;
    return cmd;
}

EscApplyResult SimulatedEscSink::apply(const EscPwmCommand& cmd) {
    last_command_ = cmd;
    if (!armed_) {
        return EscApplyResult{false, std::string("disarmed"), cmd.pulse_us};
    }
    return EscApplyResult{true, std::nullopt, cmd.pulse_us};
}

}  // namespace jarvis::fc
