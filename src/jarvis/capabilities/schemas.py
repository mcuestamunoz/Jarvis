"""Fase C · C1 — Skill/Capability/Provider schemas (`B1-fase-c-capability-registry-scaffold`).

These are typed DATA records, not a runtime: nothing here executes,
dispatches, or actuates anything. `availability` is deliberately
restricted to `stub`/`not_implemented` in C1 — no `available`/`ready`
value exists yet, so no record built against this schema can claim a
capability (flight-related or otherwise) is live. See
`jarvis.capabilities.registry.CapabilityRegistry.load_default`, which is
the only product-facing entrypoint and always returns empty.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class CapabilityAvailability(str, Enum):
    STUB = "stub"
    NOT_IMPLEMENTED = "not_implemented"


class CapabilityHealth(str, Enum):
    UNKNOWN = "unknown"


class ProviderKind(str, Enum):
    VEHICLE = "vehicle"
    DEVICE = "device"


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
    """Optional in C1 — the registry ships this schema without any
    instances of it by default (see `CapabilityRegistry.load_default`)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    version: str
    required_capability_ids: list[str] = Field(default_factory=list)
    availability: CapabilityAvailability
