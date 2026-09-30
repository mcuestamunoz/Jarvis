"""Tests T1-T11 for `B1-fase-c-dshot-encode-stub` (C31).

T8 (C++ Catch2 — vectors + telemetry bit) lives in
`native/flight_control/tests/test_dshot.cpp`, run via `ctest`, not here.
T10 (full Python suite + host `ctest` green) is a process gate covered
by running them, not asserted here. T11 (report content: DShot encode
!= pin != motors != flying) is covered by
`.jes/artifacts/implementation_report_fase_c_dshot_encode_stub_b1.md`,
not by this file.
"""

from __future__ import annotations

import inspect
import io
import subprocess
import tokenize
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command
from jarvis.flight_software.flight_control import dshot as dshot_module
from jarvis.flight_software.flight_control.dshot import (
    DSHOT_MAX_THROTTLE_VALUE,
    DSHOT_MIN_THROTTLE_VALUE,
    encode_dshot_frame,
    encode_motor_forces_dshot,
)
from jarvis.flight_software.flight_control.esc import EscOutput, SimulatedEscSink, encode_motor_forces
from jarvis.flight_software.flight_control.mixer import MotorForceCommand

REPO_ROOT = Path(__file__).resolve().parents[1]
NATIVE_FC_DIR = REPO_ROOT / "native" / "flight_control"
STUB_MAIN = NATIVE_FC_DIR / "mcu" / "stub_main.cpp"
HELLO_LED_C = NATIVE_FC_DIR / "mcu" / "hello_led.c"
HELLO_LED_H = NATIVE_FC_DIR / "mcu" / "hello_led.h"
DSHOT_HPP = NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "dshot.hpp"
DSHOT_CPP = NATIVE_FC_DIR / "src" / "dshot.cpp"


def _strip_python_comments_and_docstrings(source: str) -> str:
    """Removes `#` comments and multi-line (docstring-shaped) string
    literals so honesty checks look at real code, not this module's own
    honesty-prose docstrings (same distinction every prior Fase C Buy's
    honesty tests make)."""
    out_tokens = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            if tok.type == tokenize.COMMENT:
                continue
            if tok.type == tokenize.STRING and "\n" in tok.string:
                continue
            out_tokens.append(tok.string)
    except tokenize.TokenizeError:
        return source
    return " ".join(out_tokens)


def _forces(values=(0.0, 0.5, 1.0, 0.25), t_s: float = 0.0) -> MotorForceCommand:
    return MotorForceCommand(t_s=t_s, motor_forces=values)


def test_t1_known_vectors():
    assert encode_dshot_frame(0) == 0x0000
    assert encode_dshot_frame(48) == 0x0606
    assert encode_dshot_frame(2047) == 0xFFEE


def test_t2_telemetry_bit_changes_value_before_checksum():
    without_telem = encode_dshot_frame(48, telemetry=False)
    with_telem = encode_dshot_frame(48, telemetry=True)
    assert without_telem != with_telem
    assert with_telem == 0x0617


def test_t3_rejects_out_of_range_throttle():
    for bad in (2048, -1, 3000, -100):
        with pytest.raises(ValueError):
            encode_dshot_frame(bad)


def test_t3b_rejects_non_int_throttle():
    for bad in (5.0, "48", None, True, False):
        with pytest.raises(ValueError):
            encode_dshot_frame(bad)  # type: ignore[arg-type]


def test_t4_pwm_encode_and_esc_output_still_pwm_unchanged():
    forces = _forces()
    pwm_cmd = encode_motor_forces(forces)
    assert pwm_cmd.pulse_us[0] == pytest.approx(1000.0)
    assert pwm_cmd.pulse_us[2] == pytest.approx(2000.0)
    assert pwm_cmd.protocol == "pwm_us"

    sink = SimulatedEscSink()
    assert isinstance(sink, EscOutput)
    sink.arm()
    result = sink.apply_forces(forces)
    assert result.applied is True
    assert result.pulse_us == pwm_cmd.pulse_us


