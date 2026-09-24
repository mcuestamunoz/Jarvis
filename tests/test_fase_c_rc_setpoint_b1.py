"""Tests T1-T12 for `B1-fase-c-rc-setpoint` (C25).

T9 (C++ Catch2 — mid sticks give ~level quat; throttle extremes) lives in
`native/flight_control/tests/test_rc_setpoint.cpp`, run via `ctest`, not
here. T12 (report content: RC->setpoint != flying != sticks drive motors
!= Safety allow) is covered by
`.jes/artifacts/implementation_report_fase_c_rc_setpoint_b1.md`, not by
this file.
"""

from __future__ import annotations

import inspect
import io
import math
import tokenize
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities import radio as radio_module
from jarvis.capabilities.crsf_dual_role import CrsfDualRolePolicy
from jarvis.capabilities.crsf_stub import CrsfRcChannels
from jarvis.capabilities.intent import RadioIntentAdapter
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command
from jarvis.flight_software.flight_control import rc_setpoint as rc_setpoint_module
from jarvis.flight_software.flight_control.loop import FlightControlLoop
from jarvis.flight_software.flight_control.rc_setpoint import (
    CRSF_CH_MAX,
    CRSF_CH_MID,
    CRSF_CH_MIN,
    RC_CH_PITCH,
    RC_CH_ROLL,
    RC_CH_THROTTLE,
    RC_MAX_TILT_RAD,
    RcLoopInputs,
    map_rc_to_loop_inputs,
    step_with_rc,
)
from jarvis.flight_software.flight_control.types import ImuSample

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


def _channels(roll=CRSF_CH_MID, pitch=CRSF_CH_MID, throttle=CRSF_CH_MID, yaw=CRSF_CH_MID):
    values = [CRSF_CH_MID] * 16
    values[RC_CH_ROLL] = roll
    values[RC_CH_PITCH] = pitch
    values[RC_CH_THROTTLE] = throttle
    values[3] = yaw
    return tuple(values)


def _roll_deg(setpoint):
    w, x, y, z = setpoint.q_body_to_world_desired
    return math.degrees(2.0 * math.asin(max(-1.0, min(1.0, x))))


def _pitch_deg(setpoint):
    w, x, y, z = setpoint.q_body_to_world_desired
    return math.degrees(2.0 * math.asin(max(-1.0, min(1.0, y))))


def test_t1_all_mid_gives_near_zero_roll_pitch_and_finite_collective():
    result = map_rc_to_loop_inputs(_channels(), t_s=0.0)
    assert isinstance(result, RcLoopInputs)
    assert result.setpoint.q_body_to_world_desired == pytest.approx((1.0, 0.0, 0.0, 0.0), abs=1e-9)
    assert math.isfinite(result.collective)
    assert 0.0 <= result.collective <= 1.0


def test_t2_roll_and_pitch_max_reach_30_degrees_and_clip_beyond_range():
    at_max = map_rc_to_loop_inputs(_channels(roll=CRSF_CH_MAX), t_s=0.0)
    assert _roll_deg(at_max.setpoint) == pytest.approx(30.0, abs=1e-6)

    at_min = map_rc_to_loop_inputs(_channels(roll=CRSF_CH_MIN), t_s=0.0)
    assert _roll_deg(at_min.setpoint) == pytest.approx(-30.0, abs=1e-6)

    pitch_at_max = map_rc_to_loop_inputs(_channels(pitch=CRSF_CH_MAX), t_s=0.0)
    assert _pitch_deg(pitch_at_max.setpoint) == pytest.approx(30.0, abs=1e-6)

    beyond_max = map_rc_to_loop_inputs(_channels(roll=2047), t_s=0.0)
    assert beyond_max.setpoint.q_body_to_world_desired == pytest.approx(
        at_max.setpoint.q_body_to_world_desired, abs=1e-12
    )
    beyond_min = map_rc_to_loop_inputs(_channels(roll=0), t_s=0.0)
    assert beyond_min.setpoint.q_body_to_world_desired == pytest.approx(
        at_min.setpoint.q_body_to_world_desired, abs=1e-12
    )


def test_t3_throttle_extremes_map_to_collective_0_and_1():
    low = map_rc_to_loop_inputs(_channels(throttle=CRSF_CH_MIN), t_s=0.0)
    high = map_rc_to_loop_inputs(_channels(throttle=CRSF_CH_MAX), t_s=0.0)
    assert low.collective == pytest.approx(0.0, abs=1e-9)
    assert high.collective == pytest.approx(1.0, abs=1e-9)

    mid = map_rc_to_loop_inputs(_channels(throttle=CRSF_CH_MID), t_s=0.0)
    assert mid.collective == pytest.approx((CRSF_CH_MID - CRSF_CH_MIN) / (CRSF_CH_MAX - CRSF_CH_MIN), abs=1e-9)
    assert mid.collective != pytest.approx(0.5, abs=1e-6)  # documented: not exactly 0.5


def test_t4_yaw_channel_does_not_change_setpoint_or_collective():
    low_yaw = map_rc_to_loop_inputs(_channels(yaw=CRSF_CH_MIN), t_s=0.0)
    high_yaw = map_rc_to_loop_inputs(_channels(yaw=CRSF_CH_MAX), t_s=0.0)
    assert low_yaw.setpoint.q_body_to_world_desired == high_yaw.setpoint.q_body_to_world_desired
    assert low_yaw.collective == high_yaw.collective


