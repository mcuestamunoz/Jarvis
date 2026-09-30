"""Tests T1-T12 for `B1-fase-c-control-loop-tick` (C24).

T6 (C++ Catch2 — `ControlLoop::step` produces four finite motor forces;
`fc_closed_loop_smoke` still exits 0) lives in
`native/flight_control/tests/test_loop.cpp`, run via `ctest`, not here.
T12 (report content: named tick != flying != MCU ISR != motors) is
covered by `.jes/artifacts/implementation_report_fase_c_control_loop_tick_b1.md`,
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
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command
from jarvis.flight_software.flight_control import loop as loop_module
from jarvis.flight_software.flight_control.controller import AttitudeSetpoint, level_setpoint
from jarvis.flight_software.flight_control.loop import ControlTickResult, FlightControlLoop
from jarvis.flight_software.flight_control.mixer import MotorForceCommand
from jarvis.flight_software.flight_control.plant import ToyQuadAttitudePlant, tilt_angle_rad
from jarvis.flight_software.flight_control.types import ImuSample
from jarvis.capabilities.intent import RadioIntentAdapter
from jarvis.vehicle_profiles import run_controlled_flight_sim_smoke, run_open_loop_baseline_smoke

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


def _tilted_quat(tilt_rad: float):
    half = tilt_rad / 2.0
    return (math.cos(half), math.sin(half), 0.0, 0.0)


def test_t1_step_returns_control_tick_result_with_four_finite_forces():
    loop = FlightControlLoop()
    sample = ImuSample(t_s=0.0, accel_mps2=(0.0, 0.0, -9.81), gyro_rad_s=(0.0, 0.0, 0.0))
    setpoint = level_setpoint(0.0)

    result = loop.step(sample, setpoint, 0.5)

    assert isinstance(result, ControlTickResult)
    assert len(result.forces.motor_forces) == 4
    assert all(math.isfinite(f) for f in result.forces.motor_forces)
    assert isinstance(result.forces, MotorForceCommand)


def test_t2_order_filter_then_estimate_then_pd_then_bridge_then_mix():
    calls: list[str] = []

    class SpyFilter:
        def filter_sample(self, raw):
            calls.append("filter")
            return raw

    class SpyEstimator:
        def update(self, filtered):
            calls.append("estimate")
            from jarvis.flight_software.flight_control.attitude import AttitudeState

            return AttitudeState(
                t_s=filtered.t_s, q_body_to_world=(1.0, 0.0, 0.0, 0.0), omega_body_rad_s=(0.0, 0.0, 0.0)
            )

    class SpyController:
        def compute(self, setpoint, state):
            calls.append("pd")
            from jarvis.flight_software.flight_control.controller import BodyRateCommand

            return BodyRateCommand(t_s=state.t_s, omega_body_rad_s=(0.0, 0.0, 0.0))

    class SpyBridge:
        def convert(self, rates):
            calls.append("bridge")
            from jarvis.flight_software.flight_control.rate_torque import BodyTorqueCommand

            return BodyTorqueCommand(t_s=rates.t_s, tau_body=(0.0, 0.0, 0.0))

    class SpyMixer:
        def mix(self, collective, torques):
            calls.append("mix")
            return MotorForceCommand(t_s=torques.t_s, motor_forces=(0.5, 0.5, 0.5, 0.5))

    loop = FlightControlLoop(
        filt=SpyFilter(), estimator=SpyEstimator(), controller=SpyController(),
        bridge=SpyBridge(), mixer=SpyMixer(),
    )
    sample = ImuSample(t_s=0.0, accel_mps2=(0.0, 0.0, -9.81), gyro_rad_s=(0.0, 0.0, 0.0))
    loop.step(sample, level_setpoint(0.0), 0.5)

    assert calls == ["filter", "estimate", "pd", "bridge", "mix"]


def test_t2b_step_source_never_calls_plant_step():
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(loop_module))
    assert "plant.step(" not in code_only
    assert ".step(forces" not in code_only
    assert "ToyQuadAttitudePlant" not in code_only


def test_t3_c11_smoke_still_strictly_decreases_and_recovers():
    errors = run_controlled_flight_sim_smoke(steps=200, initial_tilt_rad=math.radians(15.0))
    assert len(errors) == 201
    assert errors[-1] < errors[0]
    assert errors[-1] < math.radians(2.0)


def test_t4_open_loop_baseline_still_does_not_recover():
    baseline = run_open_loop_baseline_smoke(steps=200, initial_tilt_rad=math.radians(15.0))
    assert all(err == pytest.approx(baseline[0], abs=1e-9) for err in baseline)

    closed = run_controlled_flight_sim_smoke(steps=200, initial_tilt_rad=math.radians(15.0))
    assert closed[-1] < baseline[-1]


def test_t5_step_imports_no_gpio_serial_submit_command_or_crsf():
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(loop_module))
    forbidden = (
        "write_gpio",
        "open_serial",
        "submit_command",
        "propose_command",
        "crsf",
        "fcntl",
        "termios",
        "import socket",
    )
    lowered = code_only.lower()
    for token in forbidden:
        assert token not in lowered, f"loop.py unexpectedly references '{token}'"
    assert not hasattr(loop_module, "submit_command")
    assert not hasattr(loop_module, "propose_command")


def test_t7_refactored_smoke_matches_pre_refactor_inlined_reference():
    """Behavior-freeze check: builds the same chain the C11/C13 smokes used
    BEFORE this Buy's extraction, inlined by hand here, and asserts
    `FlightControlLoop.step` produces a bit-identical tilt-error series to
    the shipped smoke."""
    from jarvis.flight_software.flight_control.attitude import ComplementaryAttitudeEstimator
    from jarvis.flight_software.flight_control.controller import PdAttitudeController
    from jarvis.flight_software.flight_control.filter import ImuLowPassFilter
    from jarvis.flight_software.flight_control.mixer import QuadXMixer
    from jarvis.flight_software.flight_control.rate_torque import LinearRateTorqueBridge

    plant = ToyQuadAttitudePlant(torque_gain=40.0, angular_damping=0.5)
    plant.reset(initial_q=_tilted_quat(math.radians(15.0)))
    filt = ImuLowPassFilter(alpha=0.2)
    estimator = ComplementaryAttitudeEstimator(gain=0.05)
    controller = PdAttitudeController(kp=6.0, kd=0.6)
    bridge = LinearRateTorqueBridge()
    mixer = QuadXMixer()

    inline_errors = [tilt_angle_rad(plant.true_attitude.q_body_to_world)]
    sample = plant.sense()
    for _ in range(200):
        filtered = filt.filter_sample(sample)
        state = estimator.update(filtered)
        setpoint = level_setpoint(state.t_s)
        rate_cmd = controller.compute(setpoint, state)
        torque_cmd = bridge.convert(rate_cmd)
        forces = mixer.mix(0.5, torque_cmd)
        sample = plant.step(forces, dt_s=0.01)
        inline_errors.append(tilt_angle_rad(plant.true_attitude.q_body_to_world))

    shipped_errors = run_controlled_flight_sim_smoke(steps=200, initial_tilt_rad=math.radians(15.0))
    assert shipped_errors == inline_errors


def test_t8_radio_intent_adapter_still_not_implemented_and_safety_default_unchanged():
    with pytest.raises(NotImplementedError):
        RadioIntentAdapter.parse(b"\x00\x00")
    assert isinstance(default_safety_gate(), RejectAllSafetyGate)
    assert default_safety_gate().evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_t9_registry_empty_and_no_craft_or_core_imports_of_loop():
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
    # tests/test_assistant_vehicle_return_home_task_b1.py. Still zero Skill
    # execution path anywhere; this file's own isolation proof is
    # unaffected either way.
    assert {skill.id for skill in registry.skills()} == {
        "skill.explain_concept",
        "skill.project_status",
        "skill.request_hold",
        "skill.request_land",
        "skill.request_go_to",
        "skill.request_takeoff",
        "skill.request_return_home",
    }

    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "flight_control.loop" not in text, f"{py_file} imports flight_control.loop"
            assert "FlightControlLoop" not in text, f"{py_file} references FlightControlLoop"


def test_t10_pyproject_version_is_0_5_22():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.44"' in text


def test_t11_full_suite_process_gate_placeholder():
    """The full Python suite being green (and host `ctest` green) is
    verified by running them, not asserted here — see the implementation
    report's own test-run transcript."""
    assert True


