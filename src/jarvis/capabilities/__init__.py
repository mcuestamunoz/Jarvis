"""Fase C scaffold — typed Skill/Capability/Provider schemas (C1), the
Capability Registry (C1, empty by default at scaffold time — T2/`B1-
capability-registry-product-fill` later gives `load_default()` a first
honest, non-empty product seed: `ontology.explain`/`engineering.
continuity`, both software-fulfilled and `available`, still zero
dispatcher method anywhere in this package), Intent ingress + Safety
gate stubs (C2), and a simulated radio dual-role ingress (C5).
Descriptive only: no execution path anywhere in this package. Scaffold
@ 0.5.0 != Flight Software shipped. See
`.jes/artifacts/implementation_contract_fase_c_capability_registry_scaffold_b1.md`,
`.jes/artifacts/implementation_contract_fase_c_intent_safety_stub_b1.md`,
and
`.jes/artifacts/implementation_contract_fase_c_radio_dual_role_b1.md`.

Note: there is no `AllowAllSafetyGate` anywhere in this package (C2 IC
§2.2 lock) — the only shipped gate **factory**, `default_safety_gate()`,
always returns `RejectAllSafetyGate`. Radio (C5) never bypasses it: an
`AuthoritySignal` never implies `SafetyDecision(outcome="allow")`, and
`RadioIntentAdapter.parse(...)` still always raises `NotImplementedError`
— `SimulatedRadioIngress` is a separate, explicitly-simulated API.

C17 adds `ArmedAllowlistSafetyGate` — the first real (non-RejectAll)
Safety policy: opt-in, starts disarmed, allows only `HOLD`/`LAND` once
explicitly armed, never reads `authority_signal_id`. C41
(`B1-fase-c-safety-sim-policy`) widens that same gate's allow-list to
also include `GO_TO`, matching what `SimAutonomyExecutor` (C40) can
drive in sim — still one gate class, still opt-in, still never calling
that executor or being called from it. `default_safety_gate()` is
unchanged. See `jarvis.capabilities.safety`'s own docstring.

C19 adds `jarvis.capabilities.crsf_stub` — a **separate** module (never
folded into `radio.py`, preserving its own no-decode-API lock) that
parses CRSF byte fixtures (the wire framing ExpressLRS commonly carries
on the UART between RX and FC) into typed data: frame envelope + RC
channels + link statistics. Fixture CRSF parse != live ELRS != a pilot
link — no serial/USB/SPI I/O anywhere in that module, and nothing it
produces reaches `SimulatedRadioIngress`, `RadioIntentAdapter`, autonomy
`submit_command`, or any `SafetyGate`. See
`jarvis.capabilities.crsf_stub`'s own docstring.

C20 adds `jarvis.capabilities.crsf_dual_role` — a third **separate**
module (also never folded into `radio.py`) that bridges C19's decoded
`CrsfRcChannels` into C5's typed `RadioStubFrame`/`RadioDualRoleResult`
under one documented, deterministic policy (`CrsfDualRolePolicy`:
one aux channel + threshold -> `AuthorityKind="kill"`, Authority-only,
never Intent). Authority produced this way is still trace-only relative
to Safety — every shipped gate ignores/never reads
`authority_signal_id`, `default_safety_gate()` is unchanged, and this
module never calls `submit_command` or any `SafetyGate.evaluate`. See
`jarvis.capabilities.crsf_dual_role`'s own docstring.

C21 adds `jarvis.capabilities.crsf_stream` — a fourth **separate**
module (also never folded into `radio.py`) that reassembles C19's typed
`CrsfFrame`s from bytes delivered in **arbitrary chunks** (the shape a
UART delivers data in) via `CrsfByteStreamAssembler`. It calls C19's own
`parse_crsf_frame` on exact candidate slices rather than reimplementing
CRC/envelope logic, waits on incomplete candidates, and silently
drops-and-resyncs one byte at a time on invalid complete windows —
`CrsfParseError` never reaches a caller of `feed(...)`. This is a byte
buffer, not a UART driver: no `serial`/`socket`/`pty`/USB/`open()`
anywhere in it. An optional `ingest_stream_bytes(...)` helper reuses
C20's `ingest_rc_channels(...)` unchanged for any completed `0x16`
frames. See `jarvis.capabilities.crsf_stream`'s own docstring.

C22 adds `jarvis.capabilities.crsf_serial` — a fifth **separate** module
(also never folded into `radio.py`) that pulls bytes from an already-
open host FD (tests: a POSIX `pty`) or an opt-in device path via
`CrsfHostSerialIngress`, and feeds them to C21's own
`CrsfByteStreamAssembler` unchanged. `poll(...)` does exactly one non-
blocking read then feed — no background thread, no "connected" flag, no
`/dev/cu.*` auto-scan, no `pyserial` dependency. An optional
`poll_and_ingest(...)` helper reuses C20's `ingest_rc_channels(...)`
unchanged for any completed `0x16` frames. Host serial ingest != live
ELRS != "RX connected" != Safety allow — every PASS in this repo uses a
`pty` loopback, never a physical receiver.

C23 extends `crsf_serial.py` (no sixth module) with **opt-in** Darwin
host baud configuration — `configure_host_baud(fd, baud=420000)` /
`CrsfHostSerialIngress.configure_baud(...)`. `420000` is the ELRS-typical
CRSF UART rate; baud is **no longer deferred**, but it is still never
automatic — `attach_fd`/`attach_path` never call it on their own. On
Darwin it applies raw 8N1 termios then issues the real `IOSSIOSPEED`
ioctl (request number derived from the `_IOW('T', 2, speed_t)` macro,
never hardcoded/copied); on any other `sys.platform` it fails closed with
a typed `CrsfHostSerialError`. Issuing the ioctl successfully is a host
OS configuration fact, never proof a receiver exists — every PASS in
this repo's own tests proves the Darwin path via a mocked `fcntl.ioctl`,
and the one unmocked case (a `pty`, which is not a UART) is asserted to
fail closed, not skipped for lack of hardware. See
`jarvis.capabilities.crsf_serial`'s own docstring.

T3 (`B1-assistant-task-registry-coherence`) adds the one edge T2's own
IC deliberately deferred: `jarvis.intelligence.assistant_task` now
imports `CapabilityRegistry` and soft-checks (membership only) every
capability id a Task would require before emitting it — `registry.py`
itself still never imports `jarvis.intelligence`. T4
(`B1-assistant-software-safety-bridge`) adds `SoftwareCapabilitySafetyGate`
(`gate_id="software_capability"`) — the first Assistant→Safety link,
run immediately after that membership check: `allow` iff every id is
`available` and bound to a `software`-kind provider. `default_safety_gate()`
stays `RejectAllSafetyGate`; `ArmedAllowlistSafetyGate` is untouched. T5
(`B1-capability-skills-seed`) fills the checked-in seed's `skills` array
— two declared-only, `availability=stub` `SkillRecord` rows
(`skill.explain_concept`/`skill.project_status`), naming the same two
capability ids T0/T1's Task classify already requires. `skills()` is no
longer always-empty, but there is still no Skill execution path
anywhere in this package — the Assistant does not look these rows up
before emitting a Task.
"""

