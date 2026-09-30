"""Tests T1-T12 for `B1-fase-c-crsf-dual-role-bridge` (C20).

T12 (report states bridge != live ELRS != Safety allow) is covered by
`.jes/artifacts/implementation_report_fase_c_crsf_dual_role_bridge_b1.md`,
not by this file.
"""

from __future__ import annotations

import inspect
import io
import tokenize
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities import crsf_dual_role as crsf_dual_role_module
from jarvis.capabilities import radio as radio_module
from jarvis.capabilities.crsf_dual_role import (
    CrsfDualRolePolicy,
    ingest_rc_channels,
    rc_channels_to_stub_frame,
)
from jarvis.capabilities.crsf_stub import (
    CrsfRcChannels,
    decode_link_statistics,
    decode_rc_channels_packed,
    parse_crsf_frame,
)
from jarvis.capabilities.intent import RadioIntentAdapter
from jarvis.capabilities.radio import RadioDualRoleResult, RadioStubFrame, SimulatedRadioIngress
from jarvis.capabilities.safety import ArmedAllowlistSafetyGate, SafetyRequest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "crsf"


def _strip_python_comments_and_docstrings(source: str) -> str:
    """Removes `#` comments and multi-line (docstring-shaped) string
    literals so honesty checks look at real code, not this module's own
    honesty-prose docstrings (same distinction every prior Fase C Buy's
    honesty tests make)."""
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


def _channels(*, aux_value: int, aux_index: int = 4, base: int = 992) -> CrsfRcChannels:
    values = [base] * 16
    values[aux_index] = aux_value
    return CrsfRcChannels(channels=tuple(values))


def test_t1_channel_at_or_above_threshold_gives_authority_kill_frame():
    policy = CrsfDualRolePolicy()
    channels = _channels(aux_value=policy.authority_threshold + 100)
    frame = rc_channels_to_stub_frame(channels, policy=policy)
    assert isinstance(frame, RadioStubFrame)
    assert frame.role == "authority"
    assert frame.authority_kind == "kill"
    assert frame.intent_text == ""

    # Exactly at threshold also fires (>=).
    at_threshold = _channels(aux_value=policy.authority_threshold)
    frame_at = rc_channels_to_stub_frame(at_threshold, policy=policy)
    assert frame_at is not None
    assert frame_at.role == "authority"


def test_t2_channel_below_threshold_gives_none():
    policy = CrsfDualRolePolicy()
    channels = _channels(aux_value=policy.authority_threshold - 1)
    frame = rc_channels_to_stub_frame(channels, policy=policy)
    assert frame is None


def test_t3_ingest_helper_returns_dual_role_result_with_radio_authority_and_no_intent():
    policy = CrsfDualRolePolicy()
    channels = _channels(aux_value=policy.authority_threshold + 1)
    result = ingest_rc_channels(channels, policy=policy)
    assert isinstance(result, RadioDualRoleResult)
    assert result.intent is None
    assert result.authority is not None
    assert result.authority.source == "radio"
    assert result.authority.kind == "kill"


def test_t3b_ingest_helper_returns_none_when_below_threshold():
    policy = CrsfDualRolePolicy()
    channels = _channels(aux_value=policy.authority_threshold - 1)
    result = ingest_rc_channels(channels, policy=policy)
    assert result is None


def test_t3c_ingest_helper_accepts_explicit_ingress_instance():
    policy = CrsfDualRolePolicy()
    channels = _channels(aux_value=policy.authority_threshold + 1)
    ingress = SimulatedRadioIngress()
    result = ingest_rc_channels(channels, policy=policy, ingress=ingress)
    assert isinstance(result, RadioDualRoleResult)


def test_t4_end_to_end_from_c19_fixture_parse_decode_bridge():
    data = (FIXTURES_DIR / "rc_channels_valid.bin").read_bytes()
    frame = parse_crsf_frame(data)
    rc = decode_rc_channels_packed(frame.payload)

    policy = CrsfDualRolePolicy()
    # The C19 fixture has every channel at the neutral mid value (992) —
    # confirm the real end-to-end path yields no dual-role frame there.
    assert rc_channels_to_stub_frame(rc, policy=policy) is None

    # Force the policy's aux channel high in a mutated copy of the real
    # decoded values (IC §4 T4's "synthetic/mutated payload" option).
    mutated = list(rc.channels)
    mutated[policy.authority_channel_index] = policy.authority_threshold + 200
    high_rc = CrsfRcChannels(channels=tuple(mutated))
    bridged = rc_channels_to_stub_frame(high_rc, policy=policy)
    assert bridged is not None
    assert bridged.role == "authority"
    assert bridged.authority_kind == "kill"

    # Also exercise link-statistics enrichment end-to-end from a real fixture.
    ls_data = (FIXTURES_DIR / "link_statistics_valid.bin").read_bytes()
    ls_frame = parse_crsf_frame(ls_data)
    stats = decode_link_statistics(ls_frame.payload)
    enriched = rc_channels_to_stub_frame(high_rc, policy=policy, link_stats=stats)
    assert enriched is not None
    assert enriched.notes is not None
    assert "lq=" in enriched.notes


