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


def test_t1_load_default_returns_product_seed():
    """C1 shipped this always-empty (H1). T2 (`B1-capability-registry-
    product-fill`) gave the checked-in seed its first honest, non-empty
    capabilities()/providers() rows — full assertions on that shape live
    in `tests/test_capability_registry_product_fill_b1.py`. T5
    (`B1-capability-skills-seed`) later did the same for `skills()` —
    see `tests/test_capability_skills_seed_b1.py`. This test only
    confirms `load_default()` no longer returns the C1-era all-empty
    registry, so this file's own history stays accurate."""
    registry = CapabilityRegistry.load_default()
    assert registry.capabilities() != []
    assert registry.providers() != []
    assert registry.skills() != []


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


def test_t8_availability_enum_accepts_available_still_rejects_ready():
    """C1 rejected `available` outright (T8's original name/assert). T2
    (`B1-capability-registry-product-fill`) adds `AVAILABLE` for
    non-actuation, already-shipped software fulfill paths — `ready`/
    `healthy` were deliberately not added, and stay rejected."""
    _capability(availability="available")  # no longer raises
    with pytest.raises(ValidationError):
        _capability(availability="ready")
    assert {member.value for member in CapabilityAvailability} == {
        "stub",
        "not_implemented",
        "available",
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


def test_t10_pyproject_version_is_0_6_10():
    """Bumped forward by T2 (B1-capability-registry-product-fill) per
    established pattern — was last accurate at 0.5.44 (C1's own tip),
    itself already long stale before this Buy touched the file."""
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.6.23"' in text


def test_default_seed_file_is_honestly_software_only():
    """H1/H2/H3, updated by T2: the checked-in seed loaded by
    `load_default()` is no longer empty (see `test_capability_registry_
    product_fill_b1.py` for the full shape), but T2's own two rows still
    never contain a flight-related capability id or a `vehicle`/`device`
    provider claiming live actuation.

    T6 (`B1-assistant-vehicle-hold-task`) is the later, separately-
    authorized Buy that deliberately adds the first such row —
    `flight.hold` (capability, `not_implemented`) / `provider.flight_hold`
    (provider, `vehicle`) — this test no longer claims the *whole* seed
    is software-only forever; that row's own honesty invariant (never
    `available`, never `software`) is tested in
    `tests/test_assistant_vehicle_hold_task_b1.py`, not here."""
    import json

    seed_path = REPO_ROOT / "src" / "jarvis" / "capabilities" / "data" / "default_registry.json"
    data = json.loads(seed_path.read_text())
    t2_capability_ids = {"ontology.explain", "engineering.continuity"}
    t2_provider_ids = {"provider.ontology_explain", "provider.engineering_continuity"}

    for capability in data["capabilities"]:
        if capability["id"] not in t2_capability_ids:
            continue
        capability_id = capability["id"].casefold()
        assert not capability_id.startswith("flight")
        assert "hold" not in capability_id
        assert "land" not in capability_id
        assert "go_to" not in capability_id

    for provider in data["providers"]:
        if provider["id"] not in t2_provider_ids:
            continue
        assert provider["kind"] not in {"vehicle", "device"}
        assert provider["kind"] == "software"