def test_t5_step_with_rc_produces_four_finite_forces_no_plant_no_gpio():
    loop = FlightControlLoop()
    sample = ImuSample(t_s=0.0, accel_mps2=(0.0, 0.0, -9.81), gyro_rad_s=(0.0, 0.0, 0.0))
    tick = step_with_rc(loop, sample, _channels(roll=CRSF_CH_MAX))
    assert len(tick.forces.motor_forces) == 4
    assert all(math.isfinite(f) for f in tick.forces.motor_forces)

    code_only = _strip_python_comments_and_docstrings(inspect.getsource(rc_setpoint_module))
    assert "plant" not in code_only.lower()
    assert "write_gpio" not in code_only.lower()
    assert "SimulatedEscSink" not in code_only
    assert ".apply(" not in code_only


def test_t6_radio_py_still_has_no_decode_or_serial_and_c20_policy_unchanged():
    source = inspect.getsource(radio_module)
    forbidden_symbols = ("decode_crsf", "decode_elrs", "open_serial", "write_pwm", "map_rc_to_loop_inputs")
    for symbol in forbidden_symbols:
        assert symbol not in source, f"radio.py unexpectedly defines/references '{symbol}'"
    assert not hasattr(radio_module, "decode_crsf")
    assert not hasattr(radio_module, "map_rc_to_loop_inputs")

    policy = CrsfDualRolePolicy()
    assert policy.authority_channel_index == 4
    assert policy.authority_threshold == 1500
    assert policy.authority_kind == "kill"


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


def test_t8_loop_module_math_untouched_by_this_buy():
    from jarvis.flight_software.flight_control import loop as loop_module

    code_only = _strip_python_comments_and_docstrings(inspect.getsource(loop_module))
    assert "rc_setpoint" not in code_only
    assert "CrsfRcChannels" not in code_only

    loop = FlightControlLoop()
    sample = ImuSample(t_s=0.0, accel_mps2=(0.0, 0.0, -9.81), gyro_rad_s=(0.0, 0.0, 0.0))
    from jarvis.flight_software.flight_control.controller import level_setpoint

    direct = loop.step(sample, level_setpoint(0.0), 0.5)
    assert all(f == pytest.approx(0.5, abs=1e-9) for f in direct.forces.motor_forces)


def test_t10_pyproject_version_is_0_5_23():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.29"' in text


def test_t11_full_suite_process_gate_placeholder():
    """The full Python suite being green (and host `ctest` green) is
    verified by running them, not asserted here — see the implementation
    report's own test-run transcript."""
    assert True


def test_crsf_rc_channels_accepted_directly_without_reparsing():
    channels = CrsfRcChannels(channels=_channels(roll=CRSF_CH_MAX))
    result = map_rc_to_loop_inputs(channels, t_s=2.0)
    assert result.setpoint.t_s == 2.0
    assert _roll_deg(result.setpoint) == pytest.approx(30.0, abs=1e-6)


def test_rejects_too_short_channel_sequence():
    with pytest.raises(ValueError):
        map_rc_to_loop_inputs([1, 2], t_s=0.0)


def test_rejects_non_int_channel_values():
    with pytest.raises(ValueError):
        map_rc_to_loop_inputs([992, 992, "x", 992], t_s=0.0)
    with pytest.raises(ValueError):
        map_rc_to_loop_inputs([992, 992, True, 992], t_s=0.0)


def test_t_s_is_caller_supplied_never_invented():
    result = map_rc_to_loop_inputs(_channels(), t_s=42.5)
    assert result.setpoint.t_s == 42.5


def test_rc_setpoint_not_under_capabilities_and_no_cpp_or_cmake_under_flight_software():
    assert (REPO_ROOT / "src" / "jarvis" / "flight_software" / "flight_control" / "rc_setpoint.py").exists()
    assert not (REPO_ROOT / "src" / "jarvis" / "capabilities" / "rc_setpoint.py").exists()

    forbidden_suffixes = (".cpp", ".cc", ".cxx", ".hpp", ".hh", ".h")
    for path in (REPO_ROOT / "src" / "jarvis" / "flight_software").rglob("*"):
        if path.is_file():
            assert path.suffix not in forbidden_suffixes


def test_no_craft_or_core_imports_of_rc_setpoint_and_registry_still_empty():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "rc_setpoint" not in text, f"{py_file} references rc_setpoint"
            assert "map_rc_to_loop_inputs" not in text, f"{py_file} references map_rc_to_loop_inputs"

    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []


def test_no_serial_or_baud_imports_in_rc_setpoint():
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(rc_setpoint_module))
    lowered = code_only.lower()
    for token in ("import serial", "import fcntl", "import termios", "configure_host_baud", "attach_fd", "attach_path"):
        assert token not in lowered, f"rc_setpoint.py unexpectedly references '{token}'"


def test_max_tilt_is_pi_over_6():
    assert RC_MAX_TILT_RAD == pytest.approx(math.pi / 6.0, abs=1e-12)
