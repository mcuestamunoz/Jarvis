"""Tests T1-T8 for `B1-fase-c-cpp-flight-control-scaffold` (C13).

**Wrapper choice (IC §4 "document choice"):** T2/T3 are exercised by a
*thin* pytest wrapper that looks for an already-built
`build/flight_control/fc_closed_loop_smoke` binary and runs it if
present, asserting exit 0 and the documented tilt-recovery criterion by
parsing its stdout. It deliberately does **not** invoke `cmake`/`clang++`
itself from inside the Python suite — building a native binary on every
`pytest` run would make the (fast, hermetic) Python suite depend on a
C++ toolchain being present in every environment that runs it. If the
binary has not been built yet, the test **skips with a reason** that
names the exact build command (see `native/flight_control/README.md`).
The actual configure+build was performed and verified manually for this
Buy (see the implementation report) — this wrapper re-verifies the
already-built artifact on developer/CI machines that have the toolchain.

Process gates covered elsewhere, not by this file:
- T6 (Python suite still green @ 0.5.11) — the full `pytest -q` run.
- T7 (report: material change · host-only · != flying · Python retained ·
  C++ honesty) — `.jes/artifacts/implementation_report_fase_c_cpp_flight_control_scaffold_b1.md`.
- T8 (docs updated honestly, no premature v0.5.11 tag) — README/
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
BUILT_SMOKE_BINARY = REPO_ROOT / "build" / "flight_control" / "fc_closed_loop_smoke"

_MIRRORED_HEADERS = (
    "types.hpp",
    "quat_math.hpp",
    "filter.hpp",
    "attitude.hpp",
    "controller.hpp",
    "rate_torque.hpp",
    "mixer.hpp",
    "plant.hpp",
)
_MIRRORED_SOURCES = (
    "filter.cpp",
    "attitude.cpp",
    "controller.cpp",
    "rate_torque.cpp",
    "mixer.cpp",
    "plant.cpp",
)


def test_t1_native_tree_exists_with_cmake_and_smoke_target():
    assert NATIVE_FC_DIR.is_dir()
    assert (NATIVE_FC_DIR / "CMakeLists.txt").is_file()
    assert (NATIVE_FC_DIR / "smoke" / "closed_loop_smoke.cpp").is_file()
    for header in _MIRRORED_HEADERS:
        assert (NATIVE_FC_DIR / "include" / "jarvis" / "fc" / header).is_file(), header
    for source in _MIRRORED_SOURCES:
        assert (NATIVE_FC_DIR / "src" / source).is_file(), source

    cmake_text = (NATIVE_FC_DIR / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "cmake_minimum_required" in cmake_text
    assert "CXX_STANDARD 17" in cmake_text
    assert "add_executable(fc_closed_loop_smoke" in cmake_text


def test_t2_t3_smoke_binary_builds_and_recovers_if_toolchain_available():
    if not BUILT_SMOKE_BINARY.is_file():
        pytest.skip(
            "C++ smoke binary not built. Build it first: "
            "cmake -S native/flight_control -B build/flight_control && "
            "cmake --build build/flight_control "
            "(see native/flight_control/README.md)."
        )

    result = subprocess.run(
        [str(BUILT_SMOKE_BINARY)], capture_output=True, text=True, timeout=30, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr

    initial_match = re.search(r"initial tilt error:\s*([\d.]+)\s*deg", result.stdout)
    final_match = re.search(r"final tilt error:\s*([\d.]+)\s*deg", result.stdout)
    assert initial_match is not None and final_match is not None, result.stdout

    initial_deg = float(initial_match.group(1))
    final_deg = float(final_match.group(1))
    assert final_deg < initial_deg, "tilt error did not strictly decrease"
    assert "PASS" in result.stdout


def test_t4_no_gpio_or_hardware_io_symbols_in_native_tree():
    """"dshot" was a blanket-forbidden token at C13's own landing, when
    no DShot-shaped code existed anywhere in this tree. **C31 disclosed
    exception:** `B1-fase-c-dshot-encode-stub` (★ Engineer-approved)
    explicitly adds `dshot.hpp`/`dshot.cpp`/`tests/test_dshot.cpp` — a
    pure in-RAM 16-bit frame *encoder*, still no GPIO/TIM/DMA/bit-bang
    anywhere (that remains this test's own, unweakened check on every
    file, dshot files included). So "dshot" is excluded from the
    forbidden-token scan **only** for those three C31-authorized files;
    every other native/flight_control file — including any future one —
    still may not mention it, which is exactly the guard that would
    catch DShot logic leaking into, say, mixer.cpp or hello_led.c."""
    forbidden_substrings = (
        "gpio",
        "pigpio",
        "/dev/mem",
        "termios",
        "serial_open",
        "socket(",
        "dshot",
    )
    dshot_authorized_files = {
        NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "dshot.hpp",
        NATIVE_FC_DIR / "src" / "dshot.cpp",
        NATIVE_FC_DIR / "tests" / "test_dshot.cpp",
    }
    source_files = list(NATIVE_FC_DIR.rglob("*.cpp")) + list(NATIVE_FC_DIR.rglob("*.hpp"))
    assert source_files, "expected native/flight_control source files to exist"
    for path in source_files:
        text = path.read_text(encoding="utf-8").lower()
        # Strip line-comment content so this test checks real code, not the
        # module's own honesty prose (which legitimately names these terms
        # to disclose their absence) — same "symbol(" vs prose distinction
        # used by every prior Fase C Buy's honesty tests.
        code_only_lines = []
        for line in text.splitlines():
            comment_at = line.find("//")
            code_only_lines.append(line if comment_at == -1 else line[:comment_at])
        code_text = "\n".join(code_only_lines)
        tokens = forbidden_substrings
        if path in dshot_authorized_files:
            tokens = tuple(t for t in forbidden_substrings if t != "dshot")
        for token in tokens:
            assert token not in code_text, f"{path} contains forbidden-shaped code token '{token}'"


def test_t5_no_px4_or_ardupilot_vendored_tree():
    hits = [p for p in NATIVE_FC_DIR.rglob("*") if "px4" in p.name.lower() or "ardupilot" in p.name.lower()]
    assert hits == []


def test_native_tree_outside_python_package():
    assert not str(NATIVE_FC_DIR).startswith(str(REPO_ROOT / "src" / "jarvis"))


def test_python_wooden_ladder_retained_unchanged():
    """C13 IC §0 decision 9 / §5 — the Python ladder must not be deleted
    or replaced; craft stays Python."""
    flight_control_dir = REPO_ROOT / "src" / "jarvis" / "flight_software" / "flight_control"
    for module_name in ("filter.py", "attitude.py", "controller.py", "rate_torque.py", "mixer.py", "plant.py"):
        assert (flight_control_dir / module_name).is_file(), module_name

    from jarvis.flight_software.flight_control import (
        BodyTorqueCommand,
        LinearRateTorqueBridge,
        QuadXMixer,
    )
    from jarvis.flight_software.flight_control.attitude import ComplementaryAttitudeEstimator
    from jarvis.flight_software.flight_control.controller import PdAttitudeController
    from jarvis.flight_software.flight_control.plant import ToyQuadAttitudePlant

    assert LinearRateTorqueBridge is not None
    assert BodyTorqueCommand is not None
    assert QuadXMixer is not None
    assert ComplementaryAttitudeEstimator is not None
    assert PdAttitudeController is not None
    assert ToyQuadAttitudePlant is not None


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


def test_no_native_flight_control_wiring_into_craft_or_orchestrator():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "native/flight_control" not in text, f"{py_file} references native/flight_control"
            assert "jarvis_fc" not in text, f"{py_file} references the C++ jarvis_fc target"
            assert "fc_closed_loop_smoke" not in text, f"{py_file} references the C++ smoke binary"


def test_t11_pyproject_version_is_0_5_11():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.30"' in text
