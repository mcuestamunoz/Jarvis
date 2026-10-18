"""B1-llm-interpret-unknown-guard (CI-1c, CI-INV-0 G-01).

With the Gemma default, residual `interpret` returned a *valid*
`create_project` for unclassified input ("hablar", "Gracias.") and the
create wizard opened over the active project. Bug 52 already sent
unknown-intent `iterate` to analyze; CI-1c extends that guard to every
ActionPolicy verb. Stub LLM only — no live Ollama.

CI-1d (B1-llm-unknown-situate): a non-explain unknown turn on an active
project ("hablar", "Gracias.") is now claimed *before* interpret and
situates — since CI-1e with a brief `situate` reply (T1 below). The guard itself is still
exercised by an explain-shaped unknown (`qué es el margen`), which keeps
the residual interpret → guard → analyze path (T2/T3/T5).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.orchestrator import JarvisOrchestrator
from jarvis.schemas.action_schema import OrchestratorMode
from tests.test_fn022_engineering_intent import _closed_project, _RefuseLLM

_CREATE_WIZARD_COPY = "Vamos a definir el proyecto paso a paso."
_ANALYZE_TEXT = "Respuesta contextual (stub analyze)."
# Resolver intent "unknown" and is_explain_ask True → not claimed by CI-1d.
_EXPLAIN_UNKNOWN = "qué es el margen"


class _StubInterpretLLM(_RefuseLLM):
    """`interpret` returns a fixed (ActionPolicy-valid) verb; `analyze` is recorded."""

    def __init__(self, action: str, parameters: dict | None = None) -> None:
        self.action = action
        self.parameters = parameters or {}
        self.interpret_calls: list[str] = []
        self.analyze_calls: list[str] = []

    def interpret(self, user_input, runtime_state):
        self.interpret_calls.append(user_input)
        return {"action": self.action, "parameters": dict(self.parameters), "raw_user_input": user_input}

    def analyze(self, *args, **kwargs):
        self.analyze_calls.append(kwargs.get("user_input"))
        return _ANALYZE_TEXT


def _mode(orch):
    return orch.state_manager.runtime_state.session.mode


# T1 — create_project on unknown never opens the create wizard ─────────────
# (CI-1d: on an active project these non-explain phrases are claimed before
# interpret and situate — CI-1e: brief `situate`, not the wall.)

@pytest.mark.parametrize("phrase", ["hablar", "Gracias."])
def test_t1_unknown_create_project_does_not_open_wizard(tmp_path: Path, phrase):
    orch = _closed_project(tmp_path)
    assert orch.intent_resolver.resolve_intent(phrase) == "unknown"
    llm = _StubInterpretLLM("create_project")

    result = orch.handle_user_text(phrase, llm)

    assert llm.interpret_calls == []
    assert llm.analyze_calls == []
    assert result["action"] == "situate"
    assert _CREATE_WIZARD_COPY not in str(result.get("message"))
    assert result["status"] != "interactive"
    assert _mode(orch) == OrchestratorMode.IDLE
    assert _mode(orch) != OrchestratorMode.CREATE_PROJECT_INTERACTIVE


# T2 — calculate / simulate on unknown route to analyze, no mutation ──────

@pytest.mark.parametrize("action", ["calculate", "simulate"])
def test_t2_unknown_calculate_simulate_route_to_analyze(tmp_path: Path, action):
    orch = _closed_project(tmp_path)
    before = orch.state_manager.load_active_project(orch.workspace_manager).model_dump()
    llm = _StubInterpretLLM(action)

    result = orch.handle_user_text(_EXPLAIN_UNKNOWN, llm)

    assert result["action"] == "analyze"
    assert result["message"] == _ANALYZE_TEXT
    assert llm.analyze_calls == [_EXPLAIN_UNKNOWN]
    after = orch.state_manager.load_active_project(orch.workspace_manager).model_dump()
    # No calculate/simulate ran: the persisted project (parameters,
    # latest_results, history, …) is byte-for-byte the same.
    assert after == before
    assert _mode(orch) == OrchestratorMode.IDLE


# T3 — Bug 52 iterate behaviour unchanged ──────────────────────────────────

def test_t3_unknown_iterate_still_routes_to_analyze(tmp_path: Path):
    orch = _closed_project(tmp_path)
    llm = _StubInterpretLLM(
        "iterate", {"operacion": "increase", "variable": "payload_kg", "confidence": 0.9}
    )

    result = orch.handle_user_text(_EXPLAIN_UNKNOWN, llm)

    assert result["action"] == "analyze"
    assert result["message"] == _ANALYZE_TEXT
    assert _mode(orch) == OrchestratorMode.IDLE


# T4 — deterministic create still works (0 LLM) ────────────────────────────

@pytest.mark.parametrize(
    "phrase",
    [
        "nuevo",  # path: _handle_global_commands NEW_PROJECT_WORDS shortcut
        "quiero diseñar un dron",  # path: IntentResolver "create_project" → resolve_action_request
    ],
)
def test_t4_deterministic_create_still_opens_wizard(tmp_path: Path, phrase):
    orch = _closed_project(tmp_path)

    result = orch.handle_user_text(phrase, _RefuseLLM())  # interpret/analyze would raise

    assert result["status"] == "interactive"
    assert _CREATE_WIZARD_COPY in result["message"]
    assert _mode(orch) == OrchestratorMode.CREATE_PROJECT_INTERACTIVE


# T5 — invalid_llm_output path unchanged ───────────────────────────────────

def test_t5_invalid_llm_output_keeps_error_path(tmp_path: Path):
    orch = _closed_project(tmp_path)
    llm = _StubInterpretLLM(
        "simulate", {"error": "invalid_llm_output", "message": "No se pudo interpretar la intención"}
    )

    result = orch.handle_user_text(_EXPLAIN_UNKNOWN, llm)

    assert result == {
        "status": "error",
        "error": "invalid_llm_output",
        "message": "No se pudo interpretar la intención",
    }
    assert llm.analyze_calls == []
    assert _mode(orch) == OrchestratorMode.IDLE


# Scope — no active project (Engineer 2026-10-16: guard is active-project only
# for the three new verbs; Bug 52 iterate stays unconditional) ─────────────

def test_no_project_unknown_create_project_still_reaches_handle(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    llm = _StubInterpretLLM("create_project")

    result = orch.handle_user_text("hablar", llm)

    assert result["status"] == "interactive"
    assert _CREATE_WIZARD_COPY in result["message"]
    assert llm.analyze_calls == []


def test_no_project_unknown_iterate_still_routes_to_analyze(tmp_path: Path):
    orch = JarvisOrchestrator(workspace_root=tmp_path)
    llm = _StubInterpretLLM("iterate", {"operacion": "increase", "variable": "payload_kg"})

    result = orch.handle_user_text("hablar", llm)

    assert result["action"] == "analyze"
    assert llm.analyze_calls == ["hablar"]
