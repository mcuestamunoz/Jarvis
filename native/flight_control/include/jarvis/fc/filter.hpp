// Fase C · C13 — C++ port of `flight_control/filter.py` (C6 rung).
//
// Host scaffold only — production flight_control runtime is a future,
// further-hardened iteration of this same C++ tree. Sensing post-process
// only: no quaternion, no Euler angles, no attitude output of any kind —
// see `attitude.hpp` for that rung.
#pragma once

#include <optional>

#include "jarvis/fc/types.hpp"

namespace jarvis::fc {

// EMA filter: `filtered = alpha * raw + (1 - alpha) * previous_filtered`,
// applied per axis to `accel_mps2` and `gyro_rad_s`. `t_s` is copied
// verbatim. The first sample after construction or `reset()` seeds the
// filter directly (no smoothing applied yet) — same as the Python rung.
class ImuLowPassFilter {
public:
    explicit ImuLowPassFilter(double alpha = 0.2);

    void reset();
    ImuSample filter_sample(const ImuSample& raw);

private:
    double alpha_;
    std::optional<ImuSample> state_;
};

}  // namespace jarvis::fc
