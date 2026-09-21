// Fase C · C15 — Catch2 unit cases for `jarvis::fc::LinearRateTorqueBridge`.
//
// Host-only test binary. Behavior-frozen: these cases assert the EXISTING
// C13-ported algorithm (single feedforward map, no cascaded PID), they do
// not change it. No GPIO/hardware here.
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>

#include "jarvis/fc/rate_torque.hpp"

using namespace jarvis::fc;
using Catch::Matchers::WithinAbs;

TEST_CASE("LinearRateTorqueBridge: zero rate gives zero torque", "[rate_torque]") {
    LinearRateTorqueBridge bridge;
    BodyRateCommand zero{0.0, Vec3{0.0, 0.0, 0.0}};
    BodyTorqueCommand torque = bridge.convert(zero);
    REQUIRE_THAT(torque.tau_body[0], WithinAbs(0.0, 1e-9));
    REQUIRE_THAT(torque.tau_body[1], WithinAbs(0.0, 1e-9));
    REQUIRE_THAT(torque.tau_body[2], WithinAbs(0.0, 1e-9));
}

TEST_CASE("LinearRateTorqueBridge: default gain=1.0 is an identity feedforward map", "[rate_torque]") {
    LinearRateTorqueBridge bridge;  // default gain = 1.0
    BodyRateCommand rate{0.0, Vec3{0.3, -0.1, 0.05}};
    BodyTorqueCommand torque = bridge.convert(rate);
    REQUIRE_THAT(torque.tau_body[0], WithinAbs(0.3, 1e-9));
    REQUIRE_THAT(torque.tau_body[1], WithinAbs(-0.1, 1e-9));
    REQUIRE_THAT(torque.tau_body[2], WithinAbs(0.05, 1e-9));
}

TEST_CASE("LinearRateTorqueBridge: scalar gain scales and preserves sign", "[rate_torque]") {
    LinearRateTorqueBridge bridge(2.0);
    BodyRateCommand rate{0.0, Vec3{0.3, -0.1, 0.0}};
    BodyTorqueCommand torque = bridge.convert(rate);
    REQUIRE_THAT(torque.tau_body[0], WithinAbs(0.6, 1e-9));
    REQUIRE_THAT(torque.tau_body[1], WithinAbs(-0.2, 1e-9));
    // Sign must be preserved for a positive feedforward gain.
    REQUIRE(torque.tau_body[0] > 0.0);
    REQUIRE(torque.tau_body[1] < 0.0);
}

TEST_CASE("LinearRateTorqueBridge: per-axis gains", "[rate_torque]") {
    LinearRateTorqueBridge bridge(Vec3{2.0, 3.0, 4.0});
    BodyRateCommand rate{0.0, Vec3{1.0, 1.0, 1.0}};
    BodyTorqueCommand torque = bridge.convert(rate);
    REQUIRE_THAT(torque.tau_body[0], WithinAbs(2.0, 1e-9));
    REQUIRE_THAT(torque.tau_body[1], WithinAbs(3.0, 1e-9));
    REQUIRE_THAT(torque.tau_body[2], WithinAbs(4.0, 1e-9));
}

TEST_CASE("LinearRateTorqueBridge: rejects non-positive or non-finite gains", "[rate_torque]") {
    REQUIRE_THROWS_AS(LinearRateTorqueBridge(0.0), std::invalid_argument);
    REQUIRE_THROWS_AS(LinearRateTorqueBridge(-1.0), std::invalid_argument);
    REQUIRE_THROWS_AS(LinearRateTorqueBridge(Vec3{1.0, 0.0, 1.0}), std::invalid_argument);
}
