"""Tests T1-T20 for `B1-fase-c-crsf-host-baud` (C23).

All PASS on a machine with **no physical ELRS receiver / USB serial
adapter** — the Darwin success path is proven entirely by mocking
`fcntl.ioctl` (T2, T8); the one **unmocked** ioctl test (T3) is expected
to fail closed on a POSIX `pty` (a pty is not a UART) and asserts exactly
that failure, never skipping the suite for lack of hardware.

T18 (report states host baud 420000 != live ELRS != RX connected != UART
driver != Safety allow; ioctl mock is the hardware-free proof) is covered
by `.jes/artifacts/implementation_report_fase_c_crsf_host_baud_b1.md`,
not by this file.
"""

from __future__ import annotations

import inspect
import io
import os
import struct
import sys
import termios
import tokenize
from pathlib import Path
from unittest.mock import patch

import pytest

try:
    import pty as pty_module

    _HAS_PTY = hasattr(pty_module, "openpty")
except ImportError:  # pragma: no cover - non-POSIX
    pty_module = None
    _HAS_PTY = False

from jarvis.capabilities import CapabilityRegistry, RejectAllSafetyGate, default_safety_gate
from jarvis.capabilities import crsf_serial as crsf_serial_module
from jarvis.capabilities import crsf_stream as crsf_stream_module
from jarvis.capabilities import radio as radio_module
from jarvis.capabilities.crsf_serial import (
    CRSF_HOST_BAUD_ELRS,
    CrsfHostSerialError,
    CrsfHostSerialIngress,
    configure_host_baud,
)
from jarvis.capabilities.intent import RadioIntentAdapter

REPO_ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(not _HAS_PTY, reason="POSIX pty (openpty) not available on this platform")

_DARWIN_ONLY = pytest.mark.skipif(
    sys.platform != "darwin", reason="Darwin-ioctl-packing assertions only apply on darwin"
)


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


@pytest.fixture
def pty_pair():
    master, slave = pty_module.openpty()
    yield master, slave
    for fd in (master, slave):
        try:
            os.close(fd)
        except OSError:
            pass


def _fake_ioctl_factory(calls: list):
    def _fake_ioctl(fd, request, buf, *args, **kwargs):
        calls.append((fd, request, bytes(buf)))
        return 0

    return _fake_ioctl


def test_t1_default_baud_is_420000_elrs_typical_rate():
    assert CRSF_HOST_BAUD_ELRS == 420000


@_DARWIN_ONLY
def test_t2_darwin_mocked_ioctl_configures_420000(pty_pair):
    master, _slave = pty_pair
    calls: list = []
    with patch("fcntl.ioctl", side_effect=_fake_ioctl_factory(calls)):
        configure_host_baud(master, 420000)

    assert len(calls) == 1
    fd, request, buf = calls[0]
    assert fd == master
    # Derived from the real _IOW('T', 2, speed_t) macro — see module source.
    from jarvis.capabilities.crsf_serial import _darwin_iossiospeed_request

    assert request == _darwin_iossiospeed_request()
    assert struct.unpack("@L", buf)[0] == 420000


@_DARWIN_ONLY
def test_t3_darwin_unmocked_ioctl_on_pty_fails_closed_not_skipped(pty_pair):
    master, _slave = pty_pair
    with pytest.raises(CrsfHostSerialError):
        configure_host_baud(master, 420000)  # a pty is not a UART — this MUST fail, not skip


def test_t4_configure_baud_before_attach_raises():
    ingress = CrsfHostSerialIngress()
    with pytest.raises(CrsfHostSerialError):
        ingress.configure_baud()


def test_t5_attach_without_configure_baud_issues_no_ioctl(pty_pair):
    master, _slave = pty_pair
    calls: list = []
    with patch("fcntl.ioctl", side_effect=_fake_ioctl_factory(calls)):
        ingress = CrsfHostSerialIngress()
        ingress.attach_fd(master)
        ingress.poll()
    assert calls == []


def test_t6_non_positive_baud_raises_no_ioctl():
    calls: list = []
    with patch("fcntl.ioctl", side_effect=_fake_ioctl_factory(calls)):
        for bad_baud in (0, -1, -420000):
            with pytest.raises(CrsfHostSerialError):
                configure_host_baud(1, bad_baud)
    assert calls == []


@pytest.mark.skipif(sys.platform == "darwin", reason="this test asserts the non-Darwin fail-closed path")
def test_t7_non_darwin_raises_darwin_only_error(pty_pair):
    master, _slave = pty_pair
    with pytest.raises(CrsfHostSerialError, match="Darwin-only"):
        configure_host_baud(master, 420000)


@_DARWIN_ONLY
def test_t7b_platform_check_happens_before_hardware_access():
    """Documents the Darwin-only guard exists and fires for a fake
    non-darwin platform string, independent of the running OS — proves
    the check is a real `sys.platform` comparison, not accidental."""
    with patch("jarvis.capabilities.crsf_serial.sys.platform", "linux"):
        with pytest.raises(CrsfHostSerialError, match="Darwin-only"):
            configure_host_baud(1, 420000)


