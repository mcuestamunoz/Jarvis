"""B1-llm-unknown-situate-brief (CI-1e).

Engineer REJECT of CI-1d: `hablar` situated with the full Continuity wall —
useless by voice. CI-1e keeps the CI-1d claim (unknown + active project +
not explain → 0 LLM) but answers with a brief `situate` message: fixed lead
+ project + situation + next step + readiness one-liner. `estado` keeps the
full wall. Stub LLM only — no live Ollama.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.adapters.cli.main import render_response
from jarvis.schemas.action_schema import OrchestratorMode
from tests.test_fn022_engineering_intent import _closed_project, _RefuseLLM

_LEAD = "No capté una orden clara."
_WALL_MARKERS = (
    "ENGINEERING READINESS",
    "TOP GAPS",
    "Conceptos",
    "Componentes",
    "Evidencia",
    "PROJECT STATUS",
)
_CREATE_WIZARD_COPY = "Vamos a definir el proyecto paso a paso."
_ANALYZE_TEXT = "Respuesta contextual (stub analyze)."


class _CountingLLM(_RefuseLLM):
    def __init__(self) -> None:
        self.interpret_calls: list[str] = []
        self.analyze_calls: list[str] = []

    def interpret(self, user_input, runtime_state):
        self.interpret_calls.append(user_input)
        return {"action": "create_project", "parameters": {}, "raw_user_input": user_input}

    def analyze(self, *args, **kwargs):
        self.analyze_calls.append(kwargs.get("user_input"))
        return _ANALYZE_TEXT


def _mode(orch):
    return orch.state_manager.runtime_state.session.mode


# T1 — brief situate: lead + Continuity fields, no wall blocks ────────────

@pytest.mark.parametrize("phrase", ["hablar", "gracias", "hola"])
def test_t1_situate_is_brief(tmp_path: Path, phrase):
    orch = _closed_project(tmp_path)
    continuity = orch.build_startup_context()["continuity"]

    result = orch.handle_user_text(phrase, _RefuseLLM())

    assert result["action"] == "situate"
    assert result["status"] == "ok"
    message = result["message"]
    lines = message.splitlines()
    assert lines[0] == _LEAD
    assert continuity["situation"] in message
    assert continuity["next_useful_step"] in message
    assert "Estado del proyecto: no listo para ensamblar." in message
    assert len(lines) <= 6
    for marker in _WALL_MARKERS:
        assert marker not in message, marker
    assert "startup_context" not in result


# T2 — 0 interpret / analyze; no create wizard ─────────────────────────────

@pytest.mark.parametrize("phrase", ["hablar", "gracias", "hola"])
def test_t2_zero_llm_no_wizard(tmp_path: Path, phrase):
    orch = _closed_project(tmp_path)
    llm = _CountingLLM()

    result = orch.handle_user_text(phrase, llm)

    assert llm.interpret_calls == []
    assert llm.analyze_calls == []
    assert _CREATE_WIZARD_COPY not in result["message"]
    assert _mode(orch) == OrchestratorMode.IDLE


# T3 — render_response prints only the message ─────────────────────────────

def test_t3_render_is_message_only(tmp_path: Path):
    orch = _closed_project(tmp_path)
    result = orch.attach_project_coherence(orch.handle_user_text("hablar", _RefuseLLM()))

    rendered = render_response(result)

    assert rendered == result["message"]
    assert "Acción ejecutada" not in rendered


# T4 — `estado` still prints the full wall ─────────────────────────────────

def test_t4_estado_still_full_wall(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("estado", _RefuseLLM())

    assert result["action"] == "project_status"
    rendered = render_response(result)
    for marker in ("ENGINEERING READINESS", "TOP GAPS", "Situación:"):
        assert marker in rendered, marker
    assert _LEAD not in rendered


# T5 — analyze / create / FN-022 unchanged ─────────────────────────────────

def test_t5_explicame_el_margen_still_analyze(tmp_path: Path):
    orch = _closed_project(tmp_path)
    llm = _CountingLLM()

    result = orch.handle_user_text("explicame el margen", llm)

    assert result["action"] == "analyze"
    assert result["message"] == _ANALYZE_TEXT
    assert "Plan estratégico" not in result["message"]


def test_t5_nuevo_still_opens_create_wizard(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("nuevo", _RefuseLLM())

    assert result["status"] == "interactive"
    assert _CREATE_WIZARD_COPY in result["message"]
    assert _mode(orch) == OrchestratorMode.CREATE_PROJECT_INTERACTIVE


def test_t5_poco_margen_still_fn022(tmp_path: Path):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("poco margen", _RefuseLLM())

    assert result["action"] in ("engineering_intent", "explore_design_space")


# T6 — explain-shaped unknown still reaches analyze ───────────────────────

def test_t6_explain_shaped_unknown_still_analyze(tmp_path: Path):
    orch = _closed_project(tmp_path)
    llm = _CountingLLM()

    result = orch.handle_user_text("qué es el margen", llm)

    assert result["action"] == "analyze"
    assert llm.analyze_calls == ["qué es el margen"]
    assert _LEAD not in result["message"]
