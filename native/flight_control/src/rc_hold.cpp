// Fase C · C27 — implementation of `jarvis::fc::RcHoldWatch` /
// `failsafe_loop_inputs`.
//
// Host scaffold only. See `include/jarvis/fc/rc_hold.hpp` for the full
// honesty statement. Protocol-agnostic — no radio-link protocol named
// anywhere in this file, no wall-clock call, no plant, no GPIO, no
// Safety call.
#include "jarvis/fc/rc_hold.hpp"

#include <cmath>
#include <stdexcept>

namespace jarvis::fc {

RcHoldWatch::RcHoldWatch(double timeout_s) : timeout_s_(timeout_s) {
    if (!std::isfinite(timeout_s) || timeout_s <= 0.0) {
        throw std::invalid_argument("timeout_s must be finite and > 0");
    }
}

void RcHoldWatch::note_rc(double now_s) { last_s_ = now_s; }

RcHoldDecision RcHoldWatch::evaluate(double now_s) const {
    if (!last_s_.has_value()) {
        return RcHoldDecision{true, "never", std::nullopt};
    }
    if (now_s < *last_s_) {
        throw std::invalid_argument("now_s must not precede the last noted time");
    }
    double age_s = now_s - *last_s_;
    if (age_s <= timeout_s_) {
        return RcHoldDecision{false, "fresh", age_s};
    }
    return RcHoldDecision{true, "timeout", age_s};
}

bool RcHoldWatch::is_stale(double now_s) const { return evaluate(now_s).stale; }

RcLoopInputs failsafe_loop_inputs(double t_s) {
    RcLoopInputs result;
    result.setpoint = level_setpoint(t_s);
    result.collective = 0.0;
    return result;
}

}  // namespace jarvis::fc
