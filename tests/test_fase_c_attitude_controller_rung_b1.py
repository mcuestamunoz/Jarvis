"""Tests T1-T10 for `B1-fase-c-attitude-controller-rung`.

T11 (full craft suite stays green) and T12 (report confirms PD-only +
rate cmd != motors + C++ honesty + "!= controlled flight") are process
gates covered by running the full suite and by
`.jes/artifacts/implementation_report_fase_c_attitude_controller_rung_b1.md`.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command
from jarvis.flight_software.flight_control import (
    AttitudeSetpoint,
    AttitudeState,
    BodyRateCommand,
    PdAttitudeController,
    level_setpoint,
)
from jarvis.flight_software.flight_control import controller as controller_module
from jarvis.vehicle_profiles import run_attitude_controller_smoke

REPO_ROOT = Path(__file__).resolve().parents[1]

_IDENTITY_Q = (1.0, 0.0, 0.0, 0.0)
_ZERO_RATE = (0.0, 0.0, 0.0)


def _level_state(t_s: float = 0.0) -> AttitudeState:
    return AttitudeState(t_s=t_s, q_body_to_world=_IDENTITY_Q, omega_body_rad_s=_ZERO_RATE, frame="enu")


def test_t1_level_setpoint_and_level_state_gives_near_zero_command():
    controller = PdAttitudeController()
    setpoint = level_setpoint(0.0)
    state = _level_state()
    command = controller.compute(setpoint, state)
    assert isinstance(command, BodyRateCommand)
    assert command.omega_body_rad_s == (0.0, 0.0, 0.0)


def test_t2_small_roll_tilt_produces_corrective_sign_on_expected_axis():
    controller = PdAttitudeController(kp=6.0, kd=0.6)
    setpoint = level_setpoint(0.0)

    half = 0.05
    tilted_q = (math.cos(half), math.sin(half), 0.0, 0.0)
    tilted_state = AttitudeState(
        t_s=0.0, q_body_to_world=tilted_q, omega_body_rad_s=_ZERO_RATE, frame="enu"
    )
    command = controller.compute(setpoint, tilted_state)

    assert command.omega_body_rad_s[0] < 0.0
    assert abs(command.omega_body_rad_s[1]) < 1e-9
    assert abs(command.omega_body_rad_s[2]) < 1e-9


def test_t2b_derivative_term_damps_existing_body_rate():
    controller = PdAttitudeController(kp=6.0, kd=0.6)
    setpoint = level_setpoint(0.0)
    spinning_state = AttitudeState(
        t_s=0.0, q_body_to_world=_IDENTITY_Q, omega_body_rad_s=(1.0, 0.0, 0.0), frame="enu"
    )
    command = controller.compute(setpoint, spinning_state)
    assert command.omega_body_rad_s[0] == pytest.approx(-0.6)


def test_t3_invalid_gains_rejected():
    for bad_kp in (0.0, -1.0, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            PdAttitudeController(kp=bad_kp)
    for bad_kd in (-0.1, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            PdAttitudeController(kd=bad_kd)
    PdAttitudeController(kp=1.0, kd=0.0)


def test_t4_body_rate_command_has_no_motor_pwm_thrust_fields():
    controller = PdAttitudeController()
    command = controller.compute(level_setpoint(0.0), _level_state())
    assert isinstance(command, BodyRateCommand)
    assert set(type(command).model_fields) == {"t_s", "omega_body_rad_s", "notes"}


def test_t5_no_mixer_or_esc_shaped_public_symbols_in_controller_module():
    forbidden_substrings = ("mix", "allocate", "set_pwm", "write_motor", "command_esc", "compute_thrusts")
    for name, obj in vars(controller_module).items():
        if name.startswith("_"):
            continue
        lowered = name.lower()
        for token in forbidden_substrings:
            assert token not in lowered, f"controller.{name} looks forbidden-shaped ('{token}')"
        if isinstance(obj, type):
            for attr_name in dir(obj):
                if attr_name.startswith("_"):
                    continue
                lowered_attr = attr_name.lower()
                for token in forbidden_substrings:
                    assert token not in lowered_attr, (
                        f"controller.{name}.{attr_name} looks forbidden-shaped ('{token}')"
                    )


def test_t6_no_cpp_or_cmake_under_flight_software():
    forbidden_suffixes = (".cpp", ".cc", ".cxx", ".hpp", ".hh", ".h")
    for package_dir in (
        REPO_ROOT / "src" / "jarvis" / "flight_software",
        REPO_ROOT / "src" / "jarvis" / "vehicle_profiles",
    ):
        for path in package_dir.rglob("*"):
            if not path.is_file():
                continue
            assert path.suffix not in forbidden_suffixes, f"C++ source found: {path}"
            assert path.name != "CMakeLists.txt", f"CMake tree found: {path}"


def test_t7_default_safety_and_autonomy_submit_still_reject():
    assert isinstance(default_safety_gate(), RejectAllSafetyGate)
    assert default_safety_gate().evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_t8_controller_symbols_not_imported_by_orchestrator_or_craft_paths():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "flight_control.controller" not in text, (
                f"{py_file} imports flight_control.controller — forbidden craft coupling"
            )
            assert "PdAttitudeController" not in text, (
                f"{py_file} references PdAttitudeController — forbidden craft coupling"
            )


def test_t9_capability_registry_default_still_empty():
    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []


def test_t10_pyproject_version_is_0_5_6():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.29"' in text


def test_smoke_controller_returns_at_least_one_command():
    commands = run_attitude_controller_smoke(samples=3)
    assert len(commands) == 3
    assert all(isinstance(c, BodyRateCommand) for c in commands)


def test_attitude_setpoint_rejects_unknown_extra_field():
    with pytest.raises(Exception):
        AttitudeSetpoint(t_s=0.0, q_body_to_world_desired=_IDENTITY_Q, unexpected="x")


def test_reset_is_a_harmless_noop():
    controller = PdAttitudeController()
    before = controller.compute(level_setpoint(0.0), _level_state())
    controller.reset()
    after = controller.compute(level_setpoint(0.0), _level_state())
    assert before == after


def test_determinism_same_inputs_give_identical_command():
    controller_a = PdAttitudeController(kp=4.0, kd=0.4)
    controller_b = PdAttitudeController(kp=4.0, kd=0.4)
    half = 0.03
    tilted_q = (math.cos(half), 0.0, math.sin(half), 0.0)
    state = AttitudeState(t_s=1.0, q_body_to_world=tilted_q, omega_body_rad_s=(0.0, 0.1, 0.0), frame="enu")
    setpoint = level_setpoint(1.0)
    assert controller_a.compute(setpoint, state) == controller_b.compute(setpoint, state)


def test_no_autonomy_submit_call_from_controller_module():
    """The module docstring is allowed to mention `submit_command` in prose
    (documenting that it's never called) — this checks there is no actual
    call site or import of it."""
    import inspect

    source = inspect.getsource(controller_module)
    assert "submit_command(" not in source
    assert "from jarvis.flight_software.autonomy" not in source
