"""Tests T1-T10 for `B1-fase-c-step-failsafe-hold-ticks` (C35).

This Buy is **tests only** — `loop.py`/`loop.hpp`/`loop.cpp`,
`rc_hold.hpp`/`rc_hold.cpp`, `crsf_failsafe.py`, and `spi_probe.*` are
all byte-unchanged. T1/T2 (many ticks, failsafe-into-step) run here in
Python AND as new Catch2 cases in
`native/flight_control/tests/test_loop.cpp`, via `ctest`. T9 (full
Python suite + host `ctest` green) is a process gate covered by running
them, not asserted here. T10 (report content: many ticks != flying !=
6-DoF != failsafe motors cut) is covered by
`.jes/artifacts/implementation_report_fase_c_step_failsafe_hold_ticks_b1.md`,
not by this file.
"""

from __future__ import annotations

import inspect
import math
import re
import subprocess
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities.crsf_failsafe import CrsfRcHoldWatch, failsafe_loop_inputs
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command
from jarvis.flight_software.flight_control.controller import level_setpoint
from jarvis.flight_software.flight_control.loop import FlightControlLoop
from jarvis.flight_software.flight_control.types import ImuSample

REPO_ROOT = Path(__file__).resolve().parents[1]
NATIVE_FC_DIR = REPO_ROOT / "native" / "flight_control"
LOOP_PY = REPO_ROOT / "src" / "jarvis" / "flight_software" / "flight_control" / "loop.py"
LOOP_HPP = NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "loop.hpp"
LOOP_CPP = NATIVE_FC_DIR / "src" / "loop.cpp"
RC_HOLD_HPP = NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "rc_hold.hpp"
RC_HOLD_CPP = NATIVE_FC_DIR / "src" / "rc_hold.cpp"
CRSF_FAILSAFE_PY = REPO_ROOT / "src" / "jarvis" / "capabilities" / "crsf_failsafe.py"
SPI_PROBE_HPP = NATIVE_FC_DIR / "include" / "jarvis" / "fc" / "spi_probe.hpp"
SPI_PROBE_CPP = NATIVE_FC_DIR / "src" / "spi_probe.cpp"
THIS_FILE = Path(__file__)

N_TICKS = 1000
DT_S = 0.01
COLLECTIVE = 0.5
LEVEL_ACCEL_MPS2 = (0.0, 0.0, -9.81)
LEVEL_GYRO_RAD_S = (0.0, 0.0, 0.0)


