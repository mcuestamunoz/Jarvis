// Fase C · C37 (`B1-fase-c-mag-yaw-rung`) — `MagSample` + `SimulatedMagHal`,
// C++ twin of the Python `flight_control/mag.py` + `sim_mag_hal.py`.
//
// Host scaffold only — production flight_control runtime is a future,
// further-hardened iteration of this same C++ tree. No real MCU/I2C/SPI
// driver, no claim that a magnetometer chip is present anywhere in this
// repo — `read_mag(...)` never touches a bus, a socket, or any hardware.
//
// **Not attitude-owning (locked, same as the Python twin):** unlike a
// hypothetical attitude-owning HAL, this class never consults a plant —
// `read_mag` takes the TRUE `q_body_to_world` as a required,
// caller-supplied argument. Tests and smokes pass in whatever attitude
// they want (a plant's own `true_attitude()`, or a synthetic quaternion).
//
// World field (documented toy default, not a datasheet claim):
// `kWorldMagFieldEnu = (0, 1, 0)` — East 0, North 1.0 (toy unit
// magnitude), Up 0. Real Earth field has significant vertical
// inclination at most latitudes; this Buy's own yaw correction
// (`attitude.hpp`) only ever needs the horizontal component, so a
// nonzero Up component is deliberately omitted, not an oversight.
//
// Sim mag != live mag chip != ICM SPI mag.
#pragma once

#include "jarvis/fc/types.hpp"

namespace jarvis::fc {

struct MagSample {
    double t_s = 0.0;
    Vec3 mag_body_uT{0.0, 0.0, 0.0};
};

inline constexpr Vec3 kWorldMagFieldEnu{0.0, 1.0, 0.0};

// `world_field_enu` (finite, nonzero) is the fixed toy world field.
// `read_mag` rotates it into the body frame using the caller-supplied
// true `q_body_to_world`, via the inverse (conjugate) rotation — same
// convention `ToyQuadAttitudePlant::sense()` already uses for gravity.
class SimulatedMagHal {
public:
    explicit SimulatedMagHal(Vec3 world_field_enu = kWorldMagFieldEnu);

    MagSample read_mag(const Quat& true_q_body_to_world, double t_s = 0.0) const;

private:
    Vec3 world_field_enu_;
};

}  // namespace jarvis::fc