def test_t5_module_under_test_has_no_io_imports_or_device_open():
    source = inspect.getsource(crsf_dual_role_module)
    code_only = _strip_python_comments_and_docstrings(source)
    forbidden_imports = ("import serial", "import socket", "import pty", "import subprocess", "usb")
    for token in forbidden_imports:
        assert token not in code_only.lower(), f"crsf_dual_role.py unexpectedly imports/references '{token}'"
    assert "open(" not in code_only, "crsf_dual_role.py must not open any file/device path"


def test_t6_radio_intent_adapter_still_raises_not_implemented():
    with pytest.raises(NotImplementedError, match="not_implemented"):
        RadioIntentAdapter.parse(b"\x00\x00")

    policy = CrsfDualRolePolicy()
    channels = _channels(aux_value=policy.authority_threshold + 1)
    frame = rc_channels_to_stub_frame(channels, policy=policy)
    with pytest.raises(NotImplementedError, match="not_implemented"):
        RadioIntentAdapter.parse(frame)


def test_t7_radio_py_still_has_no_public_decode_or_serial_symbols():
    """C5 T5 lock, re-pinned here for C20."""
    source = inspect.getsource(radio_module)
    forbidden_symbols = ("decode_crsf", "decode_elrs", "open_serial", "write_pwm")
    for symbol in forbidden_symbols:
        assert symbol not in source, f"radio.py unexpectedly defines/references '{symbol}'"
    assert not hasattr(radio_module, "decode_crsf")
    assert not hasattr(radio_module, "decode_elrs")
    assert not hasattr(radio_module, "open_serial")


def test_t8_bridge_never_calls_submit_command_or_imports_autonomy():
    assert not hasattr(crsf_dual_role_module, "submit_command")
    assert not hasattr(crsf_dual_role_module, "propose_command")
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(crsf_dual_role_module))
    assert "flight_software" not in code_only
    assert "submit_command" not in code_only


def test_t9_default_safety_gate_still_reject_all_and_armed_allowlist_unchanged():
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.gate_id == "reject_all"

    armed_gate = ArmedAllowlistSafetyGate()
    assert armed_gate.armed is False
    decision = armed_gate.evaluate(SafetyRequest(action_id="autonomy:HOLD:x"))
    assert decision.outcome == "reject"
    assert decision.reason == "disarmed"


def test_authority_from_bridge_never_flips_safety():
    """Even wiring the bridge's own AuthoritySignal id into a SafetyRequest
    must not flip any shipped gate's decision — Authority stays trace-only
    (C5/C17 honesty, re-affirmed here for C20's own output)."""
    policy = CrsfDualRolePolicy()
    channels = _channels(aux_value=policy.authority_threshold + 1)
    result = ingest_rc_channels(channels, policy=policy)
    assert result is not None
    assert result.authority is not None

    default_decision = default_safety_gate().evaluate(
        SafetyRequest(action_id="autonomy:HOLD:x", authority_signal_id=result.authority.id)
    )
    assert default_decision.outcome == "reject"

    armed_gate = ArmedAllowlistSafetyGate()
    armed_gate.arm()
    armed_decision = armed_gate.evaluate(
        SafetyRequest(action_id="autonomy:TAKEOFF:x", authority_signal_id=result.authority.id)
    )
    assert armed_decision.outcome == "reject"
    assert armed_decision.reason == "verb_not_allowed"


def test_policy_validates_channel_index_and_threshold_ranges():
    with pytest.raises(Exception):
        CrsfDualRolePolicy(authority_channel_index=16)
    with pytest.raises(Exception):
        CrsfDualRolePolicy(authority_channel_index=-1)
    with pytest.raises(Exception):
        CrsfDualRolePolicy(authority_threshold=2048)
    with pytest.raises(Exception):
        CrsfDualRolePolicy(authority_threshold=-1)
    # Boundaries are valid.
    CrsfDualRolePolicy(authority_channel_index=0, authority_threshold=0)
    CrsfDualRolePolicy(authority_channel_index=15, authority_threshold=2047)


def test_no_crsf_or_elrs_under_native_and_no_craft_wiring():
    native_dir = REPO_ROOT / "native"
    for path in native_dir.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "crsf" not in text.lower(), f"{path} unexpectedly references CRSF"
            assert "elrs" not in text.lower(), f"{path} unexpectedly references ELRS"

    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "crsf_dual_role" not in text, f"{py_file} references crsf_dual_role"
            assert "CrsfDualRolePolicy" not in text, f"{py_file} references CrsfDualRolePolicy"


def test_capability_registry_default_still_empty():
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
    # tests/test_assistant_vehicle_land_task_b1.py. Still zero Skill
    # execution path anywhere; this file's own isolation proof is
    # unaffected either way.
    assert {skill.id for skill in registry.skills()} == {
        "skill.explain_concept",
        "skill.project_status",
        "skill.request_hold",
        "skill.request_land",
    }


def test_t10_pyproject_version_is_0_5_18():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.44"' in text
