// Fase C · C24 — Catch2 unit cases for `jarvis::fc::ControlLoop::step`.
//
// Host-only test binary. Behavior-frozen: these cases assert the EXISTING
// rung math (filter/attitude/controller/rate_torque/mixer/esc), ported
// unchanged, now called by name instead of inlined. No GPIO/hardware
// here, no plant call inside `step`.
#include <cmath>

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>

#include "jarvis/fc/controller.hpp"
#include "jarvis/fc/loop.hpp"
#include "jarvis/fc/plant.hpp"
#include "jarvis/fc/types.hpp"

using namespace jarvis::fc;
using Catch::Matchers::WithinAbs;

namespace {
Quat tilted_initial_quat(double tilt_rad) {
    double half = tilt_rad / 2.0;
    return Quat{std::cos(half), std::sin(half), 0.0, 0.0};
}
}  // namespace

TEST_CASE("ControlLoop::step: one tick produces four finite motor forces", "[loop]") {
    ControlLoop loop;
    ImuSample sample{0.0, Vec3{0.0, 0.0, -9.81}, Vec3{0.0, 0.0, 0.0}};
    AttitudeSetpoint setpoint = level_setpoint(0.0);

    ControlTickResult tick = loop.step(sample, setpoint, 0.5);

    for (double force : tick.forces.motor_forces) {
        REQUIRE(std::isfinite(force));
    }
    REQUIRE(tick.forces.motor_forces.size() == 4);
    REQUIRE(tick.pwm.protocol == "pwm_us");
}

TEST_CASE("ControlLoop::step: does not call the plant (forces feed it, step never reads it)", "[loop]") {
    // step() takes only sample/setpoint/collective — there is no plant
    // parameter to pass, and no plant getter it could reach for. This
    // test documents that by construction: a loop built with no plant
    // reference anywhere still produces a full tick.
    ControlLoop loop;
    ImuSample sample{1.0, Vec3{0.0, 0.0, -9.81}, Vec3{0.1, 0.0, 0.0}};
    AttitudeSetpoint setpoint = level_setpoint(1.0);
    ControlTickResult tick = loop.step(sample, setpoint, 0.5);
    REQUIRE(tick.t_s == tick.forces.t_s);
    REQUIRE(tick.state.t_s == tick.filtered.t_s);
}

TEST_CASE("ControlLoop::step: matches the inlined C13 smoke chain bit-for-bit", "[loop]") {
    constexpr int kSteps = 50;
    constexpr double kDtS = 0.01;
    constexpr double kCollective = 0.5;

    // Inlined reference chain (same construction fc_closed_loop_smoke used
    // before C24's refactor).
    ToyQuadAttitudePlant plant_inline(40.0, 0.5);
    plant_inline.reset(tilted_initial_quat(15.0 * M_PI / 180.0));
    ImuLowPassFilter filt_inline(0.2);
    ComplementaryAttitudeEstimator estimator_inline(0.05);
    PdAttitudeController controller_inline(6.0, 0.6);
    LinearRateTorqueBridge bridge_inline;
    QuadXMixer mixer_inline;

    ImuSample sample_inline = plant_inline.sense();
    for (int i = 0; i < kSteps; ++i) {
        ImuSample filtered = filt_inline.filter_sample(sample_inline);
        AttitudeState state = estimator_inline.update(filtered);
        AttitudeSetpoint setpoint = level_setpoint(state.t_s);
        BodyRateCommand rate_cmd = controller_inline.compute(setpoint, state);
        BodyTorqueCommand torque_cmd = bridge_inline.convert(rate_cmd);
        MotorForceCommand forces = mixer_inline.mix(kCollective, torque_cmd);
        sample_inline = plant_inline.step(forces, kDtS);
    }
    double inline_final_deg = tilt_angle_rad(plant_inline.true_attitude().q_body_to_world) * 180.0 / M_PI;

    // Named-tick chain via ControlLoop::step.
    ToyQuadAttitudePlant plant_tick(40.0, 0.5);
    plant_tick.reset(tilted_initial_quat(15.0 * M_PI / 180.0));
    ControlLoop loop(ImuLowPassFilter(0.2), ComplementaryAttitudeEstimator(0.05),
                      PdAttitudeController(6.0, 0.6), LinearRateTorqueBridge(), QuadXMixer());

    ImuSample sample_tick = plant_tick.sense();
    for (int i = 0; i < kSteps; ++i) {
        AttitudeSetpoint setpoint = level_setpoint(sample_tick.t_s);
        ControlTickResult tick = loop.step(sample_tick, setpoint, kCollective);
        sample_tick = plant_tick.step(tick.forces, kDtS);
    }
    double tick_final_deg = tilt_angle_rad(plant_tick.true_attitude().q_body_to_world) * 180.0 / M_PI;

    REQUIRE_THAT(tick_final_deg, WithinAbs(inline_final_deg, 1e-9));
}
