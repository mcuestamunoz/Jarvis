"""Regression: runtime snapshot may restore mode as plain str."""
from __future__ import annotations

from jarvis.core.state_manager import StateManager
from jarvis.llm.prompt_builder import PromptBuilder
from jarvis.schemas.action_schema import OrchestratorMode
from jarvis.schemas.state_schema import RuntimeState


def test_restore_from_snapshot_coerces_mode_string():
    sm = StateManager()
    sm.restore_from_snapshot({"session": {"mode": "idle", "step": 0}})
    assert sm.get_runtime_session().mode == OrchestratorMode.IDLE
    assert isinstance(sm.get_runtime_session().mode, OrchestratorMode)


def test_prompt_builder_accepts_string_mode():
    runtime = RuntimeState()
    # Simulate corrupted/legacy session mode without going through restore
    runtime = runtime.model_copy(
        update={"session": runtime.session.model_copy(update={"mode": "idle"})}  # type: ignore[arg-type]
    )
    # Force string if model_copy coerced it back
    object.__setattr__(runtime.session, "mode", "idle")
    messages = PromptBuilder().build_messages("hola", runtime)
    assert "mode=idle" in messages[0]["content"]
