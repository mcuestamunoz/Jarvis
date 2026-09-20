"""Tests T1-T11 for `B1-fase-c-autonomy-surface`.

T12 (full craft suite stays green) and T13 (report confirms H-locks +
"surface != live autonomy" + C++ FC honesty) are process gates covered by
running the full suite and by
`.jes/artifacts/implementation_report_fase_c_autonomy_surface_b1.md`.
T11 (no new .cpp/CMake) is covered by
`tests/test_fase_c_first_fc_rung_b1.py::test_no_cpp_or_cmake_tree_created`,
which already walks the whole `flight_software/` tree (autonomy included).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities import safety as safety_module
from jarvis.capabilities.safety import SafetyDecision, SafetyRequest
from jarvis.flight_software.autonomy import (
    AutonomyCommand,
    AutonomySubmissionResult,
    AutonomyVerb,
    propose_command,
    smoke_hold_and_land,
    submit_command,
)
from jarvis.flight_software.autonomy import surface as surface_module
from jarvis.flight_software.autonomy import types as types_module

REPO_ROOT = Path(__file__).resolve().parents[1]


class _LocalAllowGate:
    """Test-local fake gate — never shipped in src/. Exists only to prove
    T7: even an 'allow' outcome must not make submit_command 'executed'."""

    def evaluate(self, request: SafetyRequest) -> SafetyDecision:
        return SafetyDecision(outcome="allow", reason="test-only fake", gate_id="local_allow")


def test_t1_propose_hold_command():
    command = propose_command(AutonomyVerb.HOLD)
    assert isinstance(command, AutonomyCommand)
    assert command.verb == AutonomyVerb.HOLD
    assert command.id


def test_t2_submit_hold_rejects_under_default_gate():
    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert isinstance(result, AutonomySubmissionResult)
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_t3_submit_land_rejects_under_default_gate():
    command = propose_command(AutonomyVerb.LAND)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_t4_every_verb_can_be_proposed():
    for verb in AutonomyVerb:
        command = propose_command(verb)
        assert command.verb == verb


def test_t5_no_actuator_shaped_public_methods_under_autonomy():
    forbidden_substrings = ("pwm", "esc", "motor", "mixer", "arm", "actuat")
    for module in (surface_module, types_module):
        for name, obj in vars(module).items():
            if name.startswith("_"):
                continue
            if isinstance(obj, type) and issubclass(obj, BaseModel):
                attr_names = list(obj.model_fields)
            elif callable(obj):
                attr_names = [name]
            else:
                continue
            for attr_name in attr_names:
                lowered = attr_name.lower()
                for token in forbidden_substrings:
                    assert token not in lowered, (
                        f"{module.__name__}.{name}.{attr_name} looks like an "
                        f"actuation path (matched '{token}')"
                    )


def test_t6_allow_all_gate_absent_and_default_still_reject():
    assert not hasattr(safety_module, "AllowAllSafetyGate")
    import jarvis.capabilities as capabilities_module

    assert not hasattr(capabilities_module, "AllowAllSafetyGate")
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.evaluate(SafetyRequest()).outcome == "reject"


def test_t7_local_allow_gate_still_never_executed():
    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, _LocalAllowGate())
    assert result.safety.outcome == "allow"
    assert result.execution == "not_implemented"
    assert result.execution != "executed"


def test_t8_capability_registry_default_still_empty():
    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []


def test_t9_pyproject_version_is_0_5_2():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.6"' in text


def test_t10_autonomy_not_imported_by_orchestrator_or_craft_paths():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "flight_software.autonomy" not in text, (
                f"{py_file} imports flight_software.autonomy — forbidden craft coupling"
            )


def test_smoke_hold_and_land_uses_default_reject_gate():
    results = smoke_hold_and_land()
    assert len(results) == 2
    assert [r.verb for r in results] == [AutonomyVerb.HOLD, AutonomyVerb.LAND]
    for result in results:
        assert result.safety.outcome == "reject"
        assert result.execution == "not_attempted"


def test_autonomy_command_rejects_unknown_extra_field():
    with pytest.raises(Exception):
        AutonomyCommand(verb=AutonomyVerb.HOLD, unexpected_field="x")


def test_autonomy_package_docstring_carries_python_scaffold_amendment():
    from jarvis.flight_software import autonomy

    expected = "Python scaffold / sim only — production flight_control runtime is C++"
    assert expected in (autonomy.__doc__ or "")