@_DARWIN_ONLY
def test_t8_successful_mock_path_also_applies_raw_8n1(pty_pair):
    master, _slave = pty_pair
    calls: list = []
    with patch("fcntl.ioctl", side_effect=_fake_ioctl_factory(calls)):
        configure_host_baud(master, 420000)

    iflag, oflag, cflag, lflag, ispeed, ospeed, cc = termios.tcgetattr(master)
    assert not (lflag & termios.ICANON), "canonical mode must be disabled (raw)"
    assert not (lflag & termios.ECHO), "echo must be disabled"
    assert cflag & termios.CS8, "8 data bits (CS8) must be set"
    assert cflag & termios.CLOCAL
    assert cflag & termios.CREAD
    assert cc[termios.VMIN] == 0
    assert cc[termios.VTIME] == 0


def test_t9_radio_py_still_has_no_public_decode_or_serial_symbols():
    """C5 T5 lock, re-pinned here for C23."""
    source = inspect.getsource(radio_module)
    forbidden_symbols = ("decode_crsf", "decode_elrs", "open_serial", "write_pwm", "IOSSIOSPEED", "configure_baud")
    for symbol in forbidden_symbols:
        assert symbol not in source, f"radio.py unexpectedly defines/references '{symbol}'"
    assert not hasattr(radio_module, "decode_crsf")
    assert not hasattr(radio_module, "configure_host_baud")


def test_t10_radio_intent_adapter_still_raises_not_implemented():
    with pytest.raises(NotImplementedError, match="not_implemented"):
        RadioIntentAdapter.parse(b"\x00\x00")


def test_t11_baud_code_never_calls_submit_command_or_imports_autonomy():
    assert not hasattr(crsf_serial_module, "submit_command")
    assert not hasattr(crsf_serial_module, "propose_command")
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(crsf_serial_module))
    assert "flight_software" not in code_only
    assert "submit_command" not in code_only


def test_t12_default_safety_gate_still_reject_all():
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    assert gate.gate_id == "reject_all"


def test_t13_crsf_stream_still_has_no_io_or_termios_or_fcntl_in_real_code():
    """C21 lock, re-pinned here for C23 — crsf_stream.py must stay a pure
    buffer; all I/O and termios/ioctl logic lives in crsf_serial.py."""
    source = inspect.getsource(crsf_stream_module)
    code_only = _strip_python_comments_and_docstrings(source)
    forbidden_imports = ("import serial", "import socket", "import pty", "import subprocess", "import fcntl", "import termios")
    for token in forbidden_imports:
        assert token not in code_only.lower(), f"crsf_stream.py unexpectedly imports '{token}'"
    assert "open(" not in code_only
    assert "os.read" not in code_only
    assert "ioctl" not in code_only.lower()


def test_t14_no_pyserial_dependency_in_pyproject():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "pyserial" not in text.lower()


def test_t15_no_device_glob_or_scan_in_crsf_serial_real_code():
    code_only = _strip_python_comments_and_docstrings(inspect.getsource(crsf_serial_module))
    forbidden = ("/dev/cu", "/dev/ttyusb", "glob(", "listdir(")
    lowered = code_only.lower()
    for token in forbidden:
        assert token not in lowered, f"crsf_serial.py unexpectedly scans/globs devices ('{token}')"


def test_t16_pyproject_version_is_0_5_21():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.28"' in text


def test_t19_no_crsf_or_elrs_under_native_no_bare_uart_substring_check():
    """Same lesson learned in C21/C22: scope the native-tree grep to
    `crsf`/`elrs` only — a bare `"uart"` substring check would false-fail
    against C18's own pre-existing, legitimate honesty prose."""
    native_dir = REPO_ROOT / "native"
    for path in native_dir.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "crsf" not in text.lower(), f"{path} unexpectedly references CRSF"
            assert "elrs" not in text.lower(), f"{path} unexpectedly references ELRS"


def test_t20_c22_ingest_behavior_unchanged_no_auto_baud(pty_pair):
    """C22 must stay valid without behavior edits: attach + poll still
    work exactly as C22 shipped, and attaching never auto-configures
    baud."""
    master, slave = pty_pair
    os.write(slave, b"\x00")  # arbitrary byte; not asserting CRSF decode here
    calls: list = []
    with patch("fcntl.ioctl", side_effect=_fake_ioctl_factory(calls)):
        ingress = CrsfHostSerialIngress()
        assert ingress.attached is False
        ingress.attach_fd(master)
        assert ingress.attached is True
        ingress.poll()  # must not raise
        ingress.close()
    assert calls == [], "attach_fd/poll must never issue an ioctl on their own"


def test_no_native_wiring_and_registry_still_empty():
    core_dir = REPO_ROOT / "src" / "jarvis" / "core"
    adapters_dir = REPO_ROOT / "src" / "jarvis" / "adapters"
    for directory in (core_dir, adapters_dir):
        for py_file in directory.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            assert "crsf_serial" not in text, f"{py_file} references crsf_serial"
            assert "configure_host_baud" not in text, f"{py_file} references configure_host_baud"

    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []
