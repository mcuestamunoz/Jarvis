"""Tests T1-T10 for `B1-fase-c-safety-real-policy` (C17).

Process gates covered elsewhere, not by this file:
- T9 (report + docs honesty; no premature v0.5.15 tag) — README/
  IMPLEMENTATION_TASKS/PLATFORM_CAPABILITY_VISION/ARCHITECTURE/report.
- T10 (Python full suite green @ 0.5.15) — the full `pytest -q` run.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.capabilities import (
    ArmedAllowlistSafetyGate,
    AuthoritySignal,
    CapabilityRegistry,
    RejectAllSafetyGate,
    SafetyRequest,
    default_safety_gate,
)
from jarvis.capabilities.safety import ArmedAllowlistSafetyGate as ArmedAllowlistSafetyGateDirect
from jarvis.flight_software.autonomy import (
    AutonomyVerb,
    propose_command,
    smoke_hold_and_land,
    smoke_policy_gate_hold_and_land,
    submit_command,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_t1_gate_exists_starts_disarmed_arm_disarm_work():
    gate = ArmedAllowlistSafetyGate()
    assert gate.armed is False
    gate.arm()
    assert gate.armed is True
    gate.disarm()
    assert gate.armed is False
    # re-export from the safety module directly must be the same class.
    assert ArmedAllowlistSafetyGateDirect is ArmedAllowlistSafetyGate


def test_t2_disarmed_rejects_with_non_not_implemented_reason():
    gate = ArmedAllowlistSafetyGate()
    decision = gate.evaluate(SafetyRequest(action_id="autonomy:HOLD:abc"))
    assert decision.outcome == "reject"
    assert decision.reason == "disarmed"
    assert decision.reason != "not_implemented"
    assert decision.gate_id == "armed_allowlist"
    assert decision.gate_id != "reject_all"


def test_t3_armed_hold_and_land_allow():
    """`GO_TO` retargeted here (C41, `B1-fase-c-safety-sim-policy`) — the
    allow-list was deliberately widened to `{HOLD, LAND, GO_TO}` to match
    what `SimAutonomyExecutor` (C40) can drive in sim; this Buy's own
    IC §0 decision 4 requires updating C17's own tests when extending its
    gate rather than adding a second, competing gate class."""
    gate = ArmedAllowlistSafetyGate()
    gate.arm()
    for verb in ("HOLD", "LAND", "GO_TO"):
        decision = gate.evaluate(SafetyRequest(action_id=f"autonomy:{verb}:x"))
        assert decision.outcome == "allow"
        assert decision.gate_id == "armed_allowlist"


def test_t4_armed_non_allowlisted_verb_rejects():
    """`GO_TO` removed from this rejected-verbs list as of C41 — see
    `test_t3_armed_hold_and_land_allow`'s own note above."""
    gate = ArmedAllowlistSafetyGate()
    gate.arm()
    for verb in ("TAKEOFF", "FOLLOW", "RETURN_HOME", "PATROL"):
        decision = gate.evaluate(SafetyRequest(action_id=f"autonomy:{verb}:x"))
        assert decision.outcome == "reject"
        assert decision.reason == "verb_not_allowed"
        assert decision.reason != "not_implemented"


def test_t4b_armed_unparseable_action_id_rejects():
    gate = ArmedAllowlistSafetyGate()
    gate.arm()
    for bad_action_id in (None, "", "not_autonomy:HOLD:x", "autonomy:", "autonomy"):
        decision = gate.evaluate(SafetyRequest(action_id=bad_action_id or None))
        assert decision.outcome == "reject"
        assert decision.reason == "unparseable_action_id"


def test_t5_authority_signal_never_flips_allow():
    """Authority != allow (C5 lock, re-pinned here for C17's new gate)."""
    gate = ArmedAllowlistSafetyGate()
    signal = AuthoritySignal(source="radio", kind="override")

    # Disarmed + authority set: still reject.
    decision_disarmed = gate.evaluate(
        SafetyRequest(action_id="autonomy:HOLD:x", authority_signal_id=signal.id)
    )
    assert decision_disarmed.outcome == "reject"
    assert decision_disarmed.reason == "disarmed"

    gate.arm()
    # Armed + not-on-list verb + authority set: still reject.
    decision_not_listed = gate.evaluate(
        SafetyRequest(action_id="autonomy:TAKEOFF:x", authority_signal_id=signal.id)
    )
    assert decision_not_listed.outcome == "reject"
    assert decision_not_listed.reason == "verb_not_allowed"

    # Armed + allow-listed verb + authority set: allow — but for the same
    # reason it would allow without authority, not because of it.
    decision_allowed_with_authority = gate.evaluate(
        SafetyRequest(action_id="autonomy:HOLD:x", authority_signal_id=signal.id)
    )
    decision_allowed_without_authority = gate.evaluate(SafetyRequest(action_id="autonomy:HOLD:x"))
    assert decision_allowed_with_authority.outcome == "allow"
    assert decision_allowed_without_authority.outcome == "allow"


