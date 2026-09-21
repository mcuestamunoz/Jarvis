// Fase C · C15 — Catch2 unit cases for `jarvis::fc::ComplementaryAttitudeEstimator`.
//
// Host-only test binary. Behavior-frozen: these cases assert the EXISTING
// C13-ported algorithm (including the C11 Amendment A sign fix), they do
// not change it. No GPIO/hardware here.
#include <cmath>

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>

#include "jarvis/fc/attitude.hpp"

using namespace jarvis::fc;
using Catch::Matchers::WithinAbs;

TEST_CASE("ComplementaryAttitudeEstimator: level, zero-motion input stays level", "[attitude]") {
    ComplementaryAttitudeEstimator estimator(0.02);
    ImuSample level{0.0, Vec3{0.0, 0.0, -9.81}, Vec3{0.0, 0.0, 0.0}};

    // First call seeds at identity.
    AttitudeState first = estimator.update(level);
    REQUIRE_THAT(first.q_body_to_world.w, WithinAbs(1.0, 1e-9));

    ImuSample level_next{0.01, Vec3{0.0, 0.0, -9.81}, Vec3{0.0, 0.0, 0.0}};
    AttitudeState second = estimator.update(level_next);
    REQUIRE_THAT(second.q_body_to_world.w, WithinAbs(1.0, 1e-6));
    REQUIRE_THAT(second.q_body_to_world.x, WithinAbs(0.0, 1e-6));
    REQUIRE_THAT(second.q_body_to_world.y, WithinAbs(0.0, 1e-6));
}

TEST_CASE("ComplementaryAttitudeEstimator: tilted accel correction stays finite and converges toward true tilt",
          "[attitude]") {
    // Regression guard for the C11 Amendment A cross-product argument-order
    // fix: a constant accel reading for a small true tilt must converge the
    // estimate TOWARD that tilt (same sign), never away from it or to NaN.
    ComplementaryAttitudeEstimator estimator(0.05);
    double tilt_rad = 5.0 * M_PI / 180.0;
    // Accel reading consistent with a body tilted +tilt_rad about X (roll).
    Vec3 tilted_accel{0.0, -9.81 * std::sin(tilt_rad), -9.81 * std::cos(tilt_rad)};

    AttitudeState state{0.0, Quat{1.0, 0.0, 0.0, 0.0}, Vec3{0.0, 0.0, 0.0}};
    for (int i = 0; i < 200; ++i) {
        ImuSample sample{0.01 * (i + 1), tilted_accel, Vec3{0.0, 0.0, 0.0}};
        state = estimator.update(sample);
        REQUIRE(std::isfinite(state.q_body_to_world.w));
        REQUIRE(std::isfinite(state.q_body_to_world.x));
    }

    // Converged estimate must lean the same direction as the true tilt (x
    // component positive) — the opposite sign would reproduce the C11-fixed
    // bug (correction pulling away from truth).
    REQUIRE(state.q_body_to_world.x > 0.0);
}

TEST_CASE("ComplementaryAttitudeEstimator: rejects out-of-range gain", "[attitude]") {
    REQUIRE_THROWS_AS(ComplementaryAttitudeEstimator(0.0), std::invalid_argument);
    REQUIRE_THROWS_AS(ComplementaryAttitudeEstimator(1.5), std::invalid_argument);
    REQUIRE_NOTHROW(ComplementaryAttitudeEstimator(1.0));
}
