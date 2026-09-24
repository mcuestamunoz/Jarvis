// Fase C · C32 — implementation of `jarvis::fc::LoopbackSpi`.
//
// Host scaffold only. See include/jarvis/fc/spi.hpp for the full
// honesty statement. No SPI registers, no CS/NSS GPIO, no IRQ/DMA, no
// radio-link protocol named anywhere in this file.
#include "jarvis/fc/spi.hpp"

#include <algorithm>
#include <stdexcept>

namespace jarvis::fc {

LoopbackSpi::LoopbackSpi(std::size_t max_bytes) : max_bytes_(max_bytes) {
    if (max_bytes_ == 0) {
        throw std::invalid_argument("max_bytes must be > 0");
    }
}

std::size_t LoopbackSpi::transfer(const std::uint8_t* tx, std::uint8_t* rx, std::size_t n) {
    std::size_t accepted = std::min(n, max_bytes_);
    for (std::size_t i = 0; i < accepted; ++i) {
        rx[i] = tx[i];
    }
    return accepted;
}

}  // namespace jarvis::fc
