// Fase C · C25 — `map_rc_to_loop_inputs`: RC channel units -> C24 tick
// args (`B1-fase-c-rc-setpoint`), C++ twin of the Python
// `flight_control/rc_setpoint.py`.
//
// Host scaffold only — no radio-link frame parsing exists anywhere in
// this tree (that stays a Python-only capability); this header only
// converts already-decoded integer channel values. `channels` is a
// plain `std::vector<int>` here — this tree has no decoded-channels
// type of its own and this Buy does not add one.
//
// RC->setpoint != flying != sticks drive motors != Safety allow != yaw
// lock.
//
// Channel map (illustrative, not a real TX model): `kRcChRoll`/
// `kRcChPitch`/`kRcChThrottle` = indices 0/1/2. The yaw channel
// (conventionally index 3 in AETR) is unused this Buy — there is no
// magnetometer anywhere in this tree, so there is no absolute heading
// reference a yaw stick could honestly command. `kRcChMin`/
// `kRcChMid`/`kRcChMax` = 172/992/1811, the same illustrative 11-bit
// stick-unit convention the Python twin uses. Throttle maps linearly onto
// `[0, 1]`, clipped; mid-stick (992) is therefore *not* exactly 0.5 (the
// endpoints are not perfectly symmetric around 992). Roll/pitch
// deflection is measured from 992, scaled so the maximum deflection
// reaches exactly `kRcMaxTiltRad` (pi/6, 30 degrees) at either endpoint,
// clipped beyond it, then composed into `q_body_to_world_desired` via
// the standard body 3-2-1 (yaw-pitch-roll) Euler-to-quaternion formula
// with yaw fixed at 0.
//
// `ControlLoop::step`'s own math (loop.hpp/loop.cpp) is untouched by
// this file — it only produces the two argument values `step` already
// accepts.
#pragma once

#include <vector>

#include "jarvis/fc/controller.hpp"

namespace jarvis::fc {

inline constexpr int kRcChRoll = 0;
inline constexpr int kRcChPitch = 1;
inline constexpr int kRcChThrottle = 2;

inline constexpr int kRcChMin = 172;
inline constexpr int kRcChMid = 992;
inline constexpr int kRcChMax = 1811;

inline constexpr double kRcMaxTiltRad = 3.14159265358979323846 / 6.0;

// The two arguments `ControlLoop::step` already accepts — nothing else.
struct RcLoopInputs {
    AttitudeSetpoint setpoint{};
    double collective = 0.0;
};

// `channels` must have at least 4 entries (AETR-shaped); only indices
// kRcChRoll/kRcChPitch/kRcChThrottle are read — the yaw channel is
// present-but-unused. Throws `std::invalid_argument` if `channels.size()
// < 4`. Does not parse any radio-link frame, does not read a clock, does
// not call `step`.
RcLoopInputs map_rc_to_loop_inputs(const std::vector<int>& channels, double t_s);

}  // namespace jarvis::fc