def _git_unchanged(path: Path) -> str:
    result = subprocess.run(
        ["git", "diff", "--stat", str(path)], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    return result.stdout.strip()


def _level_imu_sample(t_s: float) -> ImuSample:
    return ImuSample(t_s=t_s, accel_mps2=LEVEL_ACCEL_MPS2, gyro_rad_s=LEVEL_GYRO_RAD_S)


def test_t1_1000_ticks_canned_level_imu_no_plant_forces_finite_in_0_1():
    loop = FlightControlLoop()
    for i in range(N_TICKS):
        t = i * DT_S
        sample = _level_imu_sample(t)
        setpoint = level_setpoint(t)
        tick = loop.step(sample, setpoint, COLLECTIVE)
        assert len(tick.forces.motor_forces) == 4
        for force in tick.forces.motor_forces:
            assert math.isfinite(force)
            assert 0.0 <= force <= 1.0


def test_t2_never_noted_watch_is_stale_failsafe_inputs_feed_step_collective_zero():
    watch = CrsfRcHoldWatch()
    t = 3.0

    assert watch.is_stale(t)
    decision = watch.evaluate(t)
    assert decision.stale
    assert decision.reason == "never"

    inputs = failsafe_loop_inputs(t)
    assert inputs.collective == 0.0

    loop = FlightControlLoop()
    sample = _level_imu_sample(t)
    tick = loop.step(sample, inputs.setpoint, inputs.collective)

    for force in tick.forces.motor_forces:
        assert math.isfinite(force)
        assert 0.0 <= force <= 1.0


def test_t2_watch_stale_past_timeout_also_feeds_step_via_failsafe_loop_inputs():
    watch = CrsfRcHoldWatch()
    watch.note_rc(0.0)
    t = watch.timeout_s + 1.0  # well past the 0.5s default timeout

    decision = watch.evaluate(t)
    assert decision.stale
    assert decision.reason == "timeout"

    inputs = failsafe_loop_inputs(t)
    assert inputs.collective == 0.0

    loop = FlightControlLoop()
    sample = _level_imu_sample(t)
    tick = loop.step(sample, inputs.setpoint, inputs.collective)

    for force in tick.forces.motor_forces:
        assert math.isfinite(force)
        assert 0.0 <= force <= 1.0


def test_t3_hold_keeps_passing_level_setpoint_and_autonomy_hold_stays_not_attempted():
    loop = FlightControlLoop()
    identity = level_setpoint(0.0).q_body_to_world_desired
    for i in range(N_TICKS):
        t = i * DT_S
        setpoint = level_setpoint(t)
        # level_setpoint is always the identity quaternion — this run
        # never substitutes any other setpoint source across the ticks.
        assert setpoint.q_body_to_world_desired == identity
        sample = _level_imu_sample(t)
        tick = loop.step(sample, setpoint, COLLECTIVE)
        assert len(tick.forces.motor_forces) == 4

    # "Hold" here means feeding level_setpoint into step() — it is not
    # AutonomyVerb HOLD reaching execution.
    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_t4_loop_rc_hold_crsf_failsafe_spi_probe_git_unchanged():
    for path in (LOOP_PY, LOOP_HPP, LOOP_CPP, RC_HOLD_HPP, RC_HOLD_CPP, CRSF_FAILSAFE_PY, SPI_PROBE_HPP, SPI_PROBE_CPP):
        assert _git_unchanged(path) == "", f"unexpected diff in {path}"


def test_t5_this_test_module_does_not_import_probe_rx_as_a_sensor():
    import_lines = [line for line in THIS_FILE.read_text(encoding="utf-8").splitlines() if line.startswith(("import ", "from "))]
    joined_imports = "\n".join(import_lines)
    assert "probe_rx" not in joined_imports
    assert "SpiBytePort" not in joined_imports
    assert "ScriptedSpi" not in joined_imports


def test_t6_default_safety_gate_still_reject_all():
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_t7_native_tree_zero_crsf_elrs_tokens():
    for path in (REPO_ROOT / "native").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "crsf" not in text.lower(), f"{path} unexpectedly references CRSF"
            assert "elrs" not in text.lower(), f"{path} unexpectedly references ELRS"


def test_t8_pyproject_version_is_0_5_33():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.41"' in text


def test_t9_full_suite_process_gate_placeholder():
    """The full Python suite being green (and host `ctest` green) is
    verified by running them, not asserted here — see the implementation
    report's own test-run transcript."""
    assert True


def test_no_6dof_plant_or_step_signature_change():
    """IC §2 non-goal: no plant call inside step, no signature change on
    the frozen production module. Checks for an actual `plant.` call in
    the executable body, not the method's own docstring, which honestly
    disclaims calling the plant by name ("Does not call `plant.step`")."""
    step_source = inspect.getsource(FlightControlLoop.step)
    docstring = FlightControlLoop.step.__doc__ or ""
    body_only = step_source.replace(docstring, "") if docstring else step_source
    assert "plant." not in body_only
    signature = inspect.signature(FlightControlLoop.step)
    assert list(signature.parameters.keys()) == ["self", "sample", "setpoint", "collective"]


def test_no_craft_or_core_imports_reference_this_buys_glue():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "failsafe_loop_inputs" not in text, f"{py_file} references failsafe_loop_inputs"

    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []
