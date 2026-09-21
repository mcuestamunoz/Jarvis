# `native/flight_control/` — Fase C C++ scaffold (C13)

**What this is:** a **host-only** C++17 port of the Python
`flight_software/flight_control/` wooden ladder (filter → attitude
estimator → PD controller → rate→torque bridge → mixer → toy plant),
built with CMake. It runs the same closed-loop tip criterion as Python's
C11/C12 smoke: a toy quadrotor plant is seeded tilted, and the loop must
recover.

**What this is not:** MCU firmware, a board bring-up, anything that
touches GPIO/PWM/DShot/serial/sockets, PX4/ArduPilot, or a claim that any
real vehicle flies. See `.jes/artifacts/implementation_report_fase_c_cpp_flight_control_scaffold_b1.md`
for the full honesty statement.

## Build (host, desktop)

Requires CMake ≥ 3.16 and a C++17 compiler (tested with Apple Clang 21 /
`clang++`; any recent `g++` should also work).

```bash
cmake -S native/flight_control -B build/flight_control
cmake --build build/flight_control
```

## Run the tip smoke

```bash
./build/flight_control/fc_closed_loop_smoke
```

Prints the initial and final true tilt error (degrees) and exits `0` on
recovery, nonzero on failure. Also runnable via CTest:

```bash
cd build/flight_control && ctest --output-on-failure
```

## Layout

```text
native/flight_control/
  CMakeLists.txt
  include/jarvis/fc/    # public headers — types, filter, attitude,
                         # controller, rate_torque, mixer, plant,
                         # quat_math (shared helper, see its own header
                         # comment for the documented deviation from
                         # Python's per-module-private-helper style)
  src/                   # implementations
  smoke/closed_loop_smoke.cpp   # the tip harness (this Buy's own main())
```

`esc`/PWM encoding is not ported in this Buy (disclosed simplification —
the tip smoke never needs real PWM I/O; see the C13 IC §1 note "ESC/PWM
encode may be included or stubbed").
