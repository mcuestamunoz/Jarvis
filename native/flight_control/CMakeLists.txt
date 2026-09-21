# Fase C · C13 — `native/flight_control/` host build
# (`B1-fase-c-cpp-flight-control-scaffold`).
#
# Host scaffold only. This tree is not MCU firmware, does not cross-compile
# to any board by default, and does not touch GPIO/PWM/DShot/serial. See
# README.md in this directory and the C13 implementation report for the
# full honesty statement.

cmake_minimum_required(VERSION 3.16)
project(jarvis_flight_control_native CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
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
)
target_include_directories(jarvis_fc PUBLIC include)
target_compile_options(jarvis_fc PRIVATE -Wall -Wextra)

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
)
target_link_libraries(fc_unit_tests PRIVATE jarvis_fc Catch2::Catch2WithMain)
target_compile_options(fc_unit_tests PRIVATE -Wall -Wextra)

include(Catch)
catch_discover_tests(fc_unit_tests)
