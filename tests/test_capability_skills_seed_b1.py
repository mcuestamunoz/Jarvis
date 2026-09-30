"""Tests T1-T6 for `B1-capability-skills-seed` (T5).

Fills C1's checked-in `data/default_registry.json` `skills` array —
still empty at T2/T3/T4 time — with the first two honest, non-empty
Skill rows: `skill.explain_concept` (requires `ontology.explain`) and
`skill.project_status` (requires `engineering.continuity`), both
`availability=stub` (declared catalog rows only, no Skill execution
path anywhere in this package). Capabilities/providers rows, the
Assistant Task classify seam, both Safety gates, the orchestrator, and
Continuity ranking are all untouched by this Buy.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from jarvis.capabilities import CapabilityAvailability, CapabilityRegistry, ProviderKind
from jarvis.capabilities.registry import CapabilityRegistryError
from jarvis.capabilities.schemas import CapabilityRecord, SkillRecord

REPO_ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = (
    REPO_ROOT / "src" / "jarvis" / "capabilities" / "data" / "default_registry.json"
)


def test_t1_load_default_has_exactly_the_two_stub_skills():
    registry = CapabilityRegistry.load_default()
    skill_ids = {s.id for s in registry.skills()}
    assert skill_ids == {"skill.explain_concept", "skill.project_status"}
    for skill in registry.skills():
        assert skill.availability == CapabilityAvailability.STUB


def test_t2_each_skills_required_capability_resolves():
    registry = CapabilityRegistry.load_default()
    by_id = {s.id: s for s in registry.skills()}

    explain_skill = by_id["skill.explain_concept"]
    assert explain_skill.required_capability_ids == ["ontology.explain"]
    assert registry.get_capability("ontology.explain") is not None

    status_skill = by_id["skill.project_status"]
    assert status_skill.required_capability_ids == ["engineering.continuity"]
    assert registry.get_capability("engineering.continuity") is not None


def test_t3_capabilities_and_providers_unchanged_vs_t2_seed():
    registry = CapabilityRegistry.load_default()

    capability_ids = {c.id for c in registry.capabilities()}
    assert capability_ids == {"ontology.explain", "engineering.continuity"}
    for capability in registry.capabilities():
        assert capability.availability == CapabilityAvailability.AVAILABLE

    provider_ids = {p.id for p in registry.providers()}
    assert provider_ids == {"provider.ontology_explain", "provider.engineering_continuity"}
    for provider in registry.providers():
        assert provider.kind == ProviderKind.SOFTWARE


def test_t4_skill_requiring_unknown_capability_still_rejected_on_load():
    known_capability = CapabilityRecord(
        id="ontology.explain", version="0.1", availability=CapabilityAvailability.AVAILABLE
    )
    dangling_skill = SkillRecord(
        id="skill.bogus",
        version="0.1",
        required_capability_ids=["no.such.capability"],
        availability=CapabilityAvailability.STUB,
    )
    with pytest.raises(CapabilityRegistryError):
        CapabilityRegistry(capabilities=[known_capability], skills=[dangling_skill])


def test_t5_no_execute_dispatch_or_run_skill_public_method():
    forbidden_substrings = ("execute", "dispatch", "command_esc", "actuat", "run_skill")
    public_members = [name for name in dir(CapabilityRegistry) if not name.startswith("_")]
    for name in public_members:
        lowered = name.lower()
        for token in forbidden_substrings:
            assert token not in lowered, (
                f"CapabilityRegistry.{name} looks like an execution path "
                f"(matched '{token}') — registry must stay descriptive-only"
            )


def test_t6_pyproject_version_is_0_6_13():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.6.13"' in text


def test_seed_file_skills_shape_matches_ic_normative_seed():
    """Direct check against the checked-in JSON, independent of
    `load_default()`'s own parsing — proves the file on disk matches
    IC §1 verbatim, not just what the loader happens to produce."""
    data = json.loads(SEED_PATH.read_text())
    assert data["skills"] == [
        {
            "id": "skill.explain_concept",
            "version": "0.6.13",
            "required_capability_ids": ["ontology.explain"],
            "availability": "stub",
        },
        {
            "id": "skill.project_status",
            "version": "0.6.13",
            "required_capability_ids": ["engineering.continuity"],
            "availability": "stub",
        },
    ]
