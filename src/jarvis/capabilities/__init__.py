"""Fase C · C1 scaffold — typed Skill/Capability/Provider schemas and an
empty-by-default Capability Registry. Descriptive only: no execution path.
Scaffold @ 0.5.0 != Flight Software shipped. See
`.jes/artifacts/implementation_contract_fase_c_capability_registry_scaffold_b1.md`.
"""

from jarvis.capabilities.registry import CapabilityRegistry, CapabilityRegistryError
from jarvis.capabilities.schemas import (
    CapabilityAvailability,
    CapabilityHealth,
    CapabilityRecord,
    ProviderKind,
    ProviderRecord,
    SkillRecord,
)

__all__ = [
    "CapabilityAvailability",
    "CapabilityHealth",
    "CapabilityRecord",
    "CapabilityRegistry",
    "CapabilityRegistryError",
    "ProviderKind",
    "ProviderRecord",
    "SkillRecord",
]
