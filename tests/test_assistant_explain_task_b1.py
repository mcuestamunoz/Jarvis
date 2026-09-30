"""Tests T1-T7 for `B1-assistant-explain-task` (T0).

Exercises `jarvis.intelligence.assistant_task` — the first on-disk
Assistant Task emission (`DC-assistant-first-task`, ★ CLOSED): classify
an `Intent` into a `Task(explain_concept)` (or refuse), fulfill via
`ontology.explain`, and prove the A7 chat path now routes through this
seam with zero behavior regression and zero LLM calls.
"""

from __future__ import annotations

import ast
from pathlib import Path

from jarvis.capabilities.intent import Intent, IntentSource, Task, TerminalIntentAdapter
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.intelligence.assistant_task import (
    CAPABILITY_ONTOLOGY_EXPLAIN,
    TASK_KIND_EXPLAIN_CONCEPT,
    fulfill_ontology_explain,
    handle_explain_intent,
    try_explain_concept_task,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSISTANT_TASK_PATH = REPO_ROOT / "src" / "jarvis" / "intelligence" / "assistant_task.py"
PROJECT_CONTINUITY_PATH = REPO_ROOT / "src" / "jarvis" / "core" / "project_continuity.py"


class _ExplodingLLMInterface:
    def interpret(self, *args, **kwargs):
        raise AssertionError("llm_interface.interpret must not be called for an explain prefix")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm_interface.analyze must not be called for an explain prefix")

    def complete(self, *args, **kwargs):
        raise AssertionError("LLM complete must not be called for an explain prefix")


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


def _intent(raw_text: str) -> Intent:
    return TerminalIntentAdapter.parse(raw_text)


def test_t1_explain_shaped_intent_yields_task_with_capability():
    for raw in ("explain c-rate", "jarvis explain c-rate"):
        intent = _intent(raw)
        task = try_explain_concept_task(intent)
        assert isinstance(task, Task)
        assert task.required_capability_ids == [CAPABILITY_ONTOLOGY_EXPLAIN]
        assert task.intent_id == intent.id
        assert intent.metadata.get("task_kind") == TASK_KIND_EXPLAIN_CONCEPT
        assert intent.metadata.get("explain_query") == "c-rate"


def test_t2_non_explain_intent_yields_no_task():
    intent = _intent("quiero diseñar un dron")
    assert try_explain_concept_task(intent) is None
    assert "task_kind" not in intent.metadata

    # A line that merely contains "explain"/"explicar" without the exact
    # required prefix+space must also refuse.
    assert try_explain_concept_task(_intent("explica esto por favor")) is None
    assert try_explain_concept_task(_intent("no explain plz")) is None


def test_t3_fulfill_returns_cite_body():
    message = fulfill_ontology_explain("c-rate")
    assert "DEFINICION" in message
    assert "c-rate-de-bateria" in message or "C-rate" in message


def test_t4_fulfill_unknown_query_is_honest_miss_no_raise():
    message = fulfill_ontology_explain("totally-unknown-id-xyz")
    assert "No solid ontology note for: totally-unknown-id-xyz" in message

    # --list/--rung inside chat: honest redirect, still via fulfill, no Task.
    redirect = fulfill_ontology_explain("--list")
    assert "terminal" in redirect.lower()
    intent = _intent("explain --list")
    assert try_explain_concept_task(intent) is None
    assert "task_kind" not in intent.metadata


def test_t5_orchestrator_chat_path_routes_through_assistant_no_llm():
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()

    hit = orch.handle_user_text("explain imu", exploding)
    assert hit["status"] == "ok"
    assert "DEFINICION" in hit["message"]

    miss = orch.handle_user_text("explain does-not-exist-xyz", exploding)
    assert "No solid ontology note for" in miss["message"]

    list_redirect = orch.handle_user_text("jarvis explain --list", exploding)
    assert "terminal" in list_redirect["message"].lower()

    # Unrelated global paths still unaffected.
    assert orch._handle_global_commands("quiero diseñar un dron") is None


def test_t6_fences_hold_ast():
    forbidden = ("jarvis.core", "jarvis.flight_software", "jarvis.vehicle_profiles")
    imported = _imported_module_names(ASSISTANT_TASK_PATH)
    for module_name in imported:
        for forbidden_root in forbidden:
            assert not (
                module_name == forbidden_root or module_name.startswith(forbidden_root + ".")
            ), f"assistant_task.py imports forbidden module '{module_name}'"

    continuity_imports = _imported_module_names(PROJECT_CONTINUITY_PATH)
    assert not any(
        m == "jarvis.intelligence" or m.startswith("jarvis.intelligence.")
        for m in continuity_imports
    ), "project_continuity.py imports jarvis.intelligence"


def test_t7_pyproject_version_is_0_6_10():
    """Bumped forward by T2 (B1-capability-registry-product-fill) per
    established pattern."""
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.6.18"' in text


def test_handle_explain_intent_matches_try_plus_fulfill():
    intent = _intent("explain motores")
    combined = handle_explain_intent(_intent("explain motores"))
    task = try_explain_concept_task(intent)
    assert task is not None
    direct = fulfill_ontology_explain(intent.metadata["explain_query"])
    assert combined == direct


def test_intent_source_is_terminal():
    intent = _intent("explain imu")
    assert intent.source == IntentSource.TERMINAL
