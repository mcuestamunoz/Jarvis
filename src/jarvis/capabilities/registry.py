"""Fase C · C1 — Capability Registry stub (`B1-fase-c-capability-registry-scaffold`),
extended by T2 (`B1-capability-registry-product-fill`), T3
(`B1-assistant-task-registry-coherence`), and T5
(`B1-capability-skills-seed`).

Pure in-memory (or checked-in-JSON-seeded) catalog with a query-only API:
list / get-by-id / "who offers capability X?". No network discovery, no
process supervisor, no health probes against hardware, and — critically —
no method that turns a Capability/Provider/Skill record into an actuator
command. `load_default()` is the only product-facing constructor; C1 had
it always empty (see H1–H5 in that Implementation Contract and the report
at `.jes/artifacts/implementation_report_fase_c_capability_registry_scaffold_b1.md`).

**T2** fills the checked-in seed (`data/default_registry.json`) with the
first honest, non-empty product rows: the two capability strings
Assistant Tasks already require (`ontology.explain`,
`engineering.continuity`, both `available`) plus one `software` provider
each. No dispatcher/execute/actuate method was added anywhere in this
class. See `.jes/artifacts/implementation_report_capability_registry_product_fill_b1.md`.

**T3** adds the one edge T2 had deliberately deferred: `assistant_task.py`
now imports this module and soft-checks (`get_capability(id) is not
None`, membership only) every capability id a Task would require, before
emitting it. `registry.py` itself still never imports `jarvis.intelligence`
— the edge is one-way. See `.jes/artifacts/implementation_report_assistant_task_registry_coherence_b1.md`.

**T5** fills the checked-in seed's `skills` array too — two declared-only
`SkillRecord` rows (`skill.explain_concept`/`skill.project_status`, both
`availability=stub`), each referencing the same capability ids T0/T1's
Assistant Task classify already requires. Still zero Skill execution
path: no `run_skill`, and the Assistant does not look these rows up
before emitting a Task — the finite Task-kind classify in
`assistant_task.py` stays authoritative on its own, unaffected by this
seed's shape. See `.jes/artifacts/implementation_report_capability_skills_seed_b1.md`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from jarvis.capabilities.schemas import CapabilityRecord, ProviderRecord, SkillRecord

_DEFAULT_SEED_PATH = Path(__file__).parent / "data" / "default_registry.json"


class CapabilityRegistryError(ValueError):
    """Raised when a registry would load with duplicate ids or a dangling
    capability-id reference (provider/skill referencing an unknown
    capability). Reject-on-load, per IC §1.4 — never a silent drop."""


class CapabilityRegistry:
    def __init__(
        self,
        capabilities: Iterable[CapabilityRecord] | None = None,
        providers: Iterable[ProviderRecord] | None = None,
        skills: Iterable[SkillRecord] | None = None,
    ) -> None:
        capability_list = list(capabilities or [])
        provider_list = list(providers or [])
        skill_list = list(skills or [])

        _reject_duplicate_ids(capability_list, "capability")
        _reject_duplicate_ids(provider_list, "provider")
        _reject_duplicate_ids(skill_list, "skill")

        capability_ids = {record.id for record in capability_list}
        for provider in provider_list:
            for capability_id in provider.offered_capability_ids:
                if capability_id not in capability_ids:
                    raise CapabilityRegistryError(
                        f"provider '{provider.id}' offers unknown capability id "
                        f"'{capability_id}'"
                    )
        for skill in skill_list:
            for capability_id in skill.required_capability_ids:
                if capability_id not in capability_ids:
                    raise CapabilityRegistryError(
                        f"skill '{skill.id}' requires unknown capability id "
                        f"'{capability_id}'"
                    )

        self._capabilities = capability_list
        self._providers = provider_list
        self._skills = skill_list
        self._capabilities_by_id = {record.id: record for record in capability_list}
        self._providers_by_id = {record.id: record for record in provider_list}

    def capabilities(self) -> list[CapabilityRecord]:
        return list(self._capabilities)

    def providers(self) -> list[ProviderRecord]:
        return list(self._providers)

    def skills(self) -> list[SkillRecord]:
        return list(self._skills)

    def get_capability(self, capability_id: str) -> CapabilityRecord | None:
        return self._capabilities_by_id.get(capability_id)

    def get_provider(self, provider_id: str) -> ProviderRecord | None:
        return self._providers_by_id.get(provider_id)

    def providers_offering(self, capability_id: str) -> list[ProviderRecord]:
        return [
            provider
            for provider in self._providers
            if capability_id in provider.offered_capability_ids
        ]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CapabilityRegistry":
        return cls(
            capabilities=[
                CapabilityRecord.model_validate(item)
                for item in data.get("capabilities", [])
            ],
            providers=[
                ProviderRecord.model_validate(item) for item in data.get("providers", [])
            ],
            skills=[SkillRecord.model_validate(item) for item in data.get("skills", [])],
        )

    @classmethod
    def load_default(cls) -> "CapabilityRegistry":
        """Product default. Reads the checked-in seed at
        `data/default_registry.json` rather than hardcoding the shape
        twice. As of T2 (`B1-capability-registry-product-fill`), that
        seed is no longer empty — it declares the two software-fulfilled
        capabilities Assistant Tasks already require
        (`ontology.explain`, `engineering.continuity`), both `available`
        via a `software` provider each, zero skills. The seed still
        never contains a flight-related capability or a
        `vehicle`/`device` provider claiming live actuation (T2 IC §0
        row 9) — this stays inert descriptive data, read here, never
        dispatched from here."""
        data = json.loads(_DEFAULT_SEED_PATH.read_text())
        return cls.from_dict(data)


def _reject_duplicate_ids(records: list[Any], label: str) -> None:
    seen: set[str] = set()
    for record in records:
        if record.id in seen:
            raise CapabilityRegistryError(f"duplicate {label} id '{record.id}'")
        seen.add(record.id)
