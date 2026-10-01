"""Skill runner — software Skills (T21/T22) + first vehicle Skill gate (T23).

T5 (`B1-capability-skills-seed`) declared Skill rows. T21 added
`run_skill(skill_id, ...)`, a thin dispatcher that looks a Skill up,
checks it is `available`, then either:

* **software Skills** (`skill.explain_concept` / `skill.project_status`):
  re-runs the T4-shaped `SoftwareCapabilitySafetyGate` check and calls
  the existing fulfill path — never a second cite/Continuity brain;
* **vehicle HOLD** (`skill.request_hold`, T23): does **not** use
  `SoftwareCapabilitySafetyGate` (that gate only allows
  `available`+`software`; `flight.hold` is intentionally
  `not_implemented`/`vehicle`). Instead: registry membership that every
  required capability exists and its bound provider `kind == vehicle`.
  On pass → `outcome="ok"` as a **gate only** — no `propose_command`,
  ArmedAllowlist, sim, or imports of `jarvis.core` /
  `jarvis.flight_software` / `jarvis.vehicle_profiles`. Chat fulfill
  stays in `core/orchestrator.py` (`_handle_vehicle_hold`).

Other vehicle/ops Skills stay `stub` → `skill_stub` reject.

**Chat Skill-first:** T22 wires explain/status fulfill through
`run_skill`. T23 gates chat HOLD the same way, then orch fulfills.
Classify (`try_*_task`) still chooses the Skill/Task id — Skill-first
means fulfill-through-`run_skill`, not deleting Tasks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from pydantic import BaseModel, ConfigDict

from jarvis.capabilities.registry import CapabilityRegistry
from jarvis.capabilities.safety import SafetyRequest, SoftwareCapabilitySafetyGate
from jarvis.capabilities.schemas import CapabilityAvailability, ProviderKind, SkillRecord

SKILL_ID_EXPLAIN_CONCEPT = "skill.explain_concept"
SKILL_ID_PROJECT_STATUS = "skill.project_status"
SKILL_ID_REQUEST_HOLD = "skill.request_hold"


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
    """T23 HOLD gate: membership + provider kind==vehicle. Never software
    Safety, never propose_command/sim."""
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


def run_skill(
    skill_id: str,
    *,
    query: str | None = None,
    project_status_provider: Callable[[], dict] | None = None,
    ontology_root: Path | None = None,
) -> SkillRunResult:
    """Look `skill_id` up in `CapabilityRegistry.load_default()`, require
    `availability == AVAILABLE`, then dispatch:

    * software Skills → T4-shaped software Safety + existing fulfill;
    * `skill.request_hold` → vehicle membership/provider gate (T23);
    * other vehicle/ops still `stub` → `skill_stub`.

    Finite `reason`s: `unknown_skill` / `skill_stub` / `safety_reject` /
    `capability_unknown` / `provider_not_vehicle` / `missing_query` /
    `no_project` / `no_dispatcher`.

    T22: chat Skill-first may pass `ontology_root` through to
    `fulfill_ontology_explain` (tests / alternate vault roots).
    """
    registry = CapabilityRegistry.load_default()
    skill = next((s for s in registry.skills() if s.id == skill_id), None)
    if skill is None:
        return SkillRunResult(skill_id=skill_id, outcome="reject", reason="unknown_skill")

    if skill.availability != CapabilityAvailability.AVAILABLE:
        return SkillRunResult(skill_id=skill_id, outcome="reject", reason="skill_stub")

    # T23: vehicle HOLD must not route through SoftwareCapabilitySafetyGate.
    if skill_id == SKILL_ID_REQUEST_HOLD:
        return _vehicle_skill_gate(registry, skill)

    if not _software_safety_allows_skill(skill.required_capability_ids):
        return SkillRunResult(skill_id=skill_id, outcome="reject", reason="safety_reject")

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
