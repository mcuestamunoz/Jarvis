"""Tests T1-T13 for `B1-fase-c-sim-6dof-plant` (C36).

T9 (C++ Catch2 — `ToyQuad6DofPlant` T1/T3 equivalents) lives in
`native/flight_control/tests/test_plant.cpp`, run via `ctest`, not here.
T12 (full suite + host `ctest` green) is a process gate covered by
running them, not asserted here. T13 (report content: 6-DoF toy != flying
!= product physics != altitude hold != specific-force IMU) is covered by
`.jes/artifacts/implementation_report_fase_c_sim_6dof_plant_b1.md`, not
by this file.
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
from jarvis.flight_software.flight_control.mixer import MotorForceCommand
from jarvis.flight_software.flight_control.plant import ToyQuad6DofPlant, ToyQuadAttitudePlant, tilt_angle_rad
from jarvis.vehicle_profiles import run_controlled_flight_sim_smoke, run_sim_6dof_smoke

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


def _pitch_tilted_quat(tilt_rad: float):
    """Rotation about the Y ("pitch") axis — matches this plant's own
    torque-proxy convention. Distinct from the C11 smokes' own X ("roll")
    tilt helper; either is a valid non-level start."""
    half = tilt_rad / 2.0
    return (math.cos(half), 0.0, math.sin(half), 0.0)


def test_t1_sense_at_rest_is_level_gravity_in_body_zero_gyro():
    plant = ToyQuad6DofPlant()
    sample = plant.sense()
    assert sample.accel_mps2 == pytest.approx((0.0, 0.0, -9.81))
    assert sample.gyro_rad_s == pytest.approx((0.0, 0.0, 0.0))
    assert plant.true_position_m == (0.0, 0.0, 0.0)
    assert plant.true_velocity_mps == (0.0, 0.0, 0.0)


def test_t2_zero_forces_small_dt_position_stays_near_origin_attitude_stays_level():
    plant = ToyQuad6DofPlant()
    zero_forces = MotorForceCommand(t_s=0.0, motor_forces=(0.0, 0.0, 0.0, 0.0))
    sample = plant.step(zero_forces, dt_s=0.001)

    for value in plant.true_position_m:
        assert math.isfinite(value)
        assert abs(value) < 1e-3
    assert plant.true_attitude.q_body_to_world == pytest.approx((1.0, 0.0, 0.0, 0.0))
    assert math.isfinite(sample.accel_mps2[2])


def test_t3_level_high_collective_altitude_increases():
    plant = ToyQuad6DofPlant()  # mass_kg=1, thrust_gain=20 documented toy defaults
    full_forces = MotorForceCommand(t_s=0.0, motor_forces=(1.0, 1.0, 1.0, 1.0))  # sum=4 -> thrust=80N

    for _ in range(50):
        plant.step(full_forces, dt_s=0.01)

    assert plant.true_position_m[2] > 0.0
    assert plant.true_velocity_mps[2] > 0.0
    assert plant.true_position_m[0] == pytest.approx(0.0)
    assert plant.true_position_m[1] == pytest.approx(0.0)


def test_t4_pitch_tilted_symmetric_thrust_horizontal_displacement_in_derived_direction():
    """Symmetric forces produce zero roll/pitch/yaw proxy, so the
    attitude stays pinned exactly at the initial tilt for the whole run.
    Hand-derived: rotating body +Z thrust by a positive pitch-axis
    quaternion (cos(t/2), 0, sin(t/2), 0) yields world (sin(t)*T, 0,
    cos(t)*T) — a positive tilt must give strictly positive world-X
    displacement and exactly zero world-Y displacement."""
    plant = ToyQuad6DofPlant()
    initial_q = _pitch_tilted_quat(0.1)
    plant.reset(initial_q=initial_q)
    full_forces = MotorForceCommand(t_s=0.0, motor_forces=(1.0, 1.0, 1.0, 1.0))

    for _ in range(20):
        plant.step(full_forces, dt_s=0.01)

    assert plant.true_position_m[0] > 0.0
    assert plant.true_position_m[1] == pytest.approx(0.0, abs=1e-9)
    assert plant.true_attitude.q_body_to_world == pytest.approx(initial_q)


def test_t5_true_position_and_velocity_change_only_via_step_not_sense():
    plant = ToyQuad6DofPlant()
    full_forces = MotorForceCommand(t_s=0.0, motor_forces=(1.0, 1.0, 1.0, 1.0))
    plant.step(full_forces, dt_s=0.01)
    position_after_step = plant.true_position_m
    velocity_after_step = plant.true_velocity_mps

    plant.sense()

    assert plant.true_position_m == position_after_step
    assert plant.true_velocity_mps == velocity_after_step


def test_t6_invalid_constructor_and_step_arguments_raise():
    with pytest.raises(ValueError):
        ToyQuad6DofPlant(mass_kg=0.0)
    with pytest.raises(ValueError):
        ToyQuad6DofPlant(mass_kg=-1.0)
    with pytest.raises(ValueError):
        ToyQuad6DofPlant(thrust_gain=0.0)
    with pytest.raises(ValueError):
        ToyQuad6DofPlant(thrust_gain=-1.0)
    with pytest.raises(ValueError):
        ToyQuad6DofPlant(torque_gain=0.0)
    with pytest.raises(ValueError):
        ToyQuad6DofPlant(angular_damping=-0.1)

    plant = ToyQuad6DofPlant()
    zero_forces = MotorForceCommand(t_s=0.0, motor_forces=(0.0, 0.0, 0.0, 0.0))
    with pytest.raises(ValueError):
        plant.step(zero_forces, dt_s=0.0)
    with pytest.raises(ValueError):
        plant.step(zero_forces, dt_s=-0.01)


def test_t7_c11_attitude_plant_recovery_smoke_still_passes():
    """ToyQuadAttitudePlant (C11) is byte-unchanged by this Buy — its own
    closed-loop tilt-recovery smoke must still strictly decrease and stay
    finite, exactly as it did before ToyQuad6DofPlant existed."""
    tilt_errors_rad = run_controlled_flight_sim_smoke()
    assert tilt_errors_rad[-1] < tilt_errors_rad[0]
    assert all(math.isfinite(v) for v in tilt_errors_rad)
    assert math.degrees(tilt_errors_rad[-1]) < 2.0


def test_t8_loop_step_source_still_never_calls_any_plant():
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(loop_module))
    assert "plant.step(" not in code_only
    assert "ToyQuadAttitudePlant" not in code_only
    assert "ToyQuad6DofPlant" not in code_only


def test_t10_smoke_helper_shows_pose_moves():
    positions = run_sim_6dof_smoke()
    start = positions[0]
    end = positions[-1]
    delta = math.sqrt(sum((e - s) ** 2 for e, s in zip(end, start)))
    assert delta > 0.0
    assert all(math.isfinite(c) for c in end)


def test_t11_no_craft_continuity_library_board_edits_and_safety_default_reject_all():
    """T20 (`B1-assistant-chat-sim-copper`) deliberately and explicitly
    constructs `ToyQuad6DofPlant` inside `core/orchestrator.py` (to back
    the lazy `SimAutonomyExecutor` for the chat sim-copper bridge) —
    that one file is excluded by name here; every other file under
    `core/`/`adapters/` must still never reference it. See
    `tests/test_assistant_chat_sim_copper_b1.py`."""
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            if py_file.name == "orchestrator.py":
                continue
            text = py_file.read_text(encoding="utf-8")
            assert "ToyQuad6DofPlant" not in text, f"{py_file} references ToyQuad6DofPlant"

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
    # T19 (B1-assistant-ops-charge-task): a twelfth, skill.request_charge
    # (requires ops.charge, not_implemented/device). CHARGE is not an
    # AutonomyVerb — see tests/test_assistant_ops_charge_task_b1.py.
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
        "skill.request_charge",
    }

    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_t12_full_suite_process_gate_placeholder():
    """The full Python suite being green (and host `ctest` green) is
    verified by running them, not asserted here — see the implementation
    report's own test-run transcript."""
    assert True
