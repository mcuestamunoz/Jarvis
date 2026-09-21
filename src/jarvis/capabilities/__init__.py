"""Fase C scaffold — typed Skill/Capability/Provider schemas (C1), an
empty-by-default Capability Registry (C1), Intent ingress + Safety gate
stubs (C2), and a simulated radio dual-role ingress (C5). Descriptive
only: no execution path anywhere in this package. Scaffold @ 0.5.0 !=
Flight Software shipped. See
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
explicitly armed, never reads `authority_signal_id`. `default_safety_gate()`
is unchanged. See `jarvis.capabilities.safety`'s own docstring.

C19 adds `jarvis.capabilities.crsf_stub` — a **separate** module (never
folded into `radio.py`, preserving its own no-decode-API lock) that
parses CRSF byte fixtures (the wire framing ExpressLRS commonly carries
on the UART between RX and FC) into typed data: frame envelope + RC
channels + link statistics. Fixture CRSF parse != live ELRS != a pilot
link — no serial/USB/SPI I/O anywhere in that module, and nothing it
produces reaches `SimulatedRadioIngress`, `RadioIntentAdapter`, autonomy
`submit_command`, or any `SafetyGate`. See
`jarvis.capabilities.crsf_stub`'s own docstring.
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
    "Task",
    "TerminalIntentAdapter",
    "VoiceIntentAdapter",
    "default_safety_gate",
    "describe_dual_role",
    "run_intent_through_safety",
]
