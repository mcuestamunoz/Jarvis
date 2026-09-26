"""Tests T1-T11 for `B1-fase-c-cpp-esc-pwm-stub` (C14).

**Wrapper choice (IC §4, same choice as C13's own
`test_fase_c_cpp_flight_control_scaffold_b1.py`):** T1-T5 are exercised
inside the C++ smoke binary itself (`fc_esc_pwm_smoke`, 18 checks); this
pytest wrapper looks for the already-built binaries and runs them if
present, asserting exit 0 and parsing pass/fail markers from stdout. It
does **not** invoke `cmake`/`clang++` itself — same rationale as C13: a
native toolchain should not be a hard dependency of every `pytest` run.
If a binary has not been built yet, the relevant test **skips with a
reason** naming the exact build command.

Process gates covered elsewhere, not by this file:
- T9 (Python suite still green @ 0.5.12) — the full `pytest -q` run.
- T10 (report: PWM-us only · sim sink · steel parity · != motors spinning
  · != GPIO) — `.jes/artifacts/implementation_report_fase_c_cpp_esc_pwm_stub_b1.md`.
- T11 (docs updated honestly, no premature v0.5.12 tag) — README/
  IMPLEMENTATION_TASKS/PLATFORM_CAPABILITY_VISION/ARCHITECTURE.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command

REPO_ROOT = Path(__file__).resolve().parents[1]
NATIVE_FC_DIR = REPO_ROOT / "native" / "flight_control"
ESC_HEADER = NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "esc.hpp"
ESC_SOURCE = NATIVE_FC_DIR / "src" / "esc.cpp"
ESC_SMOKE_SOURCE = NATIVE_FC_DIR / "smoke" / "esc_pwm_smoke.cpp"
BUILD_DIR = REPO_ROOT / "build" / "flight_control"
ESC_SMOKE_BINARY = BUILD_DIR / "fc_esc_pwm_smoke"
CLOSED_LOOP_SMOKE_BINARY = BUILD_DIR / "fc_closed_loop_smoke"

_BUILD_HINT = (
    "cmake -S native/flight_control -B build/flight_control && "
    "cmake --build build/flight_control (see native/flight_control/README.md)."
)


def test_t8a_esc_sources_exist_and_wired_into_cmake():
    assert ESC_HEADER.is_file()
    assert ESC_SOURCE.is_file()
    assert ESC_SMOKE_SOURCE.is_file()

    cmake_text = (NATIVE_FC_DIR / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "src/esc.cpp" in cmake_text
    assert "add_executable(fc_esc_pwm_smoke" in cmake_text
    assert 'add_test(NAME fc_esc_pwm_smoke COMMAND fc_esc_pwm_smoke)' in cmake_text


def test_t8b_esc_cpp_not_under_python_package():
    assert not str(ESC_HEADER).startswith(str(REPO_ROOT / "src" / "jarvis"))
    assert not str(ESC_SOURCE).startswith(str(REPO_ROOT / "src" / "jarvis"))


def test_t1_t2_t3_t4_t5_esc_pwm_smoke_binary_if_built():
    """The C++ smoke binary itself asserts T1 (force->us endpoints and
    linear midpoint), T2 (4 pulses, protocol pwm_us), T3 (invalid min/max
    rejected), T4 (disarmed record-but-refuse), and T5 (armed applies,
    disarm() flips back). This wrapper re-verifies the built artifact."""
    if not ESC_SMOKE_BINARY.is_file():
        pytest.skip(f"C++ ESC smoke binary not built. Build it first: {_BUILD_HINT}")

    result = subprocess.run(
        [str(ESC_SMOKE_BINARY)], capture_output=True, text=True, timeout=30, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout
    assert "FAIL" not in result.stdout


def test_t7_closed_loop_tip_smoke_still_green_if_built():
    """C13's own tip smoke must remain unaffected by this Buy (IC §0
    decision 9 / §4 T7)."""
    if not CLOSED_LOOP_SMOKE_BINARY.is_file():
        pytest.skip(f"C++ closed-loop smoke binary not built. Build it first: {_BUILD_HINT}")

    result = subprocess.run(
        [str(CLOSED_LOOP_SMOKE_BINARY)], capture_output=True, text=True, timeout=30, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout


def test_t6_no_gpio_or_hardware_io_symbols_in_esc_sources():
    forbidden_substrings = (
        "gpio",
        "pigpio",
        "/dev/mem",
        "termios",
        "serial_open",
        "socket(",
        "dshot",
        "oneshot",
        "multishot",
        "export_pwm",
    )
    for path in (ESC_HEADER, ESC_SOURCE, ESC_SMOKE_SOURCE):
        text = path.read_text(encoding="utf-8").lower()
        code_only_lines = []
        for line in text.splitlines():
            comment_at = line.find("//")
            code_only_lines.append(line if comment_at == -1 else line[:comment_at])
        code_text = "\n".join(code_only_lines)
        for token in forbidden_substrings:
            assert token not in code_text, f"{path} contains forbidden-shaped code token '{token}'"


def test_t8c_python_esc_module_untouched():
    """C10's own esc.py must not be rewritten by this Buy (IC §0 decision
    8 / §3)."""
    from jarvis.flight_software.flight_control.esc import (
        EscApplyResult,
        EscPwmCommand,
        SimulatedEscSink,
        encode_motor_forces,
    )
    from jarvis.flight_software.flight_control.mixer import MotorForceCommand

    forces = MotorForceCommand(t_s=0.0, motor_forces=(0.0, 0.5, 1.0, 0.25))
    cmd = encode_motor_forces(forces)
    assert isinstance(cmd, EscPwmCommand)
    assert cmd.pulse_us[0] == pytest.approx(1000.0)
    assert cmd.pulse_us[2] == pytest.approx(2000.0)

    sink = SimulatedEscSink()
    result = sink.apply(cmd)
    assert isinstance(result, EscApplyResult)
    assert result.applied is False
    assert result.reason == "disarmed"


def test_no_native_esc_wiring_into_craft_or_orchestrator():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "fc_esc_pwm_smoke" not in text, f"{py_file} references the C++ ESC smoke binary"
            assert "SimulatedEscSink" not in text or "esc.hpp" not in text, (
                f"{py_file} unexpectedly references native ESC symbols"
            )


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


def test_t9_pyproject_version_is_0_5_12():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.37"' in text
