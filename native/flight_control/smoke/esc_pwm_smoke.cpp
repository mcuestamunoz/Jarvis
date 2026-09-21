// Fase C · C14 — `fc_esc_pwm_smoke`: C++ steel-ladder parity for the C10
// ESC/PWM encoding stub.
//
// Host-only executable, kept separate from `fc_closed_loop_smoke` (IC §0
// "Defaults locked" — closed-loop tip smoke stays focused; this Buy's
// smoke targets the encode+arm behavior on its own). Pure host math and
// stdout — no GPIO, no PWM hardware write, no serial, no socket, no claim
// that any motor spins or that an ESC is online. Exits 0 when every
// assertion below holds; exits 1 on the first failure.
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <string>

#include "jarvis/fc/esc.hpp"
#include "jarvis/fc/mixer.hpp"

using namespace jarvis::fc;

namespace {

int failures = 0;
int total_checks = 0;

void check(bool condition, const char* label) {
    ++total_checks;
    if (condition) {
        std::printf("  ok   %s\n", label);
    } else {
        std::printf("  FAIL %s\n", label);
        ++failures;
    }
}

bool approx(double a, double b, double tol = 1e-9) { return std::fabs(a - b) <= tol; }

MotorForceCommand forces_of(double f0, double f1, double f2, double f3) {
    return MotorForceCommand{0.0, MotorForces{f0, f1, f2, f3}};
}

}  // namespace

int main() {
    std::printf("fc_esc_pwm_smoke: host scaffold, C++ ESC/PWM stub parity (not hardware)\n");

    // T1 — force 0 -> 1000us; force 1 -> 2000us; mid linear.
    {
        EscPwmCommand zero = encode_motor_forces(forces_of(0.0, 0.0, 0.0, 0.0));
        check(approx(zero.pulse_us[0], 1000.0), "T1 force=0 -> 1000us");

        EscPwmCommand one = encode_motor_forces(forces_of(1.0, 1.0, 1.0, 1.0));
        check(approx(one.pulse_us[0], 2000.0), "T1 force=1 -> 2000us");

        EscPwmCommand half = encode_motor_forces(forces_of(0.5, 0.0, 1.0, 0.25));
        check(approx(half.pulse_us[0], 1500.0), "T1 force=0.5 -> 1500us (linear midpoint)");
        check(approx(half.pulse_us[3], 1250.0), "T1 force=0.25 -> 1250us (linear)");
    }

    // T2 — exactly 4 pulses; protocol pwm_us.
    {
        EscPwmCommand cmd = encode_motor_forces(forces_of(0.1, 0.2, 0.3, 0.4));
        check(cmd.pulse_us.size() == 4, "T2 exactly 4 pulse widths");
        check(cmd.protocol == "pwm_us", "T2 protocol locked to pwm_us");
    }

    // T3 — invalid min/max rejected.
    {
        bool threw_on_equal = false;
        try {
            encode_motor_forces(forces_of(0.0, 0.0, 0.0, 0.0), 1500.0, 1500.0);
        } catch (const std::invalid_argument&) {
            threw_on_equal = true;
        }
        check(threw_on_equal, "T3 min_us == max_us rejected");

        bool threw_on_inverted = false;
        try {
            encode_motor_forces(forces_of(0.0, 0.0, 0.0, 0.0), 2000.0, 1000.0);
        } catch (const std::invalid_argument&) {
            threw_on_inverted = true;
        }
        check(threw_on_inverted, "T3 min_us > max_us rejected");

        bool threw_on_nan = false;
        try {
            encode_motor_forces(forces_of(0.0, 0.0, 0.0, 0.0), std::nan(""), 2000.0);
        } catch (const std::invalid_argument&) {
            threw_on_nan = true;
        }
        check(threw_on_nan, "T3 non-finite min_us rejected");
    }

    // T4 — disarmed apply -> applied=false, reason disarmed, command still recorded.
    {
        SimulatedEscSink sink;
        check(!sink.armed(), "T4 sink starts disarmed");
        EscPwmCommand cmd = encode_motor_forces(forces_of(0.5, 0.5, 0.5, 0.5));
        EscApplyResult result = sink.apply(cmd);
        check(!result.applied, "T4 disarmed apply -> applied=false");
        check(result.reason.has_value() && *result.reason == "disarmed", "T4 reason=disarmed");
        check(sink.last_command().has_value(), "T4 command recorded even while disarmed");
    }

    // T5 — armed apply -> applied=true, last command stored.
    {
        SimulatedEscSink sink;
        sink.arm();
        check(sink.armed(), "T5 sink armed");
        EscPwmCommand cmd = encode_motor_forces(forces_of(0.9, 0.1, 0.9, 0.1));
        EscApplyResult result = sink.apply(cmd);
        check(result.applied, "T5 armed apply -> applied=true");
        check(!result.reason.has_value(), "T5 no reason when applied");
        check(sink.last_command().has_value() && approx(sink.last_command()->pulse_us[0], cmd.pulse_us[0]),
              "T5 last command stored matches applied command");

        sink.disarm();
        EscApplyResult after_disarm = sink.apply(cmd);
        check(!after_disarm.applied, "T5b disarm() flips back to refuse");
    }

    if (failures == 0) {
        std::printf("PASS: all ESC/PWM stub assertions held (%d checks)\n", total_checks);
        return 0;
    }
    std::printf("FAIL: %d assertion(s) failed\n", failures);
    return 1;
}
