"""Fase C · C31 — DShot 16-bit frame encode stub
(`B1-fase-c-dshot-encode-stub`).

**What this is:** the same move C10 made for PWM-µs, applied to DShot —
`encode_dshot_frame(throttle, telemetry) -> int` computes the 16-bit
packet DShot's own protocol defines, **in RAM, on the Mac**. Given "the
desk ESC (HGLRC 60A 6S, Bluejay) speaks DShot150/300/600," this rung
answers "here is the 16-bit number that protocol packs" — it does not
answer "here is a GPIO pin toggling at that rate."

**What this is not — read before using this module:** **not** GPIO,
**not** a timer/DMA bit-bang driver, **not** a claim that any ESC has
seen this frame, **not** DShot150 vs 300 vs 600 as a *pin period*
(those numbers are the protocol's own advertised bitrates in kbit/s —
this module encodes the same 16-bit value regardless of which speed a
future pin driver would eventually clock it out at), and **not** a
switch of `EscOutput`/`SimulatedEscSink` off their existing PWM-µs
default (C10/C26) — that stays exactly as it was.

**DShot encode != pin != motors != flying.**

**Frame layout (locked, C31 IC §0 decision 5):**

```text
bits 15-5  (11 bits)  throttle/command value
bit  4     (1 bit)    telemetry request
bits 3-0   (4 bits)   checksum (nibble XOR of the 12-bit value+telem field)

value    = (throttle << 1) | telemetry
checksum = (value ^ (value >> 4) ^ (value >> 8)) & 0xF
frame    = (value << 4) | checksum
```

`throttle` must be an integer in `[0, 2047]` inclusive; anything else
raises a typed `ValueError`. **Known vectors** (verified in this Buy's
own tests, both languages): `throttle=0, telemetry=False -> 0x0000`;
`throttle=48, telemetry=False -> 0x0606`; `throttle=2047,
telemetry=False -> 0xFFEE`.

**Special range (locked, decision 6):** DShot's own protocol reserves
`0..47` as **commands** (motor beep, 3D mode, save settings, etc.) and
`48..2047` as throttle. This module encodes whatever 11-bit value it is
given — it does **not** implement a command table. Passing a value in
`0..47` produces a syntactically valid frame; interpreting that frame as
a specific command is out of scope for this Buy.

**Optional force-to-DShot helper (decision 7):**
`encode_motor_forces_dshot(forces) -> tuple[int, int, int, int]` linearly
maps each clamped force `[0, 1]` onto throttle **`48..2047`** (not
`0..2047` — `0` there would collide with the command range) and encodes
each with `encode_dshot_frame`. This is a **separate, parallel** path —
C10's own `encode_motor_forces` (PWM-µs) is completely unchanged, and
`EscOutput`/`SimulatedEscSink` still default to PWM-µs (C26); nothing in
this module rewires either.

**Rates 150/300/600 (decision 9):** these may appear in comments as the
desk ESC's own advertised protocol names (Bluejay supports
DShot150/300/600) — never as a claimed timer period, GPIO toggle rate,
or bit-bang timing. No such timing exists anywhere in this module.

No `write_gpio`, `TIM`, `DMA`, `BSRR`, `pigpio`, or ESC-register access
anywhere in this module — this is a pure integer encoding, never
actuation.
"""

from __future__ import annotations

import math
from typing import Final

from jarvis.flight_software.flight_control.mixer import MotorForceCommand

_MIN_THROTTLE: Final[int] = 0
_MAX_THROTTLE: Final[int] = 2047

DSHOT_MIN_COMMAND_VALUE: Final[int] = 0
DSHOT_MAX_COMMAND_VALUE: Final[int] = 47
DSHOT_MIN_THROTTLE_VALUE: Final[int] = 48
DSHOT_MAX_THROTTLE_VALUE: Final[int] = 2047


def encode_dshot_frame(throttle: int, telemetry: bool = False) -> int:
    """Encodes the 16-bit DShot frame for `throttle` (`0..2047`) plus an
    optional telemetry-request bit. Pure integer math — no I/O, no GPIO,
    no claim any ESC has received this value."""
    if isinstance(throttle, bool) or not isinstance(throttle, int):
        raise ValueError(f"throttle must be an int, got {throttle!r}")
    if throttle < _MIN_THROTTLE or throttle > _MAX_THROTTLE:
        raise ValueError(f"throttle must be in [{_MIN_THROTTLE}, {_MAX_THROTTLE}], got {throttle}")

    value = (throttle << 1) | (1 if telemetry else 0)
    checksum = (value ^ (value >> 4) ^ (value >> 8)) & 0xF
    return (value << 4) | checksum


def encode_motor_forces_dshot(forces: MotorForceCommand) -> tuple[int, int, int, int]:
    """Linearly maps each clamped motor force `[0, 1]` onto DShot
    throttle `[48, 2047]` (never `0..47` — that range is DShot's own
    command space, not throttle) and encodes each with
    `encode_dshot_frame`. A separate, parallel path — C10's own
    `encode_motor_forces` (PWM-µs) and `EscOutput`'s PWM default are
    both unchanged by this function's existence."""
    span = DSHOT_MAX_THROTTLE_VALUE - DSHOT_MIN_THROTTLE_VALUE
    throttles = tuple(
        DSHOT_MIN_THROTTLE_VALUE + round(_clamp01(force) * span) for force in forces.motor_forces
    )
    return tuple(encode_dshot_frame(t) for t in throttles)  # type: ignore[return-value]


def _clamp01(value: float) -> float:
    if not math.isfinite(value):
        return 0.0
    return max(0.0, min(1.0, value))
