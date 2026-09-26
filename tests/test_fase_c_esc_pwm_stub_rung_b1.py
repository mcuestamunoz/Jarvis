"""Tests T1-T11 for `B1-fase-c-esc-pwm-stub-rung`.

T12 (full craft suite stays green) and T13 (report confirms PWM-us only
+ sim sink + != motors spinning + C++ honesty) are process gates covered
by running the full suite and by
`.jes/artifacts/implementation_report_fase_c_esc_pwm_stub_rung_b1.md`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command
from jarvis.flight_software.flight_control import (
    EscApplyResult,
    EscPwmCommand,
    MotorForceCommand,
    SimulatedEscSink,
    encode_motor_forces,
)
from jarvis.flight_software.flight_control import esc as esc_module
from jarvis.vehicle_profiles import run_esc_pwm_smoke

REPO_ROOT = Path(__file__).resolve().parents[1]


def _forces(values=(0.0, 0.5, 1.0, 0.25), t_s: float = 0.0) -> MotorForceCommand:
    return MotorForceCommand(t_s=t_s, motor_forces=values)


def test_t1_encoding_endpoints_and_midpoint():
    cmd = encode_motor_forces(_forces((0.0, 1.0, 0.5, 0.5)))
    assert cmd.pulse_us[0] == pytest.approx(1000.0)
    assert cmd.pulse_us[1] == pytest.approx(2000.0)
    assert cmd.pulse_us[2] == pytest.approx(1500.0)
    assert cmd.pulse_us[3] == pytest.approx(1500.0)


def test_t2_exactly_four_pulses_and_protocol():
    cmd = encode_motor_forces(_forces())
    assert isinstance(cmd, EscPwmCommand)
    assert len(cmd.pulse_us) == 4
    assert cmd.protocol == "pwm_us"


def test_t3_invalid_min_max_rejected():
    for min_us, max_us in ((1000.0, 1000.0), (1500.0, 1000.0), (float("nan"), 2000.0), (1000.0, float("inf"))):
        with pytest.raises(ValueError):
            encode_motor_forces(_forces(), min_us=min_us, max_us=max_us)


def test_t4_disarmed_apply_does_not_claim_success():
    sink = SimulatedEscSink()
    assert sink.armed is False
    cmd = encode_motor_forces(_forces())
    result = sink.apply(cmd)
    assert isinstance(result, EscApplyResult)
    assert result.applied is False
    assert result.reason == "disarmed"
    assert sink.last_command() == cmd


def test_t5_armed_apply_records_last_command():
    sink = SimulatedEscSink()
    sink.arm()
    assert sink.armed is True
    cmd = encode_motor_forces(_forces())
    result = sink.apply(cmd)
    assert result.applied is True
    assert result.reason is None
    assert sink.last_command() == cmd

    sink.disarm()
    assert sink.armed is False


def test_t6_no_gpio_serial_dshot_shaped_public_symbols():
    forbidden_substrings = (
        "write_gpio",
        "open_serial",
        "send_dshot",
        "pigpio",
        "export_pwm",
    )
    for name, obj in vars(esc_module).items():
        if name.startswith("_"):
            continue
        lowered = name.lower()
        for token in forbidden_substrings:
            assert token not in lowered, f"esc.{name} looks forbidden-shaped ('{token}')"
        if isinstance(obj, type):
            for attr_name in dir(obj):
                if attr_name.startswith("_"):
                    continue
                lowered_attr = attr_name.lower()
                for token in forbidden_substrings:
                    assert token not in lowered_attr, (
                        f"esc.{name}.{attr_name} looks forbidden-shaped ('{token}')"
                    )


def test_t6b_no_known_gpio_library_imports():
    import inspect

    source = inspect.getsource(esc_module)
    for forbidden_import in ("import RPi", "import pigpio", "import serial", "import socket"):
        assert forbidden_import not in source


def test_t7_no_cpp_or_cmake_under_flight_software():
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


def test_t9_esc_symbols_not_imported_by_orchestrator_or_craft_paths():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "flight_control.esc" not in text, (
                f"{py_file} imports flight_control.esc — forbidden craft coupling"
            )
            assert "SimulatedEscSink" not in text, (
                f"{py_file} references SimulatedEscSink — forbidden craft coupling"
            )


def test_t10_capability_registry_default_still_empty():
    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []


def test_t11_pyproject_version_is_0_5_8():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.38"' in text


def test_smoke_esc_pwm_returns_at_least_one_result_disarmed_by_default():
    results = run_esc_pwm_smoke(samples=3)
    assert len(results) == 3
    assert all(isinstance(r, EscApplyResult) for r in results)
    assert all(r.applied is False for r in results)
    assert all(r.pulse_us is not None and len(r.pulse_us) == 4 for r in results)


def test_smoke_esc_pwm_armed_reports_applied():
    results = run_esc_pwm_smoke(samples=2, armed=True)
    assert all(r.applied is True for r in results)


def test_esc_pwm_command_rejects_wrong_length():
    with pytest.raises(Exception):
        EscPwmCommand(t_s=0.0, pulse_us=(1000.0, 1000.0, 1000.0))


def test_encode_clamps_out_of_range_force_defensively():
    cmd = encode_motor_forces(_forces((-1.0, 2.0, 0.0, 1.0)))
    assert cmd.pulse_us[0] == pytest.approx(1000.0)
    assert cmd.pulse_us[1] == pytest.approx(2000.0)


def test_custom_min_max_us_range():
    cmd = encode_motor_forces(_forces((0.0, 1.0, 0.5, 0.5)), min_us=900.0, max_us=2100.0)
    assert cmd.pulse_us[0] == pytest.approx(900.0)
    assert cmd.pulse_us[1] == pytest.approx(2100.0)
    assert cmd.pulse_us[2] == pytest.approx(1500.0)


def test_no_actuator_write_call_site_in_esc_module_source():
    """The module docstring is allowed to mention GPIO/serial/DShot in
    prose (documenting what it does not do) — this checks there is no
    actual call site."""
    import inspect

    source = inspect.getsource(esc_module)
    for forbidden_call in ("write_gpio(", "open_serial(", "send_dshot(", "pigpio.", "export_pwm("):
        assert forbidden_call not in source
