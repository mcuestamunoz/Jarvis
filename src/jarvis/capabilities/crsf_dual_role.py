"""Fase C · C20 — CRSF decoded → C5 dual-role bridge
(`B1-fase-c-crsf-dual-role-bridge`).

**What this is:** a small, deterministic bridge from C19's decoded
`CrsfRcChannels` into C5's typed `RadioStubFrame`/`RadioDualRoleResult`,
under one documented policy (`CrsfDualRolePolicy`). Still fixture/host-
only — nothing here opens a serial/USB/SPI port, decodes live ELRS RF,
or claims a receiver is "connected." "Bytes C19 already understands can
produce a typed dual-role frame under an explicit policy" is the entire
claim of this module.

**Module boundary (locked, C20 IC §0 decision 4):** this is a **new,
separate** module — not folded into `crsf_stub.py` (would bloat it past
its own C19 scope) and, critically, **not** folded into `radio.py`:
C5's own honesty lock (T5 — no `decode_crsf`/`decode_elrs`/`open_serial`
public API on `radio.py`) stays untouched by this Buy. This module
*imports* both `crsf_stub` and `radio` — the dependency runs one way.

**Authority-only in this Buy (locked, C20 IC §0 decision 6):** the
bridge only ever produces `RadioStubFrame(role="authority", ...)` — it
never invents `Intent` text from RC channel values, and never returns
`role="intent"` or `role="both"`. Synthesizing Intent from sticks is
explicitly out of scope unless a later IC expands this one.

**Authority is trace-only relative to Safety (same C5/C17 honesty,
re-affirmed here, not re-implemented):** nothing in this module
constructs a `SafetyRequest`, calls `SafetyGate.evaluate(...)`, or
touches `default_safety_gate()`/`ArmedAllowlistSafetyGate` at all. An
`AuthoritySignal` produced by this bridge can carry `authority_signal_id`
into a `SafetyRequest` **only** if a caller outside this module chooses
to do that — and even then, every shipped gate (C2's `RejectAllSafetyGate`
and C17's `ArmedAllowlistSafetyGate`) already ignores or never reads that
field. This module does not change that in any way.

**No execution path (locked, C20 IC §0 decision 8):** this module never
calls `submit_command`, never imports `jarvis.flight_software.autonomy`,
and never constructs anything resembling an execution claim. Producing a
`RadioDualRoleResult` is not "the pilot's sticks control the craft" —
there is no mixer, no ESC, no actuator anywhere downstream of this
module.

**No I/O anywhere in this module** — no `serial`, `socket`, `pty`, USB,
subprocess, or `open()` of a device path; no byte-stream reassembly, no
`ElrsLink`/`connect()`. Every function here takes typed data (already
decoded by `crsf_stub`) and returns typed data.

**Policy (locked minimum, C20 IC §0 decision 5):** exactly one aux RC
channel index (`0..15`) and one threshold (CRSF 11-bit units,
`[0, 2047]`) — when that channel's value is `>= threshold`, the bridge
emits `AuthorityKind="kill"` (the one locked default for this Buy; no
other kind is selectable here). Below threshold, the bridge returns
`None` — there is no "low" Authority event, no `role="authority"` frame
carrying an implicit "all clear," in this Buy.
"""

from __future__ import annotations

from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, field_validator

from jarvis.capabilities.crsf_stub import CrsfLinkStatistics, CrsfRcChannels
from jarvis.capabilities.radio import RadioDualRoleResult, RadioStubFrame, SimulatedRadioIngress

_MIN_CHANNEL_INDEX: Final[int] = 0
_MAX_CHANNEL_INDEX: Final[int] = 15
_MIN_CRSF_UNIT: Final[int] = 0
_MAX_CRSF_UNIT: Final[int] = 2047

