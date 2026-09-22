"""Fase C · C22 — CRSF host serial-shaped ingest (`B1-fase-c-crsf-host-serial`).

**What this is:** a small, pull-based reader that pulls bytes from an
already-open host file descriptor (tests: a POSIX `pty`) or an opt-in
device **path**, and feeds them to C21's `CrsfByteStreamAssembler`. "Bytes
can be pulled from a host FD/path and handed to the C21 assembler" is the
entire claim of this module.

**What this is not — read before using this module:** this is **not**
live ExpressLRS RF, **not** a claim that a receiver is "connected," and
**not** a UART/HAL driver. It does **not** use `pyserial`, does **not**
configure `420000` baud (the rate a real ELRS CRSF link typically runs
at) or any other baud/termios setting at all — opening a path here means
"give me bytes from this node," not "I configured an ELRS receiver."
Custom-baud configuration (e.g. macOS's `IOSSIOSPEED` ioctl) is
explicitly **deferred to a later, platform-specific IC** (IC §0 decision
8) — this Buy does not attempt it.

**Module boundary (locked, C22 IC §0 decision 4):** a **new, separate**
module. `crsf_stream.py` stays **I/O-free** — this module *calls* its
`CrsfByteStreamAssembler.feed(...)`, it does not add any read/open/socket
logic to `crsf_stream.py` itself. `radio.py` grows no serial/CRSF symbols
(C5 T5 stays untouched).

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

import os
from typing import Final

from jarvis.capabilities.crsf_dual_role import CrsfDualRolePolicy, ingest_rc_channels
from jarvis.capabilities.crsf_stream import CrsfByteStreamAssembler
from jarvis.capabilities.crsf_stub import CRSF_FRAMETYPE_RC_CHANNELS_PACKED, CrsfFrame, decode_rc_channels_packed
from jarvis.capabilities.radio import RadioDualRoleResult, SimulatedRadioIngress

_DEFAULT_MAX_BYTES: Final[int] = 64


class CrsfHostSerialError(Exception):
    """Raised for a host FD/path attach or read failure — never for a
    CRSF parse failure. `CrsfParseError` stays entirely inside
    `crsf_stub`/`crsf_stream`; `poll(...)` never raises that type."""


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
        **not** configure baud or any termios setting — that is a later
        IC's scope. This ingress **owns** the resulting FD; `close()`
        will close it."""
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOCTTY | os.O_NONBLOCK)
        except OSError as exc:
            raise CrsfHostSerialError(f"failed to open {path!r}: {exc}") from exc
        self._fd = fd
        self._owns_fd = True

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
