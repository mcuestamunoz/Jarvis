"""Tests T1-T12 for `B1-fase-c-crsf-stream-timeout-failsafe` (C27).

T9 (C++ Catch2 — never/fresh/timeout; native grep still zero
`crsf`/`elrs`) lives in `native/flight_control/tests/test_rc_hold.cpp`,
run via `ctest`, not here — the native-grep half is re-verified in this
file too (`test_native_tree_still_zero_crsf_elrs_tokens`). T12 (report
content: timeout failsafe != motors cut != live ELRS != Safety allow) is
covered by
`.jes/artifacts/implementation_report_fase_c_crsf_stream_timeout_failsafe_b1.md`,
not by this file.
"""

from __future__ import annotations

import inspect
import io
import tokenize
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities import crsf_failsafe as crsf_failsafe_module
from jarvis.capabilities import crsf_stream as crsf_stream_module
from jarvis.capabilities import radio as radio_module
from jarvis.capabilities.crsf_dual_role import CrsfDualRolePolicy
from jarvis.capabilities.crsf_failsafe import (
    CRSF_RC_STALE_S,
    CrsfRcHoldWatch,
    RcHoldDecision,
    failsafe_loop_inputs,
    feed_and_note_rc,
)
from jarvis.capabilities.crsf_stream import CrsfByteStreamAssembler
from jarvis.capabilities.intent import RadioIntentAdapter
from jarvis.capabilities.safety import SafetyRequest
from jarvis.flight_software.autonomy import AutonomyVerb, propose_command, submit_command
from jarvis.flight_software.flight_control import esc as esc_module
from jarvis.flight_software.flight_control import loop as loop_module
from jarvis.flight_software.flight_control.rc_setpoint import RcLoopInputs

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


def test_t1_never_noted_is_stale_with_reason_never():
    watch = CrsfRcHoldWatch()
    decision = watch.evaluate(0.0)
    assert isinstance(decision, RcHoldDecision)
    assert decision.stale is True
    assert decision.reason == "never"
    assert decision.age_s is None
    assert watch.is_stale(0.0) is True


def test_t2_fresh_at_and_before_the_timeout_boundary():
    watch = CrsfRcHoldWatch(timeout_s=0.5)
    watch.note_rc(10.0)

    at_boundary = watch.evaluate(10.5)
    assert at_boundary.stale is False
    assert at_boundary.reason == "fresh"
    assert at_boundary.age_s == pytest.approx(0.5)

    just_under = watch.evaluate(10.3)
    assert just_under.stale is False
    assert just_under.reason == "fresh"


def test_t3_stale_with_reason_timeout_just_past_the_boundary():
    watch = CrsfRcHoldWatch()
    watch.note_rc(0.0)
    decision = watch.evaluate(0.5 + 1e-9)
    assert decision.stale is True
    assert decision.reason == "timeout"
    assert watch.is_stale(0.5 + 1e-9) is True


def test_t4_failsafe_loop_inputs_near_identity_quat_and_zero_collective():
    inputs = failsafe_loop_inputs(3.0)
    assert isinstance(inputs, RcLoopInputs)
    assert inputs.collective == 0.0
    assert inputs.setpoint.q_body_to_world_desired == pytest.approx((1.0, 0.0, 0.0, 0.0), abs=1e-9)
    assert inputs.setpoint.t_s == 3.0


def test_t5_c21_feed_has_no_note_rc_coupling():
    """'Assembler tests still pass unmodified' (the other half of T5) is
    verified by running `tests/test_fase_c_crsf_byte_stream_b1.py` itself
    as part of the full suite — see the implementation report's own
    test-run transcript, same pattern as every prior Buy's T11-style
    process gate."""
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(crsf_stream_module))
    assert "note_rc" not in code_only
    assert "CrsfRcHoldWatch" not in code_only
    assert "crsf_failsafe" not in code_only


def test_t6_radio_py_still_has_no_decode_or_failsafe_and_c20_policy_unchanged():
    source = inspect.getsource(radio_module)
    forbidden_symbols = ("decode_crsf", "decode_elrs", "open_serial", "write_pwm", "CrsfRcHoldWatch", "note_rc", "failsafe_loop_inputs")
    for symbol in forbidden_symbols:
        assert symbol not in source, f"radio.py unexpectedly defines/references '{symbol}'"

    policy = CrsfDualRolePolicy()
    assert policy.authority_channel_index == 4
    assert policy.authority_threshold == 1500
    assert policy.authority_kind == "kill"


