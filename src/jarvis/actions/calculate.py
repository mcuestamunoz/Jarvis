from __future__ import annotations

from pathlib import Path

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.endurance_sweep_writer import build_with_estimative_sweep
from jarvis.core.state_manager import StateManager
from jarvis.schemas.action_schema import ActionName
from jarvis.schemas.state_schema import HistoryEntry
from jarvis.workspace.workspace_manager import WorkspaceManager


class CalculateAction:
    def __init__(
        self,
        workspace_manager: WorkspaceManager,
        state_manager: StateManager,
        calculation_engine: CalculationEngine,
    ) -> None:
        self.workspace_manager = workspace_manager
        self.state_manager = state_manager
        self.calculation_engine = calculation_engine

    def run(self, parameters: dict) -> dict:
        project_state = self.state_manager.load_active_project(
            self.workspace_manager,
            project_id=parameters.get("project_id"),
            workspace_path=parameters.get("workspace_path"),
            project_slug=parameters.get("project_slug"),
        )
        calculations = build_with_estimative_sweep(
            self.calculation_engine, project_state.current_parameters,
        )
        workspace_path = Path(project_state.workspace_path)
        action_index = len(project_state.history)
        calculations_path = self.workspace_manager.save_calculation(
            workspace_path,
            action_index,
            calculations.model_dump(),
        )

        history_entry = HistoryEntry(
            action=ActionName.CALCULATE,
            summary="Recalculo ejecutado sobre el proyecto actual.",
            artifacts={"calculations": str(calculations_path)},
        )
        latest_results = dict(project_state.latest_results)
        latest_results["calculations"] = calculations.model_dump()
        updated_state = self.state_manager.record_action(
            state=project_state,
            action=history_entry,
            latest_results=latest_results,
            increment_iteration=False,
        )
        self.workspace_manager.save_state(updated_state)
        self.workspace_manager.append_event(
            workspace_path,
            "calculate",
            {"calc_id": action_index},
        )
        self.workspace_manager.render_views(workspace_path, updated_state)

        return {
            "status": "ok",
            "action": ActionName.CALCULATE.value,
            "project_id": updated_state.project_id,
            "workspace_path": updated_state.workspace_path,
            "calculations": calculations.model_dump(),
            "state": updated_state.model_dump(),
        }
