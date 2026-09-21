// Fase C · C15 — Catch2 unit cases for `jarvis::fc::encode_motor_forces` /
// `jarvis::fc::SimulatedEscSink`.
//
// Host-only test binary. Behavior-frozen: these cases assert the EXISTING
// C14-ported algorithm, they do not change it. May overlap in spirit with
// `fc_esc_pwm_smoke` (kept, per IC §0 decision 7) — that is fine, this is
// the per-rung unit-test home, the smoke is the separate end-to-end check.
// No GPIO/hardware here.
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>

#include "jarvis/fc/esc.hpp"

using namespace jarvis::fc;
using Catch::Matchers::WithinAbs;

namespace {
MotorForceCommand forces_of(double f0, double f1, double f2, double f3) {
    return MotorForceCommand{0.0, MotorForces{f0, f1, f2, f3}};
}
}  // namespace

TEST_CASE("encode_motor_forces: force=0 -> min_us, force=1 -> max_us", "[esc]") {
    EscPwmCommand zero = encode_motor_forces(forces_of(0.0, 0.0, 0.0, 0.0));
    REQUIRE_THAT(zero.pulse_us[0], WithinAbs(1000.0, 1e-9));

    EscPwmCommand one = encode_motor_forces(forces_of(1.0, 1.0, 1.0, 1.0));
    REQUIRE_THAT(one.pulse_us[0], WithinAbs(2000.0, 1e-9));

    REQUIRE(zero.protocol == "pwm_us");
}

TEST_CASE("encode_motor_forces: custom bounds still map linearly", "[esc]") {
    EscPwmCommand mid = encode_motor_forces(forces_of(0.5, 0.5, 0.5, 0.5), 1100.0, 1900.0);
    REQUIRE_THAT(mid.pulse_us[0], WithinAbs(1500.0, 1e-9));
}

TEST_CASE("encode_motor_forces: rejects invalid min/max bounds", "[esc]") {
    REQUIRE_THROWS_AS(encode_motor_forces(forces_of(0.0, 0.0, 0.0, 0.0), 1500.0, 1500.0),
                       std::invalid_argument);
    REQUIRE_THROWS_AS(encode_motor_forces(forces_of(0.0, 0.0, 0.0, 0.0), 2000.0, 1000.0),
                       std::invalid_argument);
}

TEST_CASE("SimulatedEscSink: starts disarmed; apply() records but refuses", "[esc]") {
    SimulatedEscSink sink;
    REQUIRE_FALSE(sink.armed());

    EscPwmCommand cmd = encode_motor_forces(forces_of(0.5, 0.5, 0.5, 0.5));
    EscApplyResult result = sink.apply(cmd);

    REQUIRE_FALSE(result.applied);
    REQUIRE(result.reason.has_value());
    REQUIRE(*result.reason == "disarmed");
    REQUIRE(sink.last_command().has_value());
}

TEST_CASE("SimulatedEscSink: armed apply() reports applied=true with no reason", "[esc]") {
    SimulatedEscSink sink;
    sink.arm();
    REQUIRE(sink.armed());

    EscPwmCommand cmd = encode_motor_forces(forces_of(0.9, 0.1, 0.9, 0.1));
    EscApplyResult result = sink.apply(cmd);

    REQUIRE(result.applied);
    REQUIRE_FALSE(result.reason.has_value());

    sink.disarm();
    REQUIRE_FALSE(sink.armed());
    EscApplyResult after = sink.apply(cmd);
    REQUIRE_FALSE(after.applied);
}
