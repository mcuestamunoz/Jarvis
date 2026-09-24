// Fase C · C31 — Catch2 unit cases for `jarvis::fc::encode_dshot_frame` /
// `encode_motor_forces_dshot`.
//
// Host-only test binary. No GPIO/hardware here, no radio-link protocol
// named anywhere in this file.
#include <catch2/catch_test_macros.hpp>

#include "jarvis/fc/dshot.hpp"

using namespace jarvis::fc;

namespace {
MotorForceCommand forces_of(double f0, double f1, double f2, double f3) {
    return MotorForceCommand{0.0, MotorForces{f0, f1, f2, f3}};
}
}  // namespace

TEST_CASE("encode_dshot_frame: known vectors 0x0000 / 0x0606 / 0xFFEE", "[dshot]") {
    REQUIRE(encode_dshot_frame(0) == 0x0000);
    REQUIRE(encode_dshot_frame(48) == 0x0606);
    REQUIRE(encode_dshot_frame(2047) == 0xFFEE);
}

TEST_CASE("encode_dshot_frame: telemetry bit changes value before checksum", "[dshot]") {
    uint16_t without_telem = encode_dshot_frame(48, false);
    uint16_t with_telem = encode_dshot_frame(48, true);
    REQUIRE(without_telem != with_telem);
    REQUIRE(with_telem == 0x0617);
}

TEST_CASE("encode_dshot_frame: rejects throttle outside [0, 2047]", "[dshot]") {
    REQUIRE_THROWS_AS(encode_dshot_frame(2048), std::invalid_argument);
    REQUIRE_THROWS_AS(encode_dshot_frame(-1), std::invalid_argument);
}

TEST_CASE("encode_motor_forces_dshot: force endpoints map to throttle 48 and 2047", "[dshot]") {
    MotorForceCommand forces = forces_of(0.0, 1.0, 0.0, 1.0);
    std::array<uint16_t, 4> frames = encode_motor_forces_dshot(forces);
    REQUIRE(frames[0] == 0x0606);
    REQUIRE(frames[1] == 0xFFEE);
    REQUIRE(frames[2] == 0x0606);
    REQUIRE(frames[3] == 0xFFEE);
}
