"""Tests T1-T9 for `B1-fase-c-first-fc-rung`.

T10 (full craft suite stays green) and T11 (report confirms H-locks + the
craft-FC vs flight_software-FC naming split) are process gates covered by
running the full suite and by
`.jes/artifacts/implementation_report_fase_c_first_fc_rung_b1.md`.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities import safety as safety_module
from jarvis.flight_software.flight_control import ImuHal, ImuSample, SimulatedImuHal
from jarvis.flight_software.flight_control import hal as hal_module
from jarvis.flight_software.flight_control import sim_imu_hal as sim_imu_hal_module
from jarvis.vehicle_profiles import VehicleProfile, load_profile, run_hal_imu_smoke

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_t1_simulated_imu_hal_returns_imu_sample_with_3_vectors():
    hal = SimulatedImuHal(seed=0)
    sample = hal.read_imu()
    assert isinstance(sample, ImuSample)
    assert len(sample.accel_mps2) == 3
    assert len(sample.gyro_rad_s) == 3
    assert isinstance(sample.t_s, float)


def test_t2_same_seed_gives_identical_first_sample():
    first = SimulatedImuHal(seed=42).read_imu()
    second = SimulatedImuHal(seed=42).read_imu()
    assert first == second

    different_seed = SimulatedImuHal(seed=43).read_imu()
    assert different_seed != first


def test_t2b_reset_replays_same_sequence():
    hal = SimulatedImuHal(seed=7)
    first_pass = [hal.read_imu() for _ in range(3)]
    hal.reset()
    second_pass = [hal.read_imu() for _ in range(3)]
    assert first_pass == second_pass


def test_t3_no_actuator_shaped_methods():
    forbidden_substrings = ("pwm", "esc", "motor", "mixer", "arm", "actuat")
    for module, classes in (
        (hal_module, [ImuHal]),
        (sim_imu_hal_module, [SimulatedImuHal]),
    ):
        for cls in classes:
            for attr_name in dir(cls):
                if attr_name.startswith("_"):
                    continue
                lowered = attr_name.lower()
                for token in forbidden_substrings:
                    assert token not in lowered, (
                        f"{module.__name__}.{cls.__name__}.{attr_name} looks "
                        f"like an actuation path (matched '{token}')"
                    )


def test_t4_smoke_profile_declares_hal_imu_rung():
    profile = load_profile("smoke_quad_hal_imu")
    assert isinstance(profile, VehicleProfile)
    assert profile.id == "smoke_quad_hal_imu"
    assert profile.rung == "hal_imu"


def test_t5_run_hal_imu_smoke_returns_at_least_one_sample():
    samples = run_hal_imu_smoke()
    assert len(samples) >= 1
    assert all(isinstance(s, ImuSample) for s in samples)


def test_t6_safety_gate_unchanged_still_reject_all():
    assert not hasattr(safety_module, "AllowAllSafetyGate")
    import jarvis.capabilities as capabilities_module

    assert not hasattr(capabilities_module, "AllowAllSafetyGate")

    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)

    from jarvis.capabilities import SafetyRequest

    decision = gate.evaluate(SafetyRequest())
    assert decision.outcome == "reject"


def test_t7_capability_registry_default_still_empty():
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


def test_t9_flight_software_not_imported_by_orchestrator_or_craft_paths():
    """This Buy's own boundary: zero `core`/`adapters` coupling to
    `jarvis.flight_software`/`jarvis.vehicle_profiles` at this Buy's
    time. T6 (`B1-assistant-vehicle-hold-task`) is the later,
    separately-authorized Buy that deliberately opens exactly one such
    edge — `core/orchestrator.py`'s own `_handle_vehicle_hold` fulfill
    helper, which proposes/submits a HOLD command through
    `flight_software.autonomy` (DC §0 row 8) — see
    `tests/test_assistant_vehicle_hold_task_b1.py` for that path's own
    tests. This test now scopes to every other `core`/`adapters` file,
    which still carries zero such coupling; the `jarvis.vehicle_profiles`
    half is completely unaffected (orchestrator still never imports
    that package)."""
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    authorized_orchestrator_path = core_dir / "orchestrator.py"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            if py_file != authorized_orchestrator_path:
                assert "jarvis.flight_software" not in text, (
                    f"{py_file} imports jarvis.flight_software — forbidden craft coupling"
                )
            assert "jarvis.vehicle_profiles" not in text, (
                f"{py_file} imports jarvis.vehicle_profiles — forbidden craft coupling"
            )


def test_vehicle_profile_rejects_unknown_rung():
    with pytest.raises(Exception):
        VehicleProfile(id="x", rung="attitude_control")


def test_imu_hal_protocol_is_structurally_satisfied_by_simulated_imu_hal():
    hal: ImuHal = SimulatedImuHal(seed=0)
    assert isinstance(hal.read_imu(), ImuSample)


def test_no_cpp_or_cmake_tree_created():
    """Engineer amendment on the C3 IC: this Buy is a Python scaffold only —
    the production flight_control runtime will be C++ in a future IC, with
    no C++ source or CMake tree created here."""
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


def test_package_docstrings_carry_python_scaffold_amendment():
    from jarvis import flight_software, vehicle_profiles
    from jarvis.flight_software import flight_control

    expected = "Python scaffold / sim only — production flight_control runtime is C++"
    for module in (flight_software, flight_control, vehicle_profiles):
        assert expected in (module.__doc__ or ""), (
            f"{module.__name__} is missing the Engineer amendment phrase"
        )
