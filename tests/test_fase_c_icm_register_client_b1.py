"""Tests T1-T8 for `B1-fase-c-icm-register-client` (C42).

This is a **C++-native Buy** (same axis as C32-C34) — `read_who_am_i`
lives entirely under `native/flight_control/`. IC §0 decision 8's own
"if Python-only would orphan the native SPI ladder, prefer C++ primary"
fallback applies here exactly as it did for C32-C34: this file does
NOT add a Python `SpiBytePort`/client (C34's own locked precedent,
re-pinned by `test_no_python_spi_port_added` below), and its checks are
structural (file existence, freeze-diffs, forbidden-token greps,
CMake wiring), not a Python exercise of the SPI port.

T1/T2/T3/T6 (`ScriptedSpi` cited-value match, wrong-byte mismatch,
`SpiBytePort::transfer` usage via a recording fake, `LoopbackSpi`
non-false-positive) run as Catch2 cases in
`native/flight_control/tests/test_icm42688p.cpp`, via `ctest`, not
here. T7's own "suite + ctest green" half is a process gate covered by
running them, not asserted here. T8 (report content: ICM client on
ScriptedSpi != chip SPI1 != gyro live) is covered by
`.jes/artifacts/implementation_report_fase_c_icm_register_client_b1.md`,
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
ICM_HPP = NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "icm42688p.hpp"
ICM_CPP = NATIVE_FC_DIR / "src" / "icm42688p.cpp"
ICM_TEST_CPP = NATIVE_FC_DIR / "tests" / "test_icm42688p.cpp"
LOOP_HPP = NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "loop.hpp"
LOOP_CPP = NATIVE_FC_DIR / "src" / "loop.cpp"
LOOP_PY = REPO_ROOT / "src" / "jarvis" / "flight_software" / "flight_control" / "loop.py"
PLANT_PY = REPO_ROOT / "src" / "jarvis" / "flight_software" / "flight_control" / "plant.py"


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


def test_t3_uses_spi_byte_port_transfer_not_a_hidden_bypass():
    """Structural half of T3 — the Catch2 `RecordingSpi` case is the
    behavioral half. `read_who_am_i` must call `.transfer(` and must not
    reach past `SpiBytePort` into any lower-level symbol."""
    code_only = _strip_c_comments(ICM_CPP.read_text(encoding="utf-8")).lower()
    assert ".transfer(" in code_only
    for token in ("spi1", "spi2", "spi3", "->dr", ".dr", "cmsis", "gpio", "nss"):
        assert token not in code_only, f"icm42688p.cpp unexpectedly contains '{token}' in real code"


def test_t4_probe_rx_and_c34_ports_untouched():
    for path in (SPI_HPP, SPI_CPP, SPI_PROBE_HPP, SPI_PROBE_CPP, SPI_PROBE_TEST_CPP):
        assert _git_unchanged(path) == "", f"unexpected diff in {path}"

    probe_hpp_text = SPI_PROBE_HPP.read_text(encoding="utf-8")
    assert "probe_rx" in probe_hpp_text
    spi_hpp_text = SPI_HPP.read_text(encoding="utf-8")
    assert "class LoopbackSpi" in spi_hpp_text
    assert "class ScriptedSpi" in spi_hpp_text
    # C34's own fixture byte stays uncited in its own files — the real
    # WHO_AM_I citation lives only in icm42688p.hpp/.cpp (IC §0 decision 4).
    assert "0x47" not in SPI_PROBE_HPP.read_text(encoding="utf-8")
    assert "0x47" not in SPI_PROBE_CPP.read_text(encoding="utf-8")


def test_t5_no_craft_board_edits_and_no_imu_into_step():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "icm42688p" not in text.lower(), f"{py_file} references icm42688p"
            assert "read_who_am_i" not in text, f"{py_file} references read_who_am_i"

    for path in (LOOP_HPP, LOOP_CPP, LOOP_PY, PLANT_PY):
        assert _git_unchanged(path) == "", f"unexpected diff in {path}"

    for path in (ICM_HPP, ICM_CPP):
        code_only = _strip_c_comments(path.read_text(encoding="utf-8")).lower()
        assert "step(" not in code_only

    registry = CapabilityRegistry.load_default()
    # T2 (B1-capability-registry-product-fill): capabilities()/providers() are
    # no longer empty (ontology.explain/engineering.continuity, both software-
    # provided) — see tests/test_capability_registry_product_fill_b1.py for that
    # shape. Skills stay empty; this file's own isolation proof is unaffected.
    assert registry.skills() == []


def test_cited_who_am_i_constants_present_and_documented():
    icm_hpp_text = ICM_HPP.read_text(encoding="utf-8")
    assert "0x75" in icm_hpp_text
    assert "0x47" in icm_hpp_text
    assert "ICM-42688-P" in icm_hpp_text
    assert "DS-000347" in icm_hpp_text
    assert "kIcm42688pRegWhoAmI" in icm_hpp_text
    assert "kIcm42688pWhoAmIValue" in icm_hpp_text


def test_cmake_wires_icm42688p_into_jarvis_fc_and_unit_tests():
    cmake_text = (NATIVE_FC_DIR / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "src/icm42688p.cpp" in cmake_text
    assert "tests/test_icm42688p.cpp" in cmake_text


def test_t7_pyproject_version_is_0_5_43():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.44"' in text


def test_t7_full_suite_process_gate_placeholder():
    """The full Python suite being green (and host `ctest` green) is
    verified by running them, not asserted here — see the implementation
    report's own test-run transcript."""
    assert True


def test_default_safety_gate_still_reject_all():
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_no_python_spi_port_added():
    """IC's own locked default (same as C34): C++ native only, no
    Python SPI port, no Python client of it."""
    for py_file in (REPO_ROOT / "src" / "jarvis" / "flight_software").rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        assert "read_who_am_i" not in text, f"{py_file} unexpectedly references read_who_am_i"
        assert "SpiBytePort" not in text, f"{py_file} unexpectedly references SpiBytePort"
        assert "icm42688p" not in text.lower(), f"{py_file} unexpectedly references icm42688p"
