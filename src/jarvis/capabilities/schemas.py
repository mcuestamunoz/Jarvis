"""Fase C · C1 — Skill/Capability/Provider schemas
(`B1-fase-c-capability-registry-scaffold`), extended by T2
(`B1-capability-registry-product-fill`).

These are typed DATA records, not a runtime: nothing here executes,
dispatches, or actuates anything. C1 restricted `availability` to
`stub`/`not_implemented` — no record could claim anything was live. T2
adds `CapabilityAvailability.AVAILABLE`, but **only** for non-actuation,
already-shipped software fulfill paths (the two Assistant Task
capabilities, `ontology.explain`/`engineering.continuity` — see
`jarvis.capabilities.data.default_registry.json`): `ready`/`healthy`
were deliberately **not** added, and no flight/vehicle/radio capability
may be marked `available` in the product seed (T2 IC §0 row 9). T2 also
adds `ProviderKind.SOFTWARE` for in-process product providers that are
neither `vehicle` nor `device`. See
`jarvis.capabilities.registry.CapabilityRegistry.load_default`, which is
the only product-facing entrypoint — no longer always empty as of T2,
but still purely descriptive (no dispatcher method exists anywhere in
this package).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class CapabilityAvailability(str, Enum):
    STUB = "stub"
    NOT_IMPLEMENTED = "not_implemented"
    AVAILABLE = "available"


class CapabilityHealth(str, Enum):
    UNKNOWN = "unknown"


class ProviderKind(str, Enum):
    VEHICLE = "vehicle"
    DEVICE = "device"
    SOFTWARE = "software"


class CapabilityRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    version: str
    provider_id: str | None = None
    availability: CapabilityAvailability
    requirements: list[str] = Field(default_factory=list)
    health: CapabilityHealth = CapabilityHealth.UNKNOWN


class ProviderRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: ProviderKind
    offered_capability_ids: list[str] = Field(default_factory=list)
    health: CapabilityHealth = CapabilityHealth.UNKNOWN


class SkillRecord(BaseModel):
    """Schema-only in C1 — the registry shipped it without any instances
    by default. T5 (`B1-capability-skills-seed`) gave `CapabilityRegistry.
    load_default()` its first two instances, `skill.explain_concept`/
    `skill.project_status`, both `availability=stub` (declared catalog
    rows only — still no Skill execution path anywhere in this package;
    the Assistant Task seam in `jarvis.intelligence.assistant_task` never
    looks these up before emitting a Task)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    version: str
    required_capability_ids: list[str] = Field(default_factory=list)
    availability: CapabilityAvailability
