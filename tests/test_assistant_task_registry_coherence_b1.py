"""Tests T1-T6 for `B1-assistant-task-registry-coherence` (T3).

Exercises the soft coherence gate added to both
`jarvis.intelligence.assistant_task.try_explain_concept_task` and
`try_defer_to_continuity_task`: before returning a `Task`, every id in
`required_capability_ids` must exist in `CapabilityRegistry.load_default()`
(`get_capability(id) is not None`), membership only — never reads
`availability`, never calls a provider, never dispatches. On an unknown
id the function refuses (`None`), leaving `intent.metadata` untouched
(no `task_kind` written).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from jarvis.capabilities.intent import Task, TerminalIntentAdapter
from jarvis.capabilities.registry import CapabilityRegistry
from jarvis.intelligence import assistant_task
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
REGISTRY_PATH = REPO_ROOT / "src" / "jarvis" / "capabilities" / "registry.py"


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


@pytest.fixture()
def empty_registry(monkeypatch):
    """Monkeypatch `CapabilityRegistry.load_default` to return an empty
    registry, so neither `ontology.explain` nor `engineering.continuity`
    are known — exercises the refuse branch of the T3 gate."""
    monkeypatch.setattr(
        CapabilityRegistry,
        "load_default",
        classmethod(lambda cls: CapabilityRegistry()),
    )


def test_t1_explain_happy_path_unchanged_with_default_seed():
    intent = _intent("explain c-rate")
    task = try_explain_concept_task(intent)
    assert isinstance(task, Task)
    assert task.required_capability_ids == [CAPABILITY_ONTOLOGY_EXPLAIN]
    assert task.intent_id == intent.id
    assert intent.metadata.get("task_kind") == TASK_KIND_EXPLAIN_CONCEPT
    assert intent.metadata.get("explain_query") == "c-rate"


def test_t2_defer_happy_path_unchanged_with_default_seed():
    intent = _intent("estado")
    task = try_defer_to_continuity_task(intent)
    assert isinstance(task, Task)
    assert task.required_capability_ids == [CAPABILITY_ENGINEERING_CONTINUITY]
    assert task.intent_id == intent.id
    assert intent.metadata.get("task_kind") == TASK_KIND_DEFER_TO_CONTINUITY


def test_t3_explain_refused_when_registry_missing_capability(empty_registry):
    intent = _intent("explain c-rate")
    task = try_explain_concept_task(intent)
    assert task is None
    assert "task_kind" not in intent.metadata
    assert "explain_query" not in intent.metadata


def test_t4_defer_refused_when_registry_missing_capability(empty_registry):
    intent = _intent("estado")
    task = try_defer_to_continuity_task(intent)
    assert task is None
    assert "task_kind" not in intent.metadata


def test_t5_fences_hold_ast():
    forbidden = (
        "jarvis.core",
        "jarvis.flight_software",
        "jarvis.vehicle_profiles",
    )
    imported = _imported_module_names(ASSISTANT_TASK_PATH)

    # New one-way edge explicitly permitted by this Buy.
    assert "jarvis.capabilities.registry" in imported

    for module_name in imported:
        for forbidden_root in forbidden:
            assert not (
                module_name == forbidden_root or module_name.startswith(forbidden_root + ".")
            ), f"assistant_task.py imports forbidden module '{module_name}'"

    registry_imports = _imported_module_names(REGISTRY_PATH)
    assert not any(
        m == "jarvis.intelligence" or m.startswith("jarvis.intelligence.")
        for m in registry_imports
    ), "registry.py imports jarvis.intelligence"


def test_t6_pyproject_version_is_0_6_11():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.6.24"' in text


def test_gate_does_not_touch_availability_or_providers(monkeypatch):
    """Optional (IC §3 note): the T3 membership *helper*
    (`_capabilities_known_in_default_registry`) is membership-only —
    assert it never calls `providers()`/`get_provider` on the registry,
    only `get_capability`.

    This deliberately exercises the helper directly rather than the
    full `try_explain_concept_task`/`try_defer_to_continuity_task` call
    chain: `B1-assistant-software-safety-bridge` (T4) added a second,
    explicitly authorized gate immediately after this one
    (`_software_safety_allows` -> `SoftwareCapabilitySafetyGate`) that
    *does* legitimately read `availability` and call `get_provider` —
    that is the whole point of T4. Watching the end-to-end call chain
    would make this test couple T3's own membership-only guarantee to
    whatever gates a later, authorized Buy adds downstream of it. See
    `tests/test_assistant_software_safety_bridge_b1.py` for T4's own
    coverage of the Safety gate's registry reads."""
    real_registry = CapabilityRegistry.load_default()
    calls: list[str] = []

    class _WatchedRegistry(CapabilityRegistry):
        def get_capability(self, capability_id):
            calls.append("get_capability")
            return real_registry.get_capability(capability_id)

        def providers(self):
            calls.append("providers")
            return real_registry.providers()

        def get_provider(self, provider_id):
            calls.append("get_provider")
            return real_registry.get_provider(provider_id)

    monkeypatch.setattr(
        CapabilityRegistry,
        "load_default",
        classmethod(lambda cls: _WatchedRegistry(
            capabilities=real_registry.capabilities(),
            providers=real_registry.providers(),
            skills=real_registry.skills(),
        )),
    )

    assistant_task._capabilities_known_in_default_registry([CAPABILITY_ONTOLOGY_EXPLAIN])
    assistant_task._capabilities_known_in_default_registry([CAPABILITY_ENGINEERING_CONTINUITY])

    assert calls == ["get_capability", "get_capability"]
