// Fase C · C28 — Catch2 unit cases for `jarvis::fc::LoopbackUart`.
//
// Host-only test binary. No USART registers, no ioctl, no termios, no
// radio-link protocol named anywhere in this file, no GPIO/hardware.
#include <vector>

#include <catch2/catch_test_macros.hpp>

#include "jarvis/fc/uart.hpp"

using namespace jarvis::fc;

TEST_CASE("LoopbackUart is convertible to UartBytePort*", "[uart]") {
    LoopbackUart uart;
    UartBytePort* port = &uart;
    REQUIRE(port != nullptr);
}

TEST_CASE("LoopbackUart: write then read round-trips bytes in order", "[uart]") {
    LoopbackUart uart;
    std::vector<std::uint8_t> sent{0x01, 0x02, 0x03, 0xFF, 0x00};

    std::size_t written = uart.write(sent.data(), sent.size());
    REQUIRE(written == sent.size());
    REQUIRE(uart.size() == sent.size());

    std::vector<std::uint8_t> received(sent.size());
    std::size_t read_count = uart.read(received.data(), received.size());

    REQUIRE(read_count == sent.size());
    REQUIRE(received == sent);
    REQUIRE(uart.size() == 0);
}

TEST_CASE("LoopbackUart: read on empty returns 0", "[uart]") {
    LoopbackUart uart;
    std::uint8_t dst[8];
    REQUIRE(uart.read(dst, 8) == 0);
}

TEST_CASE("LoopbackUart: write past capacity returns a short count, no unbounded growth", "[uart]") {
    LoopbackUart uart(4);
    std::vector<std::uint8_t> first{0x11, 0x22, 0x33};
    std::vector<std::uint8_t> second{0xAA, 0xBB, 0xCC};

    std::size_t first_written = uart.write(first.data(), first.size());
    REQUIRE(first_written == 3);
    REQUIRE(uart.size() == 3);

    std::size_t second_written = uart.write(second.data(), second.size());
    REQUIRE(second_written == 1);  // only 1 byte of remaining capacity (4 - 3)
    REQUIRE(uart.size() == 4);
    REQUIRE(uart.size() == uart.capacity());

    std::vector<std::uint8_t> received(4);
    std::size_t read_count = uart.read(received.data(), received.size());
    REQUIRE(read_count == 4);
    std::vector<std::uint8_t> expected{0x11, 0x22, 0x33, 0xAA};
    REQUIRE(received == expected);
}

TEST_CASE("LoopbackUart: partial read leaves remaining bytes queued, in order", "[uart]") {
    LoopbackUart uart;
    std::vector<std::uint8_t> sent{0x10, 0x20, 0x30, 0x40};
    uart.write(sent.data(), sent.size());

    std::uint8_t first_two[2];
    REQUIRE(uart.read(first_two, 2) == 2);
    REQUIRE(first_two[0] == 0x10);
    REQUIRE(first_two[1] == 0x20);
    REQUIRE(uart.size() == 2);

    std::uint8_t rest[2];
    REQUIRE(uart.read(rest, 2) == 2);
    REQUIRE(rest[0] == 0x30);
    REQUIRE(rest[1] == 0x40);
    REQUIRE(uart.size() == 0);
}

TEST_CASE("LoopbackUart: rejects zero capacity", "[uart]") {
    REQUIRE_THROWS_AS(LoopbackUart(0), std::invalid_argument);
}
