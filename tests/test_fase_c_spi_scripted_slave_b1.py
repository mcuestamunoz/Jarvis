"""Tests T1-T10 for `B1-fase-c-spi-scripted-slave` (C33).

This is a **C++-native Buy** (same axis as C32) — `ScriptedSpi` lives
entirely under `native/flight_control/`. T1-T4/T7 (is-a `SpiBytePort*`,
fills RX from script not TX echo, short count on a too-short script,
`LoopbackSpi` regression) run as Catch2 cases in
`native/flight_control/tests/test_spi.cpp`, via `ctest`, not here. T9
(full Python suite + host `ctest` green) is a process gate covered by
running them, not asserted here. T10 (report content: scripted SPI !=
gyro live != chip SPI) is covered by
`.jes/artifacts/implementation_report_fase_c_spi_scripted_slave_b1.md`,
not by this file.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command

REPO_ROOT = Path(__file__).resolve().parents[1]
NATIVE_FC_DIR = REPO_ROOT / "native" / "flight_control"
SPI_HPP = NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "spi.hpp"
SPI_CPP = NATIVE_FC_DIR / "src" / "spi.cpp"
SPI_TEST_CPP = NATIVE_FC_DIR / "tests" / "test_spi.cpp"
STUB_MAIN = NATIVE_FC_DIR / "mcu" / "stub_main.cpp"
HELLO_LED_C = NATIVE_FC_DIR / "mcu" / "hello_led.c"
HELLO_LED_H = NATIVE_FC_DIR / "mcu" / "hello_led.h"
DSHOT_HPP = NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "dshot.hpp"
DSHOT_CPP = NATIVE_FC_DIR / "src" / "dshot.cpp"
DSHOT_PY = REPO_ROOT / "src" / "jarvis" / "flight_software" / "flight_control" / "dshot.py"
UART_HPP = NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "uart.hpp"
UART_CPP = NATIVE_FC_DIR / "src" / "uart.cpp"


def _strip_c_comments(text: str) -> str:
    """Removes /* ... */ block comments and // line comments so honesty
    checks look at real code, not this module's own honesty-prose
    comments (same distinction every prior Fase C Buy's honesty tests
    make, adapted for C's comment syntax)."""
    without_block = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    without_line = re.sub(r"//.*", "", without_block)
    return without_line


def _git_unchanged(path: Path) -> str:
    result = subprocess.run(
        ["git", "diff", "--stat", str(path)], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    return result.stdout.strip()


def test_t5_stub_main_dshot_uart_git_unchanged():
    for path in (STUB_MAIN, HELLO_LED_C, HELLO_LED_H, DSHOT_HPP, DSHOT_CPP, DSHOT_PY, UART_HPP, UART_CPP):
        assert _git_unchanged(path) == "", f"unexpected diff in {path}"


def test_t6_native_tree_still_zero_crsf_elrs_and_no_spi_registers_in_new_code():
    for path in (REPO_ROOT / "native").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "crsf" not in text.lower(), f"{path} unexpectedly references CRSF"
            assert "elrs" not in text.lower(), f"{path} unexpectedly references ELRS"

    for path in (SPI_HPP, SPI_CPP, SPI_TEST_CPP):
        code_only = _strip_c_comments(path.read_text(encoding="utf-8")).lower()
        for token in ("spi1", "spi2", "spi3", "cr1", "->dr", ".dr", "cmsis", "gpio", "nss", "0x4001"):
            assert token not in code_only, f"{path} unexpectedly contains '{token}' in real code"


def test_who_am_i_and_icm42688p_appear_only_in_comments():
    """IC §0 decision 7: WHO_AM_I/ICM42688P may be named in a comment
    ("a future gyro test could load 0x47 here") but never in real code
    — no register map, no product driver, anywhere in this Buy."""
    for path in (SPI_HPP, SPI_CPP, SPI_TEST_CPP):
        code_only = _strip_c_comments(path.read_text(encoding="utf-8")).lower()
        assert "who_am_i" not in code_only, f"{path} unexpectedly contains WHO_AM_I in real code"
        assert "icm42688p" not in code_only, f"{path} unexpectedly contains ICM42688P in real code"


def test_scripted_spi_declared_alongside_loopback_spi_not_a_new_file():
    """IC §0 decision 1/output 1: extend the existing spi.hpp/spi.cpp —
    no new file, no new CMake registration needed."""
    hpp_text = SPI_HPP.read_text(encoding="utf-8")
    assert "class ScriptedSpi" in hpp_text
    assert "class LoopbackSpi" in hpp_text
    cpp_text = SPI_CPP.read_text(encoding="utf-8")
    assert "ScriptedSpi::transfer" in cpp_text
    assert "LoopbackSpi::transfer" in cpp_text
    assert not (NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "scripted_spi.hpp").exists()


def test_t8_pyproject_version_is_0_5_31():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.38"' in text


def test_t9_full_suite_process_gate_placeholder():
    """The full Python suite being green (and host `ctest` green) is
    verified by running them, not asserted here — see the implementation
    report's own test-run transcript."""
    assert True


def test_no_gyro_driver_or_imu_wiring_added_this_buy():
    """IC §0 decision 2: no ICM42688P register map, no WHO_AM_I product
    API, no IMU-into-`step` wiring — this Buy is the canned-RX port
    only."""
    sim_imu_hal = REPO_ROOT / "src" / "jarvis" / "flight_software" / "flight_control" / "sim_imu_hal.py"
    assert _git_unchanged(sim_imu_hal) == ""
    loop_hpp = NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "loop.hpp"
    loop_cpp = NATIVE_FC_DIR / "src" / "loop.cpp"
    loop_py = REPO_ROOT / "src" / "jarvis" / "flight_software" / "flight_control" / "loop.py"
    for path in (loop_hpp, loop_cpp, loop_py):
        assert _git_unchanged(path) == "", f"unexpected diff in {path}"


def test_default_safety_gate_still_reject_all():
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_no_craft_or_core_imports_reference_scripted_spi_and_registry_still_empty():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "ScriptedSpi" not in text, f"{py_file} references ScriptedSpi"

    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []
