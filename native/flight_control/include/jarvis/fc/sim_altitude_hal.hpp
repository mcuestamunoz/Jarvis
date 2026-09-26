// Fase C · C38 (`B1-fase-c-altitude-loop`) — `AltitudeSample` +
// `SimulatedAltitudeHal`, C++ twin of the Python
// `flight_control/sim_altitude_hal.py`.
//
// Host scaffold only — production flight_control runtime is a future,
// further-hardened iteration of this same C++ tree. No real MCU/I2C/SPI
// baro or ToF driver, no claim that a height sensor chip is present
// anywhere in this repo.
//
// Direct altitude port, not a meteorology model (locked, same as the
// Python twin): this HAL emits `altitude_m` DIRECTLY from the
// caller-supplied true height — no barometric pressure model, no ISA
// lapse-rate table, no ToF beam simulation.
//
// Not plant-owning (same pattern as SimulatedMagHal, C37): `read_altitude`
// takes the TRUE z (ENU Up, metres) as a required, caller-supplied
// argument. This HAL never owns or secretly consults a plant.
//
// Naming note: this file is deliberately `sim_altitude_hal.hpp`, not
// `altitude.hpp` — `attitude.hpp` (C7 estimator) already exists in this
// tree, and "altitude"/"attitude" differ by one letter.
//
// Sim altitude != live baro/ToF chip.
#pragma once

namespace jarvis::fc {

struct AltitudeSample {
    double t_s = 0.0;
    double altitude_m = 0.0;
};

// Stateless — `read_altitude` is a pure pass-through of the
// caller-supplied true height, never a claim about any real sensor's
// own noise/bias/lag characteristics. Throws `std::invalid_argument` if
// `true_z_m` is not finite.
class SimulatedAltitudeHal {
public:
    AltitudeSample read_altitude(double true_z_m, double t_s = 0.0) const;
};

}  // namespace jarvis::fc
