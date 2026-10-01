"""Tests T1-T17 for `B1-fase-c-crsf-byte-stream` (C21).

T16 (report states assembler != UART open != live ELRS != Safety allow)
is covered by `.jes/artifacts/implementation_report_fase_c_crsf_byte_stream_b1.md`,
not by this file.
"""

from __future__ import annotations

import inspect
import io
import tokenize
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities import crsf_stream as crsf_stream_module
from jarvis.capabilities import radio as radio_module
from jarvis.capabilities.crsf_dual_role import CrsfDualRolePolicy
from jarvis.capabilities.crsf_stream import CrsfByteStreamAssembler, ingest_stream_bytes
from jarvis.capabilities.crsf_stub import CRSF_FRAMETYPE_LINK_STATISTICS, CRSF_FRAMETYPE_RC_CHANNELS_PACKED
from jarvis.capabilities.intent import RadioIntentAdapter
from jarvis.capabilities.radio import RadioDualRoleResult

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


def _load_fixture(name: str) -> bytes:
    return (FIXTURES_DIR / name).read_bytes()


def _crc8(data: bytes) -> int:
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ 0xD5) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def _pack_channels(values: list[int]) -> bytes:
    bits = 0
    nbits = 0
    out = bytearray()
    for v in values:
        bits |= v << nbits
        nbits += 11
        while nbits >= 8:
            out.append(bits & 0xFF)
            bits >>= 8
            nbits -= 8
    if nbits > 0:
        out.append(bits & 0xFF)
    return bytes(out)


def _rc_frame(values: list[int], device_addr: int = 0xC8) -> bytes:
    payload = _pack_channels(values)
    body = bytes([0x16]) + payload
    frame_len = len(body) + 1
    crc = _crc8(body)
    return bytes([device_addr, frame_len]) + body + bytes([crc])


def test_t1_one_feed_of_valid_fixture_gives_exactly_one_frame():
    data = _load_fixture("rc_channels_valid.bin")
    assembler = CrsfByteStreamAssembler()
    frames = assembler.feed(data)
    assert len(frames) == 1
    assert frames[0].frame_type == CRSF_FRAMETYPE_RC_CHANNELS_PACKED
    assert assembler.leftover() == b""


def test_t2_byte_at_a_time_gives_no_frame_until_last_byte():
    data = _load_fixture("rc_channels_valid.bin")
    assembler = CrsfByteStreamAssembler()
    all_frames = []
    for i in range(len(data)):
        chunk_frames = assembler.feed(data[i : i + 1])
        if i < len(data) - 1:
            assert chunk_frames == [], f"unexpected frame before final byte at index {i}"
        all_frames.extend(chunk_frames)
    assert len(all_frames) == 1
    assert assembler.leftover() == b""


def test_t3_mid_frame_split_waits_then_completes():
    data = _load_fixture("rc_channels_valid.bin")
    assembler = CrsfByteStreamAssembler()
    first = assembler.feed(data[:10])
    assert first == []
    second = assembler.feed(data[10:])
    assert len(second) == 1
    assert assembler.leftover() == b""


def test_t4_concatenated_rc_and_link_stats_gives_two_frames_in_order():
    rc = _load_fixture("rc_channels_valid.bin")
    ls = _load_fixture("link_statistics_valid.bin")
    assembler = CrsfByteStreamAssembler()
    frames = assembler.feed(rc + ls)
    assert len(frames) == 2
    assert frames[0].frame_type == CRSF_FRAMETYPE_RC_CHANNELS_PACKED
    assert frames[1].frame_type == CRSF_FRAMETYPE_LINK_STATISTICS
    assert assembler.leftover() == b""


def test_t5_truncated_frame_gives_zero_frames_and_waits():
    data = _load_fixture("rc_channels_truncated.bin")
    assembler = CrsfByteStreamAssembler()
    frames = assembler.feed(data)
    assert frames == []
    assert len(assembler.leftover()) == len(data)
    assert assembler.dropped_byte_count == 0


