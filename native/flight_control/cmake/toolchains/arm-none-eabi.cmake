# Fase C · C16 — `arm-none-eabi` cross-compile toolchain
# (`B1-fase-c-cpp-mcu-cross-compile`), reused unchanged (same CPU/ABI
# flags — C18 IC §0 decision 4 locks "do not invent a second CPU class")
# by C18 (`B1-fase-c-cpp-mcu-freestanding-elf`) to also link a freestanding
# .elf — see `native/flight_control/mcu/` and this tree's CMakeLists.txt.
#
# HONESTY (read before using this file):
# This toolchain makes CMake cross-compile/cross-link for a bare-metal ARM
# Cortex-M4-class target. It does NOT flash any board, does NOT pull in a
# vendor SDK (no STM32Cube, no CMSIS device pack, no ChibiOS/FreeRTOS/
# PX4/ArduPilot), and does NOT touch GPIO/PWM/DShot in any way. Two
# artifacts can result: `libjarvis_fc.a` (C16 — the steel-ladder sources
# archived for this instruction set) and, as of C18, a linked, inspectable
# freestanding `.elf` built from OUR OWN generic linker script + startup +
# syscall stubs under `mcu/` (no vendor BSP there either). Both are
# compile/link-time proofs, not a hardware proof: no MCU has run this
# code, and this file makes no claim that either artifact would run
# correctly on, or was ever flashed to, any specific flight controller
# board.
#
# CPU (locked, C16 IC §0 decision 4): generic Cortex-M4, `-mcpu=cortex-m4
# -mthumb`. This is a common class used by many flight controllers, but
# naming the class is not a claim about any specific board's silicon,
# clock tree, or memory map — none of that is modeled here.
#
# Install hint (Homebrew, used to build this Buy's own report):
#   brew install arm-none-eabi-gcc
# Debian/Ubuntu equivalent: apt-get install gcc-arm-none-eabi

set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)

# Freestanding target: CMake must not try to link/run a test executable
# during compiler detection (there is no OS, no entry point, no libc
# startup provided here).
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

find_program(ARM_NONE_EABI_GCC arm-none-eabi-gcc)
find_program(ARM_NONE_EABI_GXX arm-none-eabi-g++)
if(NOT ARM_NONE_EABI_GCC OR NOT ARM_NONE_EABI_GXX)
    message(FATAL_ERROR
        "arm-none-eabi-gcc/g++ not found on PATH. Install it first, e.g.:\n"
        "  brew install arm-none-eabi-gcc          (macOS/Homebrew)\n"
        "  apt-get install gcc-arm-none-eabi        (Debian/Ubuntu)\n"
        "This toolchain file cross-compiles jarvis_fc only — it does not "
        "flash any board and requires no vendor SDK.")
endif()

set(CMAKE_C_COMPILER "${ARM_NONE_EABI_GCC}")
set(CMAKE_CXX_COMPILER "${ARM_NONE_EABI_GXX}")
set(CMAKE_ASM_COMPILER "${ARM_NONE_EABI_GCC}")

# Locked CPU flags (C16 IC §0 decision 4) — generic Cortex-M4, thumb mode,
# soft float ABI (no -mfpu assumed, so this stays valid across Cortex-M4
# parts with or without a hardware FPU — no specific board's silicon is
# claimed by this choice).
set(JARVIS_FC_MCU_FLAGS "-mcpu=cortex-m4 -mthumb -mfloat-abi=soft")
set(CMAKE_C_FLAGS_INIT "${JARVIS_FC_MCU_FLAGS}")
set(CMAKE_CXX_FLAGS_INIT "${JARVIS_FC_MCU_FLAGS}")

# Deliberately NOT forcing -ffreestanding/-fno-exceptions/-fno-rtti:
# - For the C16 `.a` target: `ar` archives object files without resolving
#   symbols, so unlinked C++ runtime references (e.g. the
#   `throw std::invalid_argument(...)` calls already present in the
#   behavior-frozen rung sources) do not need to be satisfied at that
#   stage regardless of this choice.
# - For the C18 `.elf` target (linked, not just archived): this is now a
#   real choice, made deliberately (C18 IC §0 decision 8, option (a)) —
#   keep the rung sources' exceptions enabled and link normally against
#   the toolchain's own libstdc++/newlib, resolving the runtime via OUR
#   OWN minimal syscall stubs (`mcu/syscalls_stub.c`) instead of disabling
#   exceptions or rewriting any rung API "while we're here."

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

# Marker this Buy's own CMakeLists.txt checks to gate host-only targets
# (Catch2 FetchContent, the unit-test binary, both smoke executables) off
# the cross build (C16 IC §0 decision 7 — no Catch2 on MCU this Buy).
set(JARVIS_FC_CROSS_COMPILING TRUE)
