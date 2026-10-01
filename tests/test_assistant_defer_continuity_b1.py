"""Tests T1-T7 for `B1-assistant-defer-continuity` (T1).

Exercises `jarvis.intelligence.assistant_task.try_defer_to_continuity_task`
— the second Assistant Task kind, per `DC-assistant-defer-continuity`
(★ CLOSED): a finite, explicit status/continuity phrase classifies to
`Task(defer_to_continuity)` requiring `engineering.continuity`, fulfilled
entirely by `core/`'s existing, already-LLM-free `_handle_project_status()`.
Explain (T0) always wins over Continuity-defer for the same line.
"""

from __future__ import annotations

import ast
from pathlib import Path

from jarvis.capabilities.intent import Task, TerminalIntentAdapter
from jarvis.config import CONTINUITY_DEFER_PHRASES
from jarvis.core.intent_resolver import IntentResolver
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.intelligence.assistant_task import (
    CAPABILITY_ENGINEERING_CONTINUITY,
    TASK_KIND_DEFER_TO_CONTINUITY,
    try_defer_to_continuity_task,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSISTANT_TASK_PATH = REPO_ROOT / "src" / "jarvis" / "intelligence" / "assistant_task.py"
PROJECT_CONTINUITY_PATH = REPO_ROOT / "src" / "jarvis" / "core" / "project_continuity.py"


class _ExplodingLLMInterface:
    def interpret(self, *args, **kwargs):
        raise AssertionError("llm_interface.interpret must not be called for a status phrase")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm_interface.analyze must not be called for a status phrase")

    def complete(self, *args, **kwargs):
        raise AssertionError("LLM complete must not be called for a status phrase")


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


def test_t1_status_phrase_yields_task_with_capability():
    for raw in ("estado", "resumen", "siguiente paso", "que falta"):
        intent = _intent(raw)
        task = try_defer_to_continuity_task(intent)
        assert isinstance(task, Task), f"{raw!r} should classify"
        assert task.required_capability_ids == [CAPABILITY_ENGINEERING_CONTINUITY]
        assert task.intent_id == intent.id
        assert intent.metadata.get("task_kind") == TASK_KIND_DEFER_TO_CONTINUITY


def test_t2_non_status_craft_line_yields_no_task():
    for raw in (
        "quiero diseñar un dron",
        "cambia el motor a XING-E",
        "monta el frame en la placa",
    ):
        intent = _intent(raw)
        assert try_defer_to_continuity_task(intent) is None
        assert "task_kind" not in intent.metadata


def test_t3_explain_shaped_line_never_gets_continuity_task():
    for raw in ("explain estado", "jarvis explain resumen", "explain c-rate"):
        intent = _intent(raw)
        assert try_defer_to_continuity_task(intent) is None


def test_t4_orchestrator_status_phrase_is_project_status_no_llm():
    orch = JarvisOrchestrator()
    exploding = _ExplodingLLMInterface()

    for raw in ("estado", "resumen", "ESTADO"):
        result = orch.handle_user_text(raw, exploding)
        assert result["status"] == "ok"
        assert result["action"] == "project_status"

    # Explain still takes precedence and is unaffected.
    explain_result = orch.handle_user_text("explain imu", exploding)
    assert explain_result["action"] == "global_command"
    assert "DEFINICION" in explain_result["message"]


def test_t5_status_patterns_sync():
    for phrase in IntentResolver.STATUS_PATTERNS:
        assert phrase in CONTINUITY_DEFER_PHRASES, (
            f"IntentResolver.STATUS_PATTERNS entry {phrase!r} missing from "
            "CONTINUITY_DEFER_PHRASES — tables have drifted"
        )


def test_t6_fences_hold_ast():
    forbidden = (
        "jarvis.core",
        "jarvis.flight_software",
        "jarvis.vehicle_profiles",
    )
    imported = _imported_module_names(ASSISTANT_TASK_PATH)
    for module_name in imported:
        for forbidden_root in forbidden:
            assert not (
                module_name == forbidden_root or module_name.startswith(forbidden_root + ".")
            ), f"assistant_task.py imports forbidden module '{module_name}'"

    # Specifically forbidden per this Buy's DC/IC (even though covered by
    # the broader jarvis.core check above, name them explicitly).
    assert "jarvis.core.intent_resolver" not in imported
    assert "jarvis.core.project_continuity" not in imported

    continuity_imports = _imported_module_names(PROJECT_CONTINUITY_PATH)
    assert not any(
        m == "jarvis.intelligence" or m.startswith("jarvis.intelligence.")
        for m in continuity_imports
    ), "project_continuity.py imports jarvis.intelligence"


def test_t7_pyproject_version_is_0_6_10():
    """Bumped forward by T3 (B1-assistant-task-registry-coherence) per
    established pattern."""
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.6.24"' in text
