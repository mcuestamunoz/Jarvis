# Fase C · C13 — `native/flight_control/` host build
# (`B1-fase-c-cpp-flight-control-scaffold`).
#
# Host scaffold only. This tree is not MCU firmware, does not cross-compile
# to any board by default, and does not touch GPIO/PWM/DShot/serial. See
# README.md in this directory and the C13 implementation report for the
# full honesty statement.

cmake_minimum_required(VERSION 3.16)
# C18 adds two .c sources (mcu/startup_cortex_m4.c, mcu/syscalls_stub.c)
# for the freestanding MCU .elf target — C must be enabled alongside CXX
# for CMake to compile them (host build never touches these files).
project(jarvis_flight_control_native C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

add_library(jarvis_fc STATIC
    src/filter.cpp
    src/attitude.cpp
    src/controller.cpp
    src/rate_torque.cpp
    src/mixer.cpp
    src/plant.cpp
    src/esc.cpp
    src/loop.cpp
    src/rc_setpoint.cpp
    src/rc_hold.cpp
    src/uart.cpp
    src/dshot.cpp
    src/spi.cpp
    src/spi_probe.cpp
    src/mag.cpp
)
target_include_directories(jarvis_fc PUBLIC include)
target_compile_options(jarvis_fc PRIVATE -Wall -Wextra)

# --- Fase C · C16 — MCU cross-compile gate (`B1-fase-c-cpp-mcu-cross-compile`) ---
#
# When configured with -DCMAKE_TOOLCHAIN_FILE=cmake/toolchains/arm-none-eabi.cmake
# (which sets JARVIS_FC_CROSS_COMPILING TRUE), this build produces ONLY the
# jarvis_fc static library for the arm-none-eabi target — no Catch2
# FetchContent (host-oriented, heavy, not needed for a library-only cross
# build), no smoke executables, no unit-test binary. The host default path
# (no toolchain file passed) is entirely unaffected and keeps building and
# registering everything below, unchanged in role from C13-C15.
if(NOT JARVIS_FC_CROSS_COMPILING)

add_executable(fc_closed_loop_smoke smoke/closed_loop_smoke.cpp)
target_link_libraries(fc_closed_loop_smoke PRIVATE jarvis_fc)

add_executable(fc_esc_pwm_smoke smoke/esc_pwm_smoke.cpp)
target_link_libraries(fc_esc_pwm_smoke PRIVATE jarvis_fc)

enable_testing()
add_test(NAME fc_closed_loop_smoke COMMAND fc_closed_loop_smoke)
add_test(NAME fc_esc_pwm_smoke COMMAND fc_esc_pwm_smoke)

# --- Fase C · C15 — real C++ unit-test harness (`B1-fase-c-cpp-unit-tests`) ---
#
# Framework: Catch2 v3, pinned to release tag v3.7.1 (commit
# fa43b77429ba76c462b1898d6cd2f2d7a9416b14), fetched via FetchContent.
# Network is needed ONCE at configure time to clone this pinned tag; once
# populated, the sources live under build/flight_control/_deps/catch2-src
# and subsequent configure/build/test cycles need no network (offline
# story documented in the C15 report and this tree's own README.md).
include(FetchContent)
FetchContent_Declare(
    Catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG        v3.7.1
)
FetchContent_MakeAvailable(Catch2)
list(APPEND CMAKE_MODULE_PATH "${catch2_SOURCE_DIR}/extras")

add_executable(fc_unit_tests
    tests/test_filter.cpp
    tests/test_attitude.cpp
    tests/test_controller.cpp
    tests/test_rate_torque.cpp
    tests/test_mixer.cpp
    tests/test_esc.cpp
    tests/test_loop.cpp
    tests/test_rc_setpoint.cpp
    tests/test_rc_hold.cpp
    tests/test_uart.cpp
    tests/test_dshot.cpp
    tests/test_spi.cpp
    tests/test_spi_probe.cpp
    tests/test_plant.cpp
    tests/test_mag.cpp
)
target_link_libraries(fc_unit_tests PRIVATE jarvis_fc Catch2::Catch2WithMain)
target_compile_options(fc_unit_tests PRIVATE -Wall -Wextra)

include(Catch)
catch_discover_tests(fc_unit_tests)

endif()  # NOT JARVIS_FC_CROSS_COMPILING

# --- Fase C · C18 — freestanding MCU .elf (`B1-fase-c-cpp-mcu-freestanding-elf`) ---
#
# Only built on the cross-compile path (JARVIS_FC_CROSS_COMPILING set by
# cmake/toolchains/arm-none-eabi.cmake — same toolchain C16 already uses,
# reused unchanged). Links OUR OWN generic startup + linker script +
# syscall stubs (mcu/) against jarvis_fc, producing one inspectable ARM
# ELF. No vendor BSP, no CMSIS — see mcu/*.{c,cpp,ld} and the C18/C30
# implementation reports for the full honesty statement. As of C30
# (`B1-fase-c-mcu-flash-observable`) this image CAN be flashed via USB
# DFU (see native/flight_control/README.md) and its idle loop toggles a
# cited status LED (mcu/hello_led.c) instead of spinning empty.
if(JARVIS_FC_CROSS_COMPILING)

add_executable(fc_mcu_stub.elf
    mcu/startup_cortex_m4.c
    mcu/syscalls_stub.c
    mcu/hello_led.c
    mcu/stub_main.cpp
)
target_link_libraries(fc_mcu_stub.elf PRIVATE jarvis_fc)
target_link_options(fc_mcu_stub.elf PRIVATE
    -T${CMAKE_CURRENT_SOURCE_DIR}/mcu/linker_cortex_m4.ld
    -nostartfiles
    -Wl,--gc-sections
    -Wl,-Map=fc_mcu_stub.map
)
target_compile_options(fc_mcu_stub.elf PRIVATE -Wall -Wextra)
set_target_properties(fc_mcu_stub.elf PROPERTIES
    SUFFIX ""
    OUTPUT_NAME "fc_mcu_stub.elf"
)

# --- Fase C · C30 (`B1-fase-c-mcu-flash-observable`) — close C29 N1 ---
#
# `-T<script>` is a linker FLAG, not a CMake source/dependency — CMake
# does not know to relink fc_mcu_stub.elf when linker_cortex_m4.ld
# itself changes unless told explicitly. This is that explicit dep: a
# stale rebuild after editing the .ld now correctly relinks (verified in
# this Buy's own report/tests by touching the .ld and rebuilding without
# deleting the prior .elf first).
set_property(TARGET fc_mcu_stub.elf APPEND PROPERTY
    LINK_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/mcu/linker_cortex_m4.ld
)

# POST_BUILD .bin for USB DFU (dfu-util expects a flat binary image, not
# an ELF). Load address stays 0x08000000 (C29's own cited FLASH origin —
# unchanged by this Buy). Optional: skipped with a status message (not a
# configure error) if arm-none-eabi-objcopy is not on PATH, since objcopy
# absence should not block a jarvis_fc-only or host build.
find_program(ARM_NONE_EABI_OBJCOPY arm-none-eabi-objcopy)
if(ARM_NONE_EABI_OBJCOPY)
    add_custom_command(TARGET fc_mcu_stub.elf POST_BUILD
        COMMAND ${ARM_NONE_EABI_OBJCOPY} -O binary
                $<TARGET_FILE:fc_mcu_stub.elf>
                ${CMAKE_CURRENT_BINARY_DIR}/fc_mcu_stub.bin
        COMMENT "C30: objcopy fc_mcu_stub.elf -> fc_mcu_stub.bin (DFU image, load addr 0x08000000)"
        VERBATIM
    )
else()
    message(STATUS "arm-none-eabi-objcopy not found — fc_mcu_stub.bin (DFU image) will not be produced")
endif()

endif()  # JARVIS_FC_CROSS_COMPILING
