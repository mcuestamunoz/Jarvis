// Fase C · C13 — C++ port of `flight_control/rate_torque.py` (C12 rung).
//
// Host scaffold only — production flight_control runtime is a future,
// further-hardened iteration of this same C++ tree. This C++ path must
// carry the same honesty the Python C12 bridge locked in: exactly one
// bridge law, feedforward only — `tau_i = gain_i * omega_cmd_i` per axis.
// Not a cascaded rate PID: no `kp * (omega_cmd - omega_measured)` term, no
// integral/derivative state, no measured-rate feedback anywhere in this
// module. `tau_body` is a normalized, dimensionless, torque-like mix
// command — never claimed as Newton-metres of any real vehicle.
#pragma once

#include "jarvis/fc/controller.hpp"
#include "jarvis/fc/types.hpp"

namespace jarvis::fc {

struct BodyTorqueCommand {
    double t_s = 0.0;
    Vec3 tau_body{0.0, 0.0, 0.0};
};

// `tau_i = gain_i * omega_cmd_i` per axis. Every resolved gain must be
// finite and `> 0`.
class LinearRateTorqueBridge {
public:
    explicit LinearRateTorqueBridge(Vec3 gains = Vec3{1.0, 1.0, 1.0});
    explicit LinearRateTorqueBridge(double gain);

    BodyTorqueCommand convert(const BodyRateCommand& rates) const;

private:
    Vec3 gains_;
};

}  // namespace jarvis::fc
