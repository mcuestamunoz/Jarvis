"""Tests T1-T5 for `B1-assistant-chat-skill-first-software` (T22).

Chat Skill-first for software Skills only — explain/status via
`run_skill`. Vehicle/ops stay Task-direct.
"""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import patch

from jarvis.capabilities.skills_runtime import run_skill
from jarvis.core.orchestrator import JarvisOrchestrator

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSISTANT_TASK_PATH = REPO_ROOT / "src" / "jarvis" / "intelligence" / "assistant_task.py"


class _ExplodingLLMInterface:
    def interpret(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def analyze(self, *args, **kwargs):
        raise AssertionError("llm must not be called")

    def complete(self, *args, **kwargs):
        raise AssertionError("llm must not be called")


def test_t1_explain_via_skill_path_cite_honesty(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    result = orch.handle_user_text("explain c-rate-de-bateria", exploding)
    assert result["status"] == "ok"
    assert result["action"] == "global_command"
    assert "DEFINICION" in result["message"]
    assert "no inventa" in result["message"]


def test_t2_status_phrase_skill_gate_and_project_status_shape(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    with patch(
        "jarvis.capabilities.skills_runtime.run_skill",
        wraps=run_skill,
    ) as spy:
        result = orch.handle_user_text("estado", exploding)
    assert spy.called
    assert any(c.args[0] == "skill.project_status" for c in spy.call_args_list)
    assert result["action"] == "project_status"
    assert "startup_context" in result


def test_t3_hold_and_charge_still_task_direct(tmp_path: Path):
    """T22: charge stays Task-direct (no ops Skill-first). T23 later
    gates HOLD via `skill.request_hold` — see
    `test_assistant_chat_skill_first_vehicle_hold_b1`."""
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    exploding = _ExplodingLLMInterface()
    with patch(
        "jarvis.capabilities.skills_runtime.run_skill",
        wraps=run_skill,
    ) as skill_spy:
        hold = orch.handle_user_text("hold", exploding)
        charge = orch.handle_user_text("charge", exploding)
    assert hold["action"] == "vehicle_hold"
    assert charge["action"] == "ops_charge"
    for call in skill_spy.call_args_list:
        assert call.args[0] != "skill.request_charge"


def test_t4_handle_explain_intent_does_not_bypass_run_skill():
    """Chat seam `handle_explain_intent` must call `run_skill`, not a
    direct `fulfill_ontology_explain` bypass."""
    source = ASSISTANT_TASK_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "handle_explain_intent":
            calls = [
                n.func.id
                for n in ast.walk(node)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            ]
            attr_calls = [
                n.func.attr
                for n in ast.walk(node)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            ]
            assert "run_skill" in calls or "run_skill" in attr_calls
            assert "fulfill_ontology_explain" not in calls
            assert "fulfill_ontology_explain" not in attr_calls
            return
    raise AssertionError("handle_explain_intent not found")


def test_t5_no_tip_version_pins_in_new_suite():
    """Policy: this Buy's suite must not pin package tip version."""
    from tests.test_suite_no_tip_version_pins_b1 import (
        test_no_pyproject_tip_version_pins_in_suite,
    )

    test_no_pyproject_tip_version_pins_in_suite()
