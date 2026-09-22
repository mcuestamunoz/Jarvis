// Fase C · C25 — Catch2 unit cases for `jarvis::fc::map_rc_to_loop_inputs`.
//
// Host-only test binary. No radio-link parsing, no plant, no GPIO/hardware
// here.
#include <cmath>
#include <vector>

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>

#include "jarvis/fc/rc_setpoint.hpp"

using namespace jarvis::fc;
using Catch::Matchers::WithinAbs;

namespace {
std::vector<int> channels_of(int roll, int pitch, int throttle, int yaw = kRcChMid) {
    return std::vector<int>{roll, pitch, throttle, yaw};
}
}  // namespace

TEST_CASE("map_rc_to_loop_inputs: all-mid sticks give ~level quat and finite collective", "[rc_setpoint]") {
    RcLoopInputs inputs = map_rc_to_loop_inputs(channels_of(kRcChMid, kRcChMid, kRcChMid), 0.0);

    REQUIRE_THAT(inputs.setpoint.q_body_to_world_desired.w, WithinAbs(1.0, 1e-9));
    REQUIRE_THAT(inputs.setpoint.q_body_to_world_desired.x, WithinAbs(0.0, 1e-9));
    REQUIRE_THAT(inputs.setpoint.q_body_to_world_desired.y, WithinAbs(0.0, 1e-9));
    REQUIRE(std::isfinite(inputs.collective));
    REQUIRE(inputs.collective >= 0.0);
    REQUIRE(inputs.collective <= 1.0);
}

TEST_CASE("map_rc_to_loop_inputs: throttle extremes map to collective 0 and 1", "[rc_setpoint]") {
    RcLoopInputs low = map_rc_to_loop_inputs(channels_of(kRcChMid, kRcChMid, kRcChMin), 0.0);
    RcLoopInputs high = map_rc_to_loop_inputs(channels_of(kRcChMid, kRcChMid, kRcChMax), 0.0);

    REQUIRE_THAT(low.collective, WithinAbs(0.0, 1e-9));
    REQUIRE_THAT(high.collective, WithinAbs(1.0, 1e-9));
}

TEST_CASE("map_rc_to_loop_inputs: roll max reaches +30 degrees, clips beyond range", "[rc_setpoint]") {
    RcLoopInputs at_max = map_rc_to_loop_inputs(channels_of(kRcChMax, kRcChMid, kRcChMid), 0.0);
    RcLoopInputs beyond_max = map_rc_to_loop_inputs(channels_of(2047, kRcChMid, kRcChMid), 0.0);

    double roll_deg = 2.0 * std::asin(std::max(-1.0, std::min(1.0, at_max.setpoint.q_body_to_world_desired.x))) *
                       180.0 / M_PI;
    REQUIRE_THAT(roll_deg, WithinAbs(30.0, 1e-6));
    REQUIRE_THAT(beyond_max.setpoint.q_body_to_world_desired.x, WithinAbs(at_max.setpoint.q_body_to_world_desired.x, 1e-12));
}

TEST_CASE("map_rc_to_loop_inputs: yaw channel changes do not change setpoint/collective", "[rc_setpoint]") {
    RcLoopInputs low_yaw = map_rc_to_loop_inputs(channels_of(kRcChMid, kRcChMid, kRcChMid, kRcChMin), 0.0);
    RcLoopInputs high_yaw = map_rc_to_loop_inputs(channels_of(kRcChMid, kRcChMid, kRcChMid, kRcChMax), 0.0);

    REQUIRE_THAT(low_yaw.collective, WithinAbs(high_yaw.collective, 1e-12));
    REQUIRE_THAT(low_yaw.setpoint.q_body_to_world_desired.w, WithinAbs(high_yaw.setpoint.q_body_to_world_desired.w, 1e-12));
    REQUIRE_THAT(low_yaw.setpoint.q_body_to_world_desired.x, WithinAbs(high_yaw.setpoint.q_body_to_world_desired.x, 1e-12));
}

TEST_CASE("map_rc_to_loop_inputs: rejects too-short channel lists", "[rc_setpoint]") {
    REQUIRE_THROWS_AS(map_rc_to_loop_inputs(std::vector<int>{1, 2}, 0.0), std::invalid_argument);
}
