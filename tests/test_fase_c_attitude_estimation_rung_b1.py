"""Tests T1-T10 for `B1-fase-c-attitude-estimation-rung`.

T11 (full craft suite stays green) and T12 (report confirms
complementary-only + no mag/GPS/bias learning + C++ honesty + "!=
flight-verified") are process gates covered by running the full suite
and by
`.jes/artifacts/implementation_report_fase_c_attitude_estimation_rung_b1.md`.
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
    ComplementaryAttitudeEstimator,
    ImuLowPassFilter,
    SimulatedImuHal,
)
from jarvis.flight_software.flight_control import attitude as attitude_module
from jarvis.flight_software.flight_control.types import ImuSample
from jarvis.vehicle_profiles import run_hal_imu_attitude_smoke

REPO_ROOT = Path(__file__).resolve().parents[1]

_LEVEL_ACCEL = (0.0, 0.0, -9.81)
_ZERO_GYRO = (0.0, 0.0, 0.0)


def _quat_angle_from_identity(q):
    w = max(-1.0, min(1.0, q[0]))
    return 2.0 * math.acos(abs(w))


def test_t1_static_stream_stays_near_level():
    estimator = ComplementaryAttitudeEstimator(gain=0.05)
    t = 0.0
    state = None
    for _ in range(20):
        sample = ImuSample(t_s=t, accel_mps2=_LEVEL_ACCEL, gyro_rad_s=_ZERO_GYRO)
        state = estimator.update(sample)
        t += 0.01
    assert state is not None
    angle = _quat_angle_from_identity(state.q_body_to_world)
    assert angle < math.radians(1.0)


def test_t1b_near_static_with_noise_stays_near_level():
    estimator = ComplementaryAttitudeEstimator(gain=0.05)
    t = 0.0
    state = None
    for _ in range(20):
        sample = ImuSample(
            t_s=t, accel_mps2=(0.01, -0.02, -9.81), gyro_rad_s=(0.001, -0.001, 0.0005)
        )
        state = estimator.update(sample)
        t += 0.01
    assert state is not None
    angle = _quat_angle_from_identity(state.q_body_to_world)
    assert angle < math.radians(1.0)


def test_t2_determinism_same_seed_alpha_gain_reset():
    def run():
        hal = SimulatedImuHal(seed=9)
        filt = ImuLowPassFilter(alpha=0.2)
        estimator = ComplementaryAttitudeEstimator(gain=0.03)
        return [estimator.update(filt.filter_sample(hal.read_imu())) for _ in range(10)]

    sequence_a = run()
    sequence_b = run()
    assert sequence_a == sequence_b


def test_t3_invalid_gain_rejected():
    for bad_gain in (0.0, -0.1, 1.1, 2.0):
        with pytest.raises(ValueError):
            ComplementaryAttitudeEstimator(gain=bad_gain)
    ComplementaryAttitudeEstimator(gain=1.0)


def test_t4_attitude_state_has_no_actuator_position_velocity_fields():
    estimator = ComplementaryAttitudeEstimator()
    state = estimator.update(ImuSample(t_s=0.0, accel_mps2=_LEVEL_ACCEL, gyro_rad_s=_ZERO_GYRO))
    assert isinstance(state, AttitudeState)
    assert set(type(state).model_fields) == {
        "t_s",
        "q_body_to_world",
        "omega_body_rad_s",
        "frame",
    }
    assert state.frame == "enu"


def test_t5_no_second_estimator_or_navigation_shaped_public_symbols():
    forbidden_substrings = (
        "run_madgwick",
        "run_ekf",
        "run_ukf",
        "run_mahony",
        "update_gps",
        "update_mag",
        "estimate_position",
        "estimate_velocity",
        "mix",
        "set_pwm",
        "write_motor",
    )
    for name, obj in vars(attitude_module).items():
        if name.startswith("_"):
            continue
        lowered = name.lower()
        for token in forbidden_substrings:
            assert token not in lowered, f"attitude.{name} looks forbidden-shaped ('{token}')"
        if isinstance(obj, type):
            for attr_name in dir(obj):
                if attr_name.startswith("_"):
                    continue
                lowered_attr = attr_name.lower()
                for token in forbidden_substrings:
                    assert token not in lowered_attr, (
                        f"attitude.{name}.{attr_name} looks forbidden-shaped ('{token}')"
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


def test_t8_attitude_symbols_not_imported_by_orchestrator_or_craft_paths():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "flight_control.attitude" not in text, (
                f"{py_file} imports flight_control.attitude — forbidden craft coupling"
            )
            assert "ComplementaryAttitudeEstimator" not in text, (
                f"{py_file} references ComplementaryAttitudeEstimator — forbidden craft coupling"
            )


def test_t9_capability_registry_default_still_empty():
    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []


def test_t10_pyproject_version_is_0_5_5():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.14"' in text


def test_smoke_attitude_returns_at_least_one_state():
    states = run_hal_imu_attitude_smoke(samples=3)
    assert len(states) == 3
    assert all(isinstance(s, AttitudeState) for s in states)
    assert all(s.frame == "enu" for s in states)


def test_yaw_only_rotation_preserves_roll_pitch_when_level():
    estimator = ComplementaryAttitudeEstimator(gain=0.05)
    t = 0.0
    state = None
    for _ in range(50):
        sample = ImuSample(t_s=t, accel_mps2=_LEVEL_ACCEL, gyro_rad_s=(0.0, 0.0, 0.1))
        state = estimator.update(sample)
        t += 0.01
    assert state is not None
    w, x, y, z = state.q_body_to_world
    assert abs(x) < 1e-9
    assert abs(y) < 1e-9
    assert abs(z) > 0.0


def test_reset_reseeds_at_initial_quaternion():
    estimator = ComplementaryAttitudeEstimator(gain=0.05)
    t = 0.0
    for _ in range(10):
        estimator.update(ImuSample(t_s=t, accel_mps2=_LEVEL_ACCEL, gyro_rad_s=(0.0, 0.0, 0.2)))
        t += 0.01
    estimator.reset()
    seeded = estimator.update(ImuSample(t_s=0.0, accel_mps2=_LEVEL_ACCEL, gyro_rad_s=_ZERO_GYRO))
    assert seeded.q_body_to_world == (1.0, 0.0, 0.0, 0.0)


def test_zero_accel_norm_skips_correction_without_crashing():
    estimator = ComplementaryAttitudeEstimator(gain=0.05)
    estimator.update(ImuSample(t_s=0.0, accel_mps2=(0.0, 0.0, 0.0), gyro_rad_s=_ZERO_GYRO))
    state = estimator.update(ImuSample(t_s=0.01, accel_mps2=(0.0, 0.0, 0.0), gyro_rad_s=(0.1, 0.0, 0.0)))
    assert isinstance(state, AttitudeState)


def test_accel_correction_converges_toward_true_tilt_not_away_from_it():
    """Regression for a C11-discovered sign bug: with zero gyro and a
    constant *non-level* accel reading (a fixed true tilt about X), the
    estimator's own correction must converge the `x` component of
    `q_body_to_world` toward the SAME sign as the true tilt — not the
    opposite sign. Every pre-existing C7 test only fed already-level accel
    (correction trivially zero), so this never got exercised until C11's
    closed-loop tip tried to use a genuinely tilted reading."""
    true_tilt_rad = math.radians(5.0)
    half = true_tilt_rad / 2.0
    # Accel a stationary IMU would read at this fixed +X tilt (gravity
    # rotated into body frame by the *inverse* of the tilt — same
    # convention SimulatedImuHal/ToyQuadAttitudePlant use elsewhere).
    accel_at_tilt = (
        0.0,
        -9.81 * math.sin(true_tilt_rad),
        -9.81 * math.cos(true_tilt_rad),
    )

    estimator = ComplementaryAttitudeEstimator(gain=0.1)
    state = None
    t = 0.0
    for _ in range(200):
        state = estimator.update(ImuSample(t_s=t, accel_mps2=accel_at_tilt, gyro_rad_s=_ZERO_GYRO))
        t += 0.01

    assert state is not None
    w, x, y, z = state.q_body_to_world
    # True tilt has a positive x-component (cos(half), +sin(half), 0, 0);
    # the estimate must land on the same side, not the antipodal one.
    assert x > 0.0, f"estimator converged with x={x} — wrong sign, diverged from true tilt"
    assert abs(y) < 1e-9
    assert abs(z) < 1e-9
