// Fase C · C13 — C++ port of `flight_control/plant.py` (C11 closed-loop
// tip).
//
// Host scaffold only — production flight_control runtime is a future,
// further-hardened iteration of this same C++ tree. Toy, attitude-only
// rigid-body-ish dynamics — no position, no velocity, no real
// aerodynamics, no motor thrust curve, no vehicle mass/inertia sourced
// from any real hardware. Never presented as a CFD/aero solver or as
// truth about any real vehicle. No GPIO/serial/DShot anywhere in this
// module — toy attitude-only integration, never actuation.
#pragma once

#include "jarvis/fc/attitude.hpp"
#include "jarvis/fc/mixer.hpp"
#include "jarvis/fc/types.hpp"

namespace jarvis::fc {

// `torque_gain` (must be finite and `> 0`) scales the motor-force
// differential proxies into a toy angular acceleration; `angular_damping`
// (must be finite and `>= 0`) is a toy passive damping term. Deterministic
// — no sensor noise, unlike the Python `SimulatedImuHal`.
class ToyQuadAttitudePlant {
public:
    explicit ToyQuadAttitudePlant(double torque_gain = 40.0, double angular_damping = 0.5);

    void reset(Quat initial_q = Quat{1.0, 0.0, 0.0, 0.0}, Vec3 initial_omega = Vec3{0.0, 0.0, 0.0});

    // The plant's own true state — never an estimate.
    AttitudeState true_attitude() const;

    // Reads the current true state as an `ImuSample` without advancing
    // dynamics.
    ImuSample sense() const;

    ImuSample step(const MotorForceCommand& forces, double dt_s);

private:
    double torque_gain_;
    double angular_damping_;
    Quat q_{1.0, 0.0, 0.0, 0.0};
    Vec3 omega_{0.0, 0.0, 0.0};
    double t_s_ = 0.0;
};

// Angle (radians, always `>= 0`) between `q` and the identity/level
// orientation — `2 * acos(|w|)`.
double tilt_angle_rad(const Quat& q);

}  // namespace jarvis::fc
