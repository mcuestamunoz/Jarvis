// Fase C · C31 — implementation of `jarvis::fc::encode_dshot_frame` /
// `encode_motor_forces_dshot`.
//
// Host scaffold only. See include/jarvis/fc/dshot.hpp for the full
// honesty statement. No GPIO, no TIM, no DMA, no ESC register access,
// no radio-link protocol named anywhere in this file.
#include "jarvis/fc/dshot.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace jarvis::fc {

namespace {
double clamp01(double value) {
    if (!std::isfinite(value)) {
        return 0.0;
    }
    return std::max(0.0, std::min(1.0, value));
}
}  // namespace

uint16_t encode_dshot_frame(int throttle, bool telemetry) {
    if (throttle < kDshotMinCommandValue || throttle > kDshotMaxThrottleValue) {
        throw std::invalid_argument("throttle must be in [0, 2047]");
    }

    uint32_t value = (static_cast<uint32_t>(throttle) << 1) | (telemetry ? 1u : 0u);
    uint32_t checksum = (value ^ (value >> 4) ^ (value >> 8)) & 0xFu;
    return static_cast<uint16_t>((value << 4) | checksum);
}

std::array<uint16_t, 4> encode_motor_forces_dshot(const MotorForceCommand& forces) {
    constexpr int span = kDshotMaxThrottleValue - kDshotMinThrottleValue;
    std::array<uint16_t, 4> frames{};
    for (std::size_t i = 0; i < frames.size(); ++i) {
        int throttle = kDshotMinThrottleValue + static_cast<int>(std::lround(clamp01(forces.motor_forces[i]) * span));
        frames[i] = encode_dshot_frame(throttle);
    }
    return frames;
}

}  // namespace jarvis::fc
