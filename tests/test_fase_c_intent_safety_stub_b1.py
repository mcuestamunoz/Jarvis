"""Tests T1-T9 for `B1-fase-c-intent-safety-stub`.

T10 (full craft suite stays green) and T11 (report confirms H-locks) are
process gates covered by running the full suite and by
`.jes/artifacts/implementation_report_fase_c_intent_safety_stub_b1.md`.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest
from pydantic import ValidationError

from jarvis.capabilities import (
    ApiIntentAdapter,
    AuthoritySignal,
    CapabilityRegistry,
    Intent,
    IntentSource,
    RadioIntentAdapter,
    RejectAllSafetyGate,
    SafetyDecision,
    SafetyGate,
    SafetyRequest,
    TerminalIntentAdapter,
    VoiceIntentAdapter,
    default_safety_gate,
    run_intent_through_safety,
)
from jarvis.capabilities import intent as intent_module
from jarvis.capabilities import safety as safety_module

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_t1_terminal_adapter_builds_intent():
    result = TerminalIntentAdapter.parse("hola")
    assert isinstance(result, Intent)
    assert result.source == IntentSource.TERMINAL
    assert result.raw_text == "hola"
    assert result.id


def test_t2_voice_radio_api_adapters_refuse():
    for adapter in (VoiceIntentAdapter, RadioIntentAdapter, ApiIntentAdapter):
        with pytest.raises(NotImplementedError, match="not_implemented"):
            adapter.parse("anything")


def test_t3_default_gate_always_rejects_not_implemented():
    decision = default_safety_gate().evaluate(SafetyRequest(intent_id="x"))
    assert isinstance(decision, SafetyDecision)
    assert decision.outcome == "reject"
    assert "not_implemented" in decision.reason
    assert isinstance(default_safety_gate(), RejectAllSafetyGate)


def test_t4_allow_all_gate_does_not_exist_under_src():
    assert not hasattr(safety_module, "AllowAllSafetyGate")
    import jarvis.capabilities as capabilities_module

    assert not hasattr(capabilities_module, "AllowAllSafetyGate")


def test_t5_run_intent_through_safety_rejects_with_default_gate():
    intent = TerminalIntentAdapter.parse("despega")
    decision = run_intent_through_safety(intent, default_safety_gate())
    assert decision.outcome == "reject"
    assert decision.reason == "not_implemented"


def test_t6_authority_signal_is_data_only():
    signal = AuthoritySignal(source="radio", kind="unknown", payload=None)
    assert signal.source == "radio"
    assert signal.kind == "unknown"
    with pytest.raises(ValidationError):
        AuthoritySignal(source="elrs_channel_3", kind="unknown")


def test_t7_no_execute_dispatch_command_esc_in_new_modules():
    forbidden_substrings = ("execute", "dispatch", "command_esc", "actuat")
    for module in (intent_module, safety_module):
        for name, obj in vars(module).items():
            if name.startswith("_") or not inspect.isclass(obj):
                continue
            for attr_name in dir(obj):
                if attr_name.startswith("_"):
                    continue
                lowered = attr_name.lower()
                for token in forbidden_substrings:
                    assert token not in lowered, (
                        f"{module.__name__}.{name}.{attr_name} looks like an "
                        f"execution path (matched '{token}')"
                    )


def test_t8_capability_registry_default_still_descriptive_only():
    """C2 originally asserted the registry stays empty (T8's original
    name/assert). T2 (`B1-capability-registry-product-fill`) gave the
    checked-in seed its first honest, non-empty capabilities()/
    providers() rows — full assertions on that shape live in
    `tests/test_capability_registry_product_fill_b1.py`. T5
    (`B1-capability-skills-seed`) later filled `skills()` too — two
    declared-only stub rows, see `tests/test_capability_skills_seed_
    b1.py`. What this test still guarantees, unchanged since C2: the
    registry is still purely descriptive (no dispatcher method — see
    T2's own T6, same grain as C1's T9)."""
    registry = CapabilityRegistry.load_default()
    forbidden_substrings = ("execute", "dispatch", "command_esc", "actuat", "run_skill")
    public_members = [name for name in dir(CapabilityRegistry) if not name.startswith("_")]
    for name in public_members:
        lowered = name.lower()
        for token in forbidden_substrings:
            assert token not in lowered


def test_t9_pyproject_version_stays_0_6_10():
    """Bumped forward by T2 (B1-capability-registry-product-fill) per
    established pattern — was last accurate at 0.5.44 (C2's own tip),
    itself already long stale before this Buy touched the file."""
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.6.15"' in text


def test_safety_decision_requires_reason_on_reject():
    with pytest.raises(ValidationError):
        SafetyDecision(outcome="reject", reason="", gate_id="x")


def test_safety_gate_is_structurally_satisfied_by_reject_all():
    gate: SafetyGate = RejectAllSafetyGate()
    assert gate.evaluate(SafetyRequest()).outcome == "reject"
