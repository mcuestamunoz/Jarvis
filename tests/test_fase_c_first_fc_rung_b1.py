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
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []


def test_t8_pyproject_version_is_0_5_1():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.29"' in text


def test_t9_flight_software_not_imported_by_orchestrator_or_craft_paths():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
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
