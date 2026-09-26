// Fase C · C39 (`B1-fase-c-position-loop`) — Catch2 unit cases for
// `jarvis::fc::SimulatedPositionHal` and `jarvis::fc::PositionController`.
//
// Host-only test binary. No real sensor bus here, no GPIO/hardware, no
// autonomy executor. File named `test_position_loop.cpp` — mirrors
// `test_altitude_loop.cpp`'s own naming/structure.
#include <cmath>
#include <stdexcept>

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>

#include "jarvis/fc/altitude_controller.hpp"
#include "jarvis/fc/controller.hpp"
#include "jarvis/fc/loop.hpp"
#include "jarvis/fc/plant.hpp"
#include "jarvis/fc/position_controller.hpp"
#include "jarvis/fc/sim_altitude_hal.hpp"
#include "jarvis/fc/sim_position_hal.hpp"

using namespace jarvis::fc;
using Catch::Matchers::WithinAbs;

TEST_CASE("SimulatedPositionHal: T1 known true xy -> x_m/y_m match, finite", "[position][c39]") {
    SimulatedPositionHal hal;
    PositionSample sample = hal.read_position(2.5, -1.5, 1.0);
    REQUIRE(std::isfinite(sample.x_m));
    REQUIRE(std::isfinite(sample.y_m));
    REQUIRE_THAT(sample.x_m, WithinAbs(2.5, 1e-12));
    REQUIRE_THAT(sample.y_m, WithinAbs(-1.5, 1e-12));
    REQUIRE_THAT(sample.t_s, WithinAbs(1.0, 1e-12));
    REQUIRE_FALSE(sample.z_m.has_value());
}

TEST_CASE("SimulatedPositionHal: optional z_m round-trips when provided", "[position][c39]") {
    SimulatedPositionHal hal;
    PositionSample sample = hal.read_position(0.0, 0.0, 0.0, 4.0);
    REQUIRE(sample.z_m.has_value());
    REQUIRE_THAT(*sample.z_m, WithinAbs(4.0, 1e-12));
}

TEST_CASE("SimulatedPositionHal: T2 rejects non-finite true_x_m/true_y_m/true_z_m", "[position][c39]") {
    SimulatedPositionHal hal;
    REQUIRE_THROWS_AS(hal.read_position(std::nan(""), 0.0, 0.0), std::invalid_argument);
    REQUIRE_THROWS_AS(hal.read_position(0.0, std::nan(""), 0.0), std::invalid_argument);
    REQUIRE_THROWS_AS(hal.read_position(0.0, 0.0, 0.0, std::nan("")), std::invalid_argument);
}

TEST_CASE("PositionController: T2 rejects invalid kp/kd/max_tilt_rad/velocity inputs", "[position][c39]") {
    REQUIRE_THROWS_AS(PositionController(0.0, 0.3, 0.5), std::invalid_argument);
    REQUIRE_THROWS_AS(PositionController(-0.1, 0.3, 0.5), std::invalid_argument);
    REQUIRE_THROWS_AS(PositionController(0.15, -0.1, 0.5), std::invalid_argument);
    REQUIRE_THROWS_AS(PositionController(0.15, 0.3, 0.0), std::invalid_argument);
    REQUIRE_THROWS_AS(PositionController(0.15, 0.3, -0.5), std::invalid_argument);

    PositionController controller;
    SimulatedPositionHal hal;
    PositionSample sample = hal.read_position(0.0, 0.0, 0.0);
    PositionSetpoint setpoint{1.0, 0.0};
    REQUIRE_THROWS_AS(controller.compute(setpoint, sample, std::nan(""), 0.0, 0.0), std::invalid_argument);
    REQUIRE_THROWS_AS(controller.compute(setpoint, sample, 0.0, std::nan(""), 0.0), std::invalid_argument);
}

TEST_CASE("PositionController: T3 East error -> positive pitch (q.y > 0), no roll", "[position][c39]") {
    PositionController controller;
    SimulatedPositionHal hal;
    PositionSample sample = hal.read_position(0.0, 0.0, 0.0);
    PositionSetpoint setpoint{5.0, 0.0};

    AttitudeSetpoint result = controller.compute(setpoint, sample, 0.0, 0.0, 0.0);
    REQUIRE(result.q_body_to_world_desired.y > 0.0);  // pitch > 0
    REQUIRE_THAT(result.q_body_to_world_desired.x, WithinAbs(0.0, 1e-12));  // roll == 0
}

TEST_CASE("PositionController: T3 North error -> negative roll (q.x < 0), no pitch", "[position][c39]") {
    PositionController controller;
    SimulatedPositionHal hal;
    PositionSample sample = hal.read_position(0.0, 0.0, 0.0);
    PositionSetpoint setpoint{0.0, 3.0};

    AttitudeSetpoint result = controller.compute(setpoint, sample, 0.0, 0.0, 0.0);
    REQUIRE(result.q_body_to_world_desired.x < 0.0);  // roll < 0
    REQUIRE_THAT(result.q_body_to_world_desired.y, WithinAbs(0.0, 1e-12));  // pitch == 0
}

TEST_CASE("PositionController: T3 yaw held at 0, extreme error clips to max_tilt_rad", "[position][c39]") {
    double max_tilt_rad = 0.4;
    PositionController controller(0.15, 0.3, max_tilt_rad);
    SimulatedPositionHal hal;
    PositionSample sample = hal.read_position(0.0, 0.0, 0.0);
    PositionSetpoint setpoint{1000.0, 0.0};

    AttitudeSetpoint result = controller.compute(setpoint, sample, 0.0, 0.0, 0.0);
    // yaw component (z) must stay 0.
    REQUIRE_THAT(result.q_body_to_world_desired.z, WithinAbs(0.0, 1e-12));
    // Clipped pitch magnitude: q = (cos(max/2), 0, sin(max/2), 0).
    REQUIRE_THAT(result.q_body_to_world_desired.w, WithinAbs(std::cos(max_tilt_rad / 2.0), 1e-9));
    REQUIRE_THAT(result.q_body_to_world_desired.y, WithinAbs(std::sin(max_tilt_rad / 2.0), 1e-9));
}

TEST_CASE(
    "ToyQuad6DofPlant + PositionController + AltitudeController: T4 closed loop horizontal distance strictly "
    "decreases",
    "[position][c39]") {
    ToyQuad6DofPlant plant;
    ControlLoop loop;
    SimulatedPositionHal pos_hal;
    PositionController pos_controller;
    SimulatedAltitudeHal alt_hal;
    AltitudeController alt_controller;
    PositionSetpoint setpoint{5.0, 0.0};
    double z_des = 2.0;
    double dt_s = 0.01;

    double x0 = plant.true_position_m()[0];
    double y0 = plant.true_position_m()[1];
    double initial_distance = std::sqrt((setpoint.x_m - x0) * (setpoint.x_m - x0) + (setpoint.y_m - y0) * (setpoint.y_m - y0));

    ImuSample sample = plant.sense();
    for (int i = 0; i < 1000; ++i) {
        PositionSample position = pos_hal.read_position(plant.true_position_m()[0], plant.true_position_m()[1], sample.t_s);
        AltitudeSample altitude = alt_hal.read_altitude(plant.true_position_m()[2], sample.t_s);
        double vx = plant.true_velocity_mps()[0];
        double vy = plant.true_velocity_mps()[1];
        double vz = plant.true_velocity_mps()[2];
        AttitudeSetpoint tilt_setpoint = pos_controller.compute(setpoint, position, vx, vy, sample.t_s);
        double collective = alt_controller.compute(z_des, altitude, vz);
        ControlTickResult tick = loop.step(sample, tilt_setpoint, collective);
        sample = plant.step(tick.forces, dt_s);
    }

    double x_final = plant.true_position_m()[0];
    double y_final = plant.true_position_m()[1];
    double final_distance =
        std::sqrt((setpoint.x_m - x_final) * (setpoint.x_m - x_final) + (setpoint.y_m - y_final) * (setpoint.y_m - y_final));

    REQUIRE(final_distance < initial_distance);
    REQUIRE(final_distance < 1.0);
    REQUIRE(std::isfinite(plant.true_position_m()[2]));
}
