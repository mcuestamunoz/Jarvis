// Fase C · C27 — Catch2 unit cases for `jarvis::fc::RcHoldWatch` /
// `failsafe_loop_inputs`.
//
// Host-only test binary. Protocol-agnostic — no radio-link protocol
// named anywhere in this file, no GPIO/hardware.
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>

#include "jarvis/fc/rc_hold.hpp"

using namespace jarvis::fc;
using Catch::Matchers::WithinAbs;

TEST_CASE("RcHoldWatch: never noted is stale with reason=never", "[rc_hold]") {
    RcHoldWatch watch;
    RcHoldDecision decision = watch.evaluate(0.0);

    REQUIRE(decision.stale);
    REQUIRE(decision.reason == "never");
    REQUIRE_FALSE(decision.age_s.has_value());
    REQUIRE(watch.is_stale(0.0));
}

TEST_CASE("RcHoldWatch: fresh at and before the timeout boundary", "[rc_hold]") {
    RcHoldWatch watch(0.5);
    watch.note_rc(10.0);

    RcHoldDecision at_boundary = watch.evaluate(10.5);
    REQUIRE_FALSE(at_boundary.stale);
    REQUIRE(at_boundary.reason == "fresh");
    REQUIRE_THAT(*at_boundary.age_s, WithinAbs(0.5, 1e-12));

    RcHoldDecision just_under = watch.evaluate(10.3);
    REQUIRE_FALSE(just_under.stale);
    REQUIRE(just_under.reason == "fresh");
}

TEST_CASE("RcHoldWatch: stale with reason=timeout just past the boundary", "[rc_hold]") {
    RcHoldWatch watch(0.5);
    watch.note_rc(0.0);

    RcHoldDecision decision = watch.evaluate(0.5 + 1e-9);
    REQUIRE(decision.stale);
    REQUIRE(decision.reason == "timeout");
    REQUIRE(watch.is_stale(0.5 + 1e-9));
}

TEST_CASE("RcHoldWatch: rejects now_s before the last noted time", "[rc_hold]") {
    RcHoldWatch watch;
    watch.note_rc(5.0);
    REQUIRE_THROWS_AS(watch.evaluate(4.0), std::invalid_argument);
}

TEST_CASE("RcHoldWatch: rejects non-positive timeout_s", "[rc_hold]") {
    REQUIRE_THROWS_AS(RcHoldWatch(0.0), std::invalid_argument);
    REQUIRE_THROWS_AS(RcHoldWatch(-1.0), std::invalid_argument);
}

TEST_CASE("failsafe_loop_inputs: level quat and zero collective", "[rc_hold]") {
    RcLoopInputs inputs = failsafe_loop_inputs(3.0);

    REQUIRE_THAT(inputs.setpoint.q_body_to_world_desired.w, WithinAbs(1.0, 1e-12));
    REQUIRE_THAT(inputs.setpoint.q_body_to_world_desired.x, WithinAbs(0.0, 1e-12));
    REQUIRE_THAT(inputs.setpoint.q_body_to_world_desired.y, WithinAbs(0.0, 1e-12));
    REQUIRE_THAT(inputs.setpoint.q_body_to_world_desired.z, WithinAbs(0.0, 1e-12));
    REQUIRE_THAT(inputs.collective, WithinAbs(0.0, 1e-12));
    REQUIRE_THAT(inputs.setpoint.t_s, WithinAbs(3.0, 1e-12));
}
