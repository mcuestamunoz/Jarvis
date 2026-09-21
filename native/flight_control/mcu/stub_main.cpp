// Fase C · C18 — MCU entry stub (`B1-fase-c-cpp-mcu-freestanding-elf`).
//
// HONESTY: this `main()` links against real `jarvis_fc` symbols (the
// SAME behavior-frozen filter/mixer/esc code the host build and the C16
// static-library cross-build use) to prove the whole chain — startup,
// linker script, syscall stubs, C++ runtime — actually links into one
// coherent freestanding ELF. It does not read any sensor, does not touch
// GPIO/PWM/DShot, does not loop "flying" anything: after exercising two
// pure-computation rung APIs once, it idles forever. This file is never
// flashed to a board.
#include "jarvis/fc/esc.hpp"
#include "jarvis/fc/filter.hpp"

using namespace jarvis::fc;

// Volatile so the compiler cannot optimize the whole call chain away —
// this is meant to prove real jarvis_fc code links and would execute if
// this image were ever run, not to be dead-code-eliminated into nothing.
volatile double g_last_filtered_accel_x = 0.0;
volatile double g_last_pulse_us_0 = 0.0;

int main() {
    ImuLowPassFilter filt(0.2);
    ImuSample raw{0.0, Vec3{1.0, 2.0, 3.0}, Vec3{0.0, 0.0, 0.0}};
    ImuSample filtered = filt.filter_sample(raw);
    g_last_filtered_accel_x = filtered.accel_mps2[0];

    MotorForceCommand forces{0.0, MotorForces{0.5, 0.5, 0.5, 0.5}};
    EscPwmCommand pwm = encode_motor_forces(forces);
    g_last_pulse_us_0 = pwm.pulse_us[0];

    while (true) {
        // Freestanding idle — no actuator, no peripheral, nothing to do
        // once past the one-shot jarvis_fc exercise above.
    }
}
