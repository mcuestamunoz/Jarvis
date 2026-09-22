"""Fase C · C21 — CRSF byte-stream assembler (`B1-fase-c-crsf-byte-stream`).

**What this is:** a pure, host-only byte buffer that reassembles CRSF
frames from bytes delivered in **arbitrary chunks** — the shape a UART
delivers data in — into the same `CrsfFrame` objects C19's
`parse_crsf_frame` already produces from a complete buffer. "Chunks of
`bytes` in, zero or more complete, CRC-valid `CrsfFrame`s out, leftover
held" is the entire claim of this module.

**What this is not — read before using this module:** this is **not** a
UART driver, **not** a serial port, **not** `pyserial`, **not** an open
`/dev/tty*`/`/dev/cu.*` device, **not** live ExpressLRS RF, and does
**not** make a receiver "connected." There is no class named like
`Serial`/`UartPort` anywhere here, and no baud-rate concept — this module
only ever sees `bytes` that a caller (a test, in this repo) already has
in memory.

**Module boundary (locked, C21 IC §0 decision 4):** a **new, separate**
module — not folded into `crsf_stub.py` or `radio.py`. `crsf_stub.py`'s
own parse/decode behavior is **unchanged** by this Buy (its own C19
tests remain the contract); `radio.py` grows no stream/serial/CRSF
symbols (C5 T5 stays untouched).

**CRC/envelope truth stays in C19 (locked, C21 IC §0 decision 5):** this
module never reimplements CRC8 or the frame envelope layout. It slices a
candidate window of exactly `frame_len + 2` bytes and hands that window,
unmodified, to `crsf_stub.parse_crsf_frame` — the single source of truth
for what makes a CRSF frame valid.

**Incomplete vs. invalid (locked, C21 IC §0 decision 6) — the two
outcomes are handled differently, on purpose:**
- **Incomplete** candidate (buffer shorter than the declared total) ->
  **wait**: `feed(...)` returns no new frame for it, and the bytes stay
  in the leftover buffer for a future `feed(...)` call to complete.
- **Invalid complete** window (a full-length candidate that
  `parse_crsf_frame` would raise `CrsfParseError` on — bad CRC, or a
  length mismatch) -> **never raised to the caller**. This module drops
  exactly one byte and retries from the new position (a UART "hunt/
  resync" pattern) until it either finds a valid frame or runs out of
  buffered bytes.

**Plausible `frame_len` (locked, C21 IC §0 decision 7):** CRSF's length
byte conventionally stays `<= 64` (`type + payload + crc`, generously
bounded — no real CRSF frame this module knows how to decode is anywhere
near that large). A declared `frame_len` outside `[2, 64]` is treated as
desync immediately (drop one byte, retry) rather than waiting for however
many bytes a bogus giant length would demand.

**Bounded leftover (locked, C21 IC §0 decision 8):** the internal buffer
is capped at `max_buffer` bytes (default `256`). If a `feed(...)` call
would leave more than that queued, the oldest bytes are dropped down to
the cap — this module never grows without bound just because it is fed
noise.

**Optional C20 bridge helper (locked, C21 IC §0 decision 9):**
`ingest_stream_bytes(...)` feeds bytes through an assembler and, for each
newly-completed `0x16` `RC_CHANNELS_PACKED` frame, decodes it and calls
C20's own `ingest_rc_channels(...)` unchanged — C20's policy (one aux
channel, one threshold, `AuthorityKind="kill"` only) is reused exactly as
shipped, not deepened or reconfigured here. Non-`0x16` frames are skipped
by this helper (they are still returned by the assembler's own
`feed(...)`). This helper never synthesizes `Intent`, never calls
`submit_command`, and never calls any `SafetyGate.evaluate(...)`.

**No I/O anywhere in this module** — no `serial`, `socket`, `pty`, USB,
subprocess, or `open()` of a device path.
"""

from __future__ import annotations

from typing import Final

