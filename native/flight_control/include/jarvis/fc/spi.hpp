// Fase C · C32/C33 — `SpiBytePort`: a named MCU-shaped SPI byte port.
// C32: `LoopbackSpi` (RX = TX). C33: `ScriptedSpi` (RX from a canned
// script, not from TX).
//
// Host scaffold only — same idea as C28's `UartBytePort`. No SPI
// peripheral register access exists here at all — no `SPI1`, no
// `CR1`/`DR`, no CMSIS device pack, no chip-select (CS/NSS) GPIO, no
// IRQ, no DMA.
//
// MCU SPI stub != chip SPI != gyro live != flying.
// Scripted SPI != gyro live != chip SPI != flying.
//
// This desk's own FC gyro (when later wired) is an ICM42688P on SPI —
// named here only as the desk identity this port is shaped for, never
// as a register driver: no WHO_AM_I read, no register map, no sample
// anywhere in this file. The shape is "bytes go out / bytes come back"
// — `SpiBytePort` — with no bus, no CS pin, and no ICM42688P driver.
// Two in-memory implementations: `LoopbackSpi` echoes TX; `ScriptedSpi`
// fills RX from a pre-loaded script. A transfer beyond that
// implementation's own bound **refuses the extra bytes** (short count).
#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

namespace jarvis::fc {

// Abstract byte port. `transfer` never blocks and never throws for an
// over-capacity request — it returns how many bytes were actually
// moved.
class SpiBytePort {
public:
    virtual ~SpiBytePort() = default;

    // Full-duplex-shaped exchange of up to `n` bytes. What lands in
    // `rx` is implementation-defined: `LoopbackSpi` copies `tx` (RX ==
    // TX); `ScriptedSpi` copies a canned script and does not read `tx`.
    // Returns the count actually moved — 0 if `n == 0`, short if that
    // implementation's own bound is exhausted. Never blocks.
    virtual std::size_t transfer(const std::uint8_t* tx, std::uint8_t* rx, std::size_t n) = 0;
};

// In-memory full-duplex loopback (C32). `max_bytes` (default 256)
// bounds a single transfer; a `transfer` requesting more than that
// accepts only what fits and returns that shorter count. Stateless
// between calls — there is no persistent queue, unlike
// `LoopbackUart`'s own FIFO, because a real SPI transfer is a single
// synchronous exchange, not an asynchronous stream.
class LoopbackSpi : public SpiBytePort {
public:
    explicit LoopbackSpi(std::size_t max_bytes = 256);

    std::size_t transfer(const std::uint8_t* tx, std::uint8_t* rx, std::size_t n) override;

    std::size_t capacity() const { return max_bytes_; }

private:
    std::size_t max_bytes_;
};

// Fase C · C33 (`B1-fase-c-spi-scripted-slave`) — a second `SpiBytePort`
// implementation: a **canned-RX** slave. `LoopbackSpi` only ever echoes
// what you send it; a real device answers with *its own* bytes,
// independent of TX. `ScriptedSpi` fills RX from a pre-loaded byte
// script instead of from TX — this is how a test pretends "a device
// answered" without any chip. TX is never inspected or required to
// match anything.
//
// Not an ICM42688P driver, not a WHO_AM_I product API, not IMU samples
// into `step`, not a chip SPI bus — a future gyro-shaped test could
// load, say, `0x47` (a placeholder byte, not a claim about any real
// register) into the script, but no such register map exists anywhere
// in this file.
//
// Each `transfer(...)` call fills RX from the **start** of the
// currently-loaded script (not a consuming stream across calls) — call
// `set_next_rx(...)` to change what subsequent transfers return. If the
// script is shorter than the requested `n`, the transfer returns that
// shorter count (same "refuse extra" shape `LoopbackSpi` already uses)
// and the untouched tail of `rx` is left exactly as the caller passed
// it in.
class ScriptedSpi : public SpiBytePort {
public:
    explicit ScriptedSpi(std::vector<std::uint8_t> canned_rx = {});

    std::size_t transfer(const std::uint8_t* tx, std::uint8_t* rx, std::size_t n) override;

    // Replaces the canned bytes returned by subsequent transfer() calls.
    void set_next_rx(std::vector<std::uint8_t> canned_rx);

private:
    std::vector<std::uint8_t> canned_rx_;
};

}  // namespace jarvis::fc
