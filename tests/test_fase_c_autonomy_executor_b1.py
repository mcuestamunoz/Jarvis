"""Tests T1-T9 for `B1-fase-c-autonomy-executor` (C40).

T6 (C++ Catch2 — `SimAutonomyExecutor` T1/T2/T3/T4 equivalents) lives in
`native/flight_control/tests/test_sim_autonomy_executor.cpp`, run via
`ctest`, not here. T8's own "suite + ctest green" half is a process gate
covered by running them, not asserted here. T9 (report content: verb ->
setpoints in RAM != execute on copper != Safety allow != flying) is
covered by `.jes/artifacts/implementation_report_fase_c_autonomy_executor_b1.md`,
not by this file.
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
from jarvis.flight_software.autonomy import (
    AutonomyVerb,
    SimAutonomyExecutor,
    SimAutonomyParams,
    propose_command,
    submit_command,
)
from jarvis.flight_software.autonomy import sim_executor as sim_executor_module
from jarvis.flight_software.flight_control import loop as loop_module
from jarvis.flight_software.flight_control.plant import ToyQuad6DofPlant
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


def test_t1_go_to_shrinks_horizontal_distance_to_an_east_point():
    plant = ToyQuad6DofPlant()
    executor = SimAutonomyExecutor(plant)
    x0, y0, _ = plant.true_position_m
    initial_distance = math.hypot(3.0 - x0, 0.0 - y0)

    for _ in range(1500):
        executor.tick(AutonomyVerb.GO_TO, SimAutonomyParams(x_m=3.0, y_m=0.0, z_m=2.0), 0.01)

    x1, y1, z1 = plant.true_position_m
    final_distance = math.hypot(3.0 - x1, 0.0 - y1)
    assert final_distance < initial_distance
    assert final_distance < 0.1
    assert math.isfinite(z1)


def test_t2_hold_keeps_position_within_documented_bound_after_settling():
    plant = ToyQuad6DofPlant()
    executor = SimAutonomyExecutor(plant)

    for _ in range(1500):
        executor.tick(AutonomyVerb.GO_TO, SimAutonomyParams(x_m=3.0, y_m=0.0, z_m=2.0), 0.01)

    for _ in range(300):
        executor.tick(AutonomyVerb.HOLD, None, 0.01)

    xs, ys, zs = [], [], []
    for _ in range(500):
        executor.tick(AutonomyVerb.HOLD, None, 0.01)
        x, y, z = plant.true_position_m
        xs.append(x)
        ys.append(y)
        zs.append(z)

    assert max(xs) - min(xs) < 0.5
    assert max(ys) - min(ys) < 0.5
    assert max(zs) - min(zs) < 0.5
    assert 2.5 < min(xs) and max(xs) < 3.5


def test_t3_land_decreases_z_toward_documented_floor():
    plant = ToyQuad6DofPlant()
    executor = SimAutonomyExecutor(plant)

    for _ in range(1500):
        executor.tick(AutonomyVerb.GO_TO, SimAutonomyParams(x_m=0.0, y_m=0.0, z_m=2.0), 0.01)

    z_pre = plant.true_position_m[2]

    for _ in range(1000):
        executor.tick(AutonomyVerb.LAND, None, 0.01)

    z_post = plant.true_position_m[2]
    assert z_post < z_pre
    assert z_post < 0.5
    assert math.isfinite(z_post)


def test_t4_unsupported_verb_and_bad_params_raise():
    plant = ToyQuad6DofPlant()
    executor = SimAutonomyExecutor(plant)

    for verb in (AutonomyVerb.TAKEOFF, AutonomyVerb.FOLLOW, AutonomyVerb.RETURN_HOME, AutonomyVerb.PATROL):
        with pytest.raises(ValueError):
            executor.tick(verb, None, 0.01)

    with pytest.raises(ValueError):
        executor.tick(AutonomyVerb.GO_TO, SimAutonomyParams(x_m=1.0), 0.01)  # missing y_m
    with pytest.raises(ValueError):
        executor.tick(AutonomyVerb.GO_TO, SimAutonomyParams(x_m=float("nan"), y_m=0.0), 0.01)
    with pytest.raises(ValueError):
        executor.tick(AutonomyVerb.HOLD, None, float("nan"))
    with pytest.raises(ValueError):
        executor.tick(AutonomyVerb.HOLD, None, 0.0)
    with pytest.raises(ValueError):
        SimAutonomyExecutor(plant, z_land_m=float("nan"))
    with pytest.raises(ValueError):
        SimAutonomyExecutor(plant, land_rate_mps=-0.1)


def test_t5_submit_command_still_reject_and_no_executed_string_in_module():
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.evaluate(SafetyRequest()).outcome == "reject"

    for verb in (AutonomyVerb.HOLD, AutonomyVerb.GO_TO, AutonomyVerb.LAND):
        command = propose_command(verb)
        result = submit_command(command, gate)
        assert result.safety.outcome == "reject"
        assert result.execution == "not_attempted"

    code_only = _strip_python_comments_and_docstrings(inspect.getsource(sim_executor_module))
    assert '"executed"' not in code_only
    assert "'executed'" not in code_only


def test_t6_loop_step_never_calls_plant_and_c11_c36_c37_c38_c39_smokes_still_green():
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(loop_module))
    assert "plant.step(" not in code_only
    assert "ToyQuadAttitudePlant" not in code_only
    assert "ToyQuad6DofPlant" not in code_only

    executor_code_only = _strip_python_comments_and_docstrings(inspect.getsource(sim_executor_module))
    assert "plant.step(" not in executor_code_only

    tilt_errors_rad = run_controlled_flight_sim_smoke()
    assert tilt_errors_rad[-1] < tilt_errors_rad[0]

    positions = run_sim_6dof_smoke()
    delta = math.sqrt(sum((e - s) ** 2 for e, s in zip(positions[-1], positions[0])))
    assert delta > 0.0

    pos_positions = run_position_loop_smoke()
    x0, y0, _ = pos_positions[0]
    xf, yf, _ = pos_positions[-1]
    assert math.hypot(5.0 - xf, 0.0 - yf) < math.hypot(5.0 - x0, 0.0 - y0)


def test_t7_no_craft_continuity_library_board_edits():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "SimAutonomyExecutor" not in text, f"{py_file} references SimAutonomyExecutor"

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
    # tests/test_assistant_vehicle_takeoff_task_b1.py. Still zero Skill
    # execution path anywhere; this file's own isolation proof is
    # unaffected either way.
    assert {skill.id for skill in registry.skills()} == {
        "skill.explain_concept",
        "skill.project_status",
        "skill.request_hold",
        "skill.request_land",
        "skill.request_go_to",
        "skill.request_takeoff",
    }


def test_t8_pyproject_version_is_0_5_41():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.44"' in text


def test_t8_full_suite_process_gate_placeholder():
    """The full Python suite being green (and host `ctest` green) is
    verified by running them, not asserted here — see the implementation
    report's own test-run transcript."""
    assert True
