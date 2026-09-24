// Fase C · C27 — `RcHoldWatch`: an age-only stale/failsafe watch,
// C++ twin of a Python capability module under `capabilities/` that
// names the radio link protocol this stays deliberately agnostic to
// (see this Buy's own IC/report in `.jes/artifacts/` for that name).
//
// Host scaffold only — protocol-agnostic on purpose: this file names no
// radio-link protocol anywhere, even in comments (same lock C25's
// `rc_setpoint.hpp` already held for `native/`). No byte parsing exists
// here at all; the caller already has a channel vector or equivalent
// before this class is ever involved.
//
// Timeout failsafe != motors cut != live link != Safety allow.
//
// `note_rc(now_s)` records that a valid RC-channels sample was available
// at that time — pure bookkeeping, nothing else. `evaluate(now_s)`/
// `is_stale(now_s)` compare `now_s` against that record and `timeout_s`:
// stale if never noted (`reason="never"`) or `now_s - last_s >
// timeout_s` (`reason="timeout"`); otherwise fresh (`reason="fresh"`).
// `age_s <= timeout_s` is fresh — equality at the boundary is fresh, not
// stale. A `now_s` earlier than the last noted time throws
// `std::invalid_argument`; this class never accepts the clock running
// backwards silently. Every method takes `now_s` as a caller-supplied
// argument — no wall-clock call anywhere in this file.
//
// `failsafe_loop_inputs(t_s)` returns `level_setpoint(t_s)` (C8) plus
// `collective = 0.0` — a plain `RcLoopInputs` (C25's own type, reused
// unchanged). It never calls `ControlLoop::step`, `EscOutput`, or any
// Safety gate.
#pragma once

#include <optional>
#include <string>

#include "jarvis/fc/controller.hpp"
#include "jarvis/fc/rc_setpoint.hpp"

namespace jarvis::fc {

inline constexpr double kRcHoldTimeoutS = 0.5;

struct RcHoldDecision {
    bool stale = true;
    std::string reason = "never";  // "fresh" | "never" | "timeout"
    std::optional<double> age_s;
};

class RcHoldWatch {
public:
    explicit RcHoldWatch(double timeout_s = kRcHoldTimeoutS);

    // Records that a valid RC-channels sample was available at now_s —
    // pure bookkeeping, no parsing.
    void note_rc(double now_s);

    bool is_stale(double now_s) const;
    RcHoldDecision evaluate(double now_s) const;

    double timeout_s() const { return timeout_s_; }

private:
    double timeout_s_;
    std::optional<double> last_s_;
};

// Stale/failsafe decision: level attitude + zero collective. Never calls
// ControlLoop::step, EscOutput, or any Safety gate.
RcLoopInputs failsafe_loop_inputs(double t_s);

}  // namespace jarvis::fc
