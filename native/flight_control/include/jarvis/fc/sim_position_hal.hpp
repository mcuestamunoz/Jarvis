// Fase C · C39 (`B1-fase-c-position-loop`) — `PositionSample` +
// `SimulatedPositionHal`, C++ twin of the Python
// `flight_control/sim_position_hal.py`.
//
// Host scaffold only — production flight_control runtime is a future,
// further-hardened iteration of this same C++ tree. No real GPS/
// optical-flow driver, no claim that a positioning chip is present
// anywhere in this repo.
//
// Direct ENU port, not a GNSS/flow stack (locked, same as the Python
// twin): this HAL emits `x_m`/`y_m` (ENU East/North) DIRECTLY from the
// caller-supplied true horizontal position — no NMEA sentences, no
// WGS84 geodesy, no optical-flow image processing.
//
// Not plant-owning (same pattern as SimulatedAltitudeHal, C38):
// `read_position` takes the TRUE x/y (ENU East/North, metres) as
// required, caller-supplied arguments. This HAL never owns or secretly
// consults a plant.
//
// `z_m` is optional and unused by `PositionController` — altitude stays
// C38's own `AltitudeController` concern, not duplicated here.
//
// Sim position != live GPS/flow chip.
#pragma once

#include <optional>

namespace jarvis::fc {

struct PositionSample {
    double t_s = 0.0;
    double x_m = 0.0;
    double y_m = 0.0;
    std::optional<double> z_m{};
};

// Stateless — `read_position` is a pure pass-through of the
// caller-supplied true horizontal position, never a claim about any
// real sensor's own noise/bias/lag characteristics. Throws
// `std::invalid_argument` if `true_x_m`/`true_y_m`/`true_z_m` (when
// provided) are not finite.
class SimulatedPositionHal {
public:
    PositionSample read_position(
        double true_x_m, double true_y_m, double t_s = 0.0, std::optional<double> true_z_m = std::nullopt) const;
};

}  // namespace jarvis::fc