from jarvis.capabilities.crsf_dual_role import CrsfDualRolePolicy, ingest_rc_channels
from jarvis.capabilities.crsf_stub import (
    CRSF_FRAMETYPE_RC_CHANNELS_PACKED,
    CrsfFrame,
    CrsfParseError,
    decode_rc_channels_packed,
    parse_crsf_frame,
)
from jarvis.capabilities.radio import RadioDualRoleResult, SimulatedRadioIngress

_DEFAULT_MAX_BUFFER: Final[int] = 256
_DEFAULT_MAX_FRAME_LEN: Final[int] = 64
_MIN_FRAME_LEN: Final[int] = 2


class CrsfByteStreamAssembler:
    """Reassembles `CrsfFrame`s from bytes fed in arbitrary chunks. Pure
    in-memory buffer — never opens anything, never blocks, never raises
    `CrsfParseError` to the caller (invalid complete windows are dropped
    and retried internally instead)."""

    def __init__(
        self,
        max_buffer: int = _DEFAULT_MAX_BUFFER,
        max_frame_len: int = _DEFAULT_MAX_FRAME_LEN,
    ) -> None:
        self.max_buffer = max_buffer
        self.max_frame_len = max_frame_len
        self._buffer = bytearray()
        self._dropped_byte_count = 0

    @property
    def dropped_byte_count(self) -> int:
        """Cumulative bytes dropped via desync-resync or leftover-cap
        overflow, across the assembler's lifetime (reset by `reset()`)."""
        return self._dropped_byte_count

    def leftover(self) -> bytes:
        """The current unconsumed buffer — bytes waiting for either more
        data (incomplete candidate) or the next `feed(...)` call."""
        return bytes(self._buffer)

    def reset(self) -> None:
        """Clears the leftover buffer and the drop counter."""
        self._buffer.clear()
        self._dropped_byte_count = 0

    def feed(self, data: bytes) -> list[CrsfFrame]:
        """Appends `data`, then extracts and returns every complete,
        CRC-valid `CrsfFrame` now available, in order. Returns `[]` when
        no frame is complete yet (including for `data == b""`)."""
        self._buffer.extend(data)
        frames: list[CrsfFrame] = []
        while True:
            frame = self._try_extract_one()
            if frame is None:
                break
            frames.append(frame)
        self._enforce_max_buffer()
        return frames

    def _try_extract_one(self) -> CrsfFrame | None:
        while True:
            if len(self._buffer) < 2:
                return None

            frame_len = self._buffer[1]
            if frame_len < _MIN_FRAME_LEN or frame_len > self.max_frame_len:
                self._drop_one_byte()
                continue

            total = frame_len + 2
            if len(self._buffer) < total:
                return None  # incomplete candidate — wait for more data

            candidate = bytes(self._buffer[:total])
            try:
                frame = parse_crsf_frame(candidate)
            except CrsfParseError:
                self._drop_one_byte()
                continue

            del self._buffer[:total]
            return frame

    def _drop_one_byte(self) -> None:
        del self._buffer[0]
        self._dropped_byte_count += 1

    def _enforce_max_buffer(self) -> None:
        overflow = len(self._buffer) - self.max_buffer
        if overflow > 0:
            del self._buffer[:overflow]
            self._dropped_byte_count += overflow


def ingest_stream_bytes(
    data: bytes,
    *,
    assembler: CrsfByteStreamAssembler,
    policy: CrsfDualRolePolicy,
    ingress: SimulatedRadioIngress | None = None,
) -> list[RadioDualRoleResult]:
    """Feeds `data` through `assembler`; for each newly-completed
    `RC_CHANNELS_PACKED` frame, decodes it and calls C20's
    `ingest_rc_channels(...)` unchanged. Below-threshold results (`None`
    from C20) are omitted, not appended. Non-`0x16` frames are skipped
    here (still present in `assembler.feed(...)`'s own return value, had
    the caller wanted them)."""
    frames = assembler.feed(data)
    results: list[RadioDualRoleResult] = []
    for frame in frames:
        if frame.frame_type != CRSF_FRAMETYPE_RC_CHANNELS_PACKED:
            continue
        channels = decode_rc_channels_packed(frame.payload)
        result = ingest_rc_channels(channels, policy=policy, ingress=ingress)
        if result is not None:
            results.append(result)
    return results
