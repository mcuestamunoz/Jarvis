"""Tests T1-T17 for `B1-fase-c-crsf-host-serial` (C22).

All PASS on a machine with **no physical ELRS receiver / USB serial
adapter** — every test uses a POSIX `pty` (or C19 fixture bytes directly)
as its loopback. `openpty` is part of the Python standard library on
POSIX; tests skip with a clear reason if it is unavailable rather than
requiring hardware.

T16 (report states host serial ingest != live ELRS != RX connected !=
Safety allow; baud 420000 deferred) is covered by
`.jes/artifacts/implementation_report_fase_c_crsf_host_serial_b1.md`,
not by this file.
"""

from __future__ import annotations

import inspect
import io
import os
import time
import tokenize
from pathlib import Path

import pytest

try:
    import pty as pty_module
    import tty as tty_module

    _HAS_PTY = hasattr(pty_module, "openpty")
except ImportError:  # pragma: no cover - non-POSIX
    pty_module = None
    tty_module = None
    _HAS_PTY = False

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities import crsf_serial as crsf_serial_module
from jarvis.capabilities import crsf_stream as crsf_stream_module
from jarvis.capabilities import radio as radio_module
from jarvis.capabilities.crsf_dual_role import CrsfDualRolePolicy
from jarvis.capabilities.crsf_serial import CrsfHostSerialError, CrsfHostSerialIngress, poll_and_ingest
from jarvis.capabilities.crsf_stub import CRSF_FRAMETYPE_RC_CHANNELS_PACKED
from jarvis.capabilities.intent import RadioIntentAdapter

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "crsf"

pytestmark = pytest.mark.skipif(not _HAS_PTY, reason="POSIX pty (openpty) not available on this platform")


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


def _rc_frame(values: list[int]) -> bytes:
    payload = _pack_channels(values)
    body = bytes([0x16]) + payload
    frame_len = len(body) + 1
    return bytes([0xC8, frame_len]) + body + bytes([_crc8(body)])


def _poll_until(fn, tries: int = 20, delay: float = 0.01):
    """Small bounded polling loop — a pty write is not guaranteed to be
    immediately readable; this avoids a flaky single `poll()` call
    without ever blocking indefinitely."""
    result = []
    for _ in range(tries):
        result = fn()
        if result:
            return result
        time.sleep(delay)
    return result


@pytest.fixture
def pty_pair():
    master, slave = pty_module.openpty()
    tty_module.setraw(master)  # disable canonical/line-buffering — see report §0 for why
    yield master, slave
    for fd in (master, slave):
        try:
            os.close(fd)
        except OSError:
            pass


def test_t1_pty_one_shot_write_gives_one_frame(pty_pair):
    master, slave = pty_pair
    os.write(slave, _load_fixture("rc_channels_valid.bin"))

    ingress = CrsfHostSerialIngress()
    ingress.attach_fd(master)
    frames = _poll_until(lambda: ingress.poll())

    assert len(frames) == 1
    assert frames[0].frame_type == CRSF_FRAMETYPE_RC_CHANNELS_PACKED


def test_t2_pty_chunked_writes_reassemble_to_one_frame(pty_pair):
    master, slave = pty_pair
    data = _load_fixture("rc_channels_valid.bin")

    ingress = CrsfHostSerialIngress()
    ingress.attach_fd(master)

    all_frames = []
    for i in range(0, len(data), 5):
        os.write(slave, data[i : i + 5])
        time.sleep(0.005)
        all_frames.extend(ingress.poll())
    if not all_frames:
        all_frames = _poll_until(lambda: ingress.poll())

    assert len(all_frames) == 1
    assert all_frames[0].frame_type == CRSF_FRAMETYPE_RC_CHANNELS_PACKED


def test_t3_poll_with_no_new_bytes_gives_empty_list_no_raise(pty_pair):
    master, _slave = pty_pair
    ingress = CrsfHostSerialIngress()
    ingress.attach_fd(master)
    assert ingress.poll() == []


def test_t4_attach_path_on_pty_slave_path_gives_valid_frame(pty_pair):
    master, slave = pty_pair
    slave_path = os.ttyname(slave)

    ingress = CrsfHostSerialIngress()
    ingress.attach_path(slave_path)
    assert ingress.attached is True

    os.write(master, _load_fixture("rc_channels_valid.bin"))
    frames = _poll_until(lambda: ingress.poll())

    assert len(frames) == 1
    assert frames[0].frame_type == CRSF_FRAMETYPE_RC_CHANNELS_PACKED
    ingress.close()


def test_t5_close_after_attach_path_releases_owned_fd(pty_pair):
    master, slave = pty_pair
    slave_path = os.ttyname(slave)

    ingress = CrsfHostSerialIngress()
    ingress.attach_path(slave_path)
    ingress.close()

    assert ingress.attached is False
    assert ingress.poll() == []  # no longer attached -> empty, not an error


def test_attach_fd_does_not_own_or_close_the_fd(pty_pair):
    master, slave = pty_pair
    ingress = CrsfHostSerialIngress()
    ingress.attach_fd(master)
    ingress.close()

    # master must still be usable — attach_fd never owns/closes it.
    os.write(slave, b"z")
    data = _poll_until(lambda: [os.read(master, 1)] if _readable(master) else [])
    assert data and data[0] == b"z"


