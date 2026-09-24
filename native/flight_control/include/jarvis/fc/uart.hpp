// Fase C · C28 — `UartBytePort`: a named MCU-shaped UART byte port
// (`B1-fase-c-mcu-uart-hal-stub`).
//
// Host scaffold only — protocol-agnostic on purpose: this file names no
// radio-link protocol anywhere, even in comments (same lock this tree
// has held since C25/C27). No USART register access exists here at
// all — no `BRR`, no CMSIS device pack, no pin alternate-function mux,
// no IRQ handler, no DMA. This is a plain in-memory byte queue with a
// port-shaped interface, nothing more.
//
// MCU UART stub != chip USART != host baud config != a live radio link.
//
// The chip now has a "bytes in / bytes out" shape — `UartBytePort` — the
// same idea a Mac host serial module already gave the desktop side of
// this tree, but with no ioctl, no termios, and no operating-system
// device path anywhere near it: this class never opens anything. Today
// the only implementation is `LoopbackUart`, an in-memory FIFO — write
// enqueues, read dequeues, in order. Writing past capacity **refuses the
// extra bytes** (short write — the caller sees how many were actually
// accepted); this class never grows without bound and never blocks.
#pragma once

#include <cstddef>
#include <cstdint>
#include <deque>

namespace jarvis::fc {

// Abstract byte port. `read`/`write` never block and never throw for a
// full/empty port — they return how many bytes were actually moved.
class UartBytePort {
public:
    virtual ~UartBytePort() = default;

    // Dequeues up to `n` bytes into `dst`. Returns the count actually
    // read (0 if the port is empty).
    virtual std::size_t read(std::uint8_t* dst, std::size_t n) = 0;

    // Enqueues up to `n` bytes from `src`. Returns the count actually
    // accepted — fewer than `n` when the port would otherwise exceed its
    // capacity (extra bytes are refused, not silently dropped from the
    // middle of the stream and not overwriting anything already queued).
    virtual std::size_t write(const std::uint8_t* src, std::size_t n) = 0;
};

// In-memory FIFO loopback — the only implementation this Buy ships.
// `max_bytes` (default 256) bounds the queue; a `write` beyond remaining
// capacity accepts only what fits and returns that shorter count.
class LoopbackUart : public UartBytePort {
public:
    explicit LoopbackUart(std::size_t max_bytes = 256);

    std::size_t read(std::uint8_t* dst, std::size_t n) override;
    std::size_t write(const std::uint8_t* src, std::size_t n) override;

    std::size_t size() const { return buffer_.size(); }
    std::size_t capacity() const { return max_bytes_; }

private:
    std::size_t max_bytes_;
    std::deque<std::uint8_t> buffer_;
};

}  // namespace jarvis::fc
