"""Tests T1-T12 for `B1-fase-c-crsf-link-stub` (C19).

T12 (report states fixture CRSF != live ELRS != pilot link; no serial
product) is covered by `.jes/artifacts/implementation_report_fase_c_crsf_link_stub_b1.md`,
not by this file.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities import crsf_stub as crsf_stub_module
from jarvis.capabilities import radio as radio_module
from jarvis.capabilities.crsf_stub import (
    CRSF_FRAMETYPE_LINK_STATISTICS,
    CRSF_FRAMETYPE_RC_CHANNELS_PACKED,
    CrsfFrame,
    CrsfLinkStatistics,
    CrsfParseError,
    CrsfRcChannels,
    decode_link_statistics,
    decode_rc_channels_packed,
    describe_crsf_frame,
    parse_crsf_frame,
)
from jarvis.capabilities.intent import RadioIntentAdapter
from jarvis.capabilities.safety import ArmedAllowlistSafetyGate

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "crsf"


def _load_fixture(name: str) -> bytes:
    return (FIXTURES_DIR / name).read_bytes()


def test_t1_valid_rc_channels_fixture_decodes_to_16_channel_ints_in_range():
    data = _load_fixture("rc_channels_valid.bin")
    frame = parse_crsf_frame(data)
    assert isinstance(frame, CrsfFrame)
    assert frame.frame_type == CRSF_FRAMETYPE_RC_CHANNELS_PACKED
    assert frame.frame_type == 0x16

    rc = decode_rc_channels_packed(frame.payload)
    assert isinstance(rc, CrsfRcChannels)
    assert len(rc.channels) == 16
    for value in rc.channels:
        assert isinstance(value, int)
        assert 0 <= value <= 0x7FF
    # This fixture was constructed with every channel at CRSF mid value.
    assert rc.channels == (992,) * 16


def test_t2_truncated_frame_raises_typed_parse_error():
    data = _load_fixture("rc_channels_truncated.bin")
    with pytest.raises(CrsfParseError):
        parse_crsf_frame(data)


def test_t3_bad_crc_frame_raises_typed_parse_error():
    data = _load_fixture("rc_channels_bad_crc.bin")
    with pytest.raises(CrsfParseError, match="CRC8"):
        parse_crsf_frame(data)


def test_t4_valid_link_statistics_fixture_populates_typed_fields():
    data = _load_fixture("link_statistics_valid.bin")
    frame = parse_crsf_frame(data)
    assert frame.frame_type == CRSF_FRAMETYPE_LINK_STATISTICS
    assert frame.frame_type == 0x14

    stats = decode_link_statistics(frame.payload)
    assert isinstance(stats, CrsfLinkStatistics)
    assert stats.uplink_rssi_1 == 80
    assert stats.uplink_link_quality == 99
    assert stats.uplink_snr == -42
    assert stats.downlink_snr == -40


def _strip_python_comments_and_docstrings(source: str) -> str:
    """Removes `#` comments and triple-quoted docstrings so honesty checks
    look at real code, not this module's own honesty-prose docstrings
    (which legitimately name forbidden terms to disclose their absence —
    same distinction every prior Fase C Buy's honesty tests make)."""
    import io
    import tokenize

    out_tokens = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            if tok.type == tokenize.COMMENT:
                continue
            if tok.type == tokenize.STRING and "\n" in tok.string:
                continue  # multi-line (docstring-shaped) string literal
            out_tokens.append(tok.string)
    except tokenize.TokenizeError:
        return source
    return " ".join(out_tokens)


def test_t5_module_under_test_has_no_io_imports_or_device_open():
    source = inspect.getsource(crsf_stub_module)
    code_only = _strip_python_comments_and_docstrings(source)
    forbidden_imports = ("import serial", "import socket", "import pty", "import subprocess", "usb")
    for token in forbidden_imports:
        assert token not in code_only.lower(), f"crsf_stub.py unexpectedly imports/references '{token}'"
    assert "open(" not in code_only, "crsf_stub.py must not open any file/device path"


def test_t6_radio_intent_adapter_still_raises_not_implemented():
    with pytest.raises(NotImplementedError, match="not_implemented"):
        RadioIntentAdapter.parse(b"\x00\x00")

    # Feeding actual CRSF fixture bytes must not make it "succeed" either.
    valid = _load_fixture("rc_channels_valid.bin")
    with pytest.raises(NotImplementedError, match="not_implemented"):
        RadioIntentAdapter.parse(valid)


def test_t7_radio_py_still_has_no_public_decode_or_serial_symbols():
    """C5 T5 lock, re-pinned here for C19."""
    source = inspect.getsource(radio_module)
    forbidden_symbols = ("decode_crsf", "decode_elrs", "open_serial", "write_pwm")
    for symbol in forbidden_symbols:
        assert symbol not in source, f"radio.py unexpectedly defines/references '{symbol}'"
    assert not hasattr(radio_module, "decode_crsf")
    assert not hasattr(radio_module, "decode_elrs")
    assert not hasattr(radio_module, "open_serial")


def test_t8_no_crsf_or_elrs_under_native_and_no_craft_wiring():
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
            assert "crsf_stub" not in text, f"{py_file} references crsf_stub"
            assert "CrsfFrame" not in text, f"{py_file} references CrsfFrame"


def test_t9_default_safety_gate_still_reject_all_and_armed_allowlist_unchanged():
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.gate_id == "reject_all"

    # ArmedAllowlistSafetyGate behavior untouched by this Buy: still starts
    # disarmed, still has no knowledge of CRSF/radio bytes whatsoever.
    gate = ArmedAllowlistSafetyGate()
    assert gate.armed is False
    from jarvis.capabilities.safety import SafetyRequest

    decision = gate.evaluate(SafetyRequest(action_id="autonomy:HOLD:x"))
    assert decision.outcome == "reject"
    assert decision.reason == "disarmed"


def test_capability_registry_default_still_empty():
    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []


def test_describe_crsf_frame_is_pure_debug_helper():
    data = _load_fixture("rc_channels_valid.bin")
    frame = parse_crsf_frame(data)
    description = describe_crsf_frame(frame)
    assert isinstance(description, str)
    assert "0x16" in description
    assert "0xC8" in description


def test_rc_channels_wrong_payload_length_raises():
    with pytest.raises(CrsfParseError):
        decode_rc_channels_packed(b"\x00" * 21)
    with pytest.raises(CrsfParseError):
        decode_rc_channels_packed(b"\x00" * 23)


def test_link_statistics_wrong_payload_length_raises():
    with pytest.raises(CrsfParseError):
        decode_link_statistics(b"\x00" * 9)
    with pytest.raises(CrsfParseError):
        decode_link_statistics(b"\x00" * 11)


def test_crsf_frame_rejects_buffer_shorter_than_minimum():
    with pytest.raises(CrsfParseError):
        parse_crsf_frame(b"\x00\x00\x00")


def test_no_route_from_crsf_to_autonomy_submit_command():
    """Explicit negative test for IC §5's 'RC channels -> mixer/ESC/
    autonomy' forbidden path: this module exposes no such function at
    all, and nothing here imports flight_software.autonomy."""
    assert not hasattr(crsf_stub_module, "submit_command")
    assert not hasattr(crsf_stub_module, "propose_command")
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(crsf_stub_module))
    assert "flight_software" not in code_only
    assert "submit_command" not in code_only


def test_t10_pyproject_version_is_0_5_17():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.24"' in text
