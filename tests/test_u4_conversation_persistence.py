"""U4 — Persistencia del historial conversacional.

Tests:
  - save_runtime_snapshot escribe history/runtime_snapshot.json con las claves correctas
  - load_runtime_snapshot retorna None cuando no existe el archivo
  - El historial se trunca a MAX_CONVERSATION_SNAPSHOT (50) al guardar en disco
  - restore_from_snapshot restaura el historial en RuntimeState
  - restore_from_snapshot restaura el modo de sesión (p.ej. DEFINE_MISSING_PARAMETERS)
  - restore_from_snapshot es robusto ante datos corruptos / claves ausentes
  - El orchestrator persiste snapshot tras handle_user_text (integración)
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from jarvis.core.state_manager import MAX_HISTORY_TURNS, StateManager, _PERSISTED_SESSION_FIELDS
from jarvis.schemas.action_schema import InteractiveSessionState, OrchestratorMode
from jarvis.schemas.state_schema import ConversationTurn
from jarvis.workspace.workspace_manager import WorkspaceManager


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    """Workspace temporal con carpeta history/ ya creada (simula un proyecto activo)."""
    (tmp_path / "history").mkdir()
    return tmp_path


@pytest.fixture
def wm() -> WorkspaceManager:
    return WorkspaceManager()


# ── WorkspaceManager.save/load_runtime_snapshot ───────────────────────────────

def test_save_runtime_snapshot_creates_file(wm: WorkspaceManager, tmp_workspace: Path) -> None:
    """save_runtime_snapshot crea history/runtime_snapshot.json con las claves esperadas."""
    history = [{"role": "user", "content": "hola"}, {"role": "assistant", "content": "hola!"}]
    session = {"mode": "idle", "step": 0}

    wm.save_runtime_snapshot(tmp_workspace, history, session)

    snapshot_path = tmp_workspace / "history" / "runtime_snapshot.json"
    assert snapshot_path.exists(), "runtime_snapshot.json no fue creado"
    data = json.loads(snapshot_path.read_text())
    assert "conversation_history" in data
    assert "session" in data
    assert data["conversation_history"] == history
    assert data["session"] == session


def test_load_runtime_snapshot_returns_none_when_absent(wm: WorkspaceManager, tmp_workspace: Path) -> None:
    """load_runtime_snapshot retorna None si el archivo no existe."""
    result = wm.load_runtime_snapshot(tmp_workspace)
    assert result is None


def test_load_runtime_snapshot_returns_data_when_present(wm: WorkspaceManager, tmp_workspace: Path) -> None:
    """load_runtime_snapshot retorna el dict guardado."""
    payload = {"conversation_history": [], "session": {"mode": "idle"}}
    (tmp_workspace / "history" / "runtime_snapshot.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    result = wm.load_runtime_snapshot(tmp_workspace)
    assert result == payload


def test_load_runtime_snapshot_returns_none_on_corrupt_json(wm: WorkspaceManager, tmp_workspace: Path) -> None:
    """load_runtime_snapshot retorna None si el JSON está corrupto."""
    (tmp_workspace / "history" / "runtime_snapshot.json").write_text(
        "{ invalid json }", encoding="utf-8"
    )
    result = wm.load_runtime_snapshot(tmp_workspace)
    assert result is None


def test_save_truncates_history_to_max_snapshot(wm: WorkspaceManager, tmp_workspace: Path) -> None:
    """Al guardar 60 turns, el archivo solo contiene 50 (MAX_CONVERSATION_SNAPSHOT)."""
    history = [{"role": "user", "content": f"msg {i}"} for i in range(60)]
    wm.save_runtime_snapshot(tmp_workspace, history, {})

    data = json.loads((tmp_workspace / "history" / "runtime_snapshot.json").read_text())
    assert len(data["conversation_history"]) == 50, "Debe truncar a 50"
    # Los últimos 50 deben preservarse (no los primeros)
    assert data["conversation_history"][0]["content"] == "msg 10"
    assert data["conversation_history"][-1]["content"] == "msg 59"


# ── StateManager.session_to_snapshot / restore_from_snapshot ──────────────────

def test_session_to_snapshot_only_persisted_fields() -> None:
    """session_to_snapshot solo incluye _PERSISTED_SESSION_FIELDS."""
    sm = StateManager()
    snapshot = sm.session_to_snapshot()
    assert set(snapshot.keys()) <= _PERSISTED_SESSION_FIELDS


def test_restore_from_snapshot_loads_history() -> None:
    """restore_from_snapshot rellena conversation_history en RuntimeState."""
    sm = StateManager()
    snapshot = {
        "conversation_history": [
            {"role": "user", "content": "definir motor"},
            {"role": "assistant", "content": "¿Cuántos vatios?"},
        ],
        "session": {},
    }
    sm.restore_from_snapshot(snapshot)

    history = sm.runtime_state.conversation_history
    assert len(history) == 2
    assert isinstance(history[0], ConversationTurn)
    assert history[0].role == "user"
    assert history[1].content == "¿Cuántos vatios?"


def test_restore_from_snapshot_restores_session_mode() -> None:
    """restore_from_snapshot restaura el modo de sesión guardado."""
    sm = StateManager()
    snapshot = {
        "conversation_history": [],
        "session": {
            "mode": OrchestratorMode.DEFINE_MISSING_PARAMETERS.value,
            "step": 2,
            "pending_define_missing": True,
            "pending_missing_params": ["motor_power_w"],
            "pending_missing_reason": "MISSING_COMPONENT_DEFINITION",
        },
    }
    sm.restore_from_snapshot(snapshot)

    session = sm.runtime_state.session
    assert session.mode == OrchestratorMode.DEFINE_MISSING_PARAMETERS
    assert session.step == 2
    assert session.pending_define_missing is True
    assert session.pending_missing_params == ["motor_power_w"]


def test_restore_truncates_history_to_max_turns() -> None:
    """restore_from_snapshot carga solo los últimos MAX_HISTORY_TURNS (≤ 6)."""
    sm = StateManager()
    # Disco puede tener hasta 50; en memoria solo cargamos MAX_HISTORY_TURNS
    turns = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
    sm.restore_from_snapshot({"conversation_history": turns, "session": {}})

    history = sm.runtime_state.conversation_history
    assert len(history) == MAX_HISTORY_TURNS
    assert history[-1].content == "msg 19"  # los últimos


def test_restore_from_snapshot_robust_on_empty_snapshot() -> None:
    """restore_from_snapshot no falla con snapshot vacío o sin claves."""
    sm = StateManager()
    sm.restore_from_snapshot({})  # no debe lanzar excepción
    assert sm.runtime_state.conversation_history == []


def test_restore_ignores_non_persisted_fields() -> None:
    """restore_from_snapshot no escribe campos no persistibles (p.ej. dismissed_suggestions)."""
    sm = StateManager()
    snapshot = {
        "conversation_history": [],
        "session": {
            "mode": "idle",
            "dismissed_suggestions": ["sugerencia_a", "sugerencia_b"],  # no persisted
        },
    }
    sm.restore_from_snapshot(snapshot)
    # dismissed_suggestions debe quedar en su valor por defecto (lista vacía)
    assert sm.runtime_state.session.dismissed_suggestions == []
