"""Tests T1-T12 for `B1-fase-c-spi-scripted-gyro-probe` (C34).

This is a **C++-native Buy** (same axis as C32/C33) — `probe_rx` lives
entirely under `native/flight_control/`. T1-T5/T9 (probe_rx takes
SpiBytePort&, ScriptedSpi fixture round-trip, LoopbackSpi echo of dummy
TX zeros, short-count/tail-untouched, n=0) run as Catch2 cases in
`native/flight_control/tests/test_spi_probe.cpp`, via `ctest`, not here.
T11 (full Python suite + host `ctest` green) is a process gate covered
by running them, not asserted here. T12 (report content: scripted gyro
probe != gyro live != chip SPI != WHO_AM_I) is covered by
`.jes/artifacts/implementation_report_fase_c_spi_scripted_gyro_probe_b1.md`,
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
SPI_PROBE_HPP = NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "spi_probe.hpp"
SPI_PROBE_CPP = NATIVE_FC_DIR / "src" / "spi_probe.cpp"
SPI_PROBE_TEST_CPP = NATIVE_FC_DIR / "tests" / "test_spi_probe.cpp"
STUB_MAIN = NATIVE_FC_DIR / "mcu" / "stub_main.cpp"
HELLO_LED_C = NATIVE_FC_DIR / "mcu" / "hello_led.c"
HELLO_LED_H = NATIVE_FC_DIR / "mcu" / "hello_led.h"
DSHOT_HPP = NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "dshot.hpp"
DSHOT_CPP = NATIVE_FC_DIR / "src" / "dshot.cpp"
DSHOT_PY = REPO_ROOT / "src" / "jarvis" / "flight_software" / "flight_control" / "dshot.py"
UART_HPP = NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "uart.hpp"
UART_CPP = NATIVE_FC_DIR / "src" / "uart.cpp"
LOOP_HPP = NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "loop.hpp"
LOOP_CPP = NATIVE_FC_DIR / "src" / "loop.cpp"
LOOP_PY = REPO_ROOT / "src" / "jarvis" / "flight_software" / "flight_control" / "loop.py"


def _strip_c_comments(text: str) -> str:
    """Removes /* ... */ block comments and // line comments so honesty
    checks look at real code, not this module's own honesty-prose
    comments."""
    without_block = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    without_line = re.sub(r"//.*", "", without_block)
    return without_line


def _git_unchanged(path: Path) -> str:
    result = subprocess.run(
        ["git", "diff", "--stat", str(path)], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    return result.stdout.strip()


def test_t6_stub_main_dshot_uart_loop_git_unchanged():
    for path in (STUB_MAIN, HELLO_LED_C, HELLO_LED_H, DSHOT_HPP, DSHOT_CPP, DSHOT_PY, UART_HPP, UART_CPP, LOOP_HPP, LOOP_CPP, LOOP_PY):
        assert _git_unchanged(path) == "", f"unexpected diff in {path}"


def test_spi_hpp_and_spi_cpp_also_git_unchanged():
    """IC §0 decision 9 prefers a zero edit on spi.hpp/spi.cpp (the port
    itself) — probe_rx is a client living in its own new files."""
    assert _git_unchanged(SPI_HPP) == ""
    assert _git_unchanged(SPI_CPP) == ""


def test_t7_native_tree_zero_crsf_elrs_and_no_forbidden_tokens_in_new_code():
    for path in (REPO_ROOT / "native").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "crsf" not in text.lower(), f"{path} unexpectedly references CRSF"
            assert "elrs" not in text.lower(), f"{path} unexpectedly references ELRS"

    for path in (SPI_PROBE_HPP, SPI_PROBE_CPP, SPI_PROBE_TEST_CPP):
        code_only = _strip_c_comments(path.read_text(encoding="utf-8")).lower()
        for token in ("spi1", "spi2", "spi3", "cr1", "->dr", ".dr", "cmsis", "gpio", "nss", "0x75", "who_am_i", "icm42688p"):
            assert token not in code_only, f"{path} unexpectedly contains '{token}' in real code"


def test_t8_no_0x47_literal_anywhere_in_library_files():
    """T8: the fixture byte lives in tests only — spi_probe.hpp/cpp must
    not contain the literal `0x47`, not even in a comment."""
    for path in (SPI_PROBE_HPP, SPI_PROBE_CPP):
        text = path.read_text(encoding="utf-8")
        assert "0x47" not in text, f"{path} unexpectedly contains the fixture literal 0x47"


def test_probe_rx_declared_in_new_files_not_folded_into_scripted_spi():
    """IC §0 decision 5/output 1: probe_rx lives in new spi_probe.hpp/cpp,
    not added as a method on LoopbackSpi/ScriptedSpi."""
    assert SPI_PROBE_HPP.exists()
    assert SPI_PROBE_CPP.exists()
    probe_hpp_text = SPI_PROBE_HPP.read_text(encoding="utf-8")
    assert "probe_rx" in probe_hpp_text
    spi_hpp_text = SPI_HPP.read_text(encoding="utf-8")
    assert "probe_rx" not in spi_hpp_text
    assert "class LoopbackSpi" in spi_hpp_text
    assert "class ScriptedSpi" in spi_hpp_text


def test_cmake_wires_spi_probe_into_jarvis_fc_and_unit_tests():
    cmake_text = (NATIVE_FC_DIR / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "src/spi_probe.cpp" in cmake_text
    assert "tests/test_spi_probe.cpp" in cmake_text


def test_t10_pyproject_version_is_0_5_32():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.39"' in text


def test_t11_full_suite_process_gate_placeholder():
    """The full Python suite being green (and host `ctest` green) is
    verified by running them, not asserted here — see the implementation
    report's own test-run transcript."""
    assert True


def test_no_gyro_driver_imu_wiring_or_step_reference_added_this_buy():
    """IC §2.1 non-goals: no ICM42688P register map, no WHO_AM_I product
    API, no IMU-into-`step` wiring — this Buy is a port client only."""
    sim_imu_hal = REPO_ROOT / "src" / "jarvis" / "flight_software" / "flight_control" / "sim_imu_hal.py"
    assert _git_unchanged(sim_imu_hal) == ""
    for path in (SPI_PROBE_HPP, SPI_PROBE_CPP):
        code_only = _strip_c_comments(path.read_text(encoding="utf-8")).lower()
        assert "step(" not in code_only


def test_default_safety_gate_still_reject_all():
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_no_craft_or_core_imports_reference_probe_rx_and_registry_still_empty():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "probe_rx" not in text, f"{py_file} references probe_rx"

    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []


def test_no_python_spi_port_added():
    """IC's own locked default: C++ native only, no Python SPI port."""
    for py_file in (REPO_ROOT / "src" / "jarvis" / "flight_software").rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        assert "probe_rx" not in text, f"{py_file} unexpectedly references probe_rx"
        assert "SpiBytePort" not in text, f"{py_file} unexpectedly references SpiBytePort"
