from __future__ import annotations

import json
from pathlib import Path

from jarvis.schemas.action_schema import InteractiveSessionState, OrchestratorMode
from jarvis.schemas.state_schema import ConversationTurn, HistoryEntry, ProjectState, RuntimeState

MAX_HISTORY_TURNS = 6

# U4: campos de InteractiveSessionState que tiene sentido restaurar tras un reinicio.
# Excluidos: dismissed_suggestions ("not persisted", doc), last_exploration_result
# (no serializable), project_draft / iteration_draft (wizards reinician solos),
# motor_suggestions, semantic_state, memory_context.
_PERSISTED_SESSION_FIELDS: frozenset[str] = frozenset({
    "mode",
    "step",
    "pending_define_missing",
    "pending_missing_params",
    "pending_missing_reason",
    "param_definition_reason",
    "pending_param_definitions",
    "collected_params",
})


class StateManager:
    def __init__(self) -> None:
        self.runtime_state = RuntimeState()

    def load(self, state_path: Path) -> ProjectState:
        state_path = Path(state_path).resolve()
        data = json.loads(state_path.read_text(encoding="utf-8"))
        # K2: normalizar alias de params legacy antes de validar el esquema.
        # 'motors' era la clave API de motor count antes de DA-MOTORS-3 (Fase 6).
        # workspace_manager.create_project_workspace() ya normaliza en proyectos nuevos,
        # pero proyectos guardados en disco antes de esa fase aún tienen 'motors'.
        # Normalizar aquí es idempotente y transparente para todos los callers.
        params = data.get("current_parameters")
        if isinstance(params, dict) and "motors" in params and "motor_count" not in params:
            params["motor_count"] = params.pop("motors")
        state = ProjectState.model_validate(data)
        return self._repair_workspace_path(state, state_path)

    @staticmethod
    def _repair_workspace_path(state: ProjectState, state_path: Path) -> ProjectState:
        """Derive workspace_path from the state.json location when stale or missing.

        Migrated projects may keep a legacy absolute path (e.g. old monorepo layout).
        Persistence uses state.workspace_path — a mismatch causes mkdir/PermissionError
        outside the real project tree. Repair is idempotent and persisted to disk.
        """
        actual = str(state_path.parent)
        stored = state.workspace_path
        needs_repair = False
        if not stored:
            needs_repair = True
        else:
            try:
                needs_repair = Path(stored).resolve() != state_path.parent
            except OSError:
                needs_repair = True
        if not needs_repair:
            return state

        repaired = state.model_copy(update={"workspace_path": actual})
        state_path.write_text(
            json.dumps(repaired.model_dump(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return repaired

    def load_active_project(
        self,
        workspace_manager,
        project_id: str | None = None,
        workspace_path: str | None = None,
        project_slug: str | None = None,
    ) -> ProjectState:
        state_path = workspace_manager.resolve_state_path(
            project_id=project_id,
            workspace_path=workspace_path,
            project_slug=project_slug,
        )
        return self.load(state_path)

    def get_runtime_session(self) -> InteractiveSessionState:
        return self.runtime_state.session

    def set_runtime_session(self, session: InteractiveSessionState) -> None:
        self.runtime_state = self.runtime_state.model_copy(update={"session": session})

    def clear_runtime_session(self) -> None:
        self.runtime_state = self.runtime_state.model_copy(
            update={
                "session": InteractiveSessionState(
                    mode=OrchestratorMode.IDLE,
                    step=0,
                    project_draft=None,
                    iteration_draft=None,
                )
            }
        )

    def append_conversation_turn(self, role: str, content: str) -> None:
        updated = list(self.runtime_state.conversation_history) + [
            ConversationTurn(role=role, content=content)
        ]
        if len(updated) > MAX_HISTORY_TURNS:
            updated = updated[-MAX_HISTORY_TURNS:]
        self.runtime_state = self.runtime_state.model_copy(
            update={"conversation_history": updated}
        )

    def clear_conversation_history(self) -> None:
        self.runtime_state = self.runtime_state.model_copy(
            update={"conversation_history": []}
        )

    # ── Runtime snapshot (U4) ──────────────────────────────────────────────

    def session_to_snapshot(self) -> dict:
        """U4: serializa los campos persistibles de la sesión activa."""
        return {
            k: v
            for k, v in self.runtime_state.session.model_dump().items()
            if k in _PERSISTED_SESSION_FIELDS
        }

    def restore_from_snapshot(self, snapshot: dict) -> None:
        """U4: restaura historial (≤ MAX_HISTORY_TURNS) y estado de sesión desde snapshot de disco."""
        raw_history = snapshot.get("conversation_history", [])
        history = [
            ConversationTurn(**t)
            for t in raw_history[-MAX_HISTORY_TURNS:]
            if isinstance(t, dict) and "role" in t and "content" in t
        ]
        self.runtime_state = self.runtime_state.model_copy(
            update={"conversation_history": history}
        )
        session_data = {
            k: v
            for k, v in snapshot.get("session", {}).items()
            if k in _PERSISTED_SESSION_FIELDS
        }
        if "mode" in session_data and not isinstance(session_data["mode"], OrchestratorMode):
            try:
                session_data["mode"] = OrchestratorMode(session_data["mode"])
            except ValueError:
                session_data["mode"] = OrchestratorMode.IDLE
        if session_data:
            restored_session = self.runtime_state.session.model_copy(update=session_data)
            self.runtime_state = self.runtime_state.model_copy(
                update={"session": restored_session}
            )

    def record_action(
        self,
        state: ProjectState,
        action: HistoryEntry,
        latest_results: dict,
        increment_iteration: bool = False,
    ) -> ProjectState:
        updated_history = [*state.history, action]
        # Extract the physical output scalar so it can be read directly
        # without coupling to the structure of latest_results.
        calculations = latest_results.get("calculations") or {}
        raw_mass = calculations.get("total_mass_kg")
        last_total_mass_kg = float(raw_mass) if raw_mass is not None else state.last_total_mass_kg
        return state.model_copy(
            update={
                "active_iteration": state.active_iteration + 1 if increment_iteration else state.active_iteration,
                "history": updated_history,
                "latest_results": latest_results,
                "last_total_mass_kg": last_total_mass_kg,
            }
        )
