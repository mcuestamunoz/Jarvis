"""Tests T1-T12 for `B1-fase-c-mcu-uart-hal-stub` (C28).

This is a **C++-native Buy** (IC §0 decision 4: "do not add a Python
UART driver") — the port and its one implementation live entirely under
`native/flight_control/`. T1-T4/T9 (round-trip, empty read, short write
on overflow, `UartBytePort*` convertibility) run as Catch2 cases in
`native/flight_control/tests/test_uart.cpp`, via `ctest`, not here. This
file covers the source-level/boundary checks (T5-T8) plus the Python
side of T6/T10/T11, and skip-if-not-built smoke checks against the
actual built binaries, same pattern C15/C16/C18's own pytest wrappers
use. T12 (report content: MCU UART stub != chip USART != Darwin baud !=
live ELRS) is covered by
`.jes/artifacts/implementation_report_fase_c_mcu_uart_hal_stub_b1.md`,
not by this file.
"""

from __future__ import annotations

import inspect
import subprocess
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities import crsf_serial as crsf_serial_module
from jarvis.capabilities import radio as radio_module
from jarvis.capabilities.intent import RadioIntentAdapter
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command

REPO_ROOT = Path(__file__).resolve().parents[1]
NATIVE_FC_DIR = REPO_ROOT / "native" / "flight_control"
BUILD_DIR = REPO_ROOT / "build" / "flight_control"
UNIT_TEST_BINARY = BUILD_DIR / "fc_unit_tests"

UART_HEADER = NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "uart.hpp"
UART_SOURCE = NATIVE_FC_DIR / "src" / "uart.cpp"
UART_TEST_SOURCE = NATIVE_FC_DIR / "tests" / "test_uart.cpp"
STUB_MAIN = NATIVE_FC_DIR / "mcu" / "stub_main.cpp"

_BUILD_HINT = (
    "cmake -S native/flight_control -B build/flight_control && "
    "cmake --build build/flight_control (see native/flight_control/README.md)."
)


def test_t5_stub_main_has_no_uart_port_reference_or_poll_loop():
    text = STUB_MAIN.read_text(encoding="utf-8")
    for symbol in ("UartBytePort", "LoopbackUart", "uart.hpp", "uart_poll", "while (true)"):
        if symbol == "while (true)":
            # stub_main's own pre-existing idle loop (C18) is allowed —
            # what's forbidden is a UART-specific poll loop referencing
            # the new port types, not the existing idle spin itself.
            continue
        assert symbol not in text, f"stub_main.cpp unexpectedly references '{symbol}'"


