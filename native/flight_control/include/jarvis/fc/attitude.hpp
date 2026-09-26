// Fase C · C13 — C++ port of `flight_control/attitude.py` (C7 rung).
//
// Host scaffold only — production flight_control runtime is a future,
// further-hardened iteration of this same C++ tree. Single, minimal,
// gravity-referenced complementary filter — NOT Mahony, NOT Madgwick, NOT
// an EKF/UKF. Carries forward the C11 Amendment A fix (correct
// accel-correction cross-product argument order: `cross(accel_dir,
// predicted_down_body)`, not the reversed order) from day one — this
// scaffold never reintroduces the bug that shipped and was later fixed in
// the Python ladder.
//
// No GPS/baro fusion, no gyro-bias learning, no world-frame velocity/
// position output — matching the Python C7 hard cut, untouched by C37.
// `frame` is always `"enu"`; gravity is `(0, 0, -g)` in that frame.
//
// Fase C · C37 (`B1-fase-c-mag-yaw-rung`) supersedes the original "no
// magnetometer fusion" cut, disclosed: `update(sample, mag)` now takes
// an optional `MagSample` (`std::nullopt` default). When absent,
// behavior is byte-for-byte identical to before this Buy — see the
// Python twin's own module docstring (`attitude.py`) for the full
// derivation of the mag yaw correction math this file mirrors exactly.
#pragma once

#include <optional>

#include "jarvis/fc/mag.hpp"
#include "jarvis/fc/types.hpp"

namespace jarvis::fc {

struct AttitudeState {
    double t_s = 0.0;
    Quat q_body_to_world{1.0, 0.0, 0.0, 0.0};
    Vec3 omega_body_rad_s{0.0, 0.0, 0.0};
};

// Gyro integration fused with accel-derived tilt via a small-angle
// proportional correction, plus (C37) an optional mag-derived yaw
// correction. `gain`/`mag_gain` must each be in `(0, 1]`.
class ComplementaryAttitudeEstimator {
public:
    explicit ComplementaryAttitudeEstimator(double gain = 0.02,
                                             Quat initial_q = Quat{1.0, 0.0, 0.0, 0.0},
                                             double mag_gain = 0.02);

    void reset();
    AttitudeState update(const ImuSample& sample, std::optional<MagSample> mag = std::nullopt);

private:
    double gain_;
    double mag_gain_;
    Quat initial_q_;
    std::optional<Quat> q_;
    std::optional<double> last_t_s_;
};

}  // namespace jarvis::fc
