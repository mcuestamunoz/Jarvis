// Fase C · C42 (`B1-fase-c-icm-register-client`) — a datasheet-cited
// ICM42688P WHO_AM_I register client on `SpiBytePort`.
//
// Host scaffold only. Talks to the same `SpiBytePort` interface C32-C34
// already ship (tests use `ScriptedSpi`/`LoopbackSpi`) — no chip SPI1,
// no CS/NSS GPIO, no full register map, no IMU sample, no wiring into
// `ControlLoop::step`. The placeholder probe (`probe_rx`, C34) is
// untouched and still exists — this is a second, named client sitting
// beside it, not a replacement.
//
// **Datasheet citation:** TDK InvenSense ICM-42688-P Datasheet
// (document DS-000347) — Register Bank 0, `WHO_AM_I` register at
// address `0x75`, expected value `0x47`. This session verified the
// address/value pair via web search cross-referenced against the
// open-source PX4-Autopilot flight-controller driver's own register
// header (`InvenSense_ICM42688P_registers.hpp`: `WHOAMI = 0x47`,
// `BANK_0::WHO_AM_I = 0x75`), which itself implements this same
// datasheet's register map — every direct fetch of the datasheet PDF
// in this session was blocked (HTTP 403 on every mirror tried), so
// this citation is corroborated by an independent, unrelated
// open-source driver rather than read directly off the PDF's own page/
// table number, and that limitation is disclosed here rather than
// papered over with an invented section number. Note (IC §0 decision
// 4): C34's own placeholder fixture byte (`0x47`) happens to equal this
// real WHO_AM_I value — a disclosed coincidence, not evidence; C34's
// own files never cited it and still do not (`spi_probe.hpp`/`.cpp`
// contain no `0x47` literal, unchanged by this Buy).
//
// **Transaction shape (IC §0 decision 5):** a single-register SPI read
// is the standard InvenSense-family 2-byte full-duplex exchange: `TX[0]
// = register address with the read bit set (0x80 | reg)`, `TX[1]` = a
// dummy byte to clock out the response; `RX[1]` holds the register's
// value (`RX[0]` is the slave's response to the still-incomplete
// address byte and is not meaningful — this is why `LoopbackSpi`, which
// echoes TX, can never accidentally produce a WHO_AM_I match unless the
// dummy byte itself happened to equal `0x47`). This client sends
// exactly those 2 bytes through `SpiBytePort::transfer` — no bypass, no
// second transfer, no CS toggle (there is no CS pin in this port
// abstraction at all).
//
// **Second register:** deliberately NOT implemented this Buy. The IC
// allows one optional extra cited register, but this session could not
// independently corroborate a second register's address/reset value
// with the same two-source confidence as `WHO_AM_I` above within this
// Buy's own scope — shipping one well-verified register beats shipping
// two, one of which is weakly sourced. Disclosed in the report, not a
// silent omission.
//
// ICM register client on ScriptedSpi != chip SPI1. WHO_AM_I in RAM !=
// gyro live != samples in step. Datasheet cite != lab measurement on
// copper.
#pragma once

#include <cstddef>
#include <cstdint>

#include "jarvis/fc/spi.hpp"

namespace jarvis::fc {

inline constexpr std::uint8_t kIcm42688pRegWhoAmI = 0x75;
inline constexpr std::uint8_t kIcm42688pWhoAmIValue = 0x47;
inline constexpr std::uint8_t kIcm42688pReadBit = 0x80;

struct WhoAmIResult {
    std::uint8_t value = 0;
    bool matches_expected = false;
    std::size_t bytes_transferred = 0;
};

// Sends the cited 2-byte WHO_AM_I read transaction through `port` via
// `SpiBytePort::transfer` and reports the byte received. `matches_expected`
// is `true` iff exactly 2 bytes moved AND the second byte equals
// `kIcm42688pWhoAmIValue` — a short transfer (`bytes_transferred < 2`,
// e.g. an exhausted `ScriptedSpi` fixture) is always a documented
// mismatch, never silently treated as a match. Never a claim about any
// real chip: `port` alone determines what byte comes back.
WhoAmIResult read_who_am_i(SpiBytePort& port);

}  // namespace jarvis::fc
