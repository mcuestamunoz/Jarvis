// Fase C · C13 — shared value types for the C++ `flight_control` scaffold
// (`B1-fase-c-cpp-flight-control-scaffold`).
//
// Host scaffold only — production flight_control runtime is a future,
// further-hardened iteration of this same C++ tree; this Buy does not
// flash, does not touch GPIO/PWM/DShot, and does not claim any real
// vehicle flies. Mirrors the Python `flight_software/flight_control/`
// wooden ladder (types.py, C3) in shape, not necessarily bit-identical
// numerics — see the C13 implementation report for the documented
// tip-recovery criterion this scaffold is held to instead.
//
// `ImuSample` is a pure sensing record — no actuator field here, matching
// the Python C3 rung's own hard cut.
#pragma once

#include <array>

namespace jarvis::fc {

using Vec3 = std::array<double, 3>;

// (w, x, y, z) — unit quaternion, body-to-world, same convention as the
// Python ladder (attitude.py's `Quat`).
struct Quat {
    double w = 1.0;
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
};

struct ImuSample {
    double t_s = 0.0;
    Vec3 accel_mps2{0.0, 0.0, 0.0};
    Vec3 gyro_rad_s{0.0, 0.0, 0.0};
};

}  // namespace jarvis::fc