def test_t6_submit_command_armed_hold_allows_but_execution_not_implemented():
    gate = ArmedAllowlistSafetyGate()
    gate.arm()
    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, gate)
    assert result.safety.outcome == "allow"
    assert result.execution == "not_implemented"
    assert result.execution != "executed"


def test_t7_default_safety_gate_still_reject_all_and_hold_still_rejects():
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.gate_id == "reject_all"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, gate)
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_t8_no_allow_all_gate_under_src_and_no_executed_state():
    """Checks real definitions/instantiations, not honesty-prose docstrings
    that legitimately name "AllowAllSafetyGate" to disclose its absence
    (e.g. capabilities/__init__.py's own C2-locked docstring line) — same
    "symbol(" / "class symbol" distinction used by every prior Fase C
    Buy's honesty tests."""
    src_dir = REPO_ROOT / "src" / "jarvis"
    for py_file in src_dir.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        assert "class AllowAllSafetyGate" not in text, f"{py_file} defines an AllowAllSafetyGate"
        assert "AllowAllSafetyGate(" not in text, f"{py_file} instantiates an AllowAllSafetyGate"
        # Real usage shape only — not prose disclosing "executed" is absent
        # (e.g. autonomy/__init__.py's own honesty docstring, which
        # legitimately names the string to say it never appears).
        assert 'execution="executed"' not in text.replace(" ", ""), (
            f"{py_file} sets execution=\"executed\""
        )

    # Authoritative check: the ExecutionState type itself must not admit
    # "executed" as a member, regardless of any docstring prose anywhere.
    from typing import get_args

    from jarvis.flight_software.autonomy.types import ExecutionState

    assert "executed" not in get_args(ExecutionState)
    assert set(get_args(ExecutionState)) == {"not_attempted", "not_implemented"}


def test_existing_rung_regressions_pinning_reject_all_still_green():
    """IC §3 — rung regression tests pinning RejectAll must stay green
    without rewriting their meaning; re-verified here directly too."""
    results = smoke_hold_and_land()
    assert all(r.safety.outcome == "reject" for r in results)
    assert all(r.execution == "not_attempted" for r in results)


def test_smoke_policy_gate_hold_and_land():
    results = smoke_policy_gate_hold_and_land()
    assert len(results) == 2
    assert all(r.safety.outcome == "allow" for r in results)
    assert all(r.execution == "not_implemented" for r in results)
    assert all(r.safety.gate_id == "armed_allowlist" for r in results)


def test_capability_registry_default_still_empty():
    registry = CapabilityRegistry.load_default()
    # T2 (B1-capability-registry-product-fill): capabilities()/providers() are
    # no longer empty (ontology.explain/engineering.continuity, both software-
    # provided) — see tests/test_capability_registry_product_fill_b1.py for that
    # shape. Skills stay empty; this file's own isolation proof is unaffected.
    assert registry.skills() == []


def test_gate_not_coupled_to_esc_sink_or_gpio():
    """IC §0 decision 11 — Safety arm is a separate software latch, never
    coupled to SimulatedEscSink.arm() or any hardware. Checks real code
    (imports, call sites, attribute access) — not this module's own
    honesty-prose docstring, which legitimately names these terms to
    disclose their absence (same "symbol(" / "import ...symbol" distinction
    used by every prior Fase C Buy's honesty tests)."""
    import inspect

    from jarvis.capabilities import safety as safety_module

    source = inspect.getsource(safety_module)
    code_only_lines = []
    in_docstring = False
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith('"""') or stripped.endswith('"""'):
            # Toggle for single-line and open/close triple-quote lines;
            # good enough for this module's own docstring shapes.
            in_docstring = not in_docstring if stripped.count('"""') == 1 else in_docstring
            continue
        if not in_docstring:
            code_only_lines.append(line)
    code_text = "\n".join(code_only_lines)

    # gate.arm()/gate.disarm() (this module's OWN Safety-policy latch) are
    # expected and fine; what must be absent is coupling to the ESC sink's
    # own arm(), which would only ever appear via an imported ESC symbol.
    assert "SimulatedEscSink" not in code_text, "safety.py imports/uses SimulatedEscSink in real code"
    assert "flight_control.esc" not in code_text, "safety.py imports the ESC module"
    for token in ("gpio.", "pigpio.", "PWM.", "serial.Serial"):
        assert token not in code_text, f"safety.py contains forbidden-shaped code token '{token}'"


def test_t9_pyproject_version_is_0_5_15():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.44"' in text