# Illustrative defaults only — not sourced from any specific radio/
# receiver's real channel mapping. Channel index 4 (the 5th channel,
# 0-indexed) is a common AUX1/arm-switch position in the CRSF/Betaflight
# convention; 1500 sits well above the CRSF mid value (992) in the
# typical calibrated [172, 1811] range, modeling a switch flipped "high."
_DEFAULT_AUTHORITY_CHANNEL_INDEX: Final[int] = 4
_DEFAULT_AUTHORITY_THRESHOLD: Final[int] = 1500
_DEFAULT_AUTHORITY_KIND: Final[Literal["kill"]] = "kill"


class CrsfDualRolePolicy(BaseModel):
    """Locked-minimum bridge policy — one aux channel, one threshold, one
    Authority kind (`"kill"`, the only value this Buy supports). Index and
    threshold are validated against the real CRSF channel/value ranges."""

    model_config = ConfigDict(extra="forbid")

    authority_channel_index: int = _DEFAULT_AUTHORITY_CHANNEL_INDEX
    authority_threshold: int = _DEFAULT_AUTHORITY_THRESHOLD
    authority_kind: Literal["kill"] = _DEFAULT_AUTHORITY_KIND

    @field_validator("authority_channel_index")
    @classmethod
    def _validate_channel_index(cls, value: int) -> int:
        if not (_MIN_CHANNEL_INDEX <= value <= _MAX_CHANNEL_INDEX):
            raise ValueError(
                f"authority_channel_index must be in [{_MIN_CHANNEL_INDEX}, {_MAX_CHANNEL_INDEX}]"
            )
        return value

    @field_validator("authority_threshold")
    @classmethod
    def _validate_threshold(cls, value: int) -> int:
        if not (_MIN_CRSF_UNIT <= value <= _MAX_CRSF_UNIT):
            raise ValueError(f"authority_threshold must be in [{_MIN_CRSF_UNIT}, {_MAX_CRSF_UNIT}]")
        return value


def rc_channels_to_stub_frame(
    channels: CrsfRcChannels,
    *,
    policy: CrsfDualRolePolicy,
    frame_id: str | None = None,
    link_stats: CrsfLinkStatistics | None = None,
) -> RadioStubFrame | None:
    """Returns `RadioStubFrame(role="authority", ...)` when
    `channels.channels[policy.authority_channel_index] >=
    policy.authority_threshold`; returns `None` otherwise — no frame is
    produced below threshold. `link_stats`, if given, is folded into
    `notes` only (never changes whether Authority fires, never touches
    Safety — IC §0 decision 7)."""
    value = channels.channels[policy.authority_channel_index]
    if value < policy.authority_threshold:
        return None

    notes = None
    if link_stats is not None:
        notes = (
            f"link: lq={link_stats.uplink_link_quality} "
            f"rssi1={link_stats.uplink_rssi_1} snr={link_stats.uplink_snr}"
        )

    kwargs: dict[str, object] = {
        "role": "authority",
        "authority_kind": policy.authority_kind,
        "authority_payload": f"crsf_aux_channel={policy.authority_channel_index} value={value}",
        "notes": notes,
    }
    if frame_id is not None:
        kwargs["id"] = frame_id
    return RadioStubFrame(**kwargs)


def ingest_rc_channels(
    channels: CrsfRcChannels,
    *,
    policy: CrsfDualRolePolicy,
    ingress: SimulatedRadioIngress | None = None,
    link_stats: CrsfLinkStatistics | None = None,
) -> RadioDualRoleResult | None:
    """Builds a stub frame via `rc_channels_to_stub_frame(...)` and, if one
    was produced, feeds it through `SimulatedRadioIngress.ingest(...)`.
    Returns `None` when no frame was produced (below threshold). Never
    calls `SafetyGate.evaluate` or `submit_command` — there is no
    execution step here, ever."""
    frame = rc_channels_to_stub_frame(channels, policy=policy, link_stats=link_stats)
    if frame is None:
        return None
    active_ingress = ingress or SimulatedRadioIngress()
    return active_ingress.ingest(frame)
