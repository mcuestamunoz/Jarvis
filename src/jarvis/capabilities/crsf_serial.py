"""Fase C · C22/C23 — CRSF host serial-shaped ingest + host baud
(`B1-fase-c-crsf-host-serial`, `B1-fase-c-crsf-host-baud`).

**What this is:** a small, pull-based reader that pulls bytes from an
already-open host file descriptor (tests: a POSIX `pty`) or an opt-in
device **path**, and feeds them to C21's `CrsfByteStreamAssembler`. As of
C23, this module can also (opt-in, never automatic) ask **Darwin** to
clock an already-attached FD at a **custom baud** — default `420000`,
the rate a real ExpressLRS CRSF UART typically runs at — and put that FD
into **raw 8N1** so binary CRSF is not held back by canonical line
buffering. "Bytes can be pulled from a host FD/path and handed to the C21
assembler, and on Darwin that FD's baud can optionally be configured to
an ELRS-typical rate" is the entire claim of this module.

**What this is not — read before using this module:** this is **not**
live ExpressLRS RF, **not** a claim that a receiver is "connected," and
**not** a UART/HAL driver. It does **not** use `pyserial`. Issuing the
`IOSSIOSPEED` ioctl successfully is a **host OS configuration fact**, not
proof that any receiver exists on the other end of the wire, and not
proof that "baud 420000 works" against real hardware — no RF, no ELRS
binding, no telemetry is implemented or claimed anywhere in this module.
`attach_path(...)`/`attach_fd(...)` still do **not** configure baud on
their own — baud is strictly opt-in via `configure_host_baud(...)`/
`CrsfHostSerialIngress.configure_baud(...)`, called explicitly by a
caller who wants it.

**Darwin only, this Buy (locked, C23 IC §0 decision 10):**
`configure_host_baud(...)` raises `CrsfHostSerialError` on any
`sys.platform != "darwin"` — no Linux `TCSETS2`/`BOTHER`, no Windows
serial stack, no cross-platform abstraction attempted here. A future,
separate IC would need to add that.

**Module boundary (locked, C22 IC §0 decision 4; reaffirmed C23 IC §0
decision 4):** a **new, separate** module (no sixth capabilities module
was created for C23 — baud is a property of the host serial FD, added to
this same module). `crsf_stream.py` stays **I/O-free** — this module
*calls* its `CrsfByteStreamAssembler.feed(...)`, it does not add any
read/open/socket/termios/ioctl logic to `crsf_stream.py` itself. `radio.py`
grows no serial/CRSF/baud symbols (C5 T5 stays untouched).

**Pull, not a live thread (locked, C22 IC §0 decision 7):** `poll(...)`
performs exactly **one** non-blocking read attempt, then feeds whatever
bytes (if any) came back to the assembler. There is no background thread,
no "link up"/"connected" flag, and no auto-reconnect loop anywhere in
this module — a caller must call `poll(...)` themselves, as many times as
they like, whenever they like.

**No auto-discovery (locked, C22 IC §0 decision 9):** this module never
globs `/dev/cu.*`/`/dev/ttyUSB*` or enumerates USB devices. A caller
always supplies an explicit file descriptor or path.

**FD vs. path ownership (locked, C22 IC §0 decision 6):** `attach_fd(fd)`
attaches to an FD the caller already owns — `close()` on this ingress
never closes it. `attach_path(path)` opens the path itself (read-only,
non-blocking, no controlling-terminal side effects) and **owns** the
resulting FD — `close()` on this ingress does close it in that case.
Neither method's open flags changed for C23 (still
`O_RDONLY | O_NOCTTY | O_NONBLOCK`) — baud configuration is a separate,
explicit, opt-in step a caller takes after attaching, never a side
effect of attaching itself.

**Baud/raw-mode call order (locked, C23 IC §0 decision 9):**
`configure_host_baud(fd, baud)` first applies raw-8N1 termios (disabling
canonical mode, echo, and the various NL/CR translations that would
corrupt binary CRSF payloads), **then** issues the Darwin `IOSSIOSPEED`
ioctl for the requested baud. If the ioctl fails, a typed
`CrsfHostSerialError` is raised and success is never claimed — the
termios mutation already applied in step one is disclosed as an
acceptable side effect on a failing attempt (see the implementation
report for the full reasoning) rather than something this module tries
to roll back.

**Optional C20 bridge helper (locked, C22 IC §0 decision 10):**
`poll_and_ingest(...)` calls `ingress.poll(...)` exactly once (never
feeding the same bytes twice into the assembler) and, for each newly
completed `0x16` `RC_CHANNELS_PACKED` frame, reuses C20's own
`ingest_rc_channels(...)` **unchanged**. It never synthesizes `Intent`,
never calls `submit_command`, and never calls any `SafetyGate.evaluate`.

**POSIX only (locked, C22 IC §0 decision 11).** No Windows serial stack
is added in this Buy.
"""

from __future__ import annotations

import fcntl
import os
import struct
import sys
import termios
from typing import Final

