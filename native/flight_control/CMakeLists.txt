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
)
target_include_directories(jarvis_fc PUBLIC include)
target_compile_options(jarvis_fc PRIVATE -Wall -Wextra)

add_executable(fc_closed_loop_smoke smoke/closed_loop_smoke.cpp)
target_link_libraries(fc_closed_loop_smoke PRIVATE jarvis_fc)

enable_testing()
add_test(NAME fc_closed_loop_smoke COMMAND fc_closed_loop_smoke)
