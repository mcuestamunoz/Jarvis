"""Tests T1-T10 for `B1-fase-c-mixer-rung`.

T11 (full craft suite stays green) and T12 (report confirms quad-X only
+ rate-as-mix-channel honesty + != ESC / != flying) are process gates
covered by running the full suite and by
`.jes/artifacts/implementation_report_fase_c_mixer_rung_b1.md`.

**Updated for C12** (`B1-fase-c-rate-torque-bridge`, `v0.5.10`):
`QuadXMixer.mix` now takes a `BodyTorqueCommand`, not a bare
`BodyRateCommand` — the rate-as-mix-channel honesty gap this file
originally documented is now closed by `rate_torque.py`'s
`LinearRateTorqueBridge`. These tests construct `BodyTorqueCommand`
directly (bypassing the bridge) since they exercise the mixer's own
allocation geometry, not the bridge's conversion — that has its own test
module, `test_fase_c_rate_torque_bridge_b1.py`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command
from jarvis.flight_software.flight_control import (
    BodyTorqueCommand,
    MotorForceCommand,
    QuadXMixer,
    hover_collective,
)
from jarvis.flight_software.flight_control import mixer as mixer_module
from jarvis.vehicle_profiles import run_mixer_smoke

REPO_ROOT = Path(__file__).resolve().parents[1]

_ZERO_TAU = (0.0, 0.0, 0.0)


def _torque_cmd(tau=_ZERO_TAU, t_s: float = 0.0) -> BodyTorqueCommand:
    return BodyTorqueCommand(t_s=t_s, tau_body=tau)


def test_t1_equal_collective_zero_rates_gives_four_equal_motors():
    mixer = QuadXMixer()
    command = mixer.mix(hover_collective(), _torque_cmd())
    forces = command.motor_forces
    assert forces[0] == forces[1] == forces[2] == forces[3]
    assert forces[0] == pytest.approx(0.5)


def test_t2_roll_channel_signs_match_documented_x_layout():
    mixer = QuadXMixer()
    command = mixer.mix(hover_collective(), _torque_cmd(tau=(0.2, 0.0, 0.0)))
    fr, fl, rl, rr = command.motor_forces
    # roll+: FR/RR decrease, FL/RL increase (module docstring geometry)
    assert fr < 0.5
    assert rr < 0.5
    assert fl > 0.5
    assert rl > 0.5
    assert fr == pytest.approx(rr)
    assert fl == pytest.approx(rl)


def test_t2b_pitch_channel_signs_match_documented_x_layout():
    mixer = QuadXMixer()
    command = mixer.mix(hover_collective(), _torque_cmd(tau=(0.0, 0.2, 0.0)))
    fr, fl, rl, rr = command.motor_forces
    assert fr > 0.5
    assert fl > 0.5
    assert rl < 0.5
    assert rr < 0.5


def test_t2c_yaw_channel_signs_match_documented_x_layout():
    mixer = QuadXMixer()
    command = mixer.mix(hover_collective(), _torque_cmd(tau=(0.0, 0.0, 0.2)))
    fr, fl, rl, rr = command.motor_forces
    assert fr < 0.5
    assert rl < 0.5
    assert fl > 0.5
    assert rr > 0.5


def test_t3_invalid_scales_rejected_collective_clamped():
    for bad_scale in (-0.1, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            QuadXMixer(roll_scale=bad_scale)
        with pytest.raises(ValueError):
            QuadXMixer(pitch_scale=bad_scale)
        with pytest.raises(ValueError):
            QuadXMixer(yaw_scale=bad_scale)

    mixer = QuadXMixer()
    below = mixer.mix(-5.0, _torque_cmd())
    above = mixer.mix(5.0, _torque_cmd())
    assert all(0.0 <= f <= 1.0 for f in below.motor_forces)
    assert all(0.0 <= f <= 1.0 for f in above.motor_forces)
    assert below.motor_forces == (0.0, 0.0, 0.0, 0.0)
    assert above.motor_forces == (1.0, 1.0, 1.0, 1.0)


def test_t4_motor_force_command_shape():
    mixer = QuadXMixer()
    command = mixer.mix(hover_collective(), _torque_cmd())
    assert isinstance(command, MotorForceCommand)
    assert len(command.motor_forces) == 4
    assert command.layout == "quad_x"
    assert set(type(command).model_fields) == {"t_s", "motor_forces", "layout", "notes"}


def test_t5_no_esc_pwm_shaped_public_symbols_in_mixer_module():
    forbidden_substrings = ("set_pwm", "write_dshot", "arm", "disarm", "command_esc", "open_serial")
    for name, obj in vars(mixer_module).items():
        if name.startswith("_"):
            continue
        lowered = name.lower()
        for token in forbidden_substrings:
            assert token not in lowered, f"mixer.{name} looks forbidden-shaped ('{token}')"
        if isinstance(obj, type):
            for attr_name in dir(obj):
                if attr_name.startswith("_"):
                    continue
                lowered_attr = attr_name.lower()
                for token in forbidden_substrings:
                    assert token not in lowered_attr, (
                        f"mixer.{name}.{attr_name} looks forbidden-shaped ('{token}')"
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


def test_t8_mixer_symbols_not_imported_by_orchestrator_or_craft_paths():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "flight_control.mixer" not in text, (
                f"{py_file} imports flight_control.mixer — forbidden craft coupling"
            )
            assert "QuadXMixer" not in text, (
                f"{py_file} references QuadXMixer — forbidden craft coupling"
            )


def test_t9_capability_registry_default_still_empty():
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


def test_smoke_mixer_returns_at_least_one_command():
    commands = run_mixer_smoke(samples=3)
    assert len(commands) == 3
    assert all(isinstance(c, MotorForceCommand) for c in commands)
    assert all(c.layout == "quad_x" for c in commands)
    assert all(len(c.motor_forces) == 4 for c in commands)
    assert all(0.0 <= f <= 1.0 for c in commands for f in c.motor_forces)


def test_motor_force_command_rejects_wrong_length():
    with pytest.raises(Exception):
        MotorForceCommand(t_s=0.0, motor_forces=(0.5, 0.5, 0.5))


def test_zero_scale_disables_channel():
    mixer = QuadXMixer(roll_scale=0.0)
    command = mixer.mix(hover_collective(), _torque_cmd(tau=(1.0, 0.0, 0.0)))
    forces = command.motor_forces
    assert forces[0] == forces[1] == forces[2] == forces[3]


def test_determinism_same_inputs_give_identical_command():
    mixer_a = QuadXMixer(roll_scale=0.1, pitch_scale=0.1, yaw_scale=0.1)
    mixer_b = QuadXMixer(roll_scale=0.1, pitch_scale=0.1, yaw_scale=0.1)
    torques = _torque_cmd(tau=(0.15, -0.1, 0.05), t_s=2.0)
    assert mixer_a.mix(0.4, torques) == mixer_b.mix(0.4, torques)


def test_no_esc_call_site_in_mixer_module_source():
    """The module docstring is allowed to mention ESC/PWM in prose
    (documenting what it does not do) — this checks there is no actual
    call site."""
    import inspect

    source = inspect.getsource(mixer_module)
    for forbidden_call in ("set_pwm(", "write_dshot(", "command_esc(", "open_serial("):
        assert forbidden_call not in source