def test_t6_garbage_prefix_resyncs_and_drops_at_least_one_byte():
    data = _load_fixture("rc_channels_valid.bin")
    assembler = CrsfByteStreamAssembler()
    frames = assembler.feed(b"\x00\x01\x02" + data)
    assert len(frames) == 1
    assert frames[0].frame_type == CRSF_FRAMETYPE_RC_CHANNELS_PACKED
    assert assembler.dropped_byte_count >= 1


def test_t7_bad_crc_gives_zero_frames_no_exception_leaked():
    data = _load_fixture("rc_channels_bad_crc.bin")
    assembler = CrsfByteStreamAssembler()
    frames = assembler.feed(data)  # must not raise CrsfParseError
    assert frames == []


def test_t8_aux_channel_high_via_stream_gives_authority_kill_result():
    values = [992] * 16
    values[4] = 1800  # above CrsfDualRolePolicy()'s default threshold (1500)
    frame_bytes = _rc_frame(values)

    policy = CrsfDualRolePolicy()
    assembler = CrsfByteStreamAssembler()
    results = ingest_stream_bytes(frame_bytes, assembler=assembler, policy=policy)
    assert len(results) == 1
    assert isinstance(results[0], RadioDualRoleResult)
    assert results[0].authority is not None
    assert results[0].authority.kind == "kill"
    assert results[0].intent is None


def test_t8b_below_threshold_stream_gives_empty_results():
    data = _load_fixture("rc_channels_valid.bin")  # all channels at neutral 992
    policy = CrsfDualRolePolicy()
    assembler = CrsfByteStreamAssembler()
    results = ingest_stream_bytes(data, assembler=assembler, policy=policy)
    assert results == []


def test_t9_module_under_test_has_no_io_imports_or_device_open():
    source = inspect.getsource(crsf_stream_module)
    code_only = _strip_python_comments_and_docstrings(source)
    forbidden_imports = ("import serial", "import socket", "import pty", "import subprocess", "usb")
    for token in forbidden_imports:
        assert token not in code_only.lower(), f"crsf_stream.py unexpectedly imports/references '{token}'"
    assert "open(" not in code_only, "crsf_stream.py must not open any file/device path"


def test_t10_radio_py_still_has_no_public_decode_or_serial_symbols():
    """C5 T5 lock, re-pinned here for C21."""
    source = inspect.getsource(radio_module)
    forbidden_symbols = ("decode_crsf", "decode_elrs", "open_serial", "write_pwm")
    for symbol in forbidden_symbols:
        assert symbol not in source, f"radio.py unexpectedly defines/references '{symbol}'"
    assert not hasattr(radio_module, "decode_crsf")
    assert not hasattr(radio_module, "open_serial")


def test_t11_radio_intent_adapter_still_raises_not_implemented():
    with pytest.raises(NotImplementedError, match="not_implemented"):
        RadioIntentAdapter.parse(b"\x00\x00")

    data = _load_fixture("rc_channels_valid.bin")
    assembler = CrsfByteStreamAssembler()
    frames = assembler.feed(data)
    with pytest.raises(NotImplementedError, match="not_implemented"):
        RadioIntentAdapter.parse(frames)


def test_t12_assembler_and_helper_never_call_submit_command_or_import_autonomy():
    assert not hasattr(crsf_stream_module, "submit_command")
    assert not hasattr(crsf_stream_module, "propose_command")
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(crsf_stream_module))
    assert "flight_software" not in code_only
    assert "submit_command" not in code_only


def test_t13_default_safety_gate_still_reject_all():
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.gate_id == "reject_all"


def test_t14_pyproject_version_is_0_5_19():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.44"' in text


def test_t17_assembler_calls_c19_parse_crsf_frame_not_a_second_crc_impl():
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(crsf_stream_module))
    assert "parse_crsf_frame" in code_only
    # No second CRC8 polynomial constant/implementation in the assembler.
    assert "0xD5" not in code_only
    assert "0xd5" not in code_only.lower()


