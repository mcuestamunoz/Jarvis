// Fase C · C34 — implementation of `jarvis::fc::probe_rx`.
//
// Host scaffold only. See include/jarvis/fc/spi_probe.hpp for the full
// honesty statement. No SPI registers, no register address, no
// WHO_AM_I read, no ICM42688P driver, no radio-link protocol named
// anywhere in this file.
#include "jarvis/fc/spi_probe.hpp"

#include <vector>

namespace jarvis::fc {

namespace {

constexpr std::size_t kDummyTxStack = 256;  // LoopbackSpi default cap

}  // namespace

std::size_t probe_rx(SpiBytePort& port, std::uint8_t* rx, std::size_t n) {
    if (n == 0) {
        return port.transfer(nullptr, rx, 0);
    }
    if (n <= kDummyTxStack) {
        std::uint8_t dummy_tx[kDummyTxStack] = {};
        return port.transfer(dummy_tx, rx, n);
    }
    std::vector<std::uint8_t> dummy_tx(n, 0);
    return port.transfer(dummy_tx.data(), rx, n);
}

}  // namespace jarvis::fc
