// Fase C · C34 (`B1-fase-c-spi-scripted-gyro-probe`) — `probe_rx`: the
// first **client** of `SpiBytePort`.
//
// C33 gave the port a way to lie with bytes (`ScriptedSpi`, canned RX).
// This Buy is the other half: a caller that asks the port for `n` bytes
// and copies back whatever RX the *current* implementation returns. On
// the desk today that implementation is `LoopbackSpi` (echo) or
// `ScriptedSpi` (canned) — the day a real SPI1 port exists, only the
// implementation behind the reference changes; this client does not.
//
// `probe_rx` sends a dummy TX of all-zero bytes — a full-duplex-shaped
// exchange, never a register address. This Buy does **not** encode any
// register address, does **not** read `WHO_AM_I`, and does **not** know
// about the ICM42688P as a driver: the desk's own future gyro is cited
// here only as *why* a byte-probe shape is useful, never as a register
// map. Tests are free to load a `ScriptedSpi` with a placeholder fixture
// byte to prove the RX path end-to-end, but that byte lives in tests
// only — this file never hardcodes an expected ID.
//
// Scripted gyro probe != gyro live != chip SPI != WHO_AM_I != flying.
#pragma once

#include <cstddef>
#include <cstdint>

#include "jarvis/fc/spi.hpp"

namespace jarvis::fc {

// Sends `n` dummy zero bytes as TX and copies back whatever `port`
// returns in RX. Returns the count `port.transfer(...)` actually moved
// (0 if `n == 0`, short if the port's own bound is exhausted). Dummy TX
// lives on the stack up to 256 bytes (same default cap as `LoopbackSpi`);
// a heap buffer is used only when `n` is larger, so a 1-byte probe does
// not allocate. Never blocks, never inspects or interprets the RX bytes
// — this is a plain pass-through client, not a decoder.
std::size_t probe_rx(SpiBytePort& port, std::uint8_t* rx, std::size_t n);

}  // namespace jarvis::fc
