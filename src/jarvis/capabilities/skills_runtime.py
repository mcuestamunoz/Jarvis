"""`B1-capability-skills-runtime-software` (T21) — first Skill **runner**,
software Skills only. T5 (`B1-capability-skills-seed`) gave
`CapabilityRegistry.load_default()` its first Skill rows, all declared
`stub` — still no execution path anywhere. This module adds exactly one:
`run_skill(skill_id, ...)`, a thin dispatcher that looks a Skill up,
checks it is `available`, re-runs the same T4-shaped software Safety
check `jarvis.intelligence.assistant_task` already uses before emitting
a software Task, then calls the *existing* fulfill path for that one
Skill — never a second, competing implementation of any of it.

**Only** `skill.explain_concept` / `skill.project_status` are marked
`available` this Buy (`default_registry.json`). Every vehicle/ops Skill
(`skill.request_hold`, …, `skill.request_patrol`, `skill.request_charge`)
stays `stub` and `run_skill` rejects it with reason `"skill_stub"` —
this module never calls `propose_command`/`AutonomyVerb`/any sim or
flight path, and never imports `jarvis.flight_software`/
`jarvis.vehicle_profiles`.

**Chat Task classify is unchanged.** `jarvis.intelligence.assistant_task`
still never looks a Skill up before emitting a Task (T0's own original
lock, still true). `run_skill` is an **additional**, separately-callable
API — nothing in this Buy wires chat to call it. That Skill-first wiring
is explicitly the next block after this one (DC §0 row 3 / IC "Not").

**`skill.explain_concept`** reuses `jarvis.intelligence.assistant_task.
fulfill_ontology_explain` byte-for-byte — no second cite path.

**`skill.project_status`** needs a live `ProjectState` to report
anything — and this module, living in `jarvis.capabilities`, never
imports `jarvis.core` (same one-directional layering `registry.py`/
`safety.py` already hold: capabilities never imports core/intelligence
upward except the one explicit exception above, which the DC itself
names). So `run_skill` never reaches into the orchestrator itself;
instead, a caller that already has the real Continuity status callable
(e.g. an orchestrator's own `build_startup_context`, unmodified — the
**read-only** builder, not `_handle_project_status`, which has a
session-mutating side effect for `proactive_question`) may pass it in
via `project_status_provider`. With no provider supplied —
the default, and the only path this Buy's own tests exercise directly —
`run_skill` honestly rejects with reason `"no_project"` rather than
duplicating any Continuity ranking logic itself (DC §0 row 2: "No new
Continuity ranking logic").
"""

from __future__ import annotations

from typing import Callable

from pydantic import BaseModel, ConfigDict

from jarvis.capabilities.registry import CapabilityRegistry
from jarvis.capabilities.safety import SafetyRequest, SoftwareCapabilitySafetyGate
from jarvis.capabilities.schemas import CapabilityAvailability

SKILL_ID_EXPLAIN_CONCEPT = "skill.explain_concept"
SKILL_ID_PROJECT_STATUS = "skill.project_status"


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


def run_skill(
    skill_id: str,
    *,
    query: str | None = None,
    project_status_provider: Callable[[], dict] | None = None,
) -> SkillRunResult:
    """Look `skill_id` up in `CapabilityRegistry.load_default()`, require
    `availability == AVAILABLE` (vehicle/ops Skills are `stub` → reject),
    re-check required capability ids through the same T4-shaped software
    Safety gate, then dispatch to the one existing fulfill path this
    Skill reuses. Finite `reason`s: `unknown_skill` / `skill_stub` /
    `safety_reject` / `missing_query` / `no_project` / `no_dispatcher`."""
    registry = CapabilityRegistry.load_default()
    skill = next((s for s in registry.skills() if s.id == skill_id), None)
    if skill is None:
        return SkillRunResult(skill_id=skill_id, outcome="reject", reason="unknown_skill")

    if skill.availability != CapabilityAvailability.AVAILABLE:
        return SkillRunResult(skill_id=skill_id, outcome="reject", reason="skill_stub")

    if not _software_safety_allows_skill(skill.required_capability_ids):
        return SkillRunResult(skill_id=skill_id, outcome="reject", reason="safety_reject")

    if skill_id == SKILL_ID_EXPLAIN_CONCEPT:
        if query is None:
            return SkillRunResult(skill_id=skill_id, outcome="reject", reason="missing_query")
        from jarvis.intelligence.assistant_task import fulfill_ontology_explain

        message = fulfill_ontology_explain(query)
        return SkillRunResult(skill_id=skill_id, outcome="ok", message=message)

    if skill_id == SKILL_ID_PROJECT_STATUS:
        if project_status_provider is None:
            return SkillRunResult(skill_id=skill_id, outcome="reject", reason="no_project")
        ctx = project_status_provider()
        if ctx.get("has_project") is False:
            return SkillRunResult(skill_id=skill_id, outcome="reject", reason="no_project")
        return SkillRunResult(skill_id=skill_id, outcome="ok", message=str(ctx))

    # Only reachable if default_registry.json ever marks a third Skill
    # `available` without this module growing a matching dispatch arm —
    # a config/code mismatch, not a normal runtime outcome.
    return SkillRunResult(skill_id=skill_id, outcome="reject", reason="no_dispatcher")
