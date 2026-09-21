// Fase C · C13 — C++ port of `flight_control/mixer.py` (C9 rung, C12
// torque-only API).
//
// Host scaffold only — production flight_control runtime is a future,
// further-hardened iteration of this same C++ tree. Exactly one airframe
// layout: quadrotor X. `mix(...)` consumes a `BodyTorqueCommand` only —
// no `BodyRateCommand` overload exists, matching the Python C12 migration
// (no silent dual API). No PWM microseconds, no DShot, no ESC UART, no
// GPIO, no claim that hardware is armed or that motors spin.
//
// Motor order: m0=FR, m1=FL, m2=RL, m3=RR — same X-frame geometry as the
// Python C9 rung's own docstring.
#pragma once

#include <array>

#include "jarvis/fc/rate_torque.hpp"

namespace jarvis::fc {

using MotorForces = std::array<double, 4>;

struct MotorForceCommand {
    double t_s = 0.0;
    MotorForces motor_forces{0.0, 0.0, 0.0, 0.0};
};

// Fixed linear allocation for a quadrotor X frame. `roll_scale`,
// `pitch_scale`, `yaw_scale` must each be finite and `>= 0`.
class QuadXMixer {
public:
    explicit QuadXMixer(double roll_scale = 0.05, double pitch_scale = 0.05,
                         double yaw_scale = 0.05);

    MotorForceCommand mix(double collective, const BodyTorqueCommand& torques) const;

private:
    double roll_scale_;
    double pitch_scale_;
    double yaw_scale_;
};

// For tests/smoke only — a symbolic mid-range collective value, not a
// claim about real hover thrust for any vehicle.
double hover_collective(double default_value = 0.5);

}  // namespace jarvis::fc