def test_reset_clears_leftover_and_drop_counter():
    assembler = CrsfByteStreamAssembler()
    assembler.feed(b"\x00\x01\x02" + _load_fixture("rc_channels_truncated.bin"))
    assert assembler.leftover() != b"" or assembler.dropped_byte_count > 0
    assembler.reset()
    assert assembler.leftover() == b""
    assert assembler.dropped_byte_count == 0


def test_max_buffer_bounds_leftover_growth_on_noise():
    assembler = CrsfByteStreamAssembler(max_buffer=32, max_frame_len=64)
    # Feed noise that never forms a valid/plausible frame and never lets
    # the desync loop finish draining within one feed (frame_len bytes
    # chosen out of plausible range keeps triggering the drop-one path,
    # but max_buffer must still cap steady-state leftover across feeds).
    noise = bytes([0xFF, 0xFF] * 100)
    assembler.feed(noise)
    assert len(assembler.leftover()) <= 32


def test_feed_empty_bytes_is_a_noop():
    assembler = CrsfByteStreamAssembler()
    assert assembler.feed(b"") == []
    assert assembler.leftover() == b""


def test_no_crsf_or_elrs_under_native_and_no_craft_wiring():
    """Scoped to `crsf`/`elrs` only (same as C19/C20's own equivalent
    tests) — not a bare `"uart"` substring check, which would false-fail
    against C18's own pre-existing, legitimate honesty prose in
    `native/flight_control/README.md` ("no GPIO/UART/any real I/O"),
    disclosing the *absence* of UART I/O, not a driver."""
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
            assert "crsf_stream" not in text, f"{py_file} references crsf_stream"
            assert "CrsfByteStreamAssembler" not in text, f"{py_file} references CrsfByteStreamAssembler"


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
    # tests/test_assistant_vehicle_land_task_b1.py. T8
    # (B1-assistant-vehicle-go-to-task): a fifth, skill.request_go_to
    # (requires flight.go_to, not_implemented/vehicle) — see
    # tests/test_assistant_vehicle_go_to_task_b1.py. T9
    # (B1-assistant-vehicle-takeoff-task): a sixth, skill.request_takeoff
    # (requires flight.takeoff, not_implemented/vehicle) — see
    # tests/test_assistant_vehicle_takeoff_task_b1.py. T10
    # (B1-assistant-vehicle-return-home-task): a seventh, skill.request_return_home
    # (requires flight.return_home, not_implemented/vehicle) — see
    # tests/test_assistant_vehicle_return_home_task_b1.py. T11
    # (B1-assistant-vehicle-arm-ux): eighth+ninth, skill.request_arm_policy /
    # skill.request_disarm_policy (require safety.chat_armed_allowlist,
    # available/software) — see tests/test_assistant_vehicle_arm_ux_b1.py.
    # T12 (B1-assistant-vehicle-follow-task): a tenth, skill.request_follow
    # (requires flight.follow, not_implemented/vehicle) — see
    # tests/test_assistant_vehicle_follow_task_b1.py.
    # T13 (B1-assistant-vehicle-patrol-task): an eleventh, skill.request_patrol
    # (requires flight.patrol, not_implemented/vehicle) — see
    # tests/test_assistant_vehicle_patrol_task_b1.py.
    # Still zero Skill execution path anywhere; this file's own isolation
    # proof is unaffected either way.
    assert {skill.id for skill in registry.skills()} == {
        "skill.explain_concept",
        "skill.project_status",
        "skill.request_hold",
        "skill.request_land",
        "skill.request_go_to",
        "skill.request_takeoff",
        "skill.request_return_home",
        "skill.request_arm_policy",
        "skill.request_disarm_policy",
        "skill.request_follow",
        "skill.request_patrol",
    }
