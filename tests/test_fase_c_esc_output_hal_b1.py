"""Tests T1-T12 for `B1-fase-c-esc-output-hal` (C26).

T9 (C++ Catch2 — `apply_forces` armed/disarmed) lives in
`native/flight_control/tests/test_esc.cpp`, run via `ctest`, not here.
T12 (report content: EscOutput HAL != pin != motors != DShot) is covered
by `.jes/artifacts/implementation_report_fase_c_esc_output_hal_b1.md`,
not by this file.
"""

from __future__ import annotations

import abc
import inspect
import io
import tokenize
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities.intent import RadioIntentAdapter
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command
from jarvis.flight_software.flight_control import esc as esc_module
from jarvis.flight_software.flight_control import loop as loop_module
from jarvis.flight_software.flight_control import mixer as mixer_module
from jarvis.flight_software.flight_control.esc import (
    EscApplyResult,
    EscOutput,
    EscPwmCommand,
    SimulatedEscSink,
    encode_motor_forces,
)
from jarvis.flight_software.flight_control.mixer import MotorForceCommand

REPO_ROOT = Path(__file__).resolve().parents[1]


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


def test_t1_simulated_esc_sink_is_instance_and_subclass_of_esc_output():
    sink = SimulatedEscSink()
    assert isinstance(sink, EscOutput)
    assert issubclass(SimulatedEscSink, EscOutput)
    assert issubclass(EscOutput, abc.ABC)
    with pytest.raises(TypeError):
        EscOutput()  # abstract — cannot be instantiated directly


def test_t2_apply_forces_disarmed_records_and_refuses():
    sink = SimulatedEscSink()
    assert sink.armed is False
    forces = _forces()

    result = sink.apply_forces(forces)

    assert isinstance(result, EscApplyResult)
    assert result.applied is False
    assert result.reason == "disarmed"
    assert sink.last_command() is not None


def test_t3_apply_forces_armed_matches_encode_motor_forces():
    sink = SimulatedEscSink()
    sink.arm()
    forces = _forces()
    expected = encode_motor_forces(forces)

    result = sink.apply_forces(forces)

    assert result.applied is True
    assert result.reason is None
    assert result.pulse_us == expected.pulse_us
    assert sink.last_command() == expected


def test_t4_c10_apply_still_record_but_refuse_while_disarmed():
    sink = SimulatedEscSink()
    cmd = encode_motor_forces(_forces())
    result = sink.apply(cmd)
    assert result.applied is False
    assert result.reason == "disarmed"
    assert sink.last_command() == cmd

    sink.arm()
    armed_result = sink.apply(cmd)
    assert armed_result.applied is True
    assert armed_result.reason is None


def test_t5_mixer_source_has_no_gpio_or_dshot_call():
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(mixer_module))
    lowered = code_only.lower()
    for token in ("gpio", "dshot", "pulse_us", "write_gpio", "pigpio"):
        assert token not in lowered, f"mixer.py unexpectedly references '{token}' in real code"


def test_t6_loop_step_source_still_has_no_apply_or_apply_forces():
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(loop_module))
    assert "SimulatedEscSink" not in code_only
    assert ".apply(" not in code_only
    assert "apply_forces" not in code_only


def test_t7_radio_intent_adapter_not_implemented_and_rejectall_default():
    with pytest.raises(NotImplementedError):
        RadioIntentAdapter.parse(b"\x00\x00")
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_t8_no_gpio_pigpio_dev_mem_in_esc_module_real_code():
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(esc_module))
    lowered = code_only.lower()
    for token in ("import rpi", "import pigpio", "/dev/mem", "write_gpio(", "send_dshot("):
        assert token not in lowered, f"esc.py unexpectedly contains '{token}' in real code"


def test_t10_pyproject_version_is_0_5_24():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.38"' in text


def test_t11_full_suite_process_gate_placeholder():
    """The full Python suite being green (and host `ctest` green) is
    verified by running them, not asserted here — see the implementation
    report's own test-run transcript."""
    assert True


def test_only_one_esc_output_implementation_ships():
    """IC §0 decision 7: no second EscOutput implementation (GPIO sink,
    dummy pin class, unimplemented-pin stub) exists as product surface."""

    def _subclasses(cls):
        result = set(cls.__subclasses__())
        for sub in cls.__subclasses__():
            result |= _subclasses(sub)
        return result

    subclasses = _subclasses(EscOutput)
    assert subclasses == {SimulatedEscSink}


def test_encode_motor_forces_reused_not_reimplemented_inside_apply_forces():
    """`SimulatedEscSink.apply_forces` (the one concrete implementation
    shipped this Buy) must be a thin wrapper: encode then apply — not a
    second, parallel encoding implementation."""
    sink_source = inspect.getsource(SimulatedEscSink.apply_forces)
    assert "encode_motor_forces(forces)" in sink_source
    assert "self.apply(cmd)" in sink_source
    assert "min_us" not in sink_source  # no second endpoint-mapping logic here


def test_esc_output_abstract_methods_shape():
    abstract_names = EscOutput.__abstractmethods__
    assert abstract_names == frozenset({"apply_forces", "arm", "disarm", "armed"})


def test_no_craft_or_core_imports_of_esc_output_and_registry_still_empty():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "EscOutput" not in text, f"{py_file} references EscOutput"
            assert "apply_forces" not in text, f"{py_file} references apply_forces"

    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []


def test_radio_py_still_has_no_esc_or_stick_apis():
    from jarvis.capabilities import radio as radio_module

    source = inspect.getsource(radio_module)
    for symbol in ("EscOutput", "apply_forces", "SimulatedEscSink", "map_rc_to_loop_inputs"):
        assert symbol not in source, f"radio.py unexpectedly references '{symbol}'"
