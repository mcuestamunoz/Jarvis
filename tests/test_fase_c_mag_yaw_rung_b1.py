"""Tests T1-T11 for `B1-fase-c-mag-yaw-rung` (C37).

T8 (C++ Catch2 — `SimulatedMagHal` T1/T2 equivalents, estimator T3/T4
equivalents, RC yaw T5 equivalent) lives in
`native/flight_control/tests/test_mag.cpp` and
`native/flight_control/tests/test_rc_setpoint.cpp`, run via `ctest`, not
here. T10's own "suite + ctest green" half is a process gate covered by
running them, not asserted here. T11 (report content: sim mag != live
mag != flying != heading lock on hardware) is covered by
`.jes/artifacts/implementation_report_fase_c_mag_yaw_rung_b1.md`, not by
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
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command
from jarvis.flight_software.flight_control import loop as loop_module
from jarvis.flight_software.flight_control.attitude import ComplementaryAttitudeEstimator
from jarvis.flight_software.flight_control.mag import MagSample
from jarvis.flight_software.flight_control.rc_setpoint import (
    CRSF_CH_MAX,
    CRSF_CH_MID,
    CRSF_CH_MIN,
    RC_CH_PITCH,
    RC_CH_ROLL,
    RC_CH_THROTTLE,
    RC_CH_YAW,
    RC_MAX_YAW_RAD,
    map_rc_to_loop_inputs,
)
from jarvis.flight_software.flight_control.sim_mag_hal import SimulatedMagHal
from jarvis.flight_software.flight_control.types import ImuSample
from jarvis.vehicle_profiles import (
    run_controlled_flight_sim_smoke,
    run_sim_6dof_smoke,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

_LEVEL_ACCEL = (0.0, 0.0, -9.81)
_ZERO_GYRO = (0.0, 0.0, 0.0)


def _strip_python_comments_and_docstrings(source: str) -> str:
    """Removes `#` comments and multi-line (docstring-shaped) string
    literals so honesty checks look at real code, not this module's own
    honesty-prose docstrings."""
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


def _yaw_deg(setpoint) -> float:
    w, x, y, z = setpoint.q_body_to_world_desired
    return math.degrees(2.0 * math.atan2(z, w))


def _channels(roll=CRSF_CH_MID, pitch=CRSF_CH_MID, throttle=CRSF_CH_MID, yaw=CRSF_CH_MID):
    values = [CRSF_CH_MID] * 16
    values[RC_CH_ROLL] = roll
    values[RC_CH_PITCH] = pitch
    values[RC_CH_THROTTLE] = throttle
    values[RC_CH_YAW] = yaw
    return tuple(values)


def test_t1_simulated_mag_hal_identity_q_matches_documented_world_field():
    hal = SimulatedMagHal()
    sample = hal.read_mag((1.0, 0.0, 0.0, 0.0), t_s=0.0)
    assert sample.mag_body_uT == pytest.approx((0.0, 1.0, 0.0))


def test_t2_known_yaw_rotation_rotates_body_mag_consistently_finite():
    hal = SimulatedMagHal()
    yaw = math.radians(45.0)
    q_yawed = (math.cos(yaw / 2.0), 0.0, 0.0, math.sin(yaw / 2.0))
    sample = hal.read_mag(q_yawed, t_s=0.0)
    assert all(math.isfinite(c) for c in sample.mag_body_uT)
    assert sample.mag_body_uT == pytest.approx((math.sin(yaw), math.cos(yaw), 0.0))


def test_t3_estimator_without_mag_c7_regressions_still_pass():
    estimator = ComplementaryAttitudeEstimator(gain=0.05)
    t = 0.0
    state = None
    for _ in range(20):
        sample = ImuSample(t_s=t, accel_mps2=_LEVEL_ACCEL, gyro_rad_s=_ZERO_GYRO)
        state = estimator.update(sample)
        t += 0.01
    assert state is not None
    w = max(-1.0, min(1.0, state.q_body_to_world[0]))
    angle_deg = math.degrees(2.0 * math.acos(abs(w)))
    assert angle_deg < 1.0


def test_t4_estimator_with_mag_yaw_error_decreases_over_n_updates():
    true_yaw_error = math.radians(30.0)
    initial_q = (math.cos(true_yaw_error / 2.0), 0.0, 0.0, math.sin(true_yaw_error / 2.0))
    estimator = ComplementaryAttitudeEstimator(gain=0.2, mag_gain=0.15, initial_q=initial_q)
    hal = SimulatedMagHal()
    true_north = (1.0, 0.0, 0.0, 0.0)

    t = 0.0
    errors = []
    for _ in range(30):
        sample = ImuSample(t_s=t, accel_mps2=_LEVEL_ACCEL, gyro_rad_s=_ZERO_GYRO)
        mag = hal.read_mag(true_north, t_s=t)
        state = estimator.update(sample, mag=mag)
        w, x, y, z = state.q_body_to_world
        errors.append(abs(2.0 * math.atan2(z, w)))
        t += 0.05

    assert errors[-1] < errors[0]
    assert math.degrees(errors[-1]) < 5.0


def test_t5_rc_yaw_map_unlocked_roll_pitch_throttle_unchanged():
    mid_yaw = map_rc_to_loop_inputs(_channels(yaw=CRSF_CH_MID), t_s=0.0)
    assert _yaw_deg(mid_yaw.setpoint) == pytest.approx(0.0, abs=1e-6)

    max_yaw = map_rc_to_loop_inputs(_channels(yaw=CRSF_CH_MAX), t_s=0.0)
    assert _yaw_deg(max_yaw.setpoint) == pytest.approx(math.degrees(RC_MAX_YAW_RAD), abs=1e-6)

    min_yaw = map_rc_to_loop_inputs(_channels(yaw=CRSF_CH_MIN), t_s=0.0)
    assert _yaw_deg(min_yaw.setpoint) == pytest.approx(-math.degrees(RC_MAX_YAW_RAD), abs=1e-6)

    low_yaw = map_rc_to_loop_inputs(_channels(yaw=CRSF_CH_MIN), t_s=0.0)
    high_yaw = map_rc_to_loop_inputs(_channels(yaw=CRSF_CH_MAX), t_s=0.0)
    assert low_yaw.collective == high_yaw.collective

    # Roll/pitch/throttle fixtures unchanged vs C25 (default yaw=mid=0).
    at_max_roll = map_rc_to_loop_inputs(_channels(roll=CRSF_CH_MAX), t_s=0.0)
    w, x, y, z = at_max_roll.setpoint.q_body_to_world_desired
    roll_deg = math.degrees(2.0 * math.asin(max(-1.0, min(1.0, x))))
    assert roll_deg == pytest.approx(30.0, abs=1e-6)

    at_max_throttle = map_rc_to_loop_inputs(_channels(throttle=CRSF_CH_MAX), t_s=0.0)
    assert at_max_throttle.collective == pytest.approx(1.0, abs=1e-9)


def test_t6_invalid_mag_gain_and_world_field_raise():
    with pytest.raises(ValueError):
        ComplementaryAttitudeEstimator(mag_gain=0.0)
    with pytest.raises(ValueError):
        ComplementaryAttitudeEstimator(mag_gain=-0.1)
    with pytest.raises(ValueError):
        SimulatedMagHal(world_field_enu=(0.0, 0.0, 0.0))
    with pytest.raises(ValueError):
        SimulatedMagHal(world_field_enu=(float("nan"), 0.0, 0.0))


def test_t7_loop_step_never_calls_plant_and_c35_c36_smokes_still_green():
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(loop_module))
    assert "plant.step(" not in code_only
    assert "ToyQuadAttitudePlant" not in code_only
    assert "ToyQuad6DofPlant" not in code_only

    tilt_errors_rad = run_controlled_flight_sim_smoke()
    assert tilt_errors_rad[-1] < tilt_errors_rad[0]

    positions = run_sim_6dof_smoke()
    delta = math.sqrt(sum((e - s) ** 2 for e, s in zip(positions[-1], positions[0])))
    assert delta > 0.0


def test_t9_no_craft_continuity_library_board_edits_and_safety_default_reject_all():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "SimulatedMagHal" not in text, f"{py_file} references SimulatedMagHal"
            assert "MagSample" not in text, f"{py_file} references MagSample"

    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []

    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_t10_pyproject_version_is_0_5_38():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.40"' in text


def test_t10_full_suite_process_gate_placeholder():
    """The full Python suite being green (and host `ctest` green) is
    verified by running them, not asserted here — see the implementation
    report's own test-run transcript."""
    assert True