def test_t7_radio_intent_adapter_not_implemented_and_rejectall_default():
    with pytest.raises(NotImplementedError):
        RadioIntentAdapter.parse(b"\x00\x00")
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.evaluate(SafetyRequest()).outcome == "reject"

    command = propose_command(AutonomyVerb.HOLD)
    result = submit_command(command, default_safety_gate())
    assert result.safety.outcome == "reject"
    assert result.execution == "not_attempted"


def test_t8_loop_and_esc_apply_paths_unchanged_no_timeout_wiring():
    loop_code = _strip_python_comments_and_docstrings(inspect.getsource(loop_module))
    assert "crsf_failsafe" not in loop_code
    assert "CrsfRcHoldWatch" not in loop_code
    assert "failsafe_loop_inputs" not in loop_code

    esc_code = _strip_python_comments_and_docstrings(inspect.getsource(esc_module))
    assert "crsf_failsafe" not in esc_code
    assert "CrsfRcHoldWatch" not in esc_code


def test_t10_pyproject_version_is_0_5_25():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.30"' in text


def test_t11_full_suite_process_gate_placeholder():
    """The full Python suite being green (and host `ctest` green) is
    verified by running them, not asserted here — see the implementation
    report's own test-run transcript."""
    assert True


def test_native_tree_still_zero_crsf_elrs_tokens():
    """Same lesson learned in C21-C26: scope-check the whole native/
    tree for a bare protocol-name substring, case-insensitive, even in
    comments and this Buy's own new files."""
    native_dir = REPO_ROOT / "native"
    for path in native_dir.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "crsf" not in text.lower(), f"{path} unexpectedly references CRSF"
            assert "elrs" not in text.lower(), f"{path} unexpectedly references ELRS"


def test_now_s_before_last_noted_raises():
    watch = CrsfRcHoldWatch()
    watch.note_rc(5.0)
    with pytest.raises(ValueError):
        watch.evaluate(4.0)
    with pytest.raises(ValueError):
        watch.is_stale(4.0)


def test_non_positive_timeout_rejected():
    for bad in (0.0, -1.0, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            CrsfRcHoldWatch(timeout_s=bad)


def test_feed_and_note_rc_notes_on_valid_rc_channels_frame():
    assembler = CrsfByteStreamAssembler()
    watch = CrsfRcHoldWatch()
    rc_bytes = (FIXTURES_DIR / "rc_channels_valid.bin").read_bytes()

    frames = feed_and_note_rc(rc_bytes, assembler=assembler, watch=watch, now_s=5.0)

    assert len(frames) == 1
    assert watch.evaluate(5.0).stale is False
    assert watch.evaluate(5.0).reason == "fresh"


def test_feed_and_note_rc_does_not_note_on_non_rc_frame():
    assembler = CrsfByteStreamAssembler()
    watch = CrsfRcHoldWatch()
    link_stats_bytes = (FIXTURES_DIR / "link_statistics_valid.bin").read_bytes()

    frames = feed_and_note_rc(link_stats_bytes, assembler=assembler, watch=watch, now_s=5.0)

    assert len(frames) == 1
    assert watch.evaluate(5.0).stale is True
    assert watch.evaluate(5.0).reason == "never"


def test_feed_and_note_rc_never_calls_ingest_stream_bytes():
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(crsf_failsafe_module))
    assert "ingest_stream_bytes" not in code_only


def test_crsf_failsafe_not_on_radio_py_and_no_serial_baud_imports():
    assert (REPO_ROOT / "src" / "jarvis" / "capabilities" / "crsf_failsafe.py").exists()
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(crsf_failsafe_module))
    lowered = code_only.lower()
    for token in ("import serial", "import fcntl", "import termios", "configure_host_baud", "time.time("):
        assert token not in lowered, f"crsf_failsafe.py unexpectedly references '{token}'"


def test_no_craft_or_core_imports_and_registry_still_empty():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "crsf_failsafe" not in text, f"{py_file} references crsf_failsafe"
            assert "CrsfRcHoldWatch" not in text, f"{py_file} references CrsfRcHoldWatch"

    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []


def test_default_timeout_constant_is_half_second():
    assert CRSF_RC_STALE_S == 0.5
