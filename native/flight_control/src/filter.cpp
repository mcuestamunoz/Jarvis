#include "jarvis/fc/filter.hpp"

#include <stdexcept>

namespace jarvis::fc {

ImuLowPassFilter::ImuLowPassFilter(double alpha) : alpha_(alpha) {
    if (!(alpha > 0.0 && alpha <= 1.0)) {
        throw std::invalid_argument("alpha must be in (0, 1]");
    }
}

void ImuLowPassFilter::reset() { state_.reset(); }

namespace {
Vec3 ema(const Vec3& previous, const Vec3& current, double alpha) {
    return Vec3{
        alpha * current[0] + (1.0 - alpha) * previous[0],
        alpha * current[1] + (1.0 - alpha) * previous[1],
        alpha * current[2] + (1.0 - alpha) * previous[2],
    };
}
}  // namespace

ImuSample ImuLowPassFilter::filter_sample(const ImuSample& raw) {
    ImuSample filtered;
    if (!state_.has_value()) {
        filtered = raw;
    } else {
        filtered.t_s = raw.t_s;
        filtered.accel_mps2 = ema(state_->accel_mps2, raw.accel_mps2, alpha_);
        filtered.gyro_rad_s = ema(state_->gyro_rad_s, raw.gyro_rad_s, alpha_);
    }
    state_ = filtered;
    return filtered;
}

}  // namespace jarvis::fc
