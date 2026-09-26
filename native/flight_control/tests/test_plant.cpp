// Fase C · C36 (`B1-fase-c-sim-6dof-plant`) — Catch2 unit cases for
// `jarvis::fc::ToyQuad6DofPlant`.
//
// Host-only test binary. `ToyQuadAttitudePlant` (C11) already has its
// own behavior locked by `fc_closed_loop_smoke` and `test_loop.cpp`'s
// bit-for-bit smoke-chain case — this file is `ToyQuad6DofPlant` only,
// and never edits/re-tests `ToyQuadAttitudePlant`. No GPIO/hardware
// here, no claim any real vehicle flies.
#include <cmath>
#include <stdexcept>

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>

#include "jarvis/fc/mixer.hpp"
#include "jarvis/fc/plant.hpp"

using namespace jarvis::fc;
using Catch::Matchers::WithinAbs;

namespace {
Quat pitch_tilted_quat(double tilt_rad) {
    // Rotation about the Y ("pitch") axis — matches this plant's own
    // torque-proxy convention (pitch_proxy feeds omega/axis_angle's Y
    // component). Distinct from the C11 smokes' own X ("roll") tilt
    // helper — either axis is a valid non-level start; this file's own
    // T4 case derives its expected sign from this exact convention.
    double half = tilt_rad / 2.0;
    return Quat{std::cos(half), 0.0, std::sin(half), 0.0};
}
}  // namespace

TEST_CASE("ToyQuad6DofPlant: T1 sense() at rest is level, gravity in body, zero gyro", "[plant][c36]") {
    ToyQuad6DofPlant plant;
    ImuSample sample = plant.sense();
    REQUIRE_THAT(sample.accel_mps2[0], WithinAbs(0.0, 1e-9));
    REQUIRE_THAT(sample.accel_mps2[1], WithinAbs(0.0, 1e-9));
    REQUIRE_THAT(sample.accel_mps2[2], WithinAbs(-9.81, 1e-9));
    REQUIRE_THAT(sample.gyro_rad_s[0], WithinAbs(0.0, 1e-12));
    REQUIRE_THAT(sample.gyro_rad_s[1], WithinAbs(0.0, 1e-12));
    REQUIRE_THAT(sample.gyro_rad_s[2], WithinAbs(0.0, 1e-12));
}

TEST_CASE("ToyQuad6DofPlant: T2 zero forces, small dt — position stays near origin, attitude stays level, finite", "[plant][c36]") {
    ToyQuad6DofPlant plant;
    MotorForceCommand zero_forces{0.0, MotorForces{0.0, 0.0, 0.0, 0.0}};
    ImuSample sample = plant.step(zero_forces, 0.001);

    for (double v : plant.true_position_m()) {
        REQUIRE(std::isfinite(v));
        REQUIRE(std::abs(v) < 1e-3);
    }
    Quat q = plant.true_attitude().q_body_to_world;
    REQUIRE_THAT(q.w, WithinAbs(1.0, 1e-12));
    REQUIRE_THAT(q.x, WithinAbs(0.0, 1e-12));
    REQUIRE_THAT(q.y, WithinAbs(0.0, 1e-12));
    REQUIRE_THAT(q.z, WithinAbs(0.0, 1e-12));
    REQUIRE(std::isfinite(sample.accel_mps2[2]));
}

TEST_CASE("ToyQuad6DofPlant: T3 level + high collective — altitude increases (thrust beats gravity)", "[plant][c36]") {
    ToyQuad6DofPlant plant;  // mass_kg=1, thrust_gain=20 (documented toy defaults)
    MotorForceCommand full_forces{0.0, MotorForces{1.0, 1.0, 1.0, 1.0}};  // sum=4 -> thrust=80N

    for (int i = 0; i < 50; ++i) {
        plant.step(full_forces, 0.01);
    }

    REQUIRE(plant.true_position_m()[2] > 0.0);
    REQUIRE(plant.true_velocity_mps()[2] > 0.0);
    REQUIRE_THAT(plant.true_position_m()[0], WithinAbs(0.0, 1e-9));
    REQUIRE_THAT(plant.true_position_m()[1], WithinAbs(0.0, 1e-9));
}

