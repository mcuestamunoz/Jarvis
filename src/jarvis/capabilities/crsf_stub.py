"""Fase C · C19 — CRSF byte-fixture parse stub (`B1-fase-c-crsf-link-stub`).

**Protocol honesty (read before using this module):** ExpressLRS (ELRS)
commonly carries **CRSF** (Crossfire) frames on the UART between the
radio receiver and the flight controller. This module parses **CRSF
bytes** — the wire framing and two documented frame payloads — from
checked-in/synthetic fixtures. It does **not** implement the ELRS *air*
protocol (RF, binding, telemetry timing), does **not** open a serial,
USB, or SPI port to a real receiver, and is never fed live radio data
anywhere in this repo. "This module can decode a CRSF byte sequence" is
the entire claim — not "ExpressLRS is connected," not "a receiver is
on air," not "a pilot's sticks drive anything."

**Module boundary (locked, C19 IC §0 decision 5):** this is a **separate**
module from `jarvis.capabilities.radio` on purpose — C5's own honesty
lock (T5) requires `radio.py` to carry no `decode_crsf`/`decode_elrs`/
`open_serial` public API, and this Buy does not touch that lock.
`jarvis.capabilities.radio.SimulatedRadioIngress` remains the only
dual-role simulated ingress path; nothing in this module feeds it,
`RadioIntentAdapter`, `submit_command`, or any `SafetyGate` — decoding a
CRSF frame here produces typed data only, never an `Intent`, never an
`AuthoritySignal`, never a Safety `allow`.

**No I/O anywhere in this module** — no `serial`, `socket`, `pty`, USB,
subprocess, or `open()` of a device path. Every function here takes
`bytes` and returns typed data or raises `CrsfParseError`; tests feed
fixture bytes.

**Frame envelope (locked, C19 IC §0 decision 6):**
`[device_addr:1][frame_len:1][frame_type:1][payload:frame_len-2][crc8:1]`,
CRC8 computed with polynomial `0xD5` (the standard CRSF/DVB-S2 CRC8) over
`frame_type + payload` (not over `device_addr`/`frame_len`/the CRC byte
itself). Truncated frames and bad-CRC frames both raise `CrsfParseError`
— there is no silent partial-success path.

**Frame types implemented (locked minimum + recommended, C19 IC §0
decision 7):**
- `0x16` `RC_CHANNELS_PACKED` — 16 channels, 11 bits each, LSB-first
  packed across 22 payload bytes, decoded to plain integers in
  `[0, 2047]`. These are **not** routed anywhere — no mixer, no ESC, no
  autonomy command.
- `0x14` `LINK_STATISTICS` — a small typed struct (RSSI/LQ/SNR/etc.),
  included per this IC's own default. Unknown/other frame types are left
  as opaque `CrsfFrame.payload` bytes — this module does not attempt to
  decode every CRSF frame type that exists.
"""

from __future__ import annotations

import struct
from typing import Final

from pydantic import BaseModel, ConfigDict

CRSF_FRAMETYPE_LINK_STATISTICS: Final[int] = 0x14
CRSF_FRAMETYPE_RC_CHANNELS_PACKED: Final[int] = 0x16

_CRC8_POLY: Final[int] = 0xD5
_RC_CHANNELS_PAYLOAD_LEN: Final[int] = 22
_RC_CHANNEL_COUNT: Final[int] = 16
_RC_CHANNEL_BITS: Final[int] = 11
_LINK_STATISTICS_PAYLOAD_LEN: Final[int] = 10
_LINK_STATISTICS_STRUCT: Final[str] = "<BBBbBBBBBb"


class CrsfParseError(Exception):
    """Raised for a malformed CRSF byte sequence (too short, a length
    field that does not match the actual byte count, or a bad CRC8) or a
    payload whose length does not match the frame type being decoded.
    Never raised for a hardware reason — there is no hardware here."""


class CrsfFrame(BaseModel):
    """One parsed CRSF envelope. `payload` is the frame-type-specific body,
    still undecoded — pass it to `decode_rc_channels_packed`/
    `decode_link_statistics` for the two frame types this module knows."""

    model_config = ConfigDict(extra="forbid")

    device_addr: int
    frame_type: int
    payload: bytes
    crc: int


class CrsfRcChannels(BaseModel):
    """16 decoded RC channel values, `[0, 2047]` each (raw 11-bit CRSF
    units — not microseconds, not normalized `[-1, 1]`, not fed to any
    mixer/ESC/autonomy path anywhere in this repo)."""

    model_config = ConfigDict(extra="forbid")

    channels: tuple[int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int]


