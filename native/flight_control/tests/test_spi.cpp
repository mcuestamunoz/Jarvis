// Fase C · C32/C33 — Catch2 unit cases for `jarvis::fc::LoopbackSpi` /
// `jarvis::fc::ScriptedSpi`.
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

// Fase C · C33 — ScriptedSpi cases.

TEST_CASE("ScriptedSpi is convertible to SpiBytePort*", "[spi][c33]") {
    ScriptedSpi spi;
    SpiBytePort* port = &spi;
    REQUIRE(port != nullptr);
}

TEST_CASE("ScriptedSpi: transfer fills RX from the script, not from TX echo", "[spi][c33]") {
    ScriptedSpi spi(std::vector<std::uint8_t>{0x09, 0x08});
    std::vector<std::uint8_t> tx{0x01, 0x02};
    std::vector<std::uint8_t> rx(tx.size(), 0xAA);

    std::size_t moved = spi.transfer(tx.data(), rx.data(), tx.size());

    REQUIRE(moved == 2);
    REQUIRE(rx[0] == 0x09);
    REQUIRE(rx[1] == 0x08);
    REQUIRE(rx != tx);  // proves RX did not echo TX
}

TEST_CASE("ScriptedSpi: script shorter than n gives a short count, tail of RX untouched", "[spi][c33]") {
    ScriptedSpi spi(std::vector<std::uint8_t>{0x47});
    std::vector<std::uint8_t> tx{0x00, 0x00, 0x00};
    std::vector<std::uint8_t> rx(tx.size(), 0xAA);

    std::size_t moved = spi.transfer(tx.data(), rx.data(), tx.size());

    REQUIRE(moved == 1);
    REQUIRE(rx[0] == 0x47);
    REQUIRE(rx[1] == 0xAA);  // untouched
    REQUIRE(rx[2] == 0xAA);
}

TEST_CASE("ScriptedSpi: set_next_rx replaces the script for subsequent transfers", "[spi][c33]") {
    ScriptedSpi spi(std::vector<std::uint8_t>{0x11});
    std::uint8_t tx[1] = {0x00};
    std::uint8_t rx[1] = {0x00};

    REQUIRE(spi.transfer(tx, rx, 1) == 1);
    REQUIRE(rx[0] == 0x11);
    rx[0] = 0x00;
    REQUIRE(spi.transfer(tx, rx, 1) == 1);
    REQUIRE(rx[0] == 0x11);  // same script again — not a consuming stream

    spi.set_next_rx(std::vector<std::uint8_t>{0x22});
    REQUIRE(spi.transfer(tx, rx, 1) == 1);
    REQUIRE(rx[0] == 0x22);
}

TEST_CASE("ScriptedSpi: an empty script returns 0 regardless of n", "[spi][c33]") {
    ScriptedSpi spi;  // default-constructed, empty script
    std::uint8_t tx[2] = {0x01, 0x02};
    std::uint8_t rx[2] = {0xAA, 0xAA};
    REQUIRE(spi.transfer(tx, rx, 2) == 0);
    REQUIRE(rx[0] == 0xAA);
    REQUIRE(rx[1] == 0xAA);
}

TEST_CASE("LoopbackSpi: still RX=TX after ScriptedSpi exists (regression)", "[spi][c33]") {
    LoopbackSpi loopback;
    std::vector<std::uint8_t> tx{0x05, 0x06, 0x07};
    std::vector<std::uint8_t> rx(tx.size(), 0x00);
    std::size_t moved = loopback.transfer(tx.data(), rx.data(), tx.size());
    REQUIRE(moved == tx.size());
    REQUIRE(rx == tx);
}
