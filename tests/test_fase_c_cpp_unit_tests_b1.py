"""Tests T1-T10 for `B1-fase-c-cpp-unit-tests` (C15).

**Wrapper choice (IC §4, same rationale as C13/C14's own wrappers):** this
pytest wrapper does not invoke `cmake`/`clang++`/`ctest` itself — it runs
the already-built `fc_unit_tests`, `fc_closed_loop_smoke`, and
`fc_esc_pwm_smoke` binaries if present, asserting exit 0 and (for the
unit-test binary) parsing Catch2's own "All tests passed" summary line.
If a binary is absent, the relevant test **skips with a reason** naming
the exact build command. Building a native toolchain + fetching Catch2
should not be a hard dependency of every `pytest` run.

Process gates covered elsewhere, not by this file:
- T8 (Python suite still green @ 0.5.13) — the full `pytest -q` run.
- T9 (report: framework pin, case inventory, honesty statement) —
  `.jes/artifacts/implementation_report_fase_c_cpp_unit_tests_b1.md`.
- T10 (docs updated honestly, no premature v0.5.13 tag) — README/
  IMPLEMENTATION_TASKS/PLATFORM_CAPABILITY_VISION/ARCHITECTURE.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command

REPO_ROOT = Path(__file__).resolve().parents[1]
NATIVE_FC_DIR = REPO_ROOT / "native" / "flight_control"
TESTS_DIR = NATIVE_FC_DIR / "tests"
BUILD_DIR = REPO_ROOT / "build" / "flight_control"
UNIT_TEST_BINARY = BUILD_DIR / "fc_unit_tests"
CLOSED_LOOP_SMOKE_BINARY = BUILD_DIR / "fc_closed_loop_smoke"
ESC_SMOKE_BINARY = BUILD_DIR / "fc_esc_pwm_smoke"

_BUILD_HINT = (
    "cmake -S native/flight_control -B build/flight_control && "
    "cmake --build build/flight_control (see native/flight_control/README.md). "
    "First configure needs network once to fetch pinned Catch2 v3.7.1."
)

_EXPECTED_RUNG_TEST_FILES = (
    "test_filter.cpp",
    "test_attitude.cpp",
    "test_controller.cpp",
    "test_rate_torque.cpp",
    "test_mixer.cpp",
    "test_esc.cpp",
)


def test_t1_cmake_wires_pinned_catch2_and_unit_test_target():
    cmake_text = (NATIVE_FC_DIR / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "FetchContent_Declare" in cmake_text
    assert "Catch2" in cmake_text
    assert "GIT_TAG        v3.7.1" in cmake_text or "GIT_TAG v3.7.1" in cmake_text
    assert "add_executable(fc_unit_tests" in cmake_text
    assert "catch_discover_tests(fc_unit_tests)" in cmake_text


def test_t2_per_rung_unit_test_sources_exist():
    for filename in _EXPECTED_RUNG_TEST_FILES:
        path = TESTS_DIR / filename
        assert path.is_file(), filename
        text = path.read_text(encoding="utf-8")
        assert "TEST_CASE(" in text, f"{filename} has no TEST_CASE"


def test_smoke_binaries_still_registered_in_cmake():
    """IC §0 decision 7 — smokes must remain, not be deleted."""
    cmake_text = (NATIVE_FC_DIR / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "add_executable(fc_closed_loop_smoke" in cmake_text
    assert "add_executable(fc_esc_pwm_smoke" in cmake_text
    assert 'add_test(NAME fc_closed_loop_smoke COMMAND fc_closed_loop_smoke)' in cmake_text
    assert 'add_test(NAME fc_esc_pwm_smoke COMMAND fc_esc_pwm_smoke)' in cmake_text
    assert (NATIVE_FC_DIR / "smoke" / "closed_loop_smoke.cpp").is_file()
    assert (NATIVE_FC_DIR / "smoke" / "esc_pwm_smoke.cpp").is_file()


def test_t3_unit_test_binary_all_cases_pass_if_built():
    if not UNIT_TEST_BINARY.is_file():
        pytest.skip(f"C++ unit-test binary not built. Build it first: {_BUILD_HINT}")

    result = subprocess.run(
        [str(UNIT_TEST_BINARY)], capture_output=True, text=True, timeout=60, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "All tests passed" in result.stdout, result.stdout

    match = re.search(r"All tests passed \((\d+) assertions? in (\d+) test cases?\)", result.stdout)
    assert match is not None, result.stdout
    assertions, cases = int(match.group(1)), int(match.group(2))
    assert cases >= 6, "expected at least one case per rung (filter/attitude/controller/rate_torque/mixer/esc)"
    assert assertions > 0


def test_t4_closed_loop_smoke_still_recovers_if_built():
    if not CLOSED_LOOP_SMOKE_BINARY.is_file():
        pytest.skip(f"C++ closed-loop smoke binary not built. Build it first: {_BUILD_HINT}")

    result = subprocess.run(
        [str(CLOSED_LOOP_SMOKE_BINARY)], capture_output=True, text=True, timeout=30, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout

    initial_match = re.search(r"initial tilt error:\s*([\d.]+)\s*deg", result.stdout)
    final_match = re.search(r"final tilt error:\s*([\d.]+)\s*deg", result.stdout)
    assert initial_match is not None and final_match is not None
    assert float(final_match.group(1)) < float(initial_match.group(1))
    assert float(final_match.group(1)) < 2.0


def test_esc_smoke_still_passes_if_built():
    if not ESC_SMOKE_BINARY.is_file():
        pytest.skip(f"C++ ESC smoke binary not built. Build it first: {_BUILD_HINT}")

    result = subprocess.run(
        [str(ESC_SMOKE_BINARY)], capture_output=True, text=True, timeout=30, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout
    assert "FAIL" not in result.stdout


def test_t5_no_gpio_or_hardware_io_symbols_in_new_unit_tests():
    forbidden_substrings = (
        "gpio",
        "pigpio",
        "/dev/mem",
        "termios",
        "serial_open",
        "socket(",
        "dshot",
    )
    for filename in _EXPECTED_RUNG_TEST_FILES:
        path = TESTS_DIR / filename
        text = path.read_text(encoding="utf-8").lower()
        code_only_lines = []
        for line in text.splitlines():
            comment_at = line.find("//")
            code_only_lines.append(line if comment_at == -1 else line[:comment_at])
        code_text = "\n".join(code_only_lines)
        for token in forbidden_substrings:
            assert token not in code_text, f"{path} contains forbidden-shaped code token '{token}'"


def test_t6_rung_sources_are_git_unchanged_by_this_buy():
    """IC §0 decision 6 — behavior freeze. This Buy's own diff must not
    touch the existing rung sources unless an Engineer-approved bugfix is
    disclosed (none was needed here)."""
    rung_files = [
        NATIVE_FC_DIR / "src" / name
        for name in ("filter.cpp", "attitude.cpp", "controller.cpp", "rate_torque.cpp", "mixer.cpp", "esc.cpp", "plant.cpp")
    ]
    for path in rung_files:
        assert path.is_file(), path
    result = subprocess.run(
        ["git", "diff", "--stat", *[str(p) for p in rung_files]],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.stdout.strip() == "", f"unexpected diff in rung sources:\n{result.stdout}"


def test_no_native_unit_test_wiring_into_craft_or_orchestrator():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "fc_unit_tests" not in text, f"{py_file} references the C++ unit-test binary"
            assert "Catch2" not in text, f"{py_file} references Catch2"


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


def test_t8_pyproject_version_is_0_5_13():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.13"' in text