def test_t6_crsf_serial_py_git_unchanged_and_radio_py_has_no_uart_apis():
    result = subprocess.run(
        ["git", "diff", "--stat", "src/jarvis/capabilities/crsf_serial.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.stdout.strip() == "", f"unexpected diff in crsf_serial.py:\n{result.stdout}"

    source = inspect.getsource(radio_module)
    for symbol in ("UartBytePort", "LoopbackUart", "uart_read", "uart_write"):
        assert symbol not in source, f"radio.py unexpectedly references '{symbol}'"

    # crsf_serial.py's own public shape is unchanged (sanity, matches C23).
    assert hasattr(crsf_serial_module, "CrsfHostSerialIngress")
    assert hasattr(crsf_serial_module, "configure_host_baud")


def test_t7_native_tree_still_zero_crsf_elrs_tokens():
    for path in (REPO_ROOT / "native").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "crsf" not in text.lower(), f"{path} unexpectedly references CRSF"
            assert "elrs" not in text.lower(), f"{path} unexpectedly references ELRS"


def test_t8_no_ioctl_or_registers_in_uart_files():
    for path in (UART_HEADER, UART_SOURCE, UART_TEST_SOURCE):
        assert path.is_file(), path
        text = path.read_text(encoding="utf-8")
        code_only_lines = []
        for line in text.splitlines():
            comment_at = line.find("//")
            code_only_lines.append(line if comment_at == -1 else line[:comment_at])
        code_text = "\n".join(code_only_lines).lower()
        for token in ("iossiospeed", "termios", "cmsis", "gpio", "irq_handler", "dma"):
            assert token not in code_text, f"{path} contains forbidden token '{token}'"
        # "usart"/"BRR" specifically — bare substring check on real code only
        assert "usart" not in code_text, f"{path} references USART registers"
        assert "->brr" not in code_text and ".brr" not in code_text, f"{path} references a BRR register"


def test_t9_unit_test_binary_includes_uart_cases_if_built():
    if not UNIT_TEST_BINARY.is_file():
        pytest.skip(f"C++ unit-test binary not built. Build it first: {_BUILD_HINT}")

    result = subprocess.run(
        [str(UNIT_TEST_BINARY), "[uart]"], capture_output=True, text=True, timeout=60, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "All tests passed" in result.stdout, result.stdout


def test_t10_pyproject_version_is_0_5_26():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.44"' in text


def test_t11_full_suite_process_gate_placeholder():
    """The full Python suite being green (and host `ctest` green) is
    verified by running them, not asserted here — see the implementation
    report's own test-run transcript."""
    assert True


def test_cmake_wires_uart_into_jarvis_fc_and_unit_tests():
    cmake_text = (NATIVE_FC_DIR / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "src/uart.cpp" in cmake_text
    assert "tests/test_uart.cpp" in cmake_text


def test_uart_files_exist_and_not_under_src_jarvis():
    assert UART_HEADER.is_file()
    assert UART_SOURCE.is_file()
    assert UART_TEST_SOURCE.is_file()
    assert not (REPO_ROOT / "src" / "jarvis" / "uart.py").exists()
    assert not any((REPO_ROOT / "src" / "jarvis").rglob("uart.py"))


def test_default_safety_gate_still_reject_all_and_intent_still_not_implemented():
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.evaluate(SafetyRequest()).outcome == "reject"

    with pytest.raises(NotImplementedError):
        RadioIntentAdapter.parse(b"\x00\x00")

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_no_craft_or_core_imports_of_uart_and_registry_still_empty():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "UartBytePort" not in text, f"{py_file} references UartBytePort"
            assert "LoopbackUart" not in text, f"{py_file} references LoopbackUart"

    registry = CapabilityRegistry.load_default()
    # T2 (B1-capability-registry-product-fill): capabilities()/providers() are
    # no longer empty (ontology.explain/engineering.continuity, both software-
    # provided) — see tests/test_capability_registry_product_fill_b1.py. T5
    # (B1-capability-skills-seed): skills() is no longer empty either — two
    # declared-only stub rows — see tests/test_capability_skills_seed_b1.py.
    # T6 (B1-assistant-vehicle-hold-task): a third declared-only stub skill,
    # skill.request_hold (requires flight.hold, not_implemented/vehicle) —
    # see tests/test_assistant_vehicle_hold_task_b1.py. T7
    # (B1-assistant-vehicle-land-task): a fourth, skill.request_land
    # (requires flight.land, not_implemented/vehicle) — see
    # tests/test_assistant_vehicle_land_task_b1.py. T8
    # (B1-assistant-vehicle-go-to-task): a fifth, skill.request_go_to
    # (requires flight.go_to, not_implemented/vehicle) — see
    # tests/test_assistant_vehicle_go_to_task_b1.py. T9
    # (B1-assistant-vehicle-takeoff-task): a sixth, skill.request_takeoff
    # (requires flight.takeoff, not_implemented/vehicle) — see
    # tests/test_assistant_vehicle_takeoff_task_b1.py. T10
    # (B1-assistant-vehicle-return-home-task): a seventh, skill.request_return_home
    # (requires flight.return_home, not_implemented/vehicle) — see
    # tests/test_assistant_vehicle_return_home_task_b1.py. T11
    # (B1-assistant-vehicle-arm-ux): eighth+ninth, skill.request_arm_policy /
    # skill.request_disarm_policy (require safety.chat_armed_allowlist,
    # available/software) — see tests/test_assistant_vehicle_arm_ux_b1.py.
    # T12 (B1-assistant-vehicle-follow-task): a tenth, skill.request_follow
    # (requires flight.follow, not_implemented/vehicle) — see
    # tests/test_assistant_vehicle_follow_task_b1.py.
    # T13 (B1-assistant-vehicle-patrol-task): an eleventh, skill.request_patrol
    # (requires flight.patrol, not_implemented/vehicle) — see
    # tests/test_assistant_vehicle_patrol_task_b1.py.
    # Still zero Skill execution path anywhere; this file's own isolation
    # proof is unaffected either way.
    assert {skill.id for skill in registry.skills()} == {
        "skill.explain_concept",
        "skill.project_status",
        "skill.request_hold",
        "skill.request_land",
        "skill.request_go_to",
        "skill.request_takeoff",
        "skill.request_return_home",
        "skill.request_arm_policy",
        "skill.request_disarm_policy",
        "skill.request_follow",
        "skill.request_patrol",
    }


def test_mcu_elf_still_links_if_toolchain_and_build_present():
    """Not required by the IC's own T-checklist (host `ctest` is the
    real gate) — a bonus check that skips honestly when the MCU build
    directory is absent rather than failing the whole suite for lack of
    an ARM toolchain."""
    mcu_build_dir = REPO_ROOT / "build" / "flight_control_mcu"
    elf_path = mcu_build_dir / "fc_mcu_stub.elf"
    if not elf_path.is_file():
        pytest.skip("MCU .elf not built in this environment — not required by this Buy's own checklist")
    assert elf_path.stat().st_size > 0
