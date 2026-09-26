// Fase C · C37 (`B1-fase-c-mag-yaw-rung`) — Catch2 unit cases for
// `jarvis::fc::SimulatedMagHal` and the mag-aware
// `ComplementaryAttitudeEstimator::update` extension.
//
// Host-only test binary. No real sensor bus here, no GPIO/hardware.
#include <cmath>
#include <stdexcept>

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>

#include "jarvis/fc/attitude.hpp"
#include "jarvis/fc/mag.hpp"

using namespace jarvis::fc;
using Catch::Matchers::WithinAbs;

TEST_CASE("SimulatedMagHal: T1 identity q gives body mag == world field", "[mag][c37]") {
    SimulatedMagHal hal;
    Quat identity{1.0, 0.0, 0.0, 0.0};

    MagSample sample = hal.read_mag(identity, 0.0);

    REQUIRE_THAT(sample.mag_body_uT[0], WithinAbs(0.0, 1e-12));
    REQUIRE_THAT(sample.mag_body_uT[1], WithinAbs(1.0, 1e-12));
    REQUIRE_THAT(sample.mag_body_uT[2], WithinAbs(0.0, 1e-12));
}

TEST_CASE("SimulatedMagHal: T2 known yaw rotation rotates body mag consistently, finite", "[mag][c37]") {
    SimulatedMagHal hal;
    double yaw = 45.0 * M_PI / 180.0;
    Quat yawed{std::cos(yaw / 2.0), 0.0, 0.0, std::sin(yaw / 2.0)};

    MagSample sample = hal.read_mag(yawed, 0.0);

    for (double c : sample.mag_body_uT) {
        REQUIRE(std::isfinite(c));
    }
    // World field (0,1,0) rotated by -45deg (body<-world via conjugate)
    // lands at (sin45, cos45, 0) — verified against the same rotation
    // formula the Python twin's own scratch check used.
    REQUIRE_THAT(sample.mag_body_uT[0], WithinAbs(std::sin(yaw), 1e-9));
    REQUIRE_THAT(sample.mag_body_uT[1], WithinAbs(std::cos(yaw), 1e-9));
    REQUIRE_THAT(sample.mag_body_uT[2], WithinAbs(0.0, 1e-9));
}

TEST_CASE("SimulatedMagHal: rejects zero/non-finite world_field_enu", "[mag][c37]") {
    REQUIRE_THROWS_AS(SimulatedMagHal(Vec3{0.0, 0.0, 0.0}), std::invalid_argument);
}

TEST_CASE("ComplementaryAttitudeEstimator: T3 without mag, C7 regression stays green (behavior freeze)", "[mag][c37]") {
    ComplementaryAttitudeEstimator estimator(0.02);
    ImuSample level{0.0, Vec3{0.0, 0.0, -9.81}, Vec3{0.0, 0.0, 0.0}};
    AttitudeState first = estimator.update(level);
    REQUIRE_THAT(first.q_body_to_world.w, WithinAbs(1.0, 1e-12));

    ImuSample level2{0.01, Vec3{0.0, 0.0, -9.81}, Vec3{0.0, 0.0, 0.0}};
    AttitudeState second = estimator.update(level2);
    REQUIRE_THAT(second.q_body_to_world.w, WithinAbs(1.0, 1e-9));
}

TEST_CASE("ComplementaryAttitudeEstimator: T4 with mag, yaw error decreases over N updates", "[mag][c37]") {
    double true_yaw_error = 30.0 * M_PI / 180.0;
    Quat initial_q{std::cos(true_yaw_error / 2.0), 0.0, 0.0, std::sin(true_yaw_error / 2.0)};
    ComplementaryAttitudeEstimator estimator(0.2, initial_q, 0.15);
    SimulatedMagHal hal;
    Quat true_north{1.0, 0.0, 0.0, 0.0};  // true heading is identity (north)

    double t_s = 0.0;
    double first_error = -1.0;
    double last_error = -1.0;
    for (int i = 0; i < 30; ++i) {
        ImuSample sample{t_s, Vec3{0.0, 0.0, -9.81}, Vec3{0.0, 0.0, 0.0}};
        MagSample mag = hal.read_mag(true_north, t_s);
        AttitudeState state = estimator.update(sample, mag);
        double yaw_est = std::abs(2.0 * std::atan2(state.q_body_to_world.z, state.q_body_to_world.w));
        if (i == 0) {
            first_error = yaw_est;
        }
        last_error = yaw_est;
        t_s += 0.05;
    }

    REQUIRE(last_error < first_error);
    REQUIRE(last_error < (5.0 * M_PI / 180.0));  // converged below 5 degrees
}

TEST_CASE("ComplementaryAttitudeEstimator: rejects invalid mag_gain", "[mag][c37]") {
    REQUIRE_THROWS_AS(ComplementaryAttitudeEstimator(0.02, Quat{1.0, 0.0, 0.0, 0.0}, 0.0), std::invalid_argument);
    REQUIRE_THROWS_AS(ComplementaryAttitudeEstimator(0.02, Quat{1.0, 0.0, 0.0, 0.0}, -0.1), std::invalid_argument);
}