from jarvis.capabilities.crsf_dual_role import CrsfDualRolePolicy, ingest_rc_channels
from jarvis.capabilities.crsf_stream import CrsfByteStreamAssembler
from jarvis.capabilities.crsf_stub import CRSF_FRAMETYPE_RC_CHANNELS_PACKED, CrsfFrame, decode_rc_channels_packed
from jarvis.capabilities.radio import RadioDualRoleResult, SimulatedRadioIngress

_DEFAULT_MAX_BYTES: Final[int] = 64

# C23 — ELRS-typical CRSF UART rate. A documented default, not an ELRS
# rate table: any positive int may be passed to configure_host_baud(...).
CRSF_HOST_BAUD_ELRS: Final[int] = 420000

# Darwin _IOC/_IOW macro constants (sys/ioccom.h) used to DERIVE the
# IOSSIOSPEED request number below, rather than hardcoding a copied
# magic constant (C23 IC §0 decision 7).
_DARWIN_IOC_IN: Final[int] = 0x80000000
_DARWIN_IOCPARM_MASK: Final[int] = 0x1FFF
_DARWIN_IOSSIOSPEED_GROUP: Final[int] = ord("T")
_DARWIN_IOSSIOSPEED_NUM: Final[int] = 2


class CrsfHostSerialError(Exception):
    """Raised for a host FD/path attach or read failure — never for a
    CRSF parse failure. `CrsfParseError` stays entirely inside
    `crsf_stub`/`crsf_stream`; `poll(...)` never raises that type. As of
    C23, also raised for a baud/termios/ioctl configuration failure, or
    for calling `configure_host_baud(...)` on a non-Darwin platform."""


def _darwin_iossiospeed_request() -> int:
    """Derives Darwin's `IOSSIOSPEED` ioctl request number from the real
    `_IOW('T', 2, speed_t)` macro (`sys/ioccom.h` + `IOKit/serial/ioss.h`)
    — computed from the macro definition, not a copied magic constant
    (C23 IC §0 decision 7)."""
    speed_t_size = struct.calcsize("@L")  # Darwin speed_t is unsigned long
    return (
        _DARWIN_IOC_IN
        | ((speed_t_size & _DARWIN_IOCPARM_MASK) << 16)
        | (_DARWIN_IOSSIOSPEED_GROUP << 8)
        | _DARWIN_IOSSIOSPEED_NUM
    )


def _set_raw_8n1(fd: int) -> None:
    """Applies raw, non-canonical 8N1 termios to `fd`: 8 data bits, no
    parity, 1 stop bit, `CLOCAL`/`CREAD`, canonical mode/echo/signal
    generation disabled, and the NL/CR input translations that would
    corrupt a binary CRSF payload disabled too. `VMIN=0`/`VTIME=0` so a
    read never blocks waiting for a fixed byte count (C22's own
    non-blocking `poll(...)` stays the actual read discipline)."""
    iflag, oflag, cflag, lflag, ispeed, ospeed, cc = termios.tcgetattr(fd)

    iflag &= ~(
        termios.IGNBRK
        | termios.BRKINT
        | termios.PARMRK
        | termios.ISTRIP
        | termios.INLCR
        | termios.IGNCR
        | termios.ICRNL
        | termios.IXON
    )
    oflag &= ~termios.OPOST
    lflag &= ~(termios.ECHO | termios.ECHONL | termios.ICANON | termios.ISIG | termios.IEXTEN)
    cflag &= ~(termios.CSIZE | termios.PARENB | termios.CSTOPB)
    cflag |= termios.CS8 | termios.CLOCAL | termios.CREAD

    cc[termios.VMIN] = 0
    cc[termios.VTIME] = 0

    termios.tcsetattr(fd, termios.TCSANOW, [iflag, oflag, cflag, lflag, ispeed, ospeed, cc])


def configure_host_baud(fd: int, baud: int = CRSF_HOST_BAUD_ELRS) -> None:
    """**Darwin only, this Buy.** Applies raw 8N1 termios to `fd`, then
    issues the `IOSSIOSPEED` ioctl requesting `baud` (default
    `CRSF_HOST_BAUD_ELRS` = `420000`, the ELRS-typical CRSF UART rate —
    any other positive `int` is accepted too, there is no rate table in
    this Buy). Does **not** open, close, attach, or poll anything, and
    does **not** mean a receiver is present — a successful ioctl is a
    host OS configuration fact, never a claim about hardware on the other
    end of the wire. Raises `CrsfHostSerialError` for a non-positive
    `baud`, for any `sys.platform != "darwin"`, or if the termios/ioctl
    call itself fails (e.g. `fd` is not a real serial-capable device —
    a POSIX `pty` is not a UART and is expected to fail here)."""
    if not isinstance(baud, int) or isinstance(baud, bool) or baud <= 0:
        raise CrsfHostSerialError(f"baud must be a positive int, got {baud!r}")

    if sys.platform != "darwin":
        raise CrsfHostSerialError(
            f"configure_host_baud is Darwin-only in this Buy (C23); unsupported on "
            f"sys.platform={sys.platform!r}"
        )

    try:
        _set_raw_8n1(fd)
    except (OSError, termios.error) as exc:
        raise CrsfHostSerialError(f"failed to set raw 8N1 termios on fd={fd}: {exc}") from exc

    try:
        request = _darwin_iossiospeed_request()
        buf = struct.pack("@L", baud)
        fcntl.ioctl(fd, request, buf)
    except OSError as exc:
        raise CrsfHostSerialError(f"IOSSIOSPEED ioctl failed for fd={fd} baud={baud}: {exc}") from exc


