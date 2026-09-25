"""Tests T1-T11 for `B1-fase-c-rate-torque-bridge`.

T12 (full craft suite stays green) and T13 (report confirms feedforward
only · normalized tau · mixer migrated · != N·m truth · != flying · next
= C++ scaffold) are process gates covered by running the full suite and
by `.jes/artifacts/implementation_report_fase_c_rate_torque_bridge_b1.md`.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command
from jarvis.flight_software.flight_control import (
    BodyRateCommand,
    BodyTorqueCommand,
    LinearRateTorqueBridge,
    QuadXMixer,
    hover_collective,
)
from jarvis.flight_software.flight_control import rate_torque as rate_torque_module
from jarvis.vehicle_profiles import run_controlled_flight_sim_smoke, run_mixer_smoke

REPO_ROOT = Path(__file__).resolve().parents[1]


def _rate_cmd(omega=(0.0, 0.0, 0.0), t_s: float = 0.0) -> BodyRateCommand:
    return BodyRateCommand(t_s=t_s, omega_body_rad_s=omega)


def test_t1_zero_rate_gives_zero_torque():
    bridge = LinearRateTorqueBridge()
    torque = bridge.convert(_rate_cmd())
    assert isinstance(torque, BodyTorqueCommand)
    assert torque.tau_body == (0.0, 0.0, 0.0)


def test_t2_positive_rate_gives_positive_torque_on_each_axis():
    bridge = LinearRateTorqueBridge(gain=2.0)
    torque = bridge.convert(_rate_cmd(omega=(0.3, 0.0, 0.0)))
    assert torque.tau_body[0] == pytest.approx(0.6)
    assert torque.tau_body[1] == pytest.approx(0.0)
    assert torque.tau_body[2] == pytest.approx(0.0)

    torque_pitch = bridge.convert(_rate_cmd(omega=(0.0, -0.1, 0.0)))
    assert torque_pitch.tau_body[1] == pytest.approx(-0.2)

    torque_yaw = bridge.convert(_rate_cmd(omega=(0.0, 0.0, 0.05)))
    assert torque_yaw.tau_body[2] == pytest.approx(0.1)


def test_t2b_per_axis_gains():
    bridge = LinearRateTorqueBridge(gains=(2.0, 3.0, 4.0))
    torque = bridge.convert(_rate_cmd(omega=(1.0, 1.0, 1.0)))
    assert torque.tau_body == (2.0, 3.0, 4.0)


def test_t3_invalid_gains_rejected():
    for bad_gain in (0.0, -1.0, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            LinearRateTorqueBridge(gain=bad_gain)
    for bad_gains in ((0.0, 1.0, 1.0), (1.0, -1.0, 1.0), (float("nan"), 1.0, 1.0)):
        with pytest.raises(ValueError):
            LinearRateTorqueBridge(gains=bad_gains)
    with pytest.raises(ValueError):
        LinearRateTorqueBridge(gain=1.0, gains=(1.0, 1.0, 1.0))
    LinearRateTorqueBridge(gain=1.0)
    LinearRateTorqueBridge(gains=(1.0, 2.0, 3.0))


def test_t4_mixer_public_mix_signature_takes_body_torque_command_only():
    signature = inspect.signature(QuadXMixer.mix)
    params = list(signature.parameters)
    assert params == ["self", "collective", "torques"]
    annotation = signature.parameters["torques"].annotation
    assert annotation in ("BodyTorqueCommand", BodyTorqueCommand)


def test_t5_equal_collective_zero_torque_gives_four_equal_motors():
    mixer = QuadXMixer()
    zero_torque = BodyTorqueCommand(t_s=0.0, tau_body=(0.0, 0.0, 0.0))
    command = mixer.mix(hover_collective(), zero_torque)
    forces = command.motor_forces
    assert forces[0] == forces[1] == forces[2] == forces[3]
    assert forces[0] == pytest.approx(0.5)


def test_t6_closed_loop_tilt_recovery_still_holds_with_bridge():
    """C11's own convergence criterion, re-run through the C12 bridge —
    default gain=1.0 makes the bridge a mathematical no-op relative to
    C11's pre-migration behavior, so no retune was needed (disclosed and
    verified in the report)."""
    import math

    errors = run_controlled_flight_sim_smoke(steps=200, initial_tilt_rad=math.radians(15.0))
    assert errors[-1] < errors[0]
    assert errors[-1] < math.radians(2.0)


def test_t7_no_cascaded_rate_pid_or_gpio_shaped_public_symbols():
    forbidden_substrings = (
        "rate_pid_step",
        "compute_inertia_torque_nm",
        "write_gpio",
        "inner_rate_loop",
        "innerrateloop",
    )
    for name, obj in vars(rate_torque_module).items():
        if name.startswith("_"):
            continue
        lowered = name.lower()
        for token in forbidden_substrings:
            assert token not in lowered, f"rate_torque.{name} looks forbidden-shaped ('{token}')"
        if isinstance(obj, type):
            for attr_name in dir(obj):
                if attr_name.startswith("_"):
                    continue
                lowered_attr = attr_name.lower()
                for token in forbidden_substrings:
                    assert token not in lowered_attr, (
                        f"rate_torque.{name}.{attr_name} looks forbidden-shaped ('{token}')"
                    )


def test_t7b_no_cpp_or_cmake_under_flight_software():
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


def test_t8_default_safety_and_autonomy_submit_still_reject():
    assert isinstance(default_safety_gate(), RejectAllSafetyGate)
    assert default_safety_gate().evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_t9_bridge_symbols_not_imported_by_orchestrator_or_craft_paths():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "flight_control.rate_torque" not in text, (
                f"{py_file} imports flight_control.rate_torque — forbidden craft coupling"
            )
            assert "LinearRateTorqueBridge" not in text, (
                f"{py_file} references LinearRateTorqueBridge — forbidden craft coupling"
            )


def test_t10_capability_registry_default_still_empty():
    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []


def test_t11_pyproject_version_is_0_5_10():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.35"' in text


def test_body_torque_command_rejects_non_finite():
    with pytest.raises(Exception):
        BodyTorqueCommand(t_s=0.0, tau_body=(float("nan"), 0.0, 0.0))


def test_body_torque_command_rejects_unknown_extra_field():
    with pytest.raises(Exception):
        BodyTorqueCommand(t_s=0.0, tau_body=(0.0, 0.0, 0.0), unexpected="x")


def test_no_rate_command_accepted_by_mixer_at_runtime():
    """Locks IC §2.3: mix(...) must not silently accept a BodyRateCommand
    as a stand-in for BodyTorqueCommand — a rate lacks tau_body, so
    passing one raises rather than being misinterpreted."""
    mixer = QuadXMixer()
    with pytest.raises(AttributeError):
        mixer.mix(hover_collective(), _rate_cmd(omega=(0.1, 0.0, 0.0)))


def test_smoke_mixer_uses_bridge_end_to_end():
    commands = run_mixer_smoke(samples=3)
    assert len(commands) == 3
    assert all(0.0 <= f <= 1.0 for c in commands for f in c.motor_forces)


def test_determinism_same_rate_input_gives_identical_torque():
    bridge_a = LinearRateTorqueBridge(gains=(1.5, 2.5, 3.5))
    bridge_b = LinearRateTorqueBridge(gains=(1.5, 2.5, 3.5))
    rate = _rate_cmd(omega=(0.2, -0.3, 0.05), t_s=1.0)
    assert bridge_a.convert(rate) == bridge_b.convert(rate)
