// Fase C · C32 — `SpiBytePort`: a named MCU-shaped SPI byte port
// (`B1-fase-c-mcu-spi-hal-stub`).
//
// Host scaffold only — same idea as C28's `UartBytePort`. No SPI
// peripheral register access exists here at all — no `SPI1`, no
// `CR1`/`DR`, no CMSIS device pack, no chip-select (CS/NSS) GPIO, no
// IRQ, no DMA. This is a plain in-memory full-duplex loopback with a
// port-shaped interface, nothing more.
//
// MCU SPI stub != chip SPI != gyro live != flying.
//
// This desk's own FC gyro (when later wired) is an ICM42688P on SPI —
// named here only as the desk identity this port is shaped for, never
// as a register driver: no WHO_AM_I read, no register map, no sample
// anywhere in this file. The chip now has a "bytes go out / bytes come
// back" shape — `SpiBytePort` — with no bus, no CS pin, and no
// ICM42688P anywhere near it: this class never opens or drives
// anything. Today the only implementation is `LoopbackSpi`, an
// in-memory full-duplex loopback — `transfer(tx, rx, n)` copies up to
// `n` TX bytes into RX, in order (RX == TX), and never blocks. A
// transfer beyond the port's own capacity **refuses the extra bytes**
// (short count — the caller sees how many were actually moved), the
// same overflow policy `LoopbackUart` already uses.
#pragma once

#include <cstddef>
#include <cstdint>

namespace jarvis::fc {

// Abstract byte port. `transfer` never blocks and never throws for an
// over-capacity request — it returns how many bytes were actually
// moved.
class SpiBytePort {
public:
    virtual ~SpiBytePort() = default;

    // Copies up to `n` bytes from `tx` into `rx`, in order (full-duplex
    // loopback shape: RX == TX for this Buy's only implementation).
    // Returns the count actually moved — 0 if `n == 0`, short if the
    // port's own capacity is exhausted.
    virtual std::size_t transfer(const std::uint8_t* tx, std::uint8_t* rx, std::size_t n) = 0;
};

// In-memory full-duplex loopback — the only implementation this Buy
// ships. `max_bytes` (default 256) bounds a single transfer; a
// `transfer` requesting more than that accepts only what fits and
// returns that shorter count. Stateless between calls — there is no
// persistent queue, unlike `LoopbackUart`'s own FIFO, because a real
// SPI transfer is a single synchronous exchange, not an asynchronous
// stream.
class LoopbackSpi : public SpiBytePort {
public:
    explicit LoopbackSpi(std::size_t max_bytes = 256);

    std::size_t transfer(const std::uint8_t* tx, std::uint8_t* rx, std::size_t n) override;

    std::size_t capacity() const { return max_bytes_; }

private:
    std::size_t max_bytes_;
};

}  // namespace jarvis::fc