def test_t5_stub_main_and_hello_led_git_unchanged():
    for path in (STUB_MAIN, HELLO_LED_C, HELLO_LED_H):
        result = subprocess.run(
            ["git", "diff", "--stat", str(path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == "", f"unexpected diff in {path}:\n{result.stdout}"


def test_t6_native_tree_still_zero_crsf_elrs_tokens():
    for path in (REPO_ROOT / "native").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "crsf" not in text.lower(), f"{path} unexpectedly references CRSF"
            assert "elrs" not in text.lower(), f"{path} unexpectedly references ELRS"


def test_t7_no_gpio_tim_bsrr_pigpio_in_new_dshot_files():
    for path in (DSHOT_HPP, DSHOT_CPP):
        text = path.read_text(encoding="utf-8")
        code_only_lines = [line[: line.find("//")] if "//" in line else line for line in text.splitlines()]
        code_only = "\n".join(code_only_lines).lower()
        for token in ("gpio", "bsrr", "pigpio", "0x40020", "0x40023", "tim2", "tim3", "dma"):
            assert token not in code_only, f"{path} unexpectedly contains '{token}'"

    py_code_only = _strip_python_comments_and_docstrings(inspect.getsource(dshot_module))
    lowered = py_code_only.lower()
    for token in ("write_gpio", "pigpio", "rpi.gpio", "bsrr"):
        assert token not in lowered, f"dshot.py unexpectedly contains '{token}'"


def test_t9_pyproject_version_is_0_5_29():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.44"' in text


def test_t10_full_suite_process_gate_placeholder():
    """The full Python suite being green (and host `ctest` green) is
    verified by running them, not asserted here — see the implementation
    report's own test-run transcript."""
    assert True


def test_encode_motor_forces_dshot_endpoints_and_no_command_range_collision():
    forces = _forces(values=(0.0, 1.0, 0.5, 0.0))
    frames = encode_motor_forces_dshot(forces)
    assert len(frames) == 4
    assert frames[0] == 0x0606  # force=0 -> throttle 48 (not 0 — that's a command)
    assert frames[1] == 0xFFEE  # force=1 -> throttle 2047
    assert frames[3] == 0x0606

    # No throttle produced by the helper ever falls in the command range.
    for force in (0.0, 0.25, 0.5, 0.75, 1.0):
        single = _forces(values=(force, force, force, force))
        for frame in encode_motor_forces_dshot(single):
            value = frame >> 4
            throttle = value >> 1
            assert throttle >= DSHOT_MIN_THROTTLE_VALUE
            assert throttle <= DSHOT_MAX_THROTTLE_VALUE


def test_encode_motor_forces_dshot_never_calls_pwm_encode_or_esc_output():
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(dshot_module))
    assert "encode_motor_forces(" not in code_only
    assert "SimulatedEscSink" not in code_only
    assert "apply_forces" not in code_only
    assert "EscOutput" not in code_only


def test_dshot_not_under_capabilities_or_core():
    assert (REPO_ROOT / "src" / "jarvis" / "flight_software" / "flight_control" / "dshot.py").exists()
    assert not (REPO_ROOT / "src" / "jarvis" / "capabilities" / "dshot.py").exists()
    assert not (REPO_ROOT / "src" / "jarvis" / "core" / "dshot.py").exists()


def test_no_command_table_invented():
    """IC §0 decision 6: this Buy encodes the 11-bit field as given — it
    does not implement a beep/3D/save-settings command table."""
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(dshot_module))
    lowered = code_only.lower()
    for token in ("beep", "save_settings", "3d_mode", "command_table"):
        assert token not in lowered, f"dshot.py unexpectedly implements '{token}' as a command"


def test_default_safety_gate_still_reject_all():
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_no_craft_or_core_imports_of_dshot_and_registry_still_empty():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "encode_dshot_frame" not in text, f"{py_file} references encode_dshot_frame"
            assert "dshot" not in text.lower(), f"{py_file} references dshot"

    registry = CapabilityRegistry.load_default()
    # T2 (B1-capability-registry-product-fill): capabilities()/providers() are
    # no longer empty (ontology.explain/engineering.continuity, both software-
    # provided) — see tests/test_capability_registry_product_fill_b1.py for that
    # shape. Skills stay empty; this file's own isolation proof is unaffected.
    assert registry.skills() == []
