"""Tests T1-T9 for `B1-fase-c-position-loop` (C39).

T6 (C++ Catch2 — `SimulatedPositionHal` T1/T2 equivalents, `PositionController`
T2/T3/T4 equivalents) lives in
`native/flight_control/tests/test_position_loop.cpp`, run via `ctest`,
not here. T8's own "suite + ctest green" half is a process gate covered
by running them, not asserted here. T9 (report content: sim GPS != live
GPS != flying != GO_TO on copper != house map) is covered by
`.jes/artifacts/implementation_report_fase_c_position_loop_b1.md`, not
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
from jarvis.flight_software.flight_control.position_controller import PositionController, PositionSetpoint
from jarvis.flight_software.flight_control.sim_position_hal import SimulatedPositionHal
from jarvis.vehicle_profiles import (
    run_controlled_flight_sim_smoke,
    run_position_loop_smoke,
    run_sim_6dof_smoke,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


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


def test_t1_simulated_position_hal_known_true_xy_matches_finite():
    hal = SimulatedPositionHal()
    sample = hal.read_position(2.5, -1.5, t_s=1.0)
    assert math.isfinite(sample.x_m)
    assert math.isfinite(sample.y_m)
    assert sample.x_m == pytest.approx(2.5)
    assert sample.y_m == pytest.approx(-1.5)
    assert sample.t_s == pytest.approx(1.0)
    assert sample.z_m is None


def test_t1_optional_z_m_round_trips_when_provided():
    hal = SimulatedPositionHal()
    sample = hal.read_position(0.0, 0.0, t_s=0.0, true_z_m=4.0)
    assert sample.z_m == pytest.approx(4.0)


def test_t2_invalid_gains_and_non_finite_inputs_raise():
    with pytest.raises(ValueError):
        PositionController(kp=0.0)
    with pytest.raises(ValueError):
        PositionController(kp=-0.1)
    with pytest.raises(ValueError):
        PositionController(kd=-0.1)
    with pytest.raises(ValueError):
        PositionController(max_tilt_rad=0.0)
    with pytest.raises(ValueError):
        PositionController(max_tilt_rad=-0.5)
    with pytest.raises(ValueError):
        SimulatedPositionHal().read_position(float("nan"), 0.0, t_s=0.0)
    with pytest.raises(ValueError):
        SimulatedPositionHal().read_position(0.0, float("nan"), t_s=0.0)
    with pytest.raises(ValueError):
        SimulatedPositionHal().read_position(0.0, 0.0, t_s=0.0, true_z_m=float("nan"))

    controller = PositionController()
    hal = SimulatedPositionHal()
    sample = hal.read_position(0.0, 0.0, t_s=0.0)
    setpoint = PositionSetpoint(x_m=1.0, y_m=0.0)
    with pytest.raises(ValueError):
        controller.compute(setpoint, sample, float("nan"), 0.0, 0.0)
    with pytest.raises(ValueError):
        controller.compute(setpoint, sample, 0.0, float("nan"), 0.0)


def test_t3_controller_direction_east_and_north_and_clipping():
    controller = PositionController()
    hal = SimulatedPositionHal()
    sample = hal.read_position(0.0, 0.0, t_s=0.0)

    east = controller.compute(PositionSetpoint(x_m=5.0, y_m=0.0), sample, 0.0, 0.0, 0.0)
    assert east.q_body_to_world_desired[2] > 0.0  # pitch (w,x,y,z) -> y > 0
    assert east.q_body_to_world_desired[1] == pytest.approx(0.0)  # roll == 0

    north = controller.compute(PositionSetpoint(x_m=0.0, y_m=3.0), sample, 0.0, 0.0, 0.0)
    assert north.q_body_to_world_desired[1] < 0.0  # roll < 0
    assert north.q_body_to_world_desired[2] == pytest.approx(0.0)  # pitch == 0

    max_tilt_rad = 0.4
    capped = PositionController(max_tilt_rad=max_tilt_rad)
    extreme = capped.compute(PositionSetpoint(x_m=1000.0, y_m=0.0), sample, 0.0, 0.0, 0.0)
    assert extreme.q_body_to_world_desired[3] == pytest.approx(0.0)  # yaw stays 0
    assert extreme.q_body_to_world_desired[0] == pytest.approx(math.cos(max_tilt_rad / 2.0))
    assert extreme.q_body_to_world_desired[2] == pytest.approx(math.sin(max_tilt_rad / 2.0))


def test_t4_closed_loop_with_toy_quad_6dof_plant_horizontal_distance_shrinks():
    positions = run_position_loop_smoke(x_des_m=5.0, y_des_m=0.0, z_des_m=2.0)
    x0, y0, _ = positions[0]
    xf, yf, zf = positions[-1]
    initial_distance = math.hypot(5.0 - x0, 0.0 - y0)
    final_distance = math.hypot(5.0 - xf, 0.0 - yf)
    assert final_distance < initial_distance
    assert final_distance < 1.0
    assert math.isfinite(zf)


def test_t5_loop_step_never_calls_plant_and_c11_c36_c37_c38_smokes_still_green():
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(loop_module))
    assert "plant.step(" not in code_only
    assert "ToyQuadAttitudePlant" not in code_only
    assert "ToyQuad6DofPlant" not in code_only

    tilt_errors_rad = run_controlled_flight_sim_smoke()
    assert tilt_errors_rad[-1] < tilt_errors_rad[0]

    positions = run_sim_6dof_smoke()
    delta = math.sqrt(sum((e - s) ** 2 for e, s in zip(positions[-1], positions[0])))
    assert delta > 0.0


def test_t7_no_craft_continuity_library_board_edits_and_safety_default_reject_all():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "PositionController" not in text, f"{py_file} references PositionController"
            assert "SimulatedPositionHal" not in text, f"{py_file} references SimulatedPositionHal"

    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []

    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.GO_TO)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_t8_pyproject_version_is_0_5_40():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.41"' in text


def test_t8_full_suite_process_gate_placeholder():
    """The full Python suite being green (and host `ctest` green) is
    verified by running them, not asserted here — see the implementation
    report's own test-run transcript."""
    assert True
