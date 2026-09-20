"""Tests T1-T10 for `B1-fase-c-capability-registry-scaffold`.

T11 (full craft suite stays green) and T12 (report content) are not unit
tests — they are process gates covered by running the full suite and by
`.jes/artifacts/implementation_report_fase_c_capability_registry_scaffold_b1.md`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from jarvis.capabilities import (
    CapabilityAvailability,
    CapabilityRecord,
    CapabilityRegistry,
    CapabilityRegistryError,
    ProviderKind,
    ProviderRecord,
    SkillRecord,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _capability(**overrides):
    payload = {
        "id": "engineering_design",
        "version": "0.1.0",
        "availability": CapabilityAvailability.STUB,
    }
    payload.update(overrides)
    return CapabilityRecord(**payload)


def _provider(**overrides):
    payload = {
        "id": "sim_bench",
        "kind": ProviderKind.DEVICE,
        "offered_capability_ids": [],
    }
    payload.update(overrides)
    return ProviderRecord(**payload)


def test_t1_load_default_is_empty():
    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() == []
    assert registry.providers() == []
    assert registry.skills() == []


def test_t2_valid_capability_and_provider_are_accepted():
    capability = _capability()
    provider = _provider(offered_capability_ids=["engineering_design"])
    registry = CapabilityRegistry(capabilities=[capability], providers=[provider])
    assert registry.capabilities() == [capability]
    assert registry.providers() == [provider]


def test_t3_duplicate_capability_id_is_rejected():
    with pytest.raises(CapabilityRegistryError, match="duplicate capability id"):
        CapabilityRegistry(capabilities=[_capability(), _capability()])


def test_t3b_duplicate_provider_and_skill_ids_are_rejected():
    with pytest.raises(CapabilityRegistryError, match="duplicate provider id"):
        CapabilityRegistry(providers=[_provider(), _provider()])
    skill = SkillRecord(
        id="plan_mission",
        version="0.1.0",
        availability=CapabilityAvailability.STUB,
    )
    with pytest.raises(CapabilityRegistryError, match="duplicate skill id"):
        CapabilityRegistry(skills=[skill, skill])


def test_t4_provider_offering_unknown_capability_is_rejected():
    provider = _provider(offered_capability_ids=["does_not_exist"])
    with pytest.raises(CapabilityRegistryError, match="unknown capability id"):
        CapabilityRegistry(providers=[provider])


def test_t4b_skill_requiring_unknown_capability_is_rejected():
    skill = SkillRecord(
        id="plan_mission",
        version="0.1.0",
        required_capability_ids=["does_not_exist"],
        availability=CapabilityAvailability.STUB,
    )
    with pytest.raises(CapabilityRegistryError, match="unknown capability id"):
        CapabilityRegistry(skills=[skill])


def test_t5_provider_kind_rejects_unknown_value():
    with pytest.raises(ValidationError):
        ProviderRecord(id="x", kind="flight_controller", offered_capability_ids=[])


def test_t6_providers_offering_returns_expected_subset():
    capability = _capability()
    offering = _provider(id="offering", offered_capability_ids=["engineering_design"])
    not_offering = _provider(id="not_offering", offered_capability_ids=[])
    registry = CapabilityRegistry(
        capabilities=[capability], providers=[offering, not_offering]
    )
    assert registry.providers_offering("engineering_design") == [offering]
    assert registry.providers_offering("nope") == []


def test_t7_missing_get_returns_none():
    registry = CapabilityRegistry.load_default()
    assert registry.get_capability("nope") is None
    assert registry.get_provider("nope") is None


def test_t8_availability_enum_rejects_available():
    with pytest.raises(ValidationError):
        _capability(availability="available")
    with pytest.raises(ValidationError):
        _capability(availability="ready")
    assert {member.value for member in CapabilityAvailability} == {
        "stub",
        "not_implemented",
    }


def test_t8b_health_enum_only_offers_unknown():
    from jarvis.capabilities import CapabilityHealth

    assert {member.value for member in CapabilityHealth} == {"unknown"}
    with pytest.raises(ValidationError):
        _capability(health="healthy")


def test_t9_no_public_method_executes_or_dispatches():
    forbidden_substrings = ("execute", "dispatch", "command_esc", "actuat", "run_skill")
    public_members = [
        name for name in dir(CapabilityRegistry) if not name.startswith("_")
    ]
    for name in public_members:
        lowered = name.lower()
        for token in forbidden_substrings:
            assert token not in lowered, (
                f"CapabilityRegistry.{name} looks like an execution path "
                f"(matched '{token}') — registry must stay descriptive-only"
            )


def test_t9b_no_execute_or_dispatch_field_on_records():
    forbidden_substrings = ("execute", "dispatch", "command_esc")
    for model in (CapabilityRecord, ProviderRecord, SkillRecord):
        for field_name in model.model_fields:
            lowered = field_name.lower()
            for token in forbidden_substrings:
                assert token not in lowered, f"{model.__name__}.{field_name} looks executable"


def test_t10_pyproject_version_is_0_5_0():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.5.0"' in text


def test_default_seed_file_is_honestly_empty():
    """H1/H2/H3 — the checked-in seed loaded by `load_default()` never
    contains a flight-related or `available`-claiming record."""
    import json

    seed_path = REPO_ROOT / "src" / "jarvis" / "capabilities" / "data" / "default_registry.json"
    data = json.loads(seed_path.read_text())
    assert data == {"capabilities": [], "providers": [], "skills": []}
