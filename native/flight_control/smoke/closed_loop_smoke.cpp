// Fase C · C13 — `fc_closed_loop_smoke`: the C++ scaffold's own tip smoke.
//
// Host-only executable. Wires the same vertical slice as the Python C11
// closed-loop tip (`run_controlled_flight_sim_smoke`, in
// `vehicle_profiles/smoke.py`): filter -> estimate -> PD -> rate-torque
// bridge -> mixer -> toy plant -> next IMU, looped. Pure host math and
// stdout — no GPIO, no PWM, no serial, no socket, no claim that any real
// vehicle flies. Exits 0 when the plant's own true tilt error has
// strictly decreased and recovered below the documented threshold; exits
// 1 otherwise.
#include <cmath>
#include <cstdio>
#include <cstdlib>

#include "jarvis/fc/attitude.hpp"
#include "jarvis/fc/controller.hpp"
#include "jarvis/fc/filter.hpp"
#include "jarvis/fc/mixer.hpp"
#include "jarvis/fc/plant.hpp"
#include "jarvis/fc/rate_torque.hpp"
#include "jarvis/fc/types.hpp"

using namespace jarvis::fc;

namespace {

Quat tilted_initial_quat(double tilt_rad) {
    double half = tilt_rad / 2.0;
    return Quat{std::cos(half), std::sin(half), 0.0, 0.0};
}

// Same defaults as Python's `run_controlled_flight_sim_smoke` (C11/C12).
constexpr int kSteps = 200;
constexpr double kDtS = 0.01;
constexpr double kInitialTiltDeg = 15.0;
constexpr double kAlpha = 0.2;
constexpr double kEstimatorGain = 0.05;
constexpr double kKp = 6.0;
constexpr double kKd = 0.6;
constexpr double kCollective = 0.5;
constexpr double kTorqueGain = 40.0;
constexpr double kAngularDamping = 0.5;

// Documented tip criterion (C13 IC T3): the smoke must recover below this
// threshold within kSteps steps, starting from kInitialTiltDeg. This is
// looser than the Python ladder's own ~0.252 degrees since bit-identical
// numerics are explicitly not required (IC §0 decision 7) — it is the
// same order of magnitude of recovery, ported to independent C++ math.
constexpr double kRecoveryThresholdDeg = 2.0;

}  // namespace

int main() {
    double initial_tilt_rad = kInitialTiltDeg * M_PI / 180.0;

    ToyQuadAttitudePlant plant(kTorqueGain, kAngularDamping);
    plant.reset(tilted_initial_quat(initial_tilt_rad));

    ImuLowPassFilter filt(kAlpha);
    ComplementaryAttitudeEstimator estimator(kEstimatorGain);
    PdAttitudeController controller(kKp, kKd);
    LinearRateTorqueBridge bridge;  // default gain=1.0, same no-op as Python
    QuadXMixer mixer;

    double initial_tilt_deg = tilt_angle_rad(plant.true_attitude().q_body_to_world) * 180.0 / M_PI;
    std::printf("fc_closed_loop_smoke: host scaffold, C++ tip smoke (not hardware, not flight)\n");
    std::printf("initial tilt error: %.3f deg\n", initial_tilt_deg);

    ImuSample sample = plant.sense();
    double final_tilt_deg = initial_tilt_deg;
    for (int i = 0; i < kSteps; ++i) {
        ImuSample filtered = filt.filter_sample(sample);
        AttitudeState state = estimator.update(filtered);
        AttitudeSetpoint setpoint = level_setpoint(state.t_s);
        BodyRateCommand rate_cmd = controller.compute(setpoint, state);
        BodyTorqueCommand torque_cmd = bridge.convert(rate_cmd);
        MotorForceCommand forces = mixer.mix(kCollective, torque_cmd);
        sample = plant.step(forces, kDtS);
        final_tilt_deg = tilt_angle_rad(plant.true_attitude().q_body_to_world) * 180.0 / M_PI;
    }

    std::printf("final tilt error:   %.3f deg (after %d steps)\n", final_tilt_deg, kSteps);

    bool decreased = final_tilt_deg < initial_tilt_deg;
    bool recovered = final_tilt_deg < kRecoveryThresholdDeg;

    if (decreased && recovered) {
        std::printf("PASS: tilt error strictly decreased and recovered below %.1f deg\n",
                    kRecoveryThresholdDeg);
        return 0;
    }
    std::printf("FAIL: decreased=%d recovered=%d (threshold %.1f deg)\n", decreased, recovered,
                kRecoveryThresholdDeg);
    return 1;
}
