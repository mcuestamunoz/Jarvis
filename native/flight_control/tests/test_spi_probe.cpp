// Fase C · C34 — Catch2 unit cases for `jarvis::fc::probe_rx`.
//
// Host-only test binary. No SPI/hardware here, no radio-link protocol
// named anywhere in this file. `0x47` below is a placeholder fixture
// byte loaded into a `ScriptedSpi` test double — not a WHO_AM_I claim,
// not a register address.
#include <vector>

#include <catch2/catch_test_macros.hpp>

#include "jarvis/fc/spi.hpp"
#include "jarvis/fc/spi_probe.hpp"

using namespace jarvis::fc;

TEST_CASE("probe_rx takes a SpiBytePort& (compiles against the abstract port)", "[spi_probe][c34]") {
    LoopbackSpi loopback;
    SpiBytePort& port = loopback;
    std::uint8_t rx[1] = {0xAA};
    REQUIRE(probe_rx(port, rx, 1) == 1);
}

TEST_CASE("probe_rx on ScriptedSpi returns the canned fixture byte", "[spi_probe][c34]") {
    ScriptedSpi spi(std::vector<std::uint8_t>{0x47});
    std::uint8_t rx[1] = {0x00};

    std::size_t moved = probe_rx(spi, rx, 1);

    REQUIRE(moved == 1);
    REQUIRE(rx[0] == 0x47);
}

TEST_CASE("probe_rx on LoopbackSpi returns zeros (dummy TX is all-zero, not a hidden script)", "[spi_probe][c34]") {
    LoopbackSpi loopback;
    std::vector<std::uint8_t> rx(4, 0xAA);

    std::size_t moved = probe_rx(loopback, rx.data(), rx.size());

    REQUIRE(moved == rx.size());
    for (std::uint8_t byte : rx) {
        REQUIRE(byte == 0x00);
    }
}

TEST_CASE("probe_rx: script shorter than n gives a short count, tail of RX untouched", "[spi_probe][c34]") {
    ScriptedSpi spi(std::vector<std::uint8_t>{0x47});
    std::vector<std::uint8_t> rx(3, 0xAA);

    std::size_t moved = probe_rx(spi, rx.data(), rx.size());

    REQUIRE(moved == 1);
    REQUIRE(rx[0] == 0x47);
    REQUIRE(rx[1] == 0xAA);  // untouched
    REQUIRE(rx[2] == 0xAA);
}

TEST_CASE("probe_rx: n=0 returns 0", "[spi_probe][c34]") {
    ScriptedSpi spi(std::vector<std::uint8_t>{0x47});
    std::uint8_t rx[1] = {0xAA};

    REQUIRE(probe_rx(spi, rx, 0) == 0);
    REQUIRE(rx[0] == 0xAA);  // untouched
}

TEST_CASE("probe_rx: n past the 256-byte stack dummy still fills RX", "[spi_probe][c34]") {
    std::vector<std::uint8_t> script(257, 0x11);
    ScriptedSpi spi(script);
    std::vector<std::uint8_t> rx(257, 0xAA);

    REQUIRE(probe_rx(spi, rx.data(), rx.size()) == 257);
    REQUIRE(rx[0] == 0x11);
    REQUIRE(rx[256] == 0x11);
}
