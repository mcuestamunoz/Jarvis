"""Tests T1-T6 for `B1-chat-explain-intercept` (A7).

Exercises `JarvisOrchestrator._handle_global_commands`'s new
"jarvis explain "/"explain " prefix intercept: resolved entirely via
`jarvis.intelligence.explain` (A3), zero LLM calls on hit or miss, and
without disturbing any other global-command path.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from jarvis.core.orchestrator import JarvisOrchestrator

REPO_ROOT = Path(__file__).resolve().parents[1]
INTELLIGENCE_DIR = REPO_ROOT / "src" / "jarvis" / "intelligence"


class _ExplodingLLMInterface:
    """Any LLM call raises — proves the explain path never reaches it."""

    def interpret(self, *args, **kwargs):
        raise AssertionError("llm_interface.interpret must not be called for an explain prefix")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm_interface.analyze must not be called for an explain prefix")

    def complete(self, *args, **kwargs):
        raise AssertionError("LLM complete must not be called for an explain prefix")


def _orchestrator() -> JarvisOrchestrator:
    return JarvisOrchestrator()


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


def test_t1_jarvis_explain_prefix_hits_no_llm():
    orch = _orchestrator()
    result = orch.handle_user_text("jarvis explain c-rate", _ExplodingLLMInterface())
    assert result["status"] == "ok"
    assert "DEFINICION" in result["message"]
    assert "c-rate-de-bateria" in result["message"] or "C-rate" in result["message"]


def test_t2_bare_explain_prefix_same_path():
    orch = _orchestrator()
    result = orch.handle_user_text("explain imu", _ExplodingLLMInterface())
    assert result["status"] == "ok"
    assert "DEFINICION" in result["message"]
    assert "imu" in result["message"].lower()


def test_t3_unknown_query_is_honest_miss_no_llm():
    orch = _orchestrator()
    result = orch.handle_user_text("explain no-existe-xyz", _ExplodingLLMInterface())
    assert result["status"] in ("ok", "error")
    assert "No solid ontology note for: no-existe-xyz" in result["message"]


def test_t4_unrelated_global_paths_unchanged():
    orch = _orchestrator()
    # Escape word still works.
    cancel = orch._handle_global_commands("cancelar")
    assert cancel is not None
    assert cancel["status"] == "ok"
    assert "cancelar" not in cancel["message"].lower() or "operación" in cancel["message"].lower()

    # A phrase that merely contains "explain"/"explicar" without the exact
    # required prefix+space is NOT swallowed by the intercept.
    assert orch._handle_global_commands("explica esto por favor") is None
    assert orch._handle_global_commands("no explain plz") is None

    # And a completely unrelated line still falls through to the normal
    # (non-global) path, i.e. the intercept returns None for it.
    assert orch._handle_global_commands("quiero diseñar un dron") is None


def test_t5_explain_works_even_if_llm_would_raise():
    """Same as T1/T2 in spirit but stated as its own IC-required case:
    the intercept must short-circuit before llm_interface is touched at
    all, so an unhealthy/exploding LLM client cannot break `explain`."""
    orch = _orchestrator()
    exploding = _ExplodingLLMInterface()
    hit = orch.handle_user_text("jarvis explain c-rate-de-bateria", exploding)
    assert hit["status"] == "ok"
    miss = orch.handle_user_text("explain totally-unknown-id", exploding)
    assert "No solid ontology note for" in miss["message"]
    list_redirect = orch.handle_user_text("explain --list", exploding)
    assert "terminal" in list_redirect["message"].lower()


def test_t6_intelligence_modules_still_do_not_import_core():
    forbidden = ("jarvis.core",)
    for path in sorted(INTELLIGENCE_DIR.rglob("*.py")):
        imported = _imported_module_names(path)
        for module_name in imported:
            for forbidden_root in forbidden:
                assert not (
                    module_name == forbidden_root
                    or module_name.startswith(forbidden_root + ".")
                ), f"{path.relative_to(REPO_ROOT)} imports forbidden module '{module_name}'"


def test_pyproject_version_is_0_6_8():
    """Bumped forward again by T0 (B1-assistant-explain-task) per its own
    IC §3 instruction ("bump prior version-checkpoint tests forward per
    established pattern") — same courtesy A8 extended to this file."""
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.6.8"' in text