from jarvis.capabilities.intent import (
    ApiIntentAdapter,
    Intent,
    IntentSource,
    RadioIntentAdapter,
    Task,
    TerminalIntentAdapter,
    VoiceIntentAdapter,
)
from jarvis.capabilities.radio import (
    RadioDualRoleResult,
    RadioStubFrame,
    SimulatedRadioIngress,
    describe_dual_role,
)
from jarvis.capabilities.registry import CapabilityRegistry, CapabilityRegistryError
from jarvis.capabilities.safety import (
    ArmedAllowlistSafetyGate,
    AuthoritySignal,
    RejectAllSafetyGate,
    SafetyDecision,
    SafetyGate,
    SafetyRequest,
    SoftwareCapabilitySafetyGate,
    default_safety_gate,
    run_intent_through_safety,
)
from jarvis.capabilities.schemas import (
    CapabilityAvailability,
    CapabilityHealth,
    CapabilityRecord,
    ProviderKind,
    ProviderRecord,
    SkillRecord,
)
from jarvis.capabilities.skills_runtime import SkillRunResult, run_skill

__all__ = [
    "ApiIntentAdapter",
    "ArmedAllowlistSafetyGate",
    "AuthoritySignal",
    "CapabilityAvailability",
    "CapabilityHealth",
    "CapabilityRecord",
    "CapabilityRegistry",
    "CapabilityRegistryError",
    "Intent",
    "IntentSource",
    "ProviderKind",
    "ProviderRecord",
    "RadioDualRoleResult",
    "RadioIntentAdapter",
    "RadioStubFrame",
    "RejectAllSafetyGate",
    "SafetyDecision",
    "SafetyGate",
    "SafetyRequest",
    "SimulatedRadioIngress",
    "SkillRecord",
    "SkillRunResult",
    "SoftwareCapabilitySafetyGate",
    "Task",
    "TerminalIntentAdapter",
    "VoiceIntentAdapter",
    "default_safety_gate",
    "describe_dual_role",
    "run_intent_through_safety",
    "run_skill",
]
