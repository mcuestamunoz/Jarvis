// Fase C · C32/C33 — `LoopbackSpi` (echo) and `ScriptedSpi` (canned RX).
//
// Host scaffold only. See include/jarvis/fc/spi.hpp for the full
// honesty statement. No SPI registers, no CS/NSS GPIO, no IRQ/DMA, no
// radio-link protocol named anywhere in this file.
#include "jarvis/fc/spi.hpp"

#include <algorithm>
#include <stdexcept>
#include <utility>

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

ScriptedSpi::ScriptedSpi(std::vector<std::uint8_t> canned_rx) : canned_rx_(std::move(canned_rx)) {}

std::size_t ScriptedSpi::transfer(const std::uint8_t* /*tx*/, std::uint8_t* rx, std::size_t n) {
    std::size_t accepted = std::min(n, canned_rx_.size());
    for (std::size_t i = 0; i < accepted; ++i) {
        rx[i] = canned_rx_[i];
    }
    return accepted;
}

void ScriptedSpi::set_next_rx(std::vector<std::uint8_t> canned_rx) { canned_rx_ = std::move(canned_rx); }

}  // namespace jarvis::fc
