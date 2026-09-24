// Fase C · C31 — DShot 16-bit frame encode stub
// (`B1-fase-c-dshot-encode-stub`), C++ twin of the Python
// `flight_control/dshot.py`.
//
// Host scaffold only. Same move C10/C14 made for PWM-us, applied to
// DShot: `encode_dshot_frame` computes the 16-bit packet DShot's own
// protocol defines, in RAM, on the host. No GPIO, no TIM, no DMA, no
// bit-bang, no ESC register access, no claim any ESC has seen this
// frame. DShot150/300/600 may appear in comments as the desk ESC's own
// advertised protocol names — never as a claimed timer period or GPIO
// toggle rate; no such timing exists anywhere in this file.
//
// DShot encode != pin != motors != flying.
//
// Frame layout (locked):
//   bits 15-5 (11 bits) throttle/command value
//   bit  4    (1 bit)   telemetry request
//   bits 3-0  (4 bits)  checksum (nibble XOR of the 12-bit value+telem)
//   value    = (throttle << 1) | telemetry
//   checksum = (value ^ (value >> 4) ^ (value >> 8)) & 0xF
//   frame    = (value << 4) | checksum
//
// `throttle` must be in [0, 2047] inclusive; out-of-range throws
// std::invalid_argument. Known vectors: throttle=0 -> 0x0000;
// throttle=48 -> 0x0606; throttle=2047 -> 0xFFEE (all telemetry=false).
//
// Special range: DShot's own protocol reserves 0..47 as commands and
// 48..2047 as throttle. This file encodes whatever 11-bit value it is
// given — it does not implement a command table.
//
// `EscOutput`/`SimulatedEscSink` (C26) still default to PWM-us — this
// file never touches either; a future pin driver would encode DShot
// inside its own override, not here and not by editing esc.hpp/.cpp.
#pragma once

#include <array>
#include <cstdint>

#include "jarvis/fc/mixer.hpp"

namespace jarvis::fc {

inline constexpr int kDshotMinCommandValue = 0;
inline constexpr int kDshotMaxCommandValue = 47;
inline constexpr int kDshotMinThrottleValue = 48;
inline constexpr int kDshotMaxThrottleValue = 2047;

// Throws std::invalid_argument if throttle is outside [0, 2047].
uint16_t encode_dshot_frame(int throttle, bool telemetry = false);

// Linearly maps each clamped motor force [0, 1] onto DShot throttle
// [48, 2047] (never 0..47 — DShot's own command range) and encodes each
// with encode_dshot_frame. A separate, parallel path from C10/C14's own
// encode_motor_forces (PWM-us), which stays completely unchanged.
std::array<uint16_t, 4> encode_motor_forces_dshot(const MotorForceCommand& forces);

}  // namespace jarvis::fc
