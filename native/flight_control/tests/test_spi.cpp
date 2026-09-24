// Fase C · C32 — Catch2 unit cases for `jarvis::fc::LoopbackSpi`.
//
// Host-only test binary. No SPI/hardware here, no radio-link protocol
// named anywhere in this file.
#include <vector>

#include <catch2/catch_test_macros.hpp>

#include "jarvis/fc/spi.hpp"

using namespace jarvis::fc;

TEST_CASE("LoopbackSpi is convertible to SpiBytePort*", "[spi]") {
    LoopbackSpi spi;
    SpiBytePort* port = &spi;
    REQUIRE(port != nullptr);
}

TEST_CASE("LoopbackSpi: transfer round-trips TX to RX in order", "[spi]") {
    LoopbackSpi spi;
    std::vector<std::uint8_t> tx{0x01, 0x02, 0x03, 0xFF, 0x00};
    std::vector<std::uint8_t> rx(tx.size(), 0xAA);

    std::size_t moved = spi.transfer(tx.data(), rx.data(), tx.size());

    REQUIRE(moved == tx.size());
    REQUIRE(rx == tx);
}

TEST_CASE("LoopbackSpi: n=0 returns 0", "[spi]") {
    LoopbackSpi spi;
    std::uint8_t tx[1] = {0x42};
    std::uint8_t rx[1] = {0x00};
    REQUIRE(spi.transfer(tx, rx, 0) == 0);
}

TEST_CASE("LoopbackSpi: transfer past capacity returns a short count, no unbounded growth", "[spi]") {
    LoopbackSpi spi(4);
    std::vector<std::uint8_t> tx{0x11, 0x22, 0x33, 0x44, 0x55, 0x66};
    std::vector<std::uint8_t> rx(tx.size(), 0xAA);

    std::size_t moved = spi.transfer(tx.data(), rx.data(), tx.size());

    REQUIRE(moved == 4);
    REQUIRE(rx[0] == 0x11);
    REQUIRE(rx[1] == 0x22);
    REQUIRE(rx[2] == 0x33);
    REQUIRE(rx[3] == 0x44);
    REQUIRE(rx[4] == 0xAA);  // untouched — beyond the accepted count
    REQUIRE(rx[5] == 0xAA);
}

TEST_CASE("LoopbackSpi: rejects zero capacity", "[spi]") {
    REQUIRE_THROWS_AS(LoopbackSpi(0), std::invalid_argument);
}