class CrsfHostSerialIngress:
    """Pull-based host byte source over an FD/path, feeding a
    `CrsfByteStreamAssembler`. Never opens anything on its own unless
    `attach_path(...)` is called explicitly; never reads unless
    `poll(...)` is called explicitly."""

    def __init__(self, assembler: CrsfByteStreamAssembler | None = None) -> None:
        self._assembler = assembler if assembler is not None else CrsfByteStreamAssembler()
        self._fd: int | None = None
        self._owns_fd = False

    @property
    def assembler(self) -> CrsfByteStreamAssembler:
        return self._assembler

    @property
    def attached(self) -> bool:
        return self._fd is not None

    def attach_fd(self, fd: int) -> None:
        """Attaches to an already-open FD the caller owns. `close()` on
        this ingress will **not** close `fd`. Forces the FD into
        non-blocking mode so `poll(...)` never blocks the caller."""
        os.set_blocking(fd, False)
        self._fd = fd
        self._owns_fd = False

    def attach_path(self, path: str) -> None:
        """Opens `path` read-only, non-blocking, with no controlling-
        terminal side effects (`O_RDONLY | O_NOCTTY | O_NONBLOCK`). Does
        **not** configure baud or any termios setting — call
        `configure_baud(...)` explicitly afterward if that is wanted.
        This ingress **owns** the resulting FD; `close()` will close it."""
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOCTTY | os.O_NONBLOCK)
        except OSError as exc:
            raise CrsfHostSerialError(f"failed to open {path!r}: {exc}") from exc
        self._fd = fd
        self._owns_fd = True

    def configure_baud(self, baud: int = CRSF_HOST_BAUD_ELRS) -> None:
        """Requires an attached FD (`attach_fd(...)`/`attach_path(...)`
        called first) — raises `CrsfHostSerialError` if not attached
        (never a silent no-op). Delegates to `configure_host_baud(fd,
        baud)`: Darwin-only this Buy, opt-in, never called automatically
        by `attach_fd`/`attach_path`."""
        if self._fd is None:
            raise CrsfHostSerialError("configure_baud requires an attached FD (call attach_fd/attach_path first)")
        configure_host_baud(self._fd, baud)

    def poll(self, *, max_bytes: int = _DEFAULT_MAX_BYTES) -> list[CrsfFrame]:
        """Exactly one non-blocking read attempt, then `feed(...)`s
        whatever came back to the assembler. Returns `[]` — never raises
        `CrsfHostSerialError` — when not attached, when there is no data
        available right now (`BlockingIOError`/EAGAIN), or when the read
        returns zero bytes (EOF on this pull)."""
        if self._fd is None:
            return []
        try:
            data = os.read(self._fd, max_bytes)
        except BlockingIOError:
            return []
        except OSError as exc:
            raise CrsfHostSerialError(f"read failed: {exc}") from exc
        if not data:
            return []
        return self._assembler.feed(data)

    def close(self) -> None:
        """Closes the FD only if this ingress opened it itself
        (`attach_path(...)`); an `attach_fd(...)`-supplied FD is left
        open for its owner to manage. Always detaches either way."""
        if self._owns_fd and self._fd is not None:
            os.close(self._fd)
        self._fd = None
        self._owns_fd = False


def poll_and_ingest(
    ingress: CrsfHostSerialIngress,
    *,
    policy: CrsfDualRolePolicy,
    ingress_radio: SimulatedRadioIngress | None = None,
    max_bytes: int = _DEFAULT_MAX_BYTES,
) -> list[RadioDualRoleResult]:
    """Calls `ingress.poll(...)` exactly once, then for each newly
    completed `0x16` frame decodes it and calls C20's
    `ingest_rc_channels(...)` unchanged. Below-threshold (`None`) results
    are omitted; non-`0x16` frames are skipped here (still present in the
    underlying `poll(...)` return value, had the caller wanted them)."""
    frames = ingress.poll(max_bytes=max_bytes)
    results: list[RadioDualRoleResult] = []
    for frame in frames:
        if frame.frame_type != CRSF_FRAMETYPE_RC_CHANNELS_PACKED:
            continue
        channels = decode_rc_channels_packed(frame.payload)
        result = ingest_rc_channels(channels, policy=policy, ingress=ingress_radio)
        if result is not None:
            results.append(result)
    return results
