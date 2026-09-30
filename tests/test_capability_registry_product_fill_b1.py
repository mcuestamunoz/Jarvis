"""Tests T1-T7 for `B1-capability-registry-product-fill` (T2).

The first honest, non-empty product seed in C1's `CapabilityRegistry.
load_default()`: the two capability strings Assistant Tasks (T0/T1)
already require, `ontology.explain`/`engineering.continuity`, both
`available` via one `software` provider each. Registry stays purely
descriptive — no dispatcher, no flight/vehicle/device row, and
`jarvis.intelligence.assistant_task` is not touched by this Buy.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from jarvis.capabilities import (
    CapabilityAvailability,
    CapabilityRegistry,
    ProviderKind,
)
from jarvis.intelligence.assistant_task import (
    CAPABILITY_ENGINEERING_CONTINUITY,
    CAPABILITY_ONTOLOGY_EXPLAIN,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = (
    REPO_ROOT / "src" / "jarvis" / "capabilities" / "data" / "default_registry.json"
)


def _imported_module_names(source_path: Path) -> set[str]:
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_t1_load_default_has_exactly_two_available_capabilities_no_skills():
    registry = CapabilityRegistry.load_default()
    capability_ids = {c.id for c in registry.capabilities()}
    assert capability_ids == {"ontology.explain", "engineering.continuity"}
    for capability in registry.capabilities():
        assert capability.availability == CapabilityAvailability.AVAILABLE
    assert registry.skills() == []


def test_t2_both_software_providers_exist_and_offer_the_right_capability():
    registry = CapabilityRegistry.load_default()
    provider_ids = {p.id for p in registry.providers()}
    assert provider_ids == {"provider.ontology_explain", "provider.engineering_continuity"}
    for provider in registry.providers():
        assert provider.kind == ProviderKind.SOFTWARE

    explain_providers = registry.providers_offering("ontology.explain")
    assert [p.id for p in explain_providers] == ["provider.ontology_explain"]

    continuity_providers = registry.providers_offering("engineering.continuity")
    assert [p.id for p in continuity_providers] == ["provider.engineering_continuity"]


def test_t3_capability_ids_match_assistant_task_constants():
    registry = CapabilityRegistry.load_default()
    capability_ids = {c.id for c in registry.capabilities()}
    assert CAPABILITY_ONTOLOGY_EXPLAIN in capability_ids
    assert CAPABILITY_ENGINEERING_CONTINUITY in capability_ids
    assert CAPABILITY_ONTOLOGY_EXPLAIN == "ontology.explain"
    assert CAPABILITY_ENGINEERING_CONTINUITY == "engineering.continuity"


def test_t4_seed_has_no_flight_vehicle_or_device_rows():
    data = json.loads(SEED_PATH.read_text())

    for capability in data["capabilities"]:
        capability_id = capability["id"].casefold()
        assert not capability_id.startswith("flight")
        assert "hold" not in capability_id
        assert "land" not in capability_id
        assert "go_to" not in capability_id

    for provider in data["providers"]:
        assert provider["kind"] not in {"vehicle", "device"}


def test_t5_enums_extended_ready_still_rejected():
    assert {member.value for member in CapabilityAvailability} == {
        "stub",
        "not_implemented",
        "available",
    }
    assert {member.value for member in ProviderKind} == {"vehicle", "device", "software"}

    from jarvis.capabilities.schemas import CapabilityRecord

    with pytest.raises(ValidationError):
        CapabilityRecord(id="x", version="0.1.0", availability="ready")


def test_t6_no_dispatcher_method_added():
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


def test_t6b_assistant_task_and_orchestrator_untouched_by_this_buy():
    """T2 IC §0 row 8: zero changes to assistant_task.py, orchestrator
    Task wire, Continuity ranking, explain cite. Verified here as an
    import-graph sanity check: the registry module itself must not
    import assistant_task (no reverse coupling), and assistant_task
    must not import the capability registry (T0/T1's own Task-string
    classify stays authoritative — T2 IC §0 row 7: no registry lookup
    before emit)."""
    registry_path = REPO_ROOT / "src" / "jarvis" / "capabilities" / "registry.py"
    assistant_task_path = (
        REPO_ROOT / "src" / "jarvis" / "intelligence" / "assistant_task.py"
    )

    registry_imports = _imported_module_names(registry_path)
    assert not any(
        m == "jarvis.intelligence" or m.startswith("jarvis.intelligence.")
        for m in registry_imports
    )

    assistant_task_imports = _imported_module_names(assistant_task_path)
    assert not any(
        m == "jarvis.capabilities.registry" or m == "jarvis.capabilities"
        for m in assistant_task_imports
    )


def test_t7_pyproject_version_is_0_6_10():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.6.10"' in text
