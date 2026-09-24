// Fase C · C28 — implementation of `jarvis::fc::LoopbackUart`.
//
// Host scaffold only. See `include/jarvis/fc/uart.hpp` for the full
// honesty statement. No USART registers, no CMSIS, no ioctl, no
// termios, no IRQ/DMA, no radio-link protocol named anywhere in this
// file, no GPIO, no Safety call.
#include "jarvis/fc/uart.hpp"

#include <algorithm>
#include <stdexcept>

namespace jarvis::fc {

LoopbackUart::LoopbackUart(std::size_t max_bytes) : max_bytes_(max_bytes) {
    if (max_bytes_ == 0) {
        throw std::invalid_argument("max_bytes must be > 0");
    }
}

std::size_t LoopbackUart::read(std::uint8_t* dst, std::size_t n) {
    std::size_t count = std::min(n, buffer_.size());
    for (std::size_t i = 0; i < count; ++i) {
        dst[i] = buffer_.front();
        buffer_.pop_front();
    }
    return count;
}

std::size_t LoopbackUart::write(const std::uint8_t* src, std::size_t n) {
    std::size_t available = max_bytes_ - buffer_.size();
    std::size_t accepted = std::min(n, available);
    for (std::size_t i = 0; i < accepted; ++i) {
        buffer_.push_back(src[i]);
    }
    return accepted;
}

}  // namespace jarvis::fc
