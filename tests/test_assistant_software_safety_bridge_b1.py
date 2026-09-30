"""Tests T1-T7 for `B1-assistant-software-safety-bridge` (T4).

Exercises `SoftwareCapabilitySafetyGate` (`jarvis.capabilities.safety`)
and its wiring into both `jarvis.intelligence.assistant_task.
try_explain_concept_task`/`try_defer_to_continuity_task`, *after* T3's
registry-membership soft-check and *before* `intent.metadata["task_kind"]`
is written. `allow` iff every capability id encoded on the request's
`action_id` (`"capability:<id>[,<id>...]"`) is a known, `available` row
in `CapabilityRegistry.load_default()` bound to a `software`-kind
provider; otherwise `reject` with one of a finite set of reason strings.
`default_safety_gate()` stays `RejectAllSafetyGate`; `ArmedAllowlistSafetyGate`
is untouched by this Buy.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from jarvis.capabilities.intent import Task, TerminalIntentAdapter
from jarvis.capabilities.registry import CapabilityRegistry
from jarvis.capabilities.safety import (
    ArmedAllowlistSafetyGate,
    RejectAllSafetyGate,
    SafetyRequest,
    SoftwareCapabilitySafetyGate,
    default_safety_gate,
)
from jarvis.capabilities.schemas import (
    CapabilityAvailability,
    CapabilityRecord,
    ProviderKind,
    ProviderRecord,
)
from jarvis.intelligence.assistant_task import (
    CAPABILITY_ENGINEERING_CONTINUITY,
    CAPABILITY_ONTOLOGY_EXPLAIN,
    TASK_KIND_DEFER_TO_CONTINUITY,
    TASK_KIND_EXPLAIN_CONCEPT,
    try_defer_to_continuity_task,
    try_explain_concept_task,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSISTANT_TASK_PATH = REPO_ROOT / "src" / "jarvis" / "intelligence" / "assistant_task.py"
SAFETY_PATH = REPO_ROOT / "src" / "jarvis" / "capabilities" / "safety.py"


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


def _intent(raw_text: str):
    return TerminalIntentAdapter.parse(raw_text)


def _registry(availability: CapabilityAvailability, provider_kind: ProviderKind) -> CapabilityRegistry:
    return CapabilityRegistry(
        capabilities=[
            CapabilityRecord(
                id="ontology.explain",
                version="0.0",
                provider_id="p1",
                availability=availability,
            )
        ],
        providers=[
            ProviderRecord(id="p1", kind=provider_kind, offered_capability_ids=["ontology.explain"])
        ],
    )


def test_t1_happy_path_unchanged_with_default_seed():
    intent = _intent("explain c-rate")
    task = try_explain_concept_task(intent)
    assert isinstance(task, Task)
    assert task.required_capability_ids == [CAPABILITY_ONTOLOGY_EXPLAIN]
    assert intent.metadata.get("task_kind") == TASK_KIND_EXPLAIN_CONCEPT

    intent2 = _intent("estado")
    task2 = try_defer_to_continuity_task(intent2)
    assert isinstance(task2, Task)
    assert task2.required_capability_ids == [CAPABILITY_ENGINEERING_CONTINUITY]
    assert intent2.metadata.get("task_kind") == TASK_KIND_DEFER_TO_CONTINUITY


def test_t2_gate_alone_allows_known_available_software_capability():
    gate = SoftwareCapabilitySafetyGate()
    decision = gate.evaluate(SafetyRequest(action_id="capability:ontology.explain"))
    assert decision.outcome == "allow"
    assert decision.gate_id == "software_capability"

    multi = gate.evaluate(
        SafetyRequest(action_id="capability:ontology.explain,engineering.continuity")
    )
    assert multi.outcome == "allow"


def test_t3_gate_alone_rejects_unknown_or_non_software(monkeypatch):
    gate = SoftwareCapabilitySafetyGate()

    unknown = gate.evaluate(SafetyRequest(action_id="capability:no.such.capability"))
    assert unknown.outcome == "reject"
    assert unknown.reason == "capability_unknown"

    monkeypatch.setattr(
        CapabilityRegistry,
        "load_default",
        classmethod(lambda cls: _registry(CapabilityAvailability.STUB, ProviderKind.SOFTWARE)),
    )
    stub = gate.evaluate(SafetyRequest(action_id="capability:ontology.explain"))
    assert stub.outcome == "reject"
    assert stub.reason == "capability_unavailable"

    monkeypatch.setattr(
        CapabilityRegistry,
        "load_default",
        classmethod(lambda cls: _registry(CapabilityAvailability.AVAILABLE, ProviderKind.VEHICLE)),
    )
    non_software = gate.evaluate(SafetyRequest(action_id="capability:ontology.explain"))
    assert non_software.outcome == "reject"
    assert non_software.reason == "provider_not_software"

    empty = gate.evaluate(SafetyRequest(action_id="capability:"))
    assert empty.outcome == "reject"
    assert empty.reason == "empty_capabilities"

    unparseable = gate.evaluate(SafetyRequest(action_id="autonomy:HOLD:1"))
    assert unparseable.outcome == "reject"
    assert unparseable.reason == "unparseable_action_id"

    unparseable_none = gate.evaluate(SafetyRequest(action_id=None))
    assert unparseable_none.outcome == "reject"
    assert unparseable_none.reason == "unparseable_action_id"


def test_t4_empty_registry_refuses_both_task_kinds_no_task_kind_written(monkeypatch):
    monkeypatch.setattr(
        CapabilityRegistry, "load_default", classmethod(lambda cls: CapabilityRegistry())
    )

    intent = _intent("explain c-rate")
    assert try_explain_concept_task(intent) is None
    assert "task_kind" not in intent.metadata
    assert "explain_query" not in intent.metadata

    intent2 = _intent("estado")
    assert try_defer_to_continuity_task(intent2) is None
    assert "task_kind" not in intent2.metadata


def test_t4b_safety_rejects_even_when_t3_membership_passes(monkeypatch):
    """T3 membership alone would pass here (the id exists); T4's own
    availability/provider-kind checks are what refuse it — proves the
    two gates are doing genuinely different work, not just duplicating
    each other."""
    monkeypatch.setattr(
        CapabilityRegistry,
        "load_default",
        classmethod(lambda cls: _registry(CapabilityAvailability.STUB, ProviderKind.SOFTWARE)),
    )
    intent = _intent("explain c-rate")
    assert try_explain_concept_task(intent) is None
    assert "task_kind" not in intent.metadata


def test_t5_default_safety_gate_and_armed_allowlist_untouched():
    gate = default_safety_gate()
    assert isinstance(gate, RejectAllSafetyGate)
    decision = gate.evaluate(SafetyRequest(action_id="capability:ontology.explain"))
    assert decision.outcome == "reject"
    assert decision.reason == "not_implemented"

    armed_gate = ArmedAllowlistSafetyGate()
    assert armed_gate.armed is False
    assert ArmedAllowlistSafetyGate._ALLOWED_VERBS == frozenset({"HOLD", "LAND", "GO_TO"})
    still_rejects = armed_gate.evaluate(SafetyRequest(action_id="autonomy:HOLD:1"))
    assert still_rejects.outcome == "reject"
    assert still_rejects.reason == "disarmed"


def test_t6_fences_hold_ast():
    forbidden = (
        "jarvis.core",
        "jarvis.flight_software",
        "jarvis.vehicle_profiles",
    )
    assistant_imports = _imported_module_names(ASSISTANT_TASK_PATH)
    assert "jarvis.capabilities.safety" in assistant_imports
    for module_name in assistant_imports:
        for forbidden_root in forbidden:
            assert not (
                module_name == forbidden_root or module_name.startswith(forbidden_root + ".")
            ), f"assistant_task.py imports forbidden module '{module_name}'"

    safety_imports = _imported_module_names(SAFETY_PATH)
    assert not any(
        m == "jarvis.intelligence" or m.startswith("jarvis.intelligence.")
        for m in safety_imports
    ), "safety.py imports jarvis.intelligence"


def test_t7_pyproject_version_is_0_6_12():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.6.14"' in text
