"""Tests T1-T10 for `B1-fase-c-imu-filtering-rung`.

T11 (full craft suite stays green) and T12 (report confirms filter rung
+ no estimation/control/ESC + C++ honesty retained) are process gates
covered by running the full suite and by
`.jes/artifacts/implementation_report_fase_c_imu_filtering_rung_b1.md`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command
from jarvis.flight_software.flight_control import ImuLowPassFilter, ImuSample, SimulatedImuHal
from jarvis.flight_software.flight_control import filter as filter_module
from jarvis.vehicle_profiles import run_hal_imu_filter_smoke

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_t1_constant_stream_converges_to_constant():
    filt = ImuLowPassFilter(alpha=0.3)
    constant = ImuSample(t_s=0.0, accel_mps2=(1.0, 2.0, -9.81), gyro_rad_s=(0.0, 0.0, 0.0))
    first = filt.filter_sample(constant)
    second = filt.filter_sample(ImuSample(t_s=0.01, accel_mps2=constant.accel_mps2, gyro_rad_s=constant.gyro_rad_s))
    assert first.accel_mps2 == constant.accel_mps2
    assert second.accel_mps2 == constant.accel_mps2
    assert second.gyro_rad_s == constant.gyro_rad_s


def test_t1b_alpha_one_equals_raw_every_time():
    filt = ImuLowPassFilter(alpha=1.0)
    hal = SimulatedImuHal(seed=1)
    for _ in range(5):
        raw = hal.read_imu()
        filtered = filt.filter_sample(
            ImuSample(t_s=raw.t_s, accel_mps2=raw.accel_mps2, gyro_rad_s=raw.gyro_rad_s)
        )
        assert filtered.accel_mps2 == raw.accel_mps2
        assert filtered.gyro_rad_s == raw.gyro_rad_s


def test_t2_same_seed_alpha_reset_gives_identical_sequence():
    hal_a = SimulatedImuHal(seed=5)
    filt_a = ImuLowPassFilter(alpha=0.2)
    sequence_a = [filt_a.filter_sample(hal_a.read_imu()) for _ in range(5)]

    hal_b = SimulatedImuHal(seed=5)
    filt_b = ImuLowPassFilter(alpha=0.2)
    sequence_b = [filt_b.filter_sample(hal_b.read_imu()) for _ in range(5)]

    assert sequence_a == sequence_b

    filt_a.reset()
    hal_a2 = SimulatedImuHal(seed=5)
    replay = [filt_a.filter_sample(hal_a2.read_imu()) for _ in range(5)]
    assert replay == sequence_a


def test_t3_invalid_alpha_rejected():
    for bad_alpha in (0.0, -0.1, 1.1, 2.0):
        with pytest.raises(ValueError):
            ImuLowPassFilter(alpha=bad_alpha)
    ImuLowPassFilter(alpha=1.0)


def test_t4_filtered_output_is_imu_sample_with_no_actuator_fields():
    filt = ImuLowPassFilter()
    raw = SimulatedImuHal(seed=0).read_imu()
    filtered = filt.filter_sample(raw)
    assert isinstance(filtered, ImuSample)
    assert set(type(filtered).model_fields) == {"t_s", "accel_mps2", "gyro_rad_s"}


def test_t5_no_estimation_or_actuation_shaped_public_symbols_in_filter_module():
    forbidden_substrings = (
        "estimate_attitude",
        "get_quaternion",
        "get_euler",
        "update_ekf",
        "write_motor",
        "mix",
        "set_pwm",
    )
    for name, obj in vars(filter_module).items():
        if name.startswith("_"):
            continue
        lowered = name.lower()
        for token in forbidden_substrings:
            assert token not in lowered, f"filter.{name} looks estimation/actuation-shaped ('{token}')"
        if isinstance(obj, type):
            for attr_name in dir(obj):
                if attr_name.startswith("_"):
                    continue
                lowered_attr = attr_name.lower()
                for token in forbidden_substrings:
                    assert token not in lowered_attr, (
                        f"filter.{name}.{attr_name} looks estimation/actuation-shaped ('{token}')"
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


def test_t8_filter_symbols_not_imported_by_orchestrator_or_craft_paths():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "flight_control.filter" not in text, (
                f"{py_file} imports flight_control.filter — forbidden craft coupling"
            )
            assert "ImuLowPassFilter" not in text, (
                f"{py_file} references ImuLowPassFilter — forbidden craft coupling"
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
    }


def test_t10_pyproject_version_is_0_5_4():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.44"' in text


def test_smoke_filter_returns_at_least_one_filtered_sample():
    samples = run_hal_imu_filter_smoke(samples=3)
    assert len(samples) == 3
    assert all(isinstance(s, ImuSample) for s in samples)


def test_reset_clears_state_so_next_sample_seeds_unfiltered():
    filt = ImuLowPassFilter(alpha=0.2)
    a = ImuSample(t_s=0.0, accel_mps2=(1.0, 1.0, 1.0), gyro_rad_s=(0.0, 0.0, 0.0))
    b = ImuSample(t_s=0.01, accel_mps2=(5.0, 5.0, 5.0), gyro_rad_s=(0.0, 0.0, 0.0))
    filt.filter_sample(a)
    smoothed = filt.filter_sample(b)
    assert smoothed.accel_mps2 != b.accel_mps2

    filt.reset()
    seeded = filt.filter_sample(b)
    assert seeded.accel_mps2 == b.accel_mps2