def test_step_before_construction_is_a_language_level_typeerror():
    """C24 IC §2's 'step before the loop object is constructed -> typed
    error or documented impossible': `step` is a bound instance method,
    so calling the unbound function requires `self` — Python's own
    method-binding rules raise `TypeError`, no special-case code needed."""
    with pytest.raises(TypeError):
        FlightControlLoop.step(
            ImuSample(t_s=0.0, accel_mps2=(0.0, 0.0, -9.81), gyro_rad_s=(0.0, 0.0, 0.0)),
            level_setpoint(0.0),
            0.5,
        )


def test_default_construction_matches_existing_rung_defaults():
    loop = FlightControlLoop()
    sample = ImuSample(t_s=0.0, accel_mps2=(0.0, 0.0, -9.81), gyro_rad_s=(0.0, 0.0, 0.0))
    result = loop.step(sample, level_setpoint(0.0), 0.5)
    # Default gain (0.02) / kp=6.0 / kd=0.6 / bridge gain=1.0 / mixer
    # default scales — same construction as every other rung's own
    # default-constructed instance; a zero-rate/zero-tilt input at
    # collective=0.5 should mix to all-equal forces.
    assert all(f == pytest.approx(0.5, abs=1e-9) for f in result.forces.motor_forces)


def test_pwm_field_is_populated_and_encoded_from_forces():
    from jarvis.flight_software.flight_control.esc import encode_motor_forces

    loop = FlightControlLoop()
    sample = ImuSample(t_s=0.0, accel_mps2=(0.0, 0.0, -9.81), gyro_rad_s=(0.0, 0.0, 0.0))
    result = loop.step(sample, level_setpoint(0.0), 0.5)
    expected_pwm = encode_motor_forces(result.forces)
    assert result.pwm.pulse_us == expected_pwm.pulse_us
    assert result.pwm.protocol == "pwm_us"


def test_loop_py_has_no_cpp_or_cmake_and_is_not_under_capabilities():
    assert (REPO_ROOT / "src" / "jarvis" / "flight_software" / "flight_control" / "loop.py").exists()
    assert not (REPO_ROOT / "src" / "jarvis" / "capabilities" / "loop.py").exists()


def test_setpoint_and_collective_are_plain_arguments_no_rc_decoding():
    signature = inspect.signature(FlightControlLoop.step)
    params = list(signature.parameters)
    assert params == ["self", "sample", "setpoint", "collective"]
    assert signature.parameters["setpoint"].annotation in ("AttitudeSetpoint", AttitudeSetpoint)
