// Fase C · C15 — Catch2 unit cases for `jarvis::fc::PdAttitudeController`.
//
// Host-only test binary. Behavior-frozen: these cases assert the EXISTING
// C13-ported algorithm, they do not change it. No GPIO/hardware here.
#include <cmath>

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>

#include "jarvis/fc/controller.hpp"

using namespace jarvis::fc;
using Catch::Matchers::WithinAbs;

TEST_CASE("PdAttitudeController: level state, level setpoint gives zero rate command", "[controller]") {
    PdAttitudeController controller(6.0, 0.6);
    AttitudeSetpoint setpoint = level_setpoint(0.0);
    AttitudeState state{0.0, Quat{1.0, 0.0, 0.0, 0.0}, Vec3{0.0, 0.0, 0.0}};

    BodyRateCommand cmd = controller.compute(setpoint, state);
    REQUIRE_THAT(cmd.omega_body_rad_s[0], WithinAbs(0.0, 1e-9));
    REQUIRE_THAT(cmd.omega_body_rad_s[1], WithinAbs(0.0, 1e-9));
    REQUIRE_THAT(cmd.omega_body_rad_s[2], WithinAbs(0.0, 1e-9));
}

TEST_CASE("PdAttitudeController: tilted state toward level setpoint gives expected sign on dominant axis",
          "[controller]") {
    PdAttitudeController controller(6.0, 0.6);
    AttitudeSetpoint setpoint = level_setpoint(0.0);

    // Body tilted +10 deg about X (roll) — small positive rotation about X.
    double half = (10.0 * M_PI / 180.0) / 2.0;
    Quat tilted{std::cos(half), std::sin(half), 0.0, 0.0};
    AttitudeState state{0.0, tilted, Vec3{0.0, 0.0, 0.0}};

    BodyRateCommand cmd = controller.compute(setpoint, state);
    // Command must command a NEGATIVE roll rate to correct back toward
    // level from a POSITIVE roll tilt (restoring/negative-feedback sign).
    REQUIRE(cmd.omega_body_rad_s[0] < 0.0);
    // Off-axis channels should stay near zero for a pure-roll tilt.
    REQUIRE_THAT(cmd.omega_body_rad_s[1], WithinAbs(0.0, 1e-6));
    REQUIRE_THAT(cmd.omega_body_rad_s[2], WithinAbs(0.0, 1e-6));
}

TEST_CASE("PdAttitudeController: kd damps a nonzero measured rate at level attitude", "[controller]") {
    PdAttitudeController controller(6.0, 0.6);
    AttitudeSetpoint setpoint = level_setpoint(0.0);
    AttitudeState state{0.0, Quat{1.0, 0.0, 0.0, 0.0}, Vec3{1.0, 0.0, 0.0}};

    BodyRateCommand cmd = controller.compute(setpoint, state);
    // e_rot is zero (already level), so omega_cmd = -kd * omega_measured.
    REQUIRE_THAT(cmd.omega_body_rad_s[0], WithinAbs(-0.6, 1e-9));
}

TEST_CASE("PdAttitudeController: rejects invalid gains", "[controller]") {
    REQUIRE_THROWS_AS(PdAttitudeController(0.0, 0.6), std::invalid_argument);
    REQUIRE_THROWS_AS(PdAttitudeController(6.0, -0.1), std::invalid_argument);
    REQUIRE_NOTHROW(PdAttitudeController(1.0, 0.0));
}
