// Fase C · C42 — implementation of `jarvis::fc::read_who_am_i`.
//
// Host scaffold only. See include/jarvis/fc/icm42688p.hpp for the full
// datasheet citation and honesty statement. No SPI1/CS GPIO, no
// register map beyond WHO_AM_I, no IMU sample, no `ControlLoop::step`
// reference anywhere in this file.
#include "jarvis/fc/icm42688p.hpp"

namespace jarvis::fc {

WhoAmIResult read_who_am_i(SpiBytePort& port) {
    std::uint8_t tx[2] = {
        static_cast<std::uint8_t>(kIcm42688pRegWhoAmI | kIcm42688pReadBit),
        0x00,
    };
    std::uint8_t rx[2] = {0, 0};
    std::size_t moved = port.transfer(tx, rx, 2);

    WhoAmIResult result;
    result.bytes_transferred = moved;
    if (moved < 2) {
        result.value = 0;
        result.matches_expected = false;
        return result;
    }
    result.value = rx[1];
    result.matches_expected = (result.value == kIcm42688pWhoAmIValue);
    return result;
}

}  // namespace jarvis::fc
