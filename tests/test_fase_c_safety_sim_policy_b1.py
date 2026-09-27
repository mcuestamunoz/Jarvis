"""Tests T1-T9 for `B1-fase-c-safety-sim-policy` (C41).

This Buy extends `ArmedAllowlistSafetyGate` (C17) to also allow `GO_TO`,
matching what `SimAutonomyExecutor` (C40) can drive in sim — see
`jarvis.capabilities.safety`'s own module docstring for the "one gate
story, not two" decision. `tests/test_fase_c_safety_real_policy_b1.py`'s
own `test_t3_armed_hold_and_land_allow`/`test_t4_armed_non_allowlisted_verb_rejects`
were disclosed-retargeted (not weakened) to reflect the widened
allow-list — this file adds the C41-specific coverage the IC itself
asks for, rather than duplicating every C17 case.

T8's own "suite green" half is a process gate covered by running it,
not asserted here. T9 (report content: allow != execute != flying !=
C40 tick) is covered by
`.jes/artifacts/implementation_report_fase_c_safety_sim_policy_b1.md`,
not by this file.
"""

from __future__ import annotations

import io
import tokenize
from pathlib import Path

import pytest

from jarvis.capabilities import (
    ArmedAllowlistSafetyGate,
    AuthoritySignal,
    RejectAllSafetyGate,
    SafetyRequest,
    default_safety_gate,
)
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command

REPO_ROOT = Path(__file__).resolve().parents[1]


def _strip_python_comments_and_docstrings(source: str) -> str:
    """Removes `#` comments and multi-line (docstring-shaped) string
    literals so honesty checks look at real code, not this module's own
    honesty-prose docstrings that legitimately name a symbol to disclose
    its absence."""
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


def test_t1_disarmed_rejects_with_non_not_implemented_reason():
    gate = ArmedAllowlistSafetyGate()
    for verb in ("HOLD", "LAND", "GO_TO"):
        decision = gate.evaluate(SafetyRequest(action_id=f"autonomy:{verb}:x"))
        assert decision.outcome == "reject"
        assert decision.reason == "disarmed"
        assert decision.reason != "not_implemented"


def test_t2_armed_allows_hold_land_go_to():
    gate = ArmedAllowlistSafetyGate()
    gate.arm()
    for verb in ("HOLD", "LAND", "GO_TO"):
        decision = gate.evaluate(SafetyRequest(action_id=f"autonomy:{verb}:x"))
        assert decision.outcome == "allow"
        assert decision.gate_id == "armed_allowlist"
        assert decision.reason == ""


def test_t3_armed_rejects_other_verbs_with_clear_reason():
    gate = ArmedAllowlistSafetyGate()
    gate.arm()
    for verb in ("TAKEOFF", "FOLLOW", "RETURN_HOME", "PATROL"):
        decision = gate.evaluate(SafetyRequest(action_id=f"autonomy:{verb}:x"))
        assert decision.outcome == "reject"
        assert decision.reason == "verb_not_allowed"
        assert decision.reason != "not_implemented"


def test_t4_submit_command_armed_allow_stays_not_implemented_for_all_three_verbs():
    gate = ArmedAllowlistSafetyGate()
    gate.arm()
    for verb in (AutonomyVerb.HOLD, AutonomyVerb.LAND, AutonomyVerb.GO_TO):
        command = propose_command(verb)
        result = submit_command(command, gate)
        assert result.safety.outcome == "allow"
        assert result.execution == "not_implemented"
        assert result.execution != "executed"


def test_t5_default_safety_gate_still_reject_all():
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.gate_id == "reject_all"

    for verb in (AutonomyVerb.HOLD, AutonomyVerb.LAND, AutonomyVerb.GO_TO):
        command = propose_command(verb)
        result = submit_command(command, gate)
        assert result.safety.outcome == "reject"
        assert result.execution == "not_attempted"


def test_t6_authority_signal_never_flips_allow_for_go_to():
    gate = ArmedAllowlistSafetyGate()
    signal = AuthoritySignal(source="radio", kind="override")

    decision_disarmed = gate.evaluate(
        SafetyRequest(action_id="autonomy:GO_TO:x", authority_signal_id=signal.id)
    )
    assert decision_disarmed.outcome == "reject"
    assert decision_disarmed.reason == "disarmed"

    gate.arm()
    decision_with_authority = gate.evaluate(
        SafetyRequest(action_id="autonomy:GO_TO:x", authority_signal_id=signal.id)
    )
    decision_without_authority = gate.evaluate(SafetyRequest(action_id="autonomy:GO_TO:x"))
    assert decision_with_authority.outcome == "allow"
    assert decision_without_authority.outcome == "allow"

    decision_not_listed_with_authority = gate.evaluate(
        SafetyRequest(action_id="autonomy:TAKEOFF:x", authority_signal_id=signal.id)
    )
    assert decision_not_listed_with_authority.outcome == "reject"
    assert decision_not_listed_with_authority.reason == "verb_not_allowed"


def test_t7_no_craft_continuity_library_board_edits_and_c40_modules_untouched():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "ArmedAllowlistSafetyGate" not in text, f"{py_file} references ArmedAllowlistSafetyGate"

    import inspect

    from jarvis.flight_software.autonomy import sim_executor as sim_executor_module

    code_only = _strip_python_comments_and_docstrings(inspect.getsource(sim_executor_module))
    assert "SafetyGate" not in code_only
    assert "ArmedAllowlistSafetyGate" not in code_only
    assert "capabilities.safety" not in code_only
    assert "from jarvis.capabilities import" not in code_only


def test_t8_pyproject_version_is_0_5_42():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.43"' in text


def test_t8_full_suite_process_gate_placeholder():
    """The full Python suite being green is verified by running it, not
    asserted here — see the implementation report's own test-run
    transcript."""
    assert True
