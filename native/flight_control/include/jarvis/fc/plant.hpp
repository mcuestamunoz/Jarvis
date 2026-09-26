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
//
// Fase C · C36 (`B1-fase-c-sim-6dof-plant`) adds `ToyQuad6DofPlant`
// below — `ToyQuadAttitudePlant` above is unchanged, byte-for-byte.
// See its own class comment and the Python twin's module docstring
// (`plant.py`) for the full honesty statement: same toy attitude
// dynamics, plus a toy translation law (`thrust_body = (0,0,thrust_gain
// * sum(motor_forces))`, semi-implicit Euler, `mass_kg`/`thrust_gain`
// both toy tuning constants, never sourced from real hardware). `ImuSample`
// stays exactly C11-shaped (gravity in body + gyro, no specific force).
// `ControlLoop::step` still never calls this or any other plant.
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

// C36 — toy 6-DoF plant: identical attitude dynamics to
// ToyQuadAttitudePlant plus a toy translation law. `mass_kg`/
// `thrust_gain` (both finite, `> 0`) are toy translation tuning
// constants, never sourced from real hardware; `torque_gain`/
// `angular_damping` are the same C11 attitude constants, unchanged in
// meaning. `ImuSample` stays C11-shaped (gravity in body + gyro) — no
// specific-force/linear-acceleration term. Deterministic, no noise.
class ToyQuad6DofPlant {
public:
    explicit ToyQuad6DofPlant(double mass_kg = 1.0, double thrust_gain = 20.0,
                               double torque_gain = 40.0, double angular_damping = 0.5);

    void reset(Vec3 position_m = Vec3{0.0, 0.0, 0.0}, Vec3 velocity_mps = Vec3{0.0, 0.0, 0.0},
               Quat initial_q = Quat{1.0, 0.0, 0.0, 0.0}, Vec3 initial_omega = Vec3{0.0, 0.0, 0.0});

    // The plant's own true state — never an estimate.
    AttitudeState true_attitude() const;
    Vec3 true_position_m() const;
    Vec3 true_velocity_mps() const;

    // Reads the current true state as a C11-shaped `ImuSample` without
    // advancing dynamics.
    ImuSample sense() const;

    ImuSample step(const MotorForceCommand& forces, double dt_s);

private:
    double mass_kg_;
    double thrust_gain_;
    double torque_gain_;
    double angular_damping_;
    Quat q_{1.0, 0.0, 0.0, 0.0};
    Vec3 omega_{0.0, 0.0, 0.0};
    Vec3 position_m_{0.0, 0.0, 0.0};
    Vec3 velocity_mps_{0.0, 0.0, 0.0};
    double t_s_ = 0.0;
};

}  // namespace jarvis::fc
