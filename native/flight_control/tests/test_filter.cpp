// Fase C · C15 — Catch2 unit cases for `jarvis::fc::ImuLowPassFilter`.
//
// Host-only test binary. Behavior-frozen: these cases assert the EXISTING
// C13-ported algorithm, they do not change it. No GPIO/hardware here.
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>

#include "jarvis/fc/filter.hpp"

using namespace jarvis::fc;
using Catch::Matchers::WithinAbs;

TEST_CASE("ImuLowPassFilter: first sample seeds unsmoothed", "[filter]") {
    ImuLowPassFilter filt(0.2);
    ImuSample raw{0.0, Vec3{1.0, 2.0, 3.0}, Vec3{0.1, 0.2, 0.3}};
    ImuSample filtered = filt.filter_sample(raw);

    REQUIRE_THAT(filtered.accel_mps2[0], WithinAbs(1.0, 1e-9));
    REQUIRE_THAT(filtered.accel_mps2[1], WithinAbs(2.0, 1e-9));
    REQUIRE_THAT(filtered.gyro_rad_s[2], WithinAbs(0.3, 1e-9));
}

TEST_CASE("ImuLowPassFilter: second sample moves toward raw by alpha (EMA shape)", "[filter]") {
    ImuLowPassFilter filt(0.2);
    filt.filter_sample(ImuSample{0.0, Vec3{0.0, 0.0, 0.0}, Vec3{0.0, 0.0, 0.0}});

    ImuSample second_raw{0.01, Vec3{10.0, 0.0, 0.0}, Vec3{0.0, 0.0, 0.0}};
    ImuSample filtered = filt.filter_sample(second_raw);

    // EMA: filtered = alpha*raw + (1-alpha)*previous = 0.2*10 + 0.8*0 = 2.0
    REQUIRE_THAT(filtered.accel_mps2[0], WithinAbs(2.0, 1e-9));
    // Must move toward the raw value, not overshoot or stay put.
    REQUIRE(filtered.accel_mps2[0] > 0.0);
    REQUIRE(filtered.accel_mps2[0] < 10.0);
}

TEST_CASE("ImuLowPassFilter: reset() re-seeds on next sample", "[filter]") {
    ImuLowPassFilter filt(0.5);
    filt.filter_sample(ImuSample{0.0, Vec3{5.0, 5.0, 5.0}, Vec3{0.0, 0.0, 0.0}});
    filt.reset();

    ImuSample raw{1.0, Vec3{1.0, 1.0, 1.0}, Vec3{0.0, 0.0, 0.0}};
    ImuSample filtered = filt.filter_sample(raw);
    REQUIRE_THAT(filtered.accel_mps2[0], WithinAbs(1.0, 1e-9));
}

TEST_CASE("ImuLowPassFilter: rejects out-of-range alpha", "[filter]") {
    REQUIRE_THROWS_AS(ImuLowPassFilter(0.0), std::invalid_argument);
    REQUIRE_THROWS_AS(ImuLowPassFilter(1.1), std::invalid_argument);
    REQUIRE_NOTHROW(ImuLowPassFilter(1.0));
}
