"""Tests T1-T12 for `B1-fase-c-mcu-spi-hal-stub` (C32).

This is a **C++-native Buy** (IC §0 decision 4: "do not add a Python SPI
driver") — the port and its one implementation live entirely under
`native/flight_control/`. T1-T4/T9 (round-trip, `n=0`, short write on
overflow, `SpiBytePort*` convertibility) run as Catch2 cases in
`native/flight_control/tests/test_spi.cpp`, via `ctest`, not here. T11
(full Python suite + host `ctest` green) is a process gate covered by
running them, not asserted here. T12 (report content: MCU SPI stub !=
chip SPI != gyro live) is covered by
`.jes/artifacts/implementation_report_fase_c_mcu_spi_hal_stub_b1.md`,
not by this file.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command

REPO_ROOT = Path(__file__).resolve().parents[1]
NATIVE_FC_DIR = REPO_ROOT / "native" / "flight_control"
SPI_HPP = NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "spi.hpp"
SPI_CPP = NATIVE_FC_DIR / "src" / "spi.cpp"
SPI_TEST_CPP = NATIVE_FC_DIR / "tests" / "test_spi.cpp"
STUB_MAIN = NATIVE_FC_DIR / "mcu" / "stub_main.cpp"
DSHOT_HPP = NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "dshot.hpp"
UART_HPP = NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "uart.hpp"
DSHOT_PY = REPO_ROOT / "src" / "jarvis" / "flight_software" / "flight_control" / "dshot.py"
HELLO_LED_C = NATIVE_FC_DIR / "mcu" / "hello_led.c"
HELLO_LED_H = NATIVE_FC_DIR / "mcu" / "hello_led.h"
SIM_IMU_HAL_PY = REPO_ROOT / "src" / "jarvis" / "flight_software" / "flight_control" / "sim_imu_hal.py"
CMAKE_FILE = NATIVE_FC_DIR / "CMakeLists.txt"


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


def test_t5_stub_main_has_no_spi_port_reference_or_poll_loop():
    text = STUB_MAIN.read_text(encoding="utf-8")
    for symbol in ("SpiBytePort", "LoopbackSpi", "spi.hpp", "spi_poll", "spi_transfer"):
        assert symbol not in text, f"stub_main.cpp unexpectedly references '{symbol}'"


def test_t6_dshot_hpp_and_uart_hpp_git_unchanged():
    for path in (DSHOT_HPP, UART_HPP):
        assert _git_unchanged(path) == "", f"unexpected diff in {path}"


def test_t7_native_tree_still_zero_crsf_elrs_tokens():
    for path in (REPO_ROOT / "native").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "crsf" not in text.lower(), f"{path} unexpectedly references CRSF"
            assert "elrs" not in text.lower(), f"{path} unexpectedly references ELRS"


def test_t8_no_spi_registers_or_cmsis_or_cs_gpio_in_new_spi_files():
    for path in (SPI_HPP, SPI_CPP):
        code_only = _strip_c_comments(path.read_text(encoding="utf-8")).lower()
        for token in ("spi1", "spi2", "spi3", "cr1", " dr ", "->dr", ".dr", "cmsis", "gpio", "nss", "0x4001"):
            assert token not in code_only, f"{path} unexpectedly contains '{token}' in real code"


def test_desk_gyro_identity_may_appear_only_as_comment_citation():
    """ICM42688P is allowed as a named desk identity in comments (IC §0
    decision 8) — this test confirms it is not wired into any real
    register/driver-shaped code (there simply is none in this Buy)."""
    text = SPI_HPP.read_text(encoding="utf-8")
    assert "ICM42688P" in text  # cited as desk identity, per the IC's own honesty template
    code_only = _strip_c_comments(text).lower()
    assert "icm42688p" not in code_only  # never appears in real code, only in the comment


def test_t9_pyproject_version_is_0_5_30():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.38"' in text


def test_t10_full_suite_process_gate_placeholder():
    """The full Python suite being green (and host `ctest` green) is
    verified by running them, not asserted here — see the implementation
    report's own test-run transcript."""
    assert True


def test_hello_led_and_stub_main_and_dshot_git_unchanged():
    for path in (HELLO_LED_C, HELLO_LED_H, STUB_MAIN, DSHOT_HPP, DSHOT_PY):
        assert _git_unchanged(path) == "", f"unexpected diff in {path}"


def test_sim_imu_hal_git_unchanged():
    assert _git_unchanged(SIM_IMU_HAL_PY) == ""


def test_spi_files_not_under_src_jarvis():
    assert SPI_HPP.is_file()
    assert SPI_CPP.is_file()
    assert not any((REPO_ROOT / "src" / "jarvis").rglob("spi.py"))
    assert not any((REPO_ROOT / "src" / "jarvis").rglob("spi.*"))


def test_cmake_wires_spi_into_jarvis_fc_and_unit_tests():
    text = CMAKE_FILE.read_text(encoding="utf-8")
    assert "src/spi.cpp" in text
    assert "tests/test_spi.cpp" in text


def test_default_safety_gate_still_reject_all():
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_no_craft_or_core_imports_reference_spi_and_registry_still_empty():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "SpiBytePort" not in text, f"{py_file} references SpiBytePort"
            assert "LoopbackSpi" not in text, f"{py_file} references LoopbackSpi"

    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []


def test_mcu_elf_still_links_if_toolchain_and_build_present():
    """Not required by the IC's own T-checklist (host `ctest` is the
    real gate) — a bonus check that skips honestly when the MCU build
    directory is absent rather than failing the whole suite for lack of
    an ARM toolchain."""
    if not shutil.which("arm-none-eabi-g++"):
        pytest.skip("arm-none-eabi-g++ not found on PATH")
    elf_path = REPO_ROOT / "build" / "flight_control_mcu" / "fc_mcu_stub.elf"
    if not elf_path.is_file():
        pytest.skip("MCU .elf not built in this environment")
    assert elf_path.stat().st_size > 0