def _readable(fd: int) -> bool:
    import select

    ready, _, _ = select.select([fd], [], [], 0)
    return bool(ready)


def test_t6_aux_channel_high_via_pty_gives_authority_kill(pty_pair):
    master, slave = pty_pair
    values = [992] * 16
    values[4] = 1800  # above CrsfDualRolePolicy()'s default threshold (1500)
    os.write(slave, _rc_frame(values))

    ingress = CrsfHostSerialIngress()
    ingress.attach_fd(master)
    policy = CrsfDualRolePolicy()

    results = _poll_until(lambda: poll_and_ingest(ingress, policy=policy))
    assert len(results) == 1
    assert results[0].authority is not None
    assert results[0].authority.kind == "kill"
    assert results[0].intent is None


def test_t6b_all_neutral_fixture_via_pty_gives_empty_results(pty_pair):
    master, slave = pty_pair
    os.write(slave, _load_fixture("rc_channels_valid.bin"))  # all channels at 992, below threshold

    ingress = CrsfHostSerialIngress()
    ingress.attach_fd(master)
    policy = CrsfDualRolePolicy()

    # Give it a few polls to actually consume the bytes, then confirm no
    # Authority result was ever produced across those polls.
    all_results = []
    for _ in range(10):
        all_results.extend(poll_and_ingest(ingress, policy=policy))
        time.sleep(0.01)
    assert all_results == []


def test_t7_radio_py_still_has_no_public_decode_or_serial_symbols():
    """C5 T5 lock, re-pinned here for C22."""
    source = inspect.getsource(radio_module)
    forbidden_symbols = ("decode_crsf", "decode_elrs", "open_serial", "write_pwm")
    for symbol in forbidden_symbols:
        assert symbol not in source, f"radio.py unexpectedly defines/references '{symbol}'"
    assert not hasattr(radio_module, "decode_crsf")
    assert not hasattr(radio_module, "open_serial")


def test_t8_radio_intent_adapter_still_raises_not_implemented():
    with pytest.raises(NotImplementedError, match="not_implemented"):
        RadioIntentAdapter.parse(b"\x00\x00")


def test_t9_module_never_calls_submit_command_or_imports_autonomy():
    assert not hasattr(crsf_serial_module, "submit_command")
    assert not hasattr(crsf_serial_module, "propose_command")
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(crsf_serial_module))
    assert "flight_software" not in code_only
    assert "submit_command" not in code_only


def test_t10_default_safety_gate_still_reject_all():
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.gate_id == "reject_all"


def test_t11_crsf_stream_still_has_no_io_imports_or_device_open():
    """C21 lock, re-pinned here for C22 — crsf_stream.py must stay a pure
    buffer; all I/O lives in crsf_serial.py instead."""
    source = inspect.getsource(crsf_stream_module)
    code_only = _strip_python_comments_and_docstrings(source)
    forbidden_imports = ("import serial", "import socket", "import pty", "import subprocess")
    for token in forbidden_imports:
        assert token not in code_only.lower(), f"crsf_stream.py unexpectedly imports '{token}'"
    assert "open(" not in code_only
    assert "os.read" not in code_only
    assert "os.open" not in code_only


def test_t12_no_pyserial_dependency_in_pyproject():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "pyserial" not in text.lower()


def test_t13_no_device_glob_or_scan_in_module_real_code():
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(crsf_serial_module))
    forbidden = ("/dev/cu", "/dev/ttyusb", "glob(", "listdir(")
    lowered = code_only.lower()
    for token in forbidden:
        assert token not in lowered, f"crsf_serial.py unexpectedly scans/globs devices ('{token}')"


def test_t14_pyproject_version_is_0_5_20():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.37"' in text


def test_t17_no_crsf_or_elrs_under_native_no_bare_uart_substring_check():
    """Same lesson learned in C21: scope the native-tree grep to
    `crsf`/`elrs` only — a bare `"uart"` substring check would false-fail
    against C18's own pre-existing, legitimate honesty prose disclosing
    the *absence* of UART I/O in the MCU scaffold."""
    native_dir = REPO_ROOT / "native"
    for path in native_dir.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "crsf" not in text.lower(), f"{path} unexpectedly references CRSF"
            assert "elrs" not in text.lower(), f"{path} unexpectedly references ELRS"


def test_poll_before_attach_gives_empty_list_not_error():
    ingress = CrsfHostSerialIngress()
    assert ingress.attached is False
    assert ingress.poll() == []


def test_attach_path_to_nonexistent_path_raises_typed_error():
    ingress = CrsfHostSerialIngress()
    with pytest.raises(CrsfHostSerialError):
        ingress.attach_path("/nonexistent/path/for/crsf/host/serial/test")


def test_no_native_wiring_and_registry_still_empty():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "crsf_serial" not in text, f"{py_file} references crsf_serial"
            assert "CrsfHostSerialIngress" not in text, f"{py_file} references CrsfHostSerialIngress"

    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []
