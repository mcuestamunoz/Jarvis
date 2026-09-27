// Fase C · C40 (`B1-fase-c-autonomy-executor`) — Catch2 unit cases for
// `jarvis::fc::SimAutonomyExecutor`.
//
// Host-only test binary. No real sensor bus here, no GPIO/hardware, no
// C4 command-surface symbol, no Safety call.
#include <cmath>
#include <stdexcept>

#include <catch2/catch_test_macros.hpp>

#include "jarvis/fc/plant.hpp"
#include "jarvis/fc/sim_autonomy_executor.hpp"

using namespace jarvis::fc;

TEST_CASE("SimAutonomyExecutor: T1 GO_TO shrinks horizontal distance to an East point", "[autonomy][c40]") {
    ToyQuad6DofPlant plant;
    SimAutonomyExecutor executor(plant);

    double x0 = plant.true_position_m()[0];
    double y0 = plant.true_position_m()[1];
    double initial_distance = std::sqrt((3.0 - x0) * (3.0 - x0) + (0.0 - y0) * (0.0 - y0));

    SimAutonomyParams params;
    params.x_m = 3.0;
    params.y_m = 0.0;
    params.z_m = 2.0;
    for (int i = 0; i < 1500; ++i) {
        executor.tick(SimAutonomyVerb::kGoTo, params, 0.01);
    }

    double x1 = plant.true_position_m()[0];
    double y1 = plant.true_position_m()[1];
    double final_distance = std::sqrt((3.0 - x1) * (3.0 - x1) + (0.0 - y1) * (0.0 - y1));

    REQUIRE(final_distance < initial_distance);
    REQUIRE(final_distance < 0.1);
    REQUIRE(std::isfinite(plant.true_position_m()[2]));
}

TEST_CASE("SimAutonomyExecutor: T2 HOLD keeps position within a documented bound after settling", "[autonomy][c40]") {
    ToyQuad6DofPlant plant;
    SimAutonomyExecutor executor(plant);

    SimAutonomyParams goto_params;
    goto_params.x_m = 3.0;
    goto_params.y_m = 0.0;
    goto_params.z_m = 2.0;
    for (int i = 0; i < 1500; ++i) {
        executor.tick(SimAutonomyVerb::kGoTo, goto_params, 0.01);
    }

    SimAutonomyParams no_params;
    for (int i = 0; i < 300; ++i) {
        executor.tick(SimAutonomyVerb::kHold, no_params, 0.01);
    }

    double x_min = 1e9, x_max = -1e9, y_min = 1e9, y_max = -1e9, z_min = 1e9, z_max = -1e9;
    for (int i = 0; i < 500; ++i) {
        executor.tick(SimAutonomyVerb::kHold, no_params, 0.01);
        Vec3 p = plant.true_position_m();
        x_min = std::min(x_min, p[0]);
        x_max = std::max(x_max, p[0]);
        y_min = std::min(y_min, p[1]);
        y_max = std::max(y_max, p[1]);
        z_min = std::min(z_min, p[2]);
        z_max = std::max(z_max, p[2]);
    }

    REQUIRE(x_max - x_min < 0.5);
    REQUIRE(y_max - y_min < 0.5);
    REQUIRE(z_max - z_min < 0.5);
    REQUIRE(x_min > 2.5);
    REQUIRE(x_max < 3.5);
}

TEST_CASE("SimAutonomyExecutor: T3 LAND decreases z toward a documented floor", "[autonomy][c40]") {
    ToyQuad6DofPlant plant;
    SimAutonomyExecutor executor(plant);

    SimAutonomyParams goto_params;
    goto_params.x_m = 0.0;
    goto_params.y_m = 0.0;
    goto_params.z_m = 2.0;
    for (int i = 0; i < 1500; ++i) {
        executor.tick(SimAutonomyVerb::kGoTo, goto_params, 0.01);
    }

    double z_pre = plant.true_position_m()[2];

    SimAutonomyParams no_params;
    for (int i = 0; i < 1000; ++i) {
        executor.tick(SimAutonomyVerb::kLand, no_params, 0.01);
    }

    double z_post = plant.true_position_m()[2];

    REQUIRE(z_post < z_pre);
    REQUIRE(z_post < 0.5);
    REQUIRE(std::isfinite(z_post));
}

TEST_CASE("SimAutonomyExecutor: T4 GO_TO missing x_m/y_m and non-finite params/dt_s raise", "[autonomy][c40]") {
    ToyQuad6DofPlant plant;
    SimAutonomyExecutor executor(plant);

    SimAutonomyParams missing;
    missing.x_m = 1.0;  // y_m left unset
    REQUIRE_THROWS_AS(executor.tick(SimAutonomyVerb::kGoTo, missing, 0.01), std::invalid_argument);

    SimAutonomyParams nan_params;
    nan_params.x_m = std::nan("");
    nan_params.y_m = 0.0;
    REQUIRE_THROWS_AS(executor.tick(SimAutonomyVerb::kGoTo, nan_params, 0.01), std::invalid_argument);

    SimAutonomyParams ok_params;
    ok_params.x_m = 1.0;
    ok_params.y_m = 0.0;
    REQUIRE_THROWS_AS(executor.tick(SimAutonomyVerb::kGoTo, ok_params, std::nan("")), std::invalid_argument);
    REQUIRE_THROWS_AS(executor.tick(SimAutonomyVerb::kGoTo, ok_params, 0.0), std::invalid_argument);

    REQUIRE_THROWS_AS(SimAutonomyExecutor(plant, std::nan(""), 0.5), std::invalid_argument);
    REQUIRE_THROWS_AS(SimAutonomyExecutor(plant, 0.0, -0.1), std::invalid_argument);
}