class CrsfLinkStatistics(BaseModel):
    """Decoded CRSF `LINK_STATISTICS` (frame type `0x14`) payload — field
    order and signedness match the widely-documented CRSF layout used by
    ExpressLRS/Betaflight/iNav. `*_snr` fields are signed (dB); everything
    else is an unsigned byte."""

    model_config = ConfigDict(extra="forbid")

    uplink_rssi_1: int
    uplink_rssi_2: int
    uplink_link_quality: int
    uplink_snr: int
    active_antenna: int
    rf_profile: int
    uplink_tx_power: int
    downlink_rssi: int
    downlink_link_quality: int
    downlink_snr: int


def _crc8_dvb_s2(data: bytes) -> int:
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ _CRC8_POLY) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


def parse_crsf_frame(data: bytes) -> CrsfFrame:
    """Parses and CRC8-validates the CRSF envelope. Raises `CrsfParseError`
    on a too-short buffer, a `frame_len` that does not match the actual
    byte count, or a CRC8 mismatch — never returns a partial/best-effort
    result."""
    if len(data) < 4:
        raise CrsfParseError(f"frame too short: {len(data)} bytes, need >= 4")

    device_addr = data[0]
    frame_len = data[1]
    if frame_len < 2:
        raise CrsfParseError(f"frame_len field too small: {frame_len} (need >= 2)")

    expected_total = frame_len + 2
    if len(data) != expected_total:
        raise CrsfParseError(
            f"frame length mismatch: header declares {expected_total} total bytes "
            f"(frame_len={frame_len}), got {len(data)}"
        )

    frame_type = data[2]
    crc_index = frame_len + 1
    payload = data[3:crc_index]
    crc_received = data[crc_index]
    crc_computed = _crc8_dvb_s2(data[2:crc_index])
    if crc_received != crc_computed:
        raise CrsfParseError(
            f"CRC8 mismatch: frame declares 0x{crc_received:02X}, computed 0x{crc_computed:02X}"
        )

    return CrsfFrame(device_addr=device_addr, frame_type=frame_type, payload=bytes(payload), crc=crc_received)


def decode_rc_channels_packed(payload: bytes) -> CrsfRcChannels:
    """Unpacks 16 channels x 11 bits, LSB-first, from a 22-byte
    `RC_CHANNELS_PACKED` payload. Raises `CrsfParseError` if `payload` is
    not exactly 22 bytes."""
    if len(payload) != _RC_CHANNELS_PAYLOAD_LEN:
        raise CrsfParseError(
            f"RC_CHANNELS_PACKED payload must be {_RC_CHANNELS_PAYLOAD_LEN} bytes, got {len(payload)}"
        )

    channels: list[int] = []
    bit_buffer = 0
    bit_count = 0
    byte_index = 0
    for _ in range(_RC_CHANNEL_COUNT):
        while bit_count < _RC_CHANNEL_BITS:
            bit_buffer |= payload[byte_index] << bit_count
            bit_count += 8
            byte_index += 1
        channels.append(bit_buffer & 0x7FF)
        bit_buffer >>= _RC_CHANNEL_BITS
        bit_count -= _RC_CHANNEL_BITS

    return CrsfRcChannels(channels=tuple(channels))


def decode_link_statistics(payload: bytes) -> CrsfLinkStatistics:
    """Decodes a 10-byte `LINK_STATISTICS` payload. Raises `CrsfParseError`
    if `payload` is not exactly 10 bytes."""
    if len(payload) != _LINK_STATISTICS_PAYLOAD_LEN:
        raise CrsfParseError(
            f"LINK_STATISTICS payload must be {_LINK_STATISTICS_PAYLOAD_LEN} bytes, got {len(payload)}"
        )
    fields = struct.unpack(_LINK_STATISTICS_STRUCT, payload)
    return CrsfLinkStatistics(
        uplink_rssi_1=fields[0],
        uplink_rssi_2=fields[1],
        uplink_link_quality=fields[2],
        uplink_snr=fields[3],
        active_antenna=fields[4],
        rf_profile=fields[5],
        uplink_tx_power=fields[6],
        downlink_rssi=fields[7],
        downlink_link_quality=fields[8],
        downlink_snr=fields[9],
    )


def describe_crsf_frame(frame: CrsfFrame) -> str:
    """Short debug string — no Safety/autonomy call, matches the
    `describe_dual_role`-style helper already shipped in `radio.py`."""
    return (
        f"CrsfFrame(device_addr=0x{frame.device_addr:02X}, "
        f"frame_type=0x{frame.frame_type:02X}, payload_len={len(frame.payload)})"
    )
