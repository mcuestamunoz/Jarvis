// Fase C · C24 — `ControlLoop::step`: the named one-cycle control tick
// (`B1-fase-c-control-loop-tick`), C++ twin of the Python
// `flight_control/loop.py`.
//
// Host scaffold only — production flight_control runtime is a future,
// further-hardened iteration of this same C++ tree; a real MCU ISR calling
// this on a fixed schedule is a later, separate Buy. Wires the SAME rungs
// this tree already ships (filter.hpp -> attitude.hpp -> controller.hpp ->
// rate_torque.hpp -> mixer.hpp -> esc.hpp), in the same order the C13
// `fc_closed_loop_smoke` already ran inlined:
//
//   filter_sample -> estimator.update -> controller.compute ->
//   bridge.convert -> mixer.mix
//
// Named control tick != flying != MCU ISR != motors != RC sticks.
//
// `step` does not call `ToyQuadAttitudePlant::step`, does not read any
// real HAL, and does not write a pin — the caller supplies an `ImuSample`
// and consumes the returned `MotorForceCommand`/`EscPwmCommand` itself
// (`plant.step(result.forces, dt)` stays in the caller's own loop, as it
// did before this Buy). `dt` is not an argument here either — same "no
// timer" lock as the Python twin. No `SafetyGate`, no autonomy submit
// path, no GPIO/PWM/DShot/serial anywhere in this header or its .cpp.
#pragma once

#include <optional>

#include "jarvis/fc/attitude.hpp"
#include "jarvis/fc/controller.hpp"
#include "jarvis/fc/esc.hpp"
#include "jarvis/fc/filter.hpp"
#include "jarvis/fc/mixer.hpp"
#include "jarvis/fc/rate_torque.hpp"
#include "jarvis/fc/types.hpp"

namespace jarvis::fc {

// Everything one `step()` call produced, in pipeline order. `pwm` is
// PWM-microsecond numbers only (via `encode_motor_forces`, C10's own
// encoder) — nothing here is written to any actuator.
struct ControlTickResult {
    double t_s = 0.0;
    ImuSample filtered{};
    AttitudeState state{};
    BodyRateCommand rate_cmd{};
    BodyTorqueCommand torque_cmd{};
    MotorForceCommand forces{};
    EscPwmCommand pwm{};
};

// Holds one instance of each existing rung — default-constructed with
// that rung's own existing defaults unless the caller injects one, same
// as `fc_closed_loop_smoke`'s own construction before this Buy. `step()`
// runs them in the locked order; it never touches a plant, a real HAL, a
// pin, or Safety.
class ControlLoop {
public:
    explicit ControlLoop(ImuLowPassFilter filt = ImuLowPassFilter(),
                          ComplementaryAttitudeEstimator estimator = ComplementaryAttitudeEstimator(),
                          PdAttitudeController controller = PdAttitudeController(),
                          LinearRateTorqueBridge bridge = LinearRateTorqueBridge(),
                          QuadXMixer mixer = QuadXMixer());

    // `filter_sample -> estimator.update -> controller.compute ->
    // bridge.convert -> mixer.mix` — exactly the C11/C13 order, calling
    // each existing rung's own unmodified method. Does not call
    // `ToyQuadAttitudePlant::step`, does not read a HAL, does not write a
    // pin.
    ControlTickResult step(const ImuSample& sample, const AttitudeSetpoint& setpoint, double collective);

private:
    ImuLowPassFilter filt_;
    ComplementaryAttitudeEstimator estimator_;
    PdAttitudeController controller_;
    LinearRateTorqueBridge bridge_;
    QuadXMixer mixer_;
};

}  // namespace jarvis::fc