TEST_CASE("ToyQuad6DofPlant: T4 pitch-tilted + symmetric thrust — horizontal displacement in the derived direction", "[plant][c36]") {
    // Symmetric forces produce zero roll/pitch/yaw proxy, so the
    // attitude stays pinned exactly at the initial tilt for the whole
    // run — isolating the translation law from any attitude coupling.
    // Hand-derived (and cross-checked against the Python twin): rotating
    // body +Z thrust by a positive pitch-axis quaternion (cos(t/2), 0,
    // sin(t/2), 0) yields world (sin(t)*T, 0, cos(t)*T) — so a positive
    // tilt must give a strictly positive world-X displacement and
    // exactly zero world-Y displacement.
    ToyQuad6DofPlant plant;
    plant.reset(Vec3{0.0, 0.0, 0.0}, Vec3{0.0, 0.0, 0.0}, pitch_tilted_quat(0.1), Vec3{0.0, 0.0, 0.0});
    MotorForceCommand full_forces{0.0, MotorForces{1.0, 1.0, 1.0, 1.0}};

    for (int i = 0; i < 20; ++i) {
        plant.step(full_forces, 0.01);
    }

    REQUIRE(plant.true_position_m()[0] > 0.0);
    REQUIRE_THAT(plant.true_position_m()[1], WithinAbs(0.0, 1e-9));
    // Attitude stayed pinned — symmetric forces never disturbed it.
    Quat q = plant.true_attitude().q_body_to_world;
    Quat expected = pitch_tilted_quat(0.1);
    REQUIRE_THAT(q.w, WithinAbs(expected.w, 1e-9));
    REQUIRE_THAT(q.y, WithinAbs(expected.y, 1e-9));
}

TEST_CASE("ToyQuad6DofPlant: T5 true_position_m/true_velocity_mps change only via step, not sense", "[plant][c36]") {
    ToyQuad6DofPlant plant;
    MotorForceCommand full_forces{0.0, MotorForces{1.0, 1.0, 1.0, 1.0}};
    plant.step(full_forces, 0.01);
    Vec3 position_after_step = plant.true_position_m();
    Vec3 velocity_after_step = plant.true_velocity_mps();

    ImuSample unused = plant.sense();
    (void)unused;

    REQUIRE(plant.true_position_m() == position_after_step);
    REQUIRE(plant.true_velocity_mps() == velocity_after_step);
}

TEST_CASE("ToyQuad6DofPlant: T6 rejects invalid mass_kg/thrust_gain/torque_gain/angular_damping/dt_s", "[plant][c36]") {
    REQUIRE_THROWS_AS(ToyQuad6DofPlant(0.0, 20.0, 40.0, 0.5), std::invalid_argument);
    REQUIRE_THROWS_AS(ToyQuad6DofPlant(-1.0, 20.0, 40.0, 0.5), std::invalid_argument);
    REQUIRE_THROWS_AS(ToyQuad6DofPlant(1.0, 0.0, 40.0, 0.5), std::invalid_argument);
    REQUIRE_THROWS_AS(ToyQuad6DofPlant(1.0, 20.0, 0.0, 0.5), std::invalid_argument);
    REQUIRE_THROWS_AS(ToyQuad6DofPlant(1.0, 20.0, 40.0, -0.1), std::invalid_argument);

    ToyQuad6DofPlant plant;
    MotorForceCommand zero_forces{0.0, MotorForces{0.0, 0.0, 0.0, 0.0}};
    REQUIRE_THROWS_AS(plant.step(zero_forces, 0.0), std::invalid_argument);
    REQUIRE_THROWS_AS(plant.step(zero_forces, -0.01), std::invalid_argument);
}
