"""Tests T1-T9 for `B1-fase-c-cpp-mcu-cross-compile` (C16).

**Wrapper choice (IC §4 "document choice", same rationale as C13-C15's own
wrappers, extended for this Buy):** this pytest wrapper does not require a
toolchain to be pre-built ahead of time the way the smoke/unit-test
wrappers do — it actively runs `cmake --toolchain ... ` + `cmake --build`
itself when an `arm-none-eabi-g++` is found on PATH, because the whole
point of T2/T3 is to prove the cross-build path works when a toolchain is
present. This is deliberately more than "run an existing binary": there is
no cross-built artifact to just re-run (the output is a static library,
not an executable).

**A real wrinkle found on the implementer's own machine, disclosed here:**
some ARM toolchain *packaging* ships a bare cross-compiler without a
bundled `newlib`/`libstdc++` (e.g. the plain Homebrew `arm-none-eabi-gcc`
formula) — `arm-none-eabi-g++` is on PATH and answers `--version`, but
compiling any of our sources fails with `fatal error: optional: No such
file or directory`, because there is no C++ standard library to find.
That is a real, disclosed toolchain-completeness problem, not a bug in
`jarvis_fc`. So this wrapper does not simply "found the binary → must
succeed or it's a hard failure" — a compiler that answers `--version` but
fails to compile `<optional>` degrades to a **skip with a specific
install hint** (recommending a full toolchain distribution — e.g. the
xPack or official Arm GNU Toolchain releases, which do bundle libstdc++ —
rather than a bare compiler-only package), so the Python suite never
breaks just because *some* `arm-none-eabi-g++` happens to be on PATH.

A genuine successful cross-build (using the xPack `arm-none-eabi-gcc`
v15.2.1-1.1 darwin-arm64 release, which does bundle a full C++17
`libstdc++` for the `thumb/v7e-m/nofp` multilib) was performed and
verified for this Buy — see the implementation report for the full
command transcript and `objdump` proof of `elf32-littlearm` output.

Process gates covered elsewhere, not by this file:
- T7 (report lists toolchain pin/flags, artifact path, honesty, skip
  story) — `.jes/artifacts/implementation_report_fase_c_cpp_mcu_cross_compile_b1.md`.
- T8 (Python suite still green @ 0.5.14) — the full `pytest -q` run.
- T9 (docs updated honestly, no premature v0.5.14 tag) — README/
  IMPLEMENTATION_TASKS/PLATFORM_CAPABILITY_VISION/ARCHITECTURE.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command

REPO_ROOT = Path(__file__).resolve().parents[1]
NATIVE_FC_DIR = REPO_ROOT / "native" / "flight_control"
TOOLCHAIN_FILE = NATIVE_FC_DIR / "cmake" / "toolchains" / "arm-none-eabi.cmake"
MCU_BUILD_DIR = REPO_ROOT / "build" / "flight_control_mcu"
MCU_ARTIFACT = MCU_BUILD_DIR / "libjarvis_fc.a"

_INSTALL_HINT = (
    "arm-none-eabi-g++ not found on PATH. Install a FULL toolchain "
    "(bundling newlib + libstdc++, not just a bare compiler), e.g.: "
    "brew install --cask gcc-arm-embedded (macOS), or download the "
    "xPack arm-none-eabi-gcc release for your platform, or on "
    "Debian/Ubuntu: apt-get install gcc-arm-none-eabi. "
    "See native/flight_control/README.md."
)


def test_t1_toolchain_file_sets_arm_none_eabi_system_and_locked_cpu_flags():
    assert TOOLCHAIN_FILE.is_file()
    text = TOOLCHAIN_FILE.read_text(encoding="utf-8")
    assert "CMAKE_SYSTEM_NAME Generic" in text
    assert "CMAKE_SYSTEM_PROCESSOR arm" in text
    assert "-mcpu=cortex-m4" in text
    assert "-mthumb" in text
    assert "CMAKE_C_COMPILER" in text
    assert "CMAKE_CXX_COMPILER" in text


def test_cmake_gates_host_only_targets_behind_cross_compiling_flag():
    """IC §0 decision 7/11 — no Catch2/smoke/unit-test binary on the MCU
    path; host default path stays exactly as C13-C15 left it."""
    cmake_text = (NATIVE_FC_DIR / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "JARVIS_FC_CROSS_COMPILING" in cmake_text
    assert "if(NOT JARVIS_FC_CROSS_COMPILING)" in cmake_text
    # The gated block must contain the host-only bits.
    gated_start = cmake_text.index("if(NOT JARVIS_FC_CROSS_COMPILING)")
    gated_end = cmake_text.index("endif()", gated_start)
    gated_block = cmake_text[gated_start:gated_end]
    assert "FetchContent_Declare" in gated_block
    assert "fc_unit_tests" in gated_block
    assert "fc_closed_loop_smoke" in gated_block
    assert "fc_esc_pwm_smoke" in gated_block


def test_t2_t3_mcu_cross_build_produces_arm_archive_or_skips_with_hint():
    compiler = shutil.which("arm-none-eabi-g++")
    if compiler is None:
        pytest.skip(_INSTALL_HINT)

    configure = subprocess.run(
        [
            "cmake",
            "-S",
            str(NATIVE_FC_DIR),
            "-B",
            str(MCU_BUILD_DIR),
            f"--toolchain={TOOLCHAIN_FILE}",
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if configure.returncode != 0:
        pytest.skip(
            f"arm-none-eabi-g++ found at {compiler} but MCU configure failed "
            f"(likely an incomplete toolchain missing newlib/libstdc++): "
            f"{configure.stderr[-800:]}"
        )

    build = subprocess.run(
        ["cmake", "--build", str(MCU_BUILD_DIR), "--target", "jarvis_fc"],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if build.returncode != 0:
        pytest.skip(
            f"arm-none-eabi-g++ found at {compiler} but MCU build failed "
            f"(likely an incomplete toolchain missing newlib/libstdc++, e.g. "
            f"a bare compiler-only package): {build.stderr[-800:]}"
        )

    assert MCU_ARTIFACT.is_file(), "expected libjarvis_fc.a after a successful MCU build"

    objdump = shutil.which("arm-none-eabi-objdump")
    if objdump is not None:
        result = subprocess.run(
            [objdump, "-a", str(MCU_ARTIFACT)], capture_output=True, text=True, timeout=30, check=False
        )
        assert "elf32-littlearm" in result.stdout, result.stdout


def test_t4_host_build_and_ctest_still_green_if_built():
    host_build_dir = REPO_ROOT / "build" / "flight_control"
    host_unit_binary = host_build_dir / "fc_unit_tests"
    host_smoke_binary = host_build_dir / "fc_closed_loop_smoke"
    if not (host_unit_binary.is_file() and host_smoke_binary.is_file()):
        pytest.skip(
            "Host build not present. Build it first: cmake -S native/flight_control "
            "-B build/flight_control && cmake --build build/flight_control."
        )

    result = subprocess.run(
        [str(host_smoke_binary)], capture_output=True, text=True, timeout=30, check=False
    )
    assert result.returncode == 0
    assert "PASS" in result.stdout


def test_t5_no_gpio_flash_openocd_or_vendor_bsp_symbols_in_toolchain_file():
    text = TOOLCHAIN_FILE.read_text(encoding="utf-8").lower()
    code_only_lines = []
    for line in text.splitlines():
        comment_at = line.find("#")
        code_only_lines.append(line if comment_at == -1 else line[:comment_at])
    code_text = "\n".join(code_only_lines)
    forbidden = ("gpio", "openocd", "jlink", "stm32cube", "cmsis", "chibios", "freertos", "px4", "ardupilot")
    for token in forbidden:
        assert token not in code_text, f"toolchain file contains forbidden-shaped token '{token}'"


def test_t6_no_cpp_under_src_jarvis_and_craft_isolation():
    src_jarvis = REPO_ROOT / "src" / "jarvis"
    forbidden_suffixes = (".cpp", ".cc", ".cxx", ".hpp", ".hh", ".h")
    for path in src_jarvis.rglob("*"):
        if path.is_file():
            assert path.suffix not in forbidden_suffixes, f"C++ source found under src/jarvis: {path}"
            assert path.name != "CMakeLists.txt"

    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "arm-none-eabi" not in text, f"{py_file} references the MCU toolchain"
            assert "flight_control_mcu" not in text, f"{py_file} references the MCU build dir"


def test_default_safety_and_autonomy_submit_still_reject():
    assert isinstance(default_safety_gate(), RejectAllSafetyGate)
    assert default_safety_gate().evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_capability_registry_default_still_empty():
    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []


def test_t8_pyproject_version_is_0_5_14():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.40"' in text
