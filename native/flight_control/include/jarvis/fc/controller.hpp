// Fase C · C13 — C++ port of `flight_control/controller.py` (C8 rung).
//
// Host scaffold only — production flight_control runtime is a future,
// further-hardened iteration of this same C++ tree. Exactly one
// controller: a PD law on the small-angle orientation error, damped by
// estimated body rate. No motor thrusts, no mixer, no PWM/ESC output, no
// position/velocity loop, no cascaded rate PID — matching the Python C8
// hard cut. Not wired to any autonomy/Safety submit path.
#pragma once

#include "jarvis/fc/attitude.hpp"
#include "jarvis/fc/types.hpp"

namespace jarvis::fc {

struct AttitudeSetpoint {
    double t_s = 0.0;
    Quat q_body_to_world_desired{1.0, 0.0, 0.0, 0.0};
};

struct BodyRateCommand {
    double t_s = 0.0;
    Vec3 omega_body_rad_s{0.0, 0.0, 0.0};
};

// `omega_cmd = kp * e_rot - kd * omega_measured`, where `e_rot` is the
// body-frame small-angle rotation vector from the estimated orientation
// toward the desired one (twice the vector part of the shortest-path
// error quaternion `conj(q_estimated) (x) q_desired`). `kp` must be `> 0`;
// `kd` must be `>= 0`.
class PdAttitudeController {
public:
    explicit PdAttitudeController(double kp = 6.0, double kd = 0.6);

    void reset();  // no-op — kept for API symmetry with the other rungs
    BodyRateCommand compute(const AttitudeSetpoint& setpoint, const AttitudeState& state) const;

private:
    double kp_;
    double kd_;
};

// Identity quaternion — level hover attitude in `enu`. For tests/smoke
// only; not a claim about hover thrust or any physical setpoint.
AttitudeSetpoint level_setpoint(double t_s);

}  // namespace jarvis::fc
