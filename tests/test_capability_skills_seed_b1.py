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


def test_t1_load_default_has_the_two_stub_skills():
    """T6 (`B1-assistant-vehicle-hold-task`) later adds a third stub
    skill, `skill.request_hold` (see
    `tests/test_assistant_vehicle_hold_task_b1.py`). This test no longer
    claims T5's two are the *only* skills, only that they remain present
    and still `stub` (membership, not exact-set equality)."""
    registry = CapabilityRegistry.load_default()
    skill_ids = {s.id for s in registry.skills()}
    t5_skill_ids = {"skill.explain_concept", "skill.project_status"}
    assert t5_skill_ids <= skill_ids
    for skill in registry.skills():
        if skill.id in t5_skill_ids:
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
    """True as stated within T5's own scope (T5 touched only `skills`).
    T6 (`B1-assistant-vehicle-hold-task`) later adds a third capability/
    provider (`flight.hold`/`provider.flight_hold`, vehicle) — see
    `tests/test_assistant_vehicle_hold_task_b1.py`. This test now checks
    T2's own two remain present and correctly shaped, not that they are
    the only ones (membership, not exact-set equality)."""
    registry = CapabilityRegistry.load_default()

    capability_ids = {c.id for c in registry.capabilities()}
    software_capability_ids = {"ontology.explain", "engineering.continuity"}
    assert software_capability_ids <= capability_ids
    for capability in registry.capabilities():
        if capability.id in software_capability_ids:
            assert capability.availability == CapabilityAvailability.AVAILABLE

    provider_ids = {p.id for p in registry.providers()}
    software_provider_ids = {"provider.ontology_explain", "provider.engineering_continuity"}
    assert software_provider_ids <= provider_ids
    for provider in registry.providers():
        if provider.id in software_provider_ids:
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
    assert 'version = "0.6.15"' in text


def test_seed_file_skills_shape_matches_ic_normative_seed():
    """Direct check against the checked-in JSON, independent of
    `load_default()`'s own parsing — proves the file on disk matches
    IC §1 verbatim, not just what the loader happens to produce.

    T6 (`B1-assistant-vehicle-hold-task`) later appends a third skill,
    `skill.request_hold` (see `tests/test_assistant_vehicle_hold_task_b1.py`
    for that row's own shape check) — this test now checks T5's own two
    rows are present with the exact shape IC §1 locked, not that they
    are the only rows in the file (membership, not full-list equality)."""
    data = json.loads(SEED_PATH.read_text())
    assert {
        "id": "skill.explain_concept",
        "version": "0.6.13",
        "required_capability_ids": ["ontology.explain"],
        "availability": "stub",
    } in data["skills"]
    assert {
        "id": "skill.project_status",
        "version": "0.6.13",
        "required_capability_ids": ["engineering.continuity"],
        "availability": "stub",
    } in data["skills"]
