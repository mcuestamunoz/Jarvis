// Fase C · C24 — implementation of `jarvis::fc::ControlLoop::step`.
//
// Host scaffold only. See `include/jarvis/fc/loop.hpp` for the full
// honesty statement. No plant, no HAL, no GPIO/PWM/DShot/serial, no
// Safety call anywhere in this file.
#include "jarvis/fc/loop.hpp"

#include <utility>

namespace jarvis::fc {

ControlLoop::ControlLoop(ImuLowPassFilter filt, ComplementaryAttitudeEstimator estimator,
                          PdAttitudeController controller, LinearRateTorqueBridge bridge,
                          QuadXMixer mixer)
    : filt_(std::move(filt)),
      estimator_(std::move(estimator)),
      controller_(std::move(controller)),
      bridge_(std::move(bridge)),
      mixer_(std::move(mixer)) {}

ControlTickResult ControlLoop::step(const ImuSample& sample, const AttitudeSetpoint& setpoint,
                                     double collective) {
    ImuSample filtered = filt_.filter_sample(sample);
    AttitudeState state = estimator_.update(filtered);
    BodyRateCommand rate_cmd = controller_.compute(setpoint, state);
    BodyTorqueCommand torque_cmd = bridge_.convert(rate_cmd);
    MotorForceCommand forces = mixer_.mix(collective, torque_cmd);
    EscPwmCommand pwm = encode_motor_forces(forces);

    ControlTickResult result;
    result.t_s = forces.t_s;
    result.filtered = filtered;
    result.state = state;
    result.rate_cmd = rate_cmd;
    result.torque_cmd = torque_cmd;
    result.forces = forces;
    result.pwm = pwm;
    return result;
}

}  // namespace jarvis::fc
