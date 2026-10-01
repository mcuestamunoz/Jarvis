"""Tests T1-T9 for `B1-fase-c-altitude-loop` (C38).

T6 (C++ Catch2 — `SimulatedAltitudeHal` T1 equivalent, `AltitudeController`
T3/T4 equivalents) lives in
`native/flight_control/tests/test_altitude_loop.cpp`, run via `ctest`,
not here. T8's own "suite + ctest green" half is a process gate covered
by running them, not asserted here. T9 (report content: sim altitude !=
live baro != flying != HOLD in air) is covered by
`.jes/artifacts/implementation_report_fase_c_altitude_loop_b1.md`, not
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
from jarvis.flight_software.flight_control.altitude_controller import AltitudeController
from jarvis.flight_software.flight_control.sim_altitude_hal import SimulatedAltitudeHal
from jarvis.vehicle_profiles import (
    run_altitude_loop_smoke,
    run_controlled_flight_sim_smoke,
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


def test_t1_simulated_altitude_hal_known_true_z_matches_finite():
    hal = SimulatedAltitudeHal()
    sample = hal.read_altitude(3.5, t_s=1.0)
    assert math.isfinite(sample.altitude_m)
    assert sample.altitude_m == pytest.approx(3.5)
    assert sample.t_s == pytest.approx(1.0)


def test_t2_invalid_gains_and_non_finite_inputs_raise():
    with pytest.raises(ValueError):
        AltitudeController(kp=0.0)
    with pytest.raises(ValueError):
        AltitudeController(kp=-0.1)
    with pytest.raises(ValueError):
        AltitudeController(kd=-0.1)
    with pytest.raises(ValueError):
        AltitudeController(hover_bias=-0.1)
    with pytest.raises(ValueError):
        AltitudeController(hover_bias=1.1)
    with pytest.raises(ValueError):
        SimulatedAltitudeHal().read_altitude(float("nan"), t_s=0.0)

    controller = AltitudeController()
    hal = SimulatedAltitudeHal()
    sample = hal.read_altitude(0.0, t_s=0.0)
    with pytest.raises(ValueError):
        controller.compute(float("nan"), sample, 0.0)
    with pytest.raises(ValueError):
        controller.compute(1.0, sample, float("nan"))


def test_t3_controller_direction_and_clipping():
    controller = AltitudeController(kp=0.2, kd=0.3, hover_bias=0.1226)
    hal = SimulatedAltitudeHal()

    below = hal.read_altitude(0.0, t_s=0.0)
    collective_below = controller.compute(2.0, below, 0.0)
    assert collective_below > 0.1226

    above = hal.read_altitude(5.0, t_s=0.0)
    collective_above = controller.compute(2.0, above, 0.0)
    assert collective_above < 0.1226

    for c in (collective_below, collective_above):
        assert 0.0 <= c <= 1.0

    far_below = hal.read_altitude(-100.0, t_s=0.0)
    assert controller.compute(2.0, far_below, 0.0) == pytest.approx(1.0)


def test_t4_closed_loop_with_toy_quad_6dof_plant_climbs_and_error_shrinks():
    altitudes = run_altitude_loop_smoke(z_des_m=2.0)
    initial_error = abs(2.0 - altitudes[0])
    final_error = abs(2.0 - altitudes[-1])
    assert altitudes[-1] > 0.0
    assert final_error < initial_error
    assert final_error < 0.2


def test_t5_loop_step_never_calls_plant_and_c11_c36_c37_smokes_still_green():
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
            assert "AltitudeController" not in text, f"{py_file} references AltitudeController"
            assert "SimulatedAltitudeHal" not in text, f"{py_file} references SimulatedAltitudeHal"

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
    }

    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_t8_full_suite_process_gate_placeholder():
    """The full Python suite being green (and host `ctest` green) is
    verified by running them, not asserted here — see the implementation
    report's own test-run transcript."""
    assert True
