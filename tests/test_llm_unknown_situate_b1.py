"""B1-llm-unknown-situate (CI-1d).

Engineer smoke after CI-1c: `hablar` / `gracias` no longer opened the create
wizard but answered with a generic analyze dump. Intent: a meaningless turn
must *situate* the user, 0 LLM. CI-1e replaced the full Continuity wall
(`project_status`) with a brief `situate` reply — see
`test_llm_unknown_situate_brief_b1.py` for the message shape. Explain-shaped unknowns keep the residual analyze path. Stub LLM
only — no live Ollama.
"""
from __future__ import annotations

from pathlib import Path

import pytest

import jarvis.core.orchestrator as orchestrator_module
from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import OrchestratorMode
from tests.test_fn022_engineering_intent import _closed_project, _RefuseLLM

_CREATE_WIZARD_COPY = "Vamos a definir el proyecto paso a paso."
_ANALYZE_TEXT = "Respuesta contextual (stub analyze)."


class _StubLLM(_RefuseLLM):
    def __init__(self, action: str = "create_project") -> None:
        self.action = action
        self.interpret_calls: list[str] = []
        self.analyze_calls: list[str] = []

    def interpret(self, user_input, runtime_state):
        self.interpret_calls.append(user_input)
        return {"action": self.action, "parameters": {}, "raw_user_input": user_input}

    def analyze(self, *args, **kwargs):
        self.analyze_calls.append(kwargs.get("user_input"))
        return _ANALYZE_TEXT


def _mode(orch):
    return orch.state_manager.runtime_state.session.mode


# T1 — nonsense on an active project situates, 0 LLM ──────────────────────

@pytest.mark.parametrize("phrase", ["hablar", "Gracias.", "hola"])
def test_t1_unknown_nonsense_situates_with_zero_llm(tmp_path: Path, phrase):
    orch = _closed_project(tmp_path)
    assert orch.intent_resolver.resolve_intent(phrase) == "unknown"

    result = orch.handle_user_text(phrase, _RefuseLLM())  # any LLM call raises

    assert result["action"] == "situate"
    assert result["message"].startswith("No capté una orden clara.")
    assert _mode(orch) == OrchestratorMode.IDLE


# T2 — interpret never runs; backstop still situates if it did ────────────

def test_t2_create_project_stub_never_consulted(tmp_path: Path):
    orch = _closed_project(tmp_path)
    llm = _StubLLM("create_project")

    result = orch.handle_user_text("hablar", llm)

    assert llm.interpret_calls == []
    assert llm.analyze_calls == []
    assert result["action"] == "situate"
    assert _CREATE_WIZARD_COPY not in str(result.get("message"))


def test_t2_backstop_situates_if_interpret_runs(tmp_path: Path, monkeypatch):
    # Force the early claim to be skipped (first is_explain_ask call → True)
    # so the residual interpret runs; the CI-1c guard must then situate
    # (second call → False), never open the wizard nor analyze.
    answers = iter([True, False])
    monkeypatch.setattr(orchestrator_module, "is_explain_ask", lambda _text: next(answers))
    orch = _closed_project(tmp_path)
    llm = _StubLLM("create_project")

    result = orch.handle_user_text("hablar", llm)

    assert llm.interpret_calls == ["hablar"]
    assert llm.analyze_calls == []
    assert result["action"] == "situate"
    assert _mode(orch) == OrchestratorMode.IDLE


# T3 — explain-shaped unknown still reaches analyze ───────────────────────

def test_t3_explain_shaped_unknown_still_reaches_analyze(tmp_path: Path):
    orch = _closed_project(tmp_path)
    assert orch.intent_resolver.resolve_intent("qué es el margen") == "unknown"
    llm = _StubLLM("calculate")

    result = orch.handle_user_text("qué es el margen", llm)

    assert result["action"] == "analyze"
    assert result["message"] == _ANALYZE_TEXT
    assert llm.analyze_calls == ["qué es el margen"]


# T4 — "explicame el margen" stays on the analyze intent path (CI-1b) ─────

def test_t4_explicame_el_margen_still_analyze_no_plan(tmp_path: Path):
    orch = _closed_project(tmp_path)
    assert orch.intent_resolver.resolve_intent("explicame el margen") == "analyze"
    llm = _StubLLM()

    result = orch.handle_user_text("explicame el margen", llm)

    assert result["action"] == "analyze"
    assert result["message"] == _ANALYZE_TEXT
    assert "Plan estratégico" not in result["message"]
    assert llm.interpret_calls == []
    assert _mode(orch) == OrchestratorMode.IDLE


# T5 — deterministic create still opens the wizard (0 LLM) ─────────────────

@pytest.mark.parametrize("phrase", ["nuevo", "quiero diseñar un dron"])
def test_t5_deterministic_create_still_opens_wizard(tmp_path: Path, phrase):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text(phrase, _RefuseLLM())

    assert result["status"] == "interactive"
    assert _CREATE_WIZARD_COPY in result["message"]
    assert _mode(orch) == OrchestratorMode.CREATE_PROJECT_INTERACTIVE


# T6 — no project: unknown + LLM create_project still opens the wizard ─────

def test_t6_no_project_unknown_create_still_opens_wizard(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    llm = _StubLLM("create_project")

    result = orch.handle_user_text("hablar", llm)

    assert llm.interpret_calls == ["hablar"]
    assert result["status"] == "interactive"
    assert _CREATE_WIZARD_COPY in result["message"]


# FN-022 regression — real intention keeps its plan ────────────────────────

def test_poco_margen_still_gets_fn022_plan(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("poco margen", _RefuseLLM())

    assert result["action"] in ("engineering_intent", "explore_design_space")
