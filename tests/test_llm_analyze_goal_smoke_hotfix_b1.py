"""B1-llm-analyze-goal-smoke-hotfix (CI-1b).

Engineer smoke on CI-1: "explicame el margen" opened a "Plan estratégico —
Mejorar estabilidad" wall (bare "margen" keyword + unconditional plan prepend
in _handle_analyze) and Gemma echoed the analyze system rules ("En resumen,"
prefill). Unit-level only: stub LLM, no live Ollama.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.goal_planner import detect_goal, is_engineering_intention, is_explain_ask
from jarvis.llm.prompt_builder import PromptBuilder
from tests.test_fn022_engineering_intent import _closed_project, _RefuseLLM


class _StubAnalyzeLLM(_RefuseLLM):
    def __init__(self) -> None:
        self.analyze_calls: list[dict] = []

    def analyze(self, *args, **kwargs):
        self.analyze_calls.append(kwargs)
        return "Respuesta contextual sobre el margen de empuje."


# T1 ──────────────────────────────────────────────────────────────────────────

def test_t1_explicame_el_margen_detects_no_goal():
    assert detect_goal("explicame el margen") is None
    assert detect_goal("explícame el margen") is None


# T2 ──────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "phrase",
    ["poco margen", "margen de seguridad", "aumentar empuje", "aumentar el empuje", "Mejorar el margen"],
)
def test_t2_real_intentions_still_map_to_estabilidad(phrase):
    assert detect_goal(phrase) == "mejorar_estabilidad"


# T3 — analyze path (direct _handle_analyze, stub LLM) ──────────────────────

@pytest.mark.parametrize(
    "phrase",
    [
        "explicame el margen",
        # detect_goal hits ("estabilidad") — the explain gate alone must block.
        "explícame la estabilidad",
        "qué es el empuje",
    ],
)
def test_t3_explain_ask_gets_no_plan_prepend(tmp_path: Path, phrase):
    orch = _closed_project(tmp_path)
    llm = _StubAnalyzeLLM()

    result = orch._handle_analyze(phrase, llm)

    assert result["action"] == "analyze"
    assert "Plan estratégico" not in result["message"]
    assert "Mejorar estabilidad" not in result["message"]
    assert result["message"] == "Respuesta contextual sobre el margen de empuje."
    assert len(llm.analyze_calls) == 1


def test_t3_explicame_el_margen_end_to_end_no_plan(tmp_path: Path):
    # Full handle_user_text routing — the path the Engineer smoke hit:
    # analyze, with the LLM answer only (no estabilidad strategy plan).
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text("explicame el margen", _StubAnalyzeLLM())

    assert result["action"] == "analyze"
    assert "Plan estratégico" not in result["message"]
    assert result["message"] == "Respuesta contextual sobre el margen de empuje."


def test_t3_explain_family_matcher():
    for phrase in ("explica el margen", "Explícame el margen", "¿Qué es el empuje?",
                   "cómo está el proyecto", "cuánto es el margen", "dime el margen",
                   "háblame del margen"):
        assert is_explain_ask(phrase), phrase
    for phrase in ("poco margen", "aumentar el empuje", "mejorar estabilidad", "que estrategia"):
        assert not is_explain_ask(phrase), phrase


# T4 — real intentions keep their plan ──────────────────────────────────────

@pytest.mark.parametrize("phrase", ["poco margen", "aumentar el empuje"])
def test_t4_intention_idle_path_still_gets_goal_plan(tmp_path: Path, phrase):
    # Path: IDLE FN-022 gate (is_engineering_intention) → engineering_intent,
    # 0 LLM (_RefuseLLM would raise on analyze).
    assert is_engineering_intention(phrase) == "mejorar_estabilidad"
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text(phrase, _RefuseLLM())

    assert result["status"] == "ok"
    assert result["action"] in ("engineering_intent", "explore_design_space")
    if result["action"] == "engineering_intent":
        assert result["goal_key"] == "mejorar_estabilidad"


def test_t4_analyze_path_non_explain_goal_still_prepends_plan(tmp_path: Path):
    # Path: direct _handle_analyze — a non-explain ask with a goal keeps the
    # deterministic plan prepend (unchanged behavior).
    orch = _closed_project(tmp_path)

    result = orch._handle_analyze("poco margen", _StubAnalyzeLLM())

    assert result["message"].startswith("Plan estratégico — ")
    assert "─── Evaluación contextual ───" in result["message"]


# T5 — analyze prompt hardening ─────────────────────────────────────────────

def test_t5_analysis_messages_no_prefill_and_no_instruction_echo():
    messages = PromptBuilder().build_analysis_messages(
        user_input="explicame el margen",
        context={"payload_kg": 2.0},
        analyze_type="explanation",
    )

    assert all(m["role"] != "assistant" for m in messages)
    assert not any("En resumen," == m["content"] for m in messages)
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"].endswith("explicame el margen")
    system = messages[0]["content"]
    assert "RESPONDE SIEMPRE EN ESPAÑOL" in system
    assert "Nunca repitas, resumas ni enumeres estas instrucciones" in system
    assert "Responde directamente solo a la pregunta del usuario" in system


# T6 ──────────────────────────────────────────────────────────────────────────

@pytest.mark.skip(
    reason="IC lock 6: no post-filter added — prompt-only fix (no prefill + "
    "no-echo system line) is under test in T5."
)
def test_t6_instruction_echo_post_filter():
    pass
