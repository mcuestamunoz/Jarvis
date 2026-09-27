// Fase C · C42 (`B1-fase-c-icm-register-client`) — Catch2 unit cases
// for `jarvis::fc::read_who_am_i`.
//
// Host-only test binary. No SPI1/CS GPIO/register map beyond WHO_AM_I,
// no IMU sample, no `ControlLoop::step` reference anywhere in this
// file.
#include <algorithm>
#include <cstdint>
#include <vector>

#include <catch2/catch_test_macros.hpp>

#include "jarvis/fc/icm42688p.hpp"
#include "jarvis/fc/spi.hpp"

using namespace jarvis::fc;

namespace {

// A recording fake `SpiBytePort` — captures the exact TX bytes a
// client sent, so tests can verify the transaction shape (IC T3)
// without inspecting any private state on the real port
// implementations.
class RecordingSpi : public SpiBytePort {
public:
    explicit RecordingSpi(std::vector<std::uint8_t> canned_rx) : canned_rx_(std::move(canned_rx)) {}

    std::size_t transfer(const std::uint8_t* tx, std::uint8_t* rx, std::size_t n) override {
        last_tx_.assign(tx, tx + n);
        std::size_t moved = std::min(n, canned_rx_.size());
        for (std::size_t i = 0; i < moved; ++i) {
            rx[i] = canned_rx_[i];
        }
        return moved;
    }

    std::vector<std::uint8_t> last_tx_;

private:
    std::vector<std::uint8_t> canned_rx_;
};

}  // namespace

TEST_CASE("read_who_am_i: T1 ScriptedSpi with the cited value -> matches", "[icm42688p][c42]") {
    ScriptedSpi spi(std::vector<std::uint8_t>{0x00, kIcm42688pWhoAmIValue});

    WhoAmIResult result = read_who_am_i(spi);

    REQUIRE(result.bytes_transferred == 2);
    REQUIRE(result.value == kIcm42688pWhoAmIValue);
    REQUIRE(result.matches_expected);
}

TEST_CASE("read_who_am_i: T2 ScriptedSpi with a wrong byte -> documented mismatch, not silent success", "[icm42688p][c42]") {
    ScriptedSpi spi(std::vector<std::uint8_t>{0x00, 0x99});

    WhoAmIResult result = read_who_am_i(spi);

    REQUIRE(result.bytes_transferred == 2);
    REQUIRE(result.value == 0x99);
    REQUIRE_FALSE(result.matches_expected);
}

TEST_CASE("read_who_am_i: T3 sends exactly the cited 2-byte transaction via SpiBytePort::transfer", "[icm42688p][c42]") {
    RecordingSpi spi(std::vector<std::uint8_t>{0x00, kIcm42688pWhoAmIValue});

    WhoAmIResult result = read_who_am_i(spi);

    REQUIRE(spi.last_tx_.size() == 2);
    REQUIRE(spi.last_tx_[0] == static_cast<std::uint8_t>(kIcm42688pRegWhoAmI | kIcm42688pReadBit));
    REQUIRE(spi.last_tx_[1] == 0x00);
    REQUIRE(result.matches_expected);
}

TEST_CASE("read_who_am_i: LoopbackSpi path does not falsely claim a WHO_AM_I match", "[icm42688p][c42]") {
    LoopbackSpi loopback;

    WhoAmIResult result = read_who_am_i(loopback);

    // LoopbackSpi echoes TX -> RX; RX[1] equals the dummy TX byte (0x00),
    // which is not the cited WHO_AM_I value (0x47).
    REQUIRE(result.bytes_transferred == 2);
    REQUIRE(result.value == 0x00);
    REQUIRE_FALSE(result.matches_expected);
}

TEST_CASE("read_who_am_i: a short transfer (exhausted ScriptedSpi script) is a documented mismatch", "[icm42688p][c42]") {
    ScriptedSpi spi(std::vector<std::uint8_t>{0x00});  // only 1 byte, request is 2

    WhoAmIResult result = read_who_am_i(spi);

    REQUIRE(result.bytes_transferred == 1);
    REQUIRE_FALSE(result.matches_expected);
}

TEST_CASE("read_who_am_i: cited constants are the documented values", "[icm42688p][c42]") {
    REQUIRE(kIcm42688pRegWhoAmI == 0x75);
    REQUIRE(kIcm42688pWhoAmIValue == 0x47);
    REQUIRE(kIcm42688pReadBit == 0x80);
}
