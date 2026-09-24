// Fase C · C14 — C++ port of `flight_control/esc.py` (C10 rung).
//
// Host scaffold only — production flight_control runtime is a future,
// further-hardened iteration of this same C++ tree. Consumes a C13
// `MotorForceCommand` (4x `[0,1]`) and produces an `EscPwmCommand` — 4 PWM
// pulse widths in microseconds, one documented linear map.
// `SimulatedEscSink::apply(...)` records that command **in memory only**.
//
// **Hard cut (matching Python C10 IC §0 decisions 5-7):**
// - no GPIO, no pigpio, no `/dev/mem`, no serial/USB opens, no sockets —
//   `SimulatedEscSink` only ever mutates its own in-memory state
// - no DShot/Oneshot/Multishot bit-banging as a shipped product encoding
//   (classic PWM-in-us is the only encoding in this Buy)
// - no claim that arming powers anything physical — `armed` is a plain
//   in-memory flag, nothing more
//
// **Encoding (locked):** `encode_motor_forces` maps each (clamped) motor
// force linearly onto `[min_us, max_us]`, default `1000`-`2000` us —
// `force=0 -> min_us`, `force=1 -> max_us`. `min_us`/`max_us` must be
// finite with `min_us < max_us`.
//
// **Arming behavior (locked):** `SimulatedEscSink` starts `armed=false`.
// `apply(cmd)` always records `cmd` as the sink's last command, but only
// reports `applied=true` when armed at the moment of the call — while
// disarmed, `applied=false` with `reason="disarmed"`. Neither branch ever
// claims a physical write happened: there is no actuator here.
//
// Fase C · C26 — `EscOutput`: naming the port (`B1-fase-c-esc-output-hal`).
// The mixer speaks forces only, still — `mixer.hpp`/`mixer.cpp` gain no
// PWM/DShot/pin knowledge here. `EscOutput` is an abstract base with a
// virtual destructor; `SimulatedEscSink` public-inherits it. Today the
// only implementation is `SimulatedEscSink` (in-memory only, unchanged
// from C14); a future pin driver would implement the same
// `apply_forces` virtual and encode inside its own override, never in
// the mixer. `EscOutput HAL != pin != motors != DShot`.
#pragma once

#include <array>
#include <optional>
#include <string>

#include "jarvis/fc/mixer.hpp"

namespace jarvis::fc {

using PulseWidths = std::array<double, 4>;

struct EscPwmCommand {
    double t_s = 0.0;
    PulseWidths pulse_us{1000.0, 1000.0, 1000.0, 1000.0};
    std::string protocol = "pwm_us";  // locked — the only encoding this Buy ships
};

struct EscApplyResult {
    bool applied = false;
    std::optional<std::string> reason;
    std::optional<PulseWidths> pulse_us;
};

// Linear map: `force=0 -> min_us`, `force=1 -> max_us`. Each force is
// defensively clamped to `[0, 1]` before mixing in.
EscPwmCommand encode_motor_forces(const MotorForceCommand& forces, double min_us = 1000.0,
                                   double max_us = 2000.0);

// The named ESC output port (C26). Same contract for today's in-memory
// `SimulatedEscSink` and any future pin driver — the mixer never sees
// this type, it only ever produces `MotorForceCommand`. `apply_forces`
// is where encoding into a wire-shaped command belongs.
class EscOutput {
public:
    virtual ~EscOutput() = default;

    // Encode `forces` however this port's device expects, then apply
    // it. Must never claim a physical write happened.
    virtual EscApplyResult apply_forces(const MotorForceCommand& forces) = 0;
    virtual void arm() = 0;     // flips an in-memory flag only — never claims physical power
    virtual void disarm() = 0;
    virtual bool armed() const = 0;
};

// In-memory only — never opens a pin, a port, or a socket. `armed`
// defaults to `false`; `apply(cmd)` always records `cmd` as the last
// command but only marks `applied=true` while armed. `apply_forces`
// (C26) is a thin wrapper: `encode_motor_forces(forces)` then
// `apply(cmd)` — the C10 `apply(EscPwmCommand)` path is unchanged.
class SimulatedEscSink : public EscOutput {
public:
    bool armed() const override { return armed_; }
    void arm() override { armed_ = true; }
    void disarm() override { armed_ = false; }

    EscApplyResult apply(const EscPwmCommand& cmd);
    EscApplyResult apply_forces(const MotorForceCommand& forces) override;
    std::optional<EscPwmCommand> last_command() const { return last_command_; }

private:
    bool armed_ = false;
    std::optional<EscPwmCommand> last_command_;
};

}  // namespace jarvis::fc
