"""Skill runner — software Skills (T21/T22) + vehicle Skill gate
(T23-T29) + policy Skill gate (T30) + device Skill gate (T31).

T5 (`B1-capability-skills-seed`) declared Skill rows. T21 added
`run_skill(skill_id, ...)`, a thin dispatcher that looks a Skill up,
checks it is `available`, then either:

* **software Skills** (`skill.explain_concept` / `skill.project_status`):
  re-runs the T4-shaped `SoftwareCapabilitySafetyGate` check and calls
  the existing fulfill path — never a second cite/Continuity brain;
* **vehicle Skills** (`skill.request_hold`, T23; `skill.request_land`,
  T24; `skill.request_go_to`, T25; `skill.request_takeoff`, T26;
  `skill.request_return_home`, T27; `skill.request_follow`, T28;
  `skill.request_patrol`, T29 — this closes the full seven-verb chat
  AutonomyVerb Skill-first set): shared `_vehicle_skill_gate` — does
  **not** use
  `SoftwareCapabilitySafetyGate` (that gate only allows
  `available`+`software`; `flight.*` is intentionally
  `not_implemented`/`vehicle`). Registry membership that every
  required capability exists and its bound provider `kind == vehicle`.
  On pass → `outcome="ok"` as a **gate only** — no `propose_command`,
  ArmedAllowlist, sim, or imports of `jarvis.core` /
  `jarvis.flight_software` / `jarvis.vehicle_profiles`. Chat fulfill
  stays in `core/orchestrator.py`;
* **policy Skills** (`skill.request_arm_policy` / `skill.request_disarm_policy`,
  T30 — first policy slice, deliberately separate from the vehicle gate
  since ARM/DISARM are a software latch, not an `AutonomyVerb`): same
  `SoftwareCapabilitySafetyGate` check as software Skills (their
  required capability, `safety.chat_armed_allowlist`, is
  `available`+`software`); on allow → gate-only `outcome="ok"`, no
  latch mutate here — `core/orchestrator.py`'s existing
  `_handle_arm_policy`/`_handle_disarm_policy` still own the real
  `gate.arm()`/`gate.disarm()` call and honesty message;
* **device Skills** (`skill.request_charge`, T31 — last chat Skill
  stub, closing all twelve declared Skills): shared `_device_skill_gate`
  — membership + provider `kind == device`, checked **before** the
  software Safety branch (that gate would reject `ops.charge`'s
  `not_implemented`+`device` shape outright). On pass → gate-only
  `outcome="ok"` — no `propose_command`/AutonomyVerb/ArmedAllowlist/sim
  /real battery here; `core/orchestrator.py`'s existing
  `_handle_ops_charge` still owns the honest not-implemented message.

**Chat Skill-first:** T22 wires explain/status; T23 HOLD; T24 LAND; T25
GO_TO; T26 TAKEOFF; T27 RETURN_HOME; T28 FOLLOW; T29 PATROL; T30
ARM/DISARM; T31 CHARGE — classify (`try_*_task`) still chooses the
Skill/Task id. GO_TO's own `flight.go_to` capability stays
`not_implemented` — only the Skill row flips `available`; SD-GO_TO
(chat GO_TO never parses a destination, while the T20 sim executor
requires one) stays explicitly OPEN, not touched by this gate.
TAKEOFF's/RETURN_HOME's/FOLLOW's/PATROL's own
`flight.takeoff`/`flight.return_home`/`flight.follow`/`flight.patrol`
capabilities likewise stay `not_implemented`; none of the four is in
the T20 sim-copper tick set (that only covers HOLD/LAND/GO_TO) — this
gate never changes that. RETURN_HOME also keeps the FN-016 wizard
nav-back cancel (`is_navigation_back_phrase`) winning over this gate
whenever `DEFINE_MISSING_PARAMETERS` is active — that check runs
earlier in `core/orchestrator.py`, untouched by this module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Final

from pydantic import BaseModel, ConfigDict

from jarvis.capabilities.registry import CapabilityRegistry
from jarvis.capabilities.safety import SafetyRequest, SoftwareCapabilitySafetyGate
from jarvis.capabilities.schemas import CapabilityAvailability, ProviderKind, SkillRecord

SKILL_ID_EXPLAIN_CONCEPT = "skill.explain_concept"
SKILL_ID_PROJECT_STATUS = "skill.project_status"
SKILL_ID_REQUEST_HOLD = "skill.request_hold"
SKILL_ID_REQUEST_LAND = "skill.request_land"
SKILL_ID_REQUEST_GO_TO = "skill.request_go_to"
SKILL_ID_REQUEST_TAKEOFF = "skill.request_takeoff"
SKILL_ID_REQUEST_RETURN_HOME = "skill.request_return_home"
SKILL_ID_REQUEST_FOLLOW = "skill.request_follow"
SKILL_ID_REQUEST_PATROL = "skill.request_patrol"
SKILL_ID_REQUEST_ARM_POLICY = "skill.request_arm_policy"
SKILL_ID_REQUEST_DISARM_POLICY = "skill.request_disarm_policy"
SKILL_ID_REQUEST_CHARGE = "skill.request_charge"

# T23-T29: finite set of vehicle Skills that use the shared vehicle gate.
_VEHICLE_GATE_SKILL_IDS: Final[frozenset[str]] = frozenset(
    {
        SKILL_ID_REQUEST_HOLD,
        SKILL_ID_REQUEST_LAND,
        SKILL_ID_REQUEST_GO_TO,
        SKILL_ID_REQUEST_TAKEOFF,
        SKILL_ID_REQUEST_RETURN_HOME,
        SKILL_ID_REQUEST_FOLLOW,
        SKILL_ID_REQUEST_PATROL,
    }
)

# T30: first policy Skill-first pair — software Safety gate-only, never the
# vehicle gate (ARM/DISARM are a software latch, not an AutonomyVerb).
_POLICY_GATE_SKILL_IDS: Final[frozenset[str]] = frozenset(
    {
        SKILL_ID_REQUEST_ARM_POLICY,
        SKILL_ID_REQUEST_DISARM_POLICY,
    }
)

# T31: device Skill-first set — membership + provider kind==device gate,
# never vehicle, never policy, never SoftwareCapabilitySafetyGate (which
# would reject ops.charge's not_implemented+device shape outright).
_DEVICE_GATE_SKILL_IDS: Final[frozenset[str]] = frozenset(
    {
        SKILL_ID_REQUEST_CHARGE,
    }
)


class SkillRunResult(BaseModel):
    """Everything one `run_skill(...)` call produced — finite outcomes,
    never a second Task/intent record."""

    model_config = ConfigDict(extra="forbid")

    skill_id: str
    outcome: str  # "ok" | "reject"
    reason: str | None = None
    message: str | None = None


def _software_safety_allows_skill(required_capability_ids: list[str]) -> bool:
    """Same T4-shaped check `jarvis.intelligence.assistant_task.
    _software_safety_allows` already performs for a software Task —
    reimplemented at this same shallow depth (one `SafetyRequest` +
    `SoftwareCapabilitySafetyGate().evaluate`) rather than imported,
    since that helper is private to `assistant_task.py`.
    `default_safety_gate()` (always `RejectAllSafetyGate`) is never
    touched by this check."""
    action_id = "capability:" + ",".join(required_capability_ids)
    decision = SoftwareCapabilitySafetyGate().evaluate(SafetyRequest(action_id=action_id))
    return decision.outcome == "allow"


def _vehicle_skill_gate(
    registry: CapabilityRegistry, skill: SkillRecord
) -> SkillRunResult:
    """Shared vehicle Skill gate (T23 HOLD / T24 LAND): membership +
    provider kind==vehicle. Never software Safety, never propose_command/sim."""
    for capability_id in skill.required_capability_ids:
        capability = registry.get_capability(capability_id)
        if capability is None:
            return SkillRunResult(
                skill_id=skill.id, outcome="reject", reason="capability_unknown"
            )
        if not capability.provider_id:
            return SkillRunResult(
                skill_id=skill.id, outcome="reject", reason="provider_not_vehicle"
            )
        provider = registry.get_provider(capability.provider_id)
        if provider is None or provider.kind != ProviderKind.VEHICLE:
            return SkillRunResult(
                skill_id=skill.id, outcome="reject", reason="provider_not_vehicle"
            )
    return SkillRunResult(skill_id=skill.id, outcome="ok")


def _device_skill_gate(
    registry: CapabilityRegistry, skill: SkillRecord
) -> SkillRunResult:
    """Device Skill gate (T31 CHARGE): membership + provider kind==device.
    Never software Safety (ops.charge is not_implemented+device, which
    SoftwareCapabilitySafetyGate would reject outright), never
    propose_command/AutonomyVerb/ArmedAllowlist/sim."""
    for capability_id in skill.required_capability_ids:
        capability = registry.get_capability(capability_id)
        if capability is None:
            return SkillRunResult(
                skill_id=skill.id, outcome="reject", reason="capability_unknown"
            )
        if not capability.provider_id:
            return SkillRunResult(
                skill_id=skill.id, outcome="reject", reason="provider_not_device"
            )
        provider = registry.get_provider(capability.provider_id)
        if provider is None or provider.kind != ProviderKind.DEVICE:
            return SkillRunResult(
                skill_id=skill.id, outcome="reject", reason="provider_not_device"
            )
    return SkillRunResult(skill_id=skill.id, outcome="ok")


def run_skill(
    skill_id: str,
    *,
    query: str | None = None,
    project_status_provider: Callable[[], dict] | None = None,
    ontology_root: Path | None = None,
) -> SkillRunResult:
    """Look `skill_id` up in `CapabilityRegistry.load_default()`, require
    `availability == AVAILABLE`, then dispatch:

    * vehicle Skills (HOLD…PATROL) → shared vehicle membership/provider
      gate (T23-T29), never `SoftwareCapabilitySafetyGate`;
    * device Skills (CHARGE, T31) → membership/provider `kind==device`
      gate, also never `SoftwareCapabilitySafetyGate` (it would reject
      `ops.charge`'s `not_implemented`+`device` shape outright);
    * policy Skills (ARM/DISARM, T30) → `SoftwareCapabilitySafetyGate`
      on `safety.chat_armed_allowlist`; on allow, gate-only `ok` — no
      latch mutate here, orch owns `_handle_arm_policy`/`_handle_disarm_policy`;
    * software Skills (explain/status) → same software Safety check +
      existing fulfill.

    After T31 there are no remaining stub Skills among the twelve
    declared rows — an unknown id still `unknown_skill`, and a future
    stub row would still `skill_stub`.

    Finite `reason`s: `unknown_skill` / `skill_stub` / `safety_reject` /
    `capability_unknown` / `provider_not_vehicle` / `provider_not_device` /
    `missing_query` / `no_project` / `no_dispatcher`.

    T22: chat Skill-first may pass `ontology_root` through to
    `fulfill_ontology_explain` (tests / alternate vault roots).
    """
    registry = CapabilityRegistry.load_default()
    skill = next((s for s in registry.skills() if s.id == skill_id), None)
    if skill is None:
        return SkillRunResult(skill_id=skill_id, outcome="reject", reason="unknown_skill")

    if skill.availability != CapabilityAvailability.AVAILABLE:
        return SkillRunResult(skill_id=skill_id, outcome="reject", reason="skill_stub")

    # T23-T29: vehicle Skills must not route through SoftwareCapabilitySafetyGate.
    if skill_id in _VEHICLE_GATE_SKILL_IDS:
        return _vehicle_skill_gate(registry, skill)

    # T31: device Skills (CHARGE) must not route through
    # SoftwareCapabilitySafetyGate either — ops.charge is
    # not_implemented+device, which that gate would reject outright.
    if skill_id in _DEVICE_GATE_SKILL_IDS:
        return _device_skill_gate(registry, skill)

    if not _software_safety_allows_skill(skill.required_capability_ids):
        return SkillRunResult(skill_id=skill_id, outcome="reject", reason="safety_reject")

    # T30: policy Skills (ARM/DISARM) are gate-only after software Safety
    # allow — no latch mutate inside skills_runtime; orch owns fulfill.
    if skill_id in _POLICY_GATE_SKILL_IDS:
        return SkillRunResult(skill_id=skill_id, outcome="ok")

    if skill_id == SKILL_ID_EXPLAIN_CONCEPT:
        if query is None:
            return SkillRunResult(skill_id=skill_id, outcome="reject", reason="missing_query")
        from jarvis.intelligence.assistant_task import fulfill_ontology_explain

        message = fulfill_ontology_explain(query, ontology_root=ontology_root)
        return SkillRunResult(skill_id=skill_id, outcome="ok", message=message)

    if skill_id == SKILL_ID_PROJECT_STATUS:
        if project_status_provider is None:
            return SkillRunResult(skill_id=skill_id, outcome="reject", reason="no_project")
        ctx = project_status_provider()
        if ctx.get("has_project") is False:
            return SkillRunResult(skill_id=skill_id, outcome="reject", reason="no_project")
        return SkillRunResult(skill_id=skill_id, outcome="ok", message=str(ctx))

    # Only reachable if default_registry.json marks another Skill
    # `available` without a matching dispatch arm — config/code mismatch.
    return SkillRunResult(skill_id=skill_id, outcome="reject", reason="no_dispatcher")
