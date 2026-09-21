// Fase C · C15 — Catch2 unit cases for `jarvis::fc::QuadXMixer`.
//
// Host-only test binary. Behavior-frozen: these cases assert the EXISTING
// C13-ported algorithm, they do not change it. No GPIO/hardware here.
#include <cmath>

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>

#include "jarvis/fc/mixer.hpp"

using namespace jarvis::fc;
using Catch::Matchers::WithinAbs;

TEST_CASE("QuadXMixer: hover collective, zero torque gives four equal, finite, in-range forces", "[mixer]") {
    QuadXMixer mixer;
    BodyTorqueCommand zero_torque{0.0, Vec3{0.0, 0.0, 0.0}};
    MotorForceCommand cmd = mixer.mix(0.5, zero_torque);

    for (double force : cmd.motor_forces) {
        REQUIRE(std::isfinite(force));
        REQUIRE(force >= 0.0);
        REQUIRE(force <= 1.0);
    }
    REQUIRE_THAT(cmd.motor_forces[0], WithinAbs(0.5, 1e-9));
    REQUIRE_THAT(cmd.motor_forces[1], WithinAbs(0.5, 1e-9));
    REQUIRE_THAT(cmd.motor_forces[2], WithinAbs(0.5, 1e-9));
    REQUIRE_THAT(cmd.motor_forces[3], WithinAbs(0.5, 1e-9));
}

TEST_CASE("QuadXMixer: positive roll torque raises FL/RL and lowers FR/RR (m1,m2 up / m0,m3 down)", "[mixer]") {
    QuadXMixer mixer(0.05, 0.05, 0.05);
    BodyTorqueCommand roll_torque{0.0, Vec3{1.0, 0.0, 0.0}};
    MotorForceCommand cmd = mixer.mix(0.5, roll_torque);

    REQUIRE(cmd.motor_forces[1] > 0.5);  // FL up
    REQUIRE(cmd.motor_forces[2] > 0.5);  // RL up
    REQUIRE(cmd.motor_forces[0] < 0.5);  // FR down
    REQUIRE(cmd.motor_forces[3] < 0.5);  // RR down
}

TEST_CASE("QuadXMixer: output is clamped to [0, 1] even for extreme torque", "[mixer]") {
    QuadXMixer mixer;
    BodyTorqueCommand extreme{0.0, Vec3{1000.0, 1000.0, 1000.0}};
    MotorForceCommand cmd = mixer.mix(0.5, extreme);
    for (double force : cmd.motor_forces) {
        REQUIRE(force >= 0.0);
        REQUIRE(force <= 1.0);
    }
}

TEST_CASE("QuadXMixer: collective is clamped to [0, 1] before mixing", "[mixer]") {
    QuadXMixer mixer;
    BodyTorqueCommand zero_torque{0.0, Vec3{0.0, 0.0, 0.0}};
    MotorForceCommand over = mixer.mix(5.0, zero_torque);
    for (double force : over.motor_forces) {
        REQUIRE_THAT(force, WithinAbs(1.0, 1e-9));
    }
}

TEST_CASE("QuadXMixer: rejects negative scales", "[mixer]") {
    REQUIRE_THROWS_AS(QuadXMixer(-0.1, 0.05, 0.05), std::invalid_argument);
    REQUIRE_NOTHROW(QuadXMixer(0.0, 0.0, 0.0));
}
