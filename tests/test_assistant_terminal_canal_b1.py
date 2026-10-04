"""Tests T1-T6 for `B1-assistant-terminal-canal`.

Exercises `jarvis.intelligence.explain` (resolve + format + CLI entry)
against the real `ontology/` vault. CLI smoke invokes the resolve/format
functions directly (per IC §3), plus one `subprocess` smoke of the
actual `jarvis explain` argv path.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

from jarvis.intelligence.explain import (
    format_explain_cite,
    resolve_explain_query,
    run_explain_cli,
)
from jarvis.intelligence.explain_aliases import EXPLAIN_ALIASES

REPO_ROOT = Path(__file__).resolve().parents[1]
EXPLAIN_MODULE_PATHS = [
    REPO_ROOT / "src" / "jarvis" / "intelligence" / "explain.py",
    REPO_ROOT / "src" / "jarvis" / "intelligence" / "explain_aliases.py",
]
NOTE_ID = "c-rate-de-bateria"


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


def _called_names(source_path: Path) -> set[str]:
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    return names


def test_t1_resolve_by_id_yields_cite_with_nonempty_definicion():
    cite = resolve_explain_query(NOTE_ID)
    assert cite is not None
    assert cite.id == NOTE_ID
    assert cite.definicion != ""


def test_t2_seed_alias_resolves_to_same_note_id():
    assert "c-rate" in EXPLAIN_ALIASES
    via_alias = resolve_explain_query("c-rate")
    via_id = resolve_explain_query(NOTE_ID)
    assert via_alias is not None
    assert via_id is not None
    assert via_alias.id == via_id.id == NOTE_ID

    # Second seeded alias, verified solid before shipping (IC §1.1).
    op_id = "punto-de-operacion-vs-capacidad-intrinseca"
    via_op_alias = resolve_explain_query("op")
    assert via_op_alias is not None
    assert via_op_alias.id == op_id


def test_t3_unknown_query_is_an_honest_miss():
    assert resolve_explain_query("this-alias-does-not-exist-anywhere") is None

    exit_code = run_explain_cli("this-alias-does-not-exist-anywhere")
    assert exit_code == 1


def test_t4_formatted_output_includes_never_invents_honesty():
    cite = resolve_explain_query(NOTE_ID)
    assert cite is not None
    assert cite.never_invents  # non-empty per frontmatter
    rendered = format_explain_cite(cite)
    for token in cite.never_invents:
        assert token in rendered
    assert "no inventa" in rendered
    assert cite.definicion in rendered
    assert cite.intuicion in rendered
    assert cite.path in rendered


def test_t5_no_continuity_submit_command_or_orchestrator_construction():
    for path in EXPLAIN_MODULE_PATHS:
        imported = _imported_module_names(path)
        assert not any(
            module_name == "jarvis.core" or module_name.startswith("jarvis.core.")
            for module_name in imported
        ), f"{path.name} imports jarvis.core (Continuity/orchestrator)"
        called = _called_names(path)
        assert "submit_command" not in called
        assert "JarvisOrchestrator" not in called


def test_t6_no_llm_client_import():
    forbidden_substrings = ("llm", "ollama", "openai", "anthropic")
    for path in EXPLAIN_MODULE_PATHS:
        imported = _imported_module_names(path)
        for module_name in imported:
            lowered = module_name.lower()
            for token in forbidden_substrings:
                assert token not in lowered, (
                    f"{path.name} imports '{module_name}', looks LLM-related"
                )


def test_cli_argv_smoke_success_and_miss():
    ok = subprocess.run(
        [sys.executable, "-m", "jarvis.main", "explain", NOTE_ID],
        cwd=REPO_ROOT,
        env={"PYTHONPATH": str(REPO_ROOT / "src")},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert ok.returncode == 0
    assert "DEFINICION" in ok.stdout
    assert NOTE_ID in ok.stdout

    miss = subprocess.run(
        [sys.executable, "-m", "jarvis.main", "explain", "not-a-real-id-xyz"],
        cwd=REPO_ROOT,
        env={"PYTHONPATH": str(REPO_ROOT / "src")},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert miss.returncode == 1
    assert "No solid ontology note" in miss.stderr

