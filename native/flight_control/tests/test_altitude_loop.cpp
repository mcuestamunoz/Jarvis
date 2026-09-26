// Fase C · C38 (`B1-fase-c-altitude-loop`) — Catch2 unit cases for
// `jarvis::fc::SimulatedAltitudeHal` and `jarvis::fc::AltitudeController`.
//
// Host-only test binary. No real sensor bus here, no GPIO/hardware.
// File named `test_altitude_loop.cpp`, not `test_altitude.cpp` — this
// tree already ships `test_attitude.cpp` (C7 estimator); "altitude"/
// "attitude" differ by one letter, avoided here the same way the
// production headers avoid it.
#include <cmath>
#include <stdexcept>

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>

#include "jarvis/fc/altitude_controller.hpp"
#include "jarvis/fc/controller.hpp"
#include "jarvis/fc/loop.hpp"
#include "jarvis/fc/plant.hpp"
#include "jarvis/fc/sim_altitude_hal.hpp"

using namespace jarvis::fc;
using Catch::Matchers::WithinAbs;

TEST_CASE("SimulatedAltitudeHal: T1 known true z -> altitude_m matches, finite", "[altitude][c38]") {
    SimulatedAltitudeHal hal;
    AltitudeSample sample = hal.read_altitude(3.5, 1.0);
    REQUIRE(std::isfinite(sample.altitude_m));
    REQUIRE_THAT(sample.altitude_m, WithinAbs(3.5, 1e-12));
    REQUIRE_THAT(sample.t_s, WithinAbs(1.0, 1e-12));
}

TEST_CASE("SimulatedAltitudeHal: rejects non-finite true_z_m", "[altitude][c38]") {
    SimulatedAltitudeHal hal;
    REQUIRE_THROWS_AS(hal.read_altitude(std::nan(""), 0.0), std::invalid_argument);
}

TEST_CASE("AltitudeController: rejects invalid kp/kd/hover_bias/z_des_m/vz_mps", "[altitude][c38]") {
    REQUIRE_THROWS_AS(AltitudeController(0.0, 0.3, 0.1), std::invalid_argument);
    REQUIRE_THROWS_AS(AltitudeController(-0.1, 0.3, 0.1), std::invalid_argument);
    REQUIRE_THROWS_AS(AltitudeController(0.2, -0.1, 0.1), std::invalid_argument);
    REQUIRE_THROWS_AS(AltitudeController(0.2, 0.3, -0.1), std::invalid_argument);
    REQUIRE_THROWS_AS(AltitudeController(0.2, 0.3, 1.1), std::invalid_argument);

    AltitudeController controller;
    SimulatedAltitudeHal hal;
    AltitudeSample sample = hal.read_altitude(0.0, 0.0);
    REQUIRE_THROWS_AS(controller.compute(std::nan(""), sample, 0.0), std::invalid_argument);
    REQUIRE_THROWS_AS(controller.compute(1.0, sample, std::nan("")), std::invalid_argument);
}

TEST_CASE("AltitudeController: T3 z below setpoint raises collective, z above lowers it, clipped to [0,1]", "[altitude][c38]") {
    AltitudeController controller(0.2, 0.3, 0.1226);
    SimulatedAltitudeHal hal;

    AltitudeSample below = hal.read_altitude(0.0, 0.0);
    double collective_below = controller.compute(2.0, below, 0.0);
    REQUIRE(collective_below > 0.1226);

    AltitudeSample above = hal.read_altitude(5.0, 0.0);
    double collective_above = controller.compute(2.0, above, 0.0);
    REQUIRE(collective_above < 0.1226);

    REQUIRE(collective_below >= 0.0);
    REQUIRE(collective_below <= 1.0);
    REQUIRE(collective_above >= 0.0);
    REQUIRE(collective_above <= 1.0);

    // Extreme error clips to 1.0, never exceeds it.
    AltitudeSample far_below = hal.read_altitude(-100.0, 0.0);
    REQUIRE_THAT(controller.compute(2.0, far_below, 0.0), WithinAbs(1.0, 1e-12));
}

TEST_CASE("ToyQuad6DofPlant + AltitudeController: T4 closed loop climbs toward z_des, error strictly decreases", "[altitude][c38]") {
    ToyQuad6DofPlant plant;
    ControlLoop loop;
    SimulatedAltitudeHal hal;
    AltitudeController alt;
    double z_des = 2.0;
    double dt_s = 0.01;

    double initial_error = std::abs(z_des - plant.true_position_m()[2]);

    ImuSample sample = plant.sense();
    for (int i = 0; i < 500; ++i) {
        AltitudeSample altitude = hal.read_altitude(plant.true_position_m()[2], sample.t_s);
        double vz = plant.true_velocity_mps()[2];
        double collective = alt.compute(z_des, altitude, vz);
        AttitudeSetpoint setpoint = level_setpoint(sample.t_s);
        ControlTickResult tick = loop.step(sample, setpoint, collective);
        sample = plant.step(tick.forces, dt_s);
    }

    double final_error = std::abs(z_des - plant.true_position_m()[2]);

    REQUIRE(plant.true_position_m()[2] > 0.0);
    REQUIRE(final_error < initial_error);
    REQUIRE(final_error < 0.2);
}
