"""Fase C · C27 — CRSF stream-timeout failsafe
(`B1-fase-c-crsf-stream-timeout-failsafe`).

**What this is:** an **age watch**. If a valid RC-channels frame has not
been **noted** within a documented timeout (default `0.5` s), the last
stick values are no longer treated as live — the caller gets a typed
stale/failsafe decision instead of silently keeping the last decoded
AETR tuple "current" forever. Nothing here parses bytes: C21's own
`CrsfByteStreamAssembler.feed(...)` math is unchanged, C20's `kill`
policy is unchanged, and C25's `map_rc_to_loop_inputs` math is unchanged
— this module only tracks *when* a valid sample last arrived.

**What this is not — read before using this module:** this is **not**
"ExpressLRS failsafe" as a product, **not** a claim that any real
receiver has detected link loss, **not** a GPIO/motor cut, **not** a
Safety decision, and does **not** call `FlightControlLoop.step`,
`EscOutput`, or `SafetyGate.evaluate`. `0.5` s is an illustrative
hold-loss window chosen for this Buy, not a spec sourced from any real
ExpressLRS/CRSF product's own failsafe timing.

**Module boundary (locked, C27 IC §0 decision 1/9):** a **new, separate**
module — not folded into `radio.py` (C5 T5 stays untouched: no
`decode_*`/`open_serial`/failsafe API grows there) and not a rewrite of
C21's `feed()` hunt/resync logic. The optional glue helper in this module
(`feed_and_note_rc`) calls C21's own `assembler.feed(data)` unchanged and
never calls `ingest_stream_bytes` — C21's own default helper's behavior
is untouched by this Buy.

**Clock (locked, decision 4):** every watch method takes `now_s` as a
caller-supplied argument. This module never calls `time.time()` (or any
wall-clock source) as its own source of truth — tests are deterministic
by construction, and a future caller decides what clock feeds `now_s`.

**Timeout (locked, decision 5):** `CRSF_RC_STALE_S = 0.5` is the default;
the constructor accepts a finite `timeout_s > 0` override.

**Note vs evaluate (locked, decision 6):** `note_rc(now_s)` records "a
valid RC-channels sample was available at this time" — nothing about
frame parsing happens inside `note_rc` itself, it is just a timestamp
record. `is_stale(now_s)`/`evaluate(now_s)` are stale when either no
sample was ever noted (`reason="never"`) or `now_s - last_s >
timeout_s` (`reason="timeout"`); otherwise fresh (`reason="fresh"`).
`age_s <= timeout_s` is fresh, `age_s > timeout_s` is stale — equality
at the boundary is fresh, not stale. Passing a `now_s` earlier than the
last noted time to `evaluate`/`is_stale` raises a typed `ValueError` —
this module does not silently accept the clock running backwards.

**Failsafe inputs (locked, decision 7):** `failsafe_loop_inputs(t_s)`
returns C8's own `level_setpoint(t_s)` plus `collective=0.0` — a plain
`RcLoopInputs` (C25's own type, reused unchanged). It never calls
`FlightControlLoop.step`, `EscOutput.apply_forces`, or any
`SafetyGate.evaluate`.

**Fresh path (locked, decision 8):** this module does **not** remap
sticks when fresh — that stays C25's `map_rc_to_loop_inputs` job, called
by the caller on the last noted channels. A watch is only an age check,
never a second AETR map.

**Timeout failsafe != motors cut != live ELRS != Safety allow.**

**Exists:** an age watch; after the timeout without a noted RC sample,
sticks are not "live"; the recommended inputs are level attitude plus
zero collective. **Impossible:** a radio that cuts ESCs; ExpressLRS
failsafe as a shipped product; Safety opening on timeout. Nothing here
is any of those.
"""

from __future__ import annotations

import math
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict

from jarvis.capabilities.crsf_stream import CrsfByteStreamAssembler
from jarvis.capabilities.crsf_stub import CRSF_FRAMETYPE_RC_CHANNELS_PACKED, CrsfFrame
from jarvis.flight_software.flight_control.controller import level_setpoint
from jarvis.flight_software.flight_control.rc_setpoint import RcLoopInputs

CRSF_RC_STALE_S: Final[float] = 0.5


class RcHoldDecision(BaseModel):
    """Typed stale/failsafe decision — never a bare `bool`, so the reason
    is always inspectable."""

    model_config = ConfigDict(extra="forbid")

    stale: bool
    reason: Literal["fresh", "never", "timeout"]
    age_s: float | None = None


class CrsfRcHoldWatch:
    """Age-only watch — holds a single "last noted" timestamp, nothing
    about channel values. `note_rc(now_s)` records that a valid
    RC-channels sample was available; `evaluate(now_s)`/`is_stale(now_s)`
    compare `now_s` against that record and `timeout_s`."""

    def __init__(self, timeout_s: float = CRSF_RC_STALE_S) -> None:
        if not math.isfinite(timeout_s) or timeout_s <= 0.0:
            raise ValueError("timeout_s must be finite and > 0")
        self._timeout_s = timeout_s
        self._last_s: float | None = None

    @property
    def timeout_s(self) -> float:
        return self._timeout_s

    def note_rc(self, now_s: float) -> None:
        """Records `now_s` as the last time a valid RC-channels sample
        was available. Pure bookkeeping — no frame parsing, no decoding,
        happens here."""
        self._last_s = now_s

    def is_stale(self, now_s: float) -> bool:
        return self.evaluate(now_s).stale

    def evaluate(self, now_s: float) -> RcHoldDecision:
        if self._last_s is None:
            return RcHoldDecision(stale=True, reason="never", age_s=None)
        if now_s < self._last_s:
            raise ValueError("now_s must not precede the last noted time")
        age_s = now_s - self._last_s
        if age_s <= self._timeout_s:
            return RcHoldDecision(stale=False, reason="fresh", age_s=age_s)
        return RcHoldDecision(stale=True, reason="timeout", age_s=age_s)


def failsafe_loop_inputs(t_s: float) -> RcLoopInputs:
    """Stale/failsafe decision: level attitude (C8's own `level_setpoint`)
    plus `collective=0.0`. Never calls `FlightControlLoop.step`,
    `EscOutput.apply_forces`, or any `SafetyGate.evaluate`."""
    return RcLoopInputs(setpoint=level_setpoint(t_s), collective=0.0)


def feed_and_note_rc(
    data: bytes, *, assembler: CrsfByteStreamAssembler, watch: CrsfRcHoldWatch, now_s: float
) -> list[CrsfFrame]:
    """Optional glue helper (decision 9): `assembler.feed(data)` — C21's
    own method, unchanged — then `watch.note_rc(now_s)` if at least one
    completed frame this call was a valid `RC_CHANNELS_PACKED` (`0x16`).
    Notes on raw channel arrival, independent of C20's own aux-channel
    Authority threshold — "RC data arrived" and "Authority kill fired"
    are different questions. Never calls `ingest_stream_bytes` — C21's
    own default helper is untouched by this function."""
    frames = assembler.feed(data)
    if any(frame.frame_type == CRSF_FRAMETYPE_RC_CHANNELS_PACKED for frame in frames):
        watch.note_rc(now_s)
    return frames
