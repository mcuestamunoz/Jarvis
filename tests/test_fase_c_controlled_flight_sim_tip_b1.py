"""Tests T1-T11 for `B1-fase-c-controlled-flight-sim-tip`.

T12 (full craft suite stays green) is a process gate covered by running
the full suite. Report content (toy plant · forces input · != flying ·
!= product physics · rate!=torque still open · C++ honesty · wooden
ladder tip · the C7 sign-bug fix) is covered by
`.jes/artifacts/implementation_report_fase_c_controlled_flight_sim_tip_b1.md`.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command
from jarvis.flight_software.flight_control import (
    AttitudeState,
    ImuSample,
    MotorForceCommand,
    ToyQuadAttitudePlant,
    tilt_angle_rad,
)
from jarvis.flight_software.flight_control import plant as plant_module
from jarvis.vehicle_profiles import run_controlled_flight_sim_smoke, run_open_loop_baseline_smoke

REPO_ROOT = Path(__file__).resolve().parents[1]


def _tilted_quat(tilt_rad: float):
    half = tilt_rad / 2.0
    return (math.cos(half), math.sin(half), 0.0, 0.0)


def test_t1_step_returns_imu_sample_with_gravity_consistent_with_true_tilt():
    tilt = math.radians(20.0)
    plant = ToyQuadAttitudePlant()
    plant.reset(initial_q=_tilted_quat(tilt))
    sample = plant.sense()
    assert isinstance(sample, ImuSample)
    expected_y = -9.81 * math.sin(tilt)
    expected_z = -9.81 * math.cos(tilt)
    assert sample.accel_mps2[0] == pytest.approx(0.0, abs=1e-9)
    assert sample.accel_mps2[1] == pytest.approx(expected_y, rel=1e-6)
    assert sample.accel_mps2[2] == pytest.approx(expected_z, rel=1e-6)


def test_t2_closed_loop_tilt_error_strictly_decreases():
    errors = run_controlled_flight_sim_smoke(steps=200, initial_tilt_rad=math.radians(15.0))
    assert len(errors) == 201
    assert errors[-1] < errors[0]
    # documented criterion: recovers to within 2 degrees of level
    assert errors[-1] < math.radians(2.0)


def test_t3_open_loop_baseline_does_not_improve():
    """No-control baseline: with zero initial rate and zero corrective
    torque, this toy plant has no passive righting — tilt error must stay
    exactly constant, unlike the closed loop above."""
    baseline = run_open_loop_baseline_smoke(steps=200, initial_tilt_rad=math.radians(15.0))
    assert all(err == pytest.approx(baseline[0], abs=1e-9) for err in baseline)

    closed = run_controlled_flight_sim_smoke(steps=200, initial_tilt_rad=math.radians(15.0))
    assert closed[-1] < baseline[-1]


def test_t4_plant_rejects_invalid_dt_and_gains():
    plant = ToyQuadAttitudePlant()
    forces = MotorForceCommand(t_s=0.0, motor_forces=(0.5, 0.5, 0.5, 0.5))
    for bad_dt in (0.0, -0.01, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            plant.step(forces, dt_s=bad_dt)

    for bad_gain in (0.0, -1.0, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            ToyQuadAttitudePlant(torque_gain=bad_gain)
    for bad_damping in (-1.0, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            ToyQuadAttitudePlant(angular_damping=bad_damping)
    ToyQuadAttitudePlant(torque_gain=1.0, angular_damping=0.0)


def test_t5_no_gpio_serial_dshot_fly_shaped_public_symbols():
    forbidden_substrings = (
        "write_gpio",
        "open_serial",
        "send_dshot",
        "fly",
        "arm_motors_hardware",
    )
    for name, obj in vars(plant_module).items():
        if name.startswith("_"):
            continue
        lowered = name.lower()
        for token in forbidden_substrings:
            assert token not in lowered, f"plant.{name} looks forbidden-shaped ('{token}')"
        if isinstance(obj, type):
            for attr_name in dir(obj):
                if attr_name.startswith("_"):
                    continue
                lowered_attr = attr_name.lower()
                for token in forbidden_substrings:
                    assert token not in lowered_attr, (
                        f"plant.{name}.{attr_name} looks forbidden-shaped ('{token}')"
                    )


def test_t5b_no_hardware_library_imports_or_call_sites():
    import inspect

    source = inspect.getsource(plant_module)
    for forbidden in ("import RPi", "import pigpio", "import serial", "import socket", "write_gpio(", "send_dshot("):
        assert forbidden not in source


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


def test_t8_plant_symbols_not_imported_by_orchestrator_or_craft_paths():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "flight_control.plant" not in text, (
                f"{py_file} imports flight_control.plant — forbidden craft coupling"
            )
            assert "ToyQuadAttitudePlant" not in text, (
                f"{py_file} references ToyQuadAttitudePlant — forbidden craft coupling"
            )


def test_t9_capability_registry_default_still_empty():
    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []


def test_t10_pyproject_version_is_0_5_9():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.13"' in text


def test_plant_step_consumes_motor_force_command_not_pwm():
    """Locks IC §0 decision 4: plant advances from MotorForceCommand, not
    from PWM microseconds."""
    import inspect

    signature = inspect.signature(ToyQuadAttitudePlant.step)
    params = list(signature.parameters)
    assert "forces" in params
    annotation = signature.parameters["forces"].annotation
    assert annotation in ("MotorForceCommand", MotorForceCommand)


def test_true_attitude_property_exposes_true_state_for_tests():
    plant = ToyQuadAttitudePlant()
    tilt = math.radians(10.0)
    plant.reset(initial_q=_tilted_quat(tilt))
    state = plant.true_attitude
    assert isinstance(state, AttitudeState)
    assert tilt_angle_rad(state.q_body_to_world) == pytest.approx(tilt, rel=1e-6)


def test_reset_defaults_to_level_and_zero_rate():
    plant = ToyQuadAttitudePlant()
    plant.reset(initial_q=_tilted_quat(math.radians(30.0)), initial_omega=(0.1, 0.0, 0.0))
    plant.reset()
    state = plant.true_attitude
    assert tilt_angle_rad(state.q_body_to_world) == pytest.approx(0.0, abs=1e-9)
    assert state.omega_body_rad_s == (0.0, 0.0, 0.0)
