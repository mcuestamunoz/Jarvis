from __future__ import annotations

from pathlib import Path

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.endurance_sweep_writer import build_with_estimative_sweep
from jarvis.core.reasoning_layer import ReasoningLayer
from jarvis.core.state_manager import StateManager
from jarvis.schemas.action_schema import ActionName
from jarvis.schemas.state_schema import HistoryEntry
from jarvis.schemas.tool_schema import CalculationBundle
from jarvis.simulation.simulator import FlightSimulator
from jarvis.suggestions.suggestion_engine import SuggestionEngine
from jarvis.workspace.workspace_manager import WorkspaceManager


class SimulateAction:
    def __init__(
        self,
        workspace_manager: WorkspaceManager,
        state_manager: StateManager,
        simulator: FlightSimulator,
        calculation_engine: CalculationEngine,
        suggestion_engine: SuggestionEngine,
        reasoning_layer: ReasoningLayer,
    ) -> None:
        self.workspace_manager = workspace_manager
        self.state_manager = state_manager
        self.simulator = simulator
        self.calculation_engine = calculation_engine
        self.suggestion_engine = suggestion_engine
        self.reasoning_layer = reasoning_layer

    def run(self, parameters: dict) -> dict:
        project_state = self.state_manager.load_active_project(
            self.workspace_manager,
            project_id=parameters.get("project_id"),
            workspace_path=parameters.get("workspace_path"),
            project_slug=parameters.get("project_slug"),
        )
        calculations = self._resolve_calculations(project_state)
        autonomy_threshold = project_state.parsed_constraints.get("autonomy_min")
        simulation = self.simulator.evaluate(calculations, autonomy_threshold=autonomy_threshold)
        suggestions = self.suggestion_engine.generate_suggestions(simulation, calculations)
        suggestions_payload = [suggestion.model_dump() for suggestion in suggestions]
        reasoning = self.reasoning_layer.build(
            {
                "objective": project_state.objective,
                "current_parameters": project_state.current_parameters,
                "design_properties": project_state.design_properties.model_dump(),
                "last_calculation": calculations.model_dump(),
                "last_simulation": simulation.model_dump(),
                "memory": project_state.memory.model_dump(),
                "last_mutation": project_state.latest_results.get("mutation"),
                "mutation_mode": None,
            },
            suggestions=suggestions_payload,
        )
        workspace_path = Path(project_state.workspace_path)
        action_index = len(project_state.history)
        simulation_path = self.workspace_manager.save_simulation(
            workspace_path,
            action_index,
            simulation.model_dump(),
        )

        history_entry = HistoryEntry(
            action=ActionName.SIMULATE,
            summary="Simulación ejecutada sobre el proyecto actual.",
            artifacts={"simulation": str(simulation_path)},
        )
        latest_results = dict(project_state.latest_results)
        latest_results["calculations"] = calculations.model_dump()
        latest_results["simulation"] = simulation.model_dump()
        updated_state = self.state_manager.record_action(
            state=project_state,
            action=history_entry,
            latest_results=latest_results,
            increment_iteration=False,
        )
        self.workspace_manager.save_state(updated_state)
        self.workspace_manager.append_event(
            workspace_path,
            "simulation",
            {"sim_id": action_index, "status": simulation.status},
        )
        self.workspace_manager.render_views(workspace_path, updated_state, reasoning.model_dump())

        return {
            "status": "ok",
            "action": ActionName.SIMULATE.value,
            "project_id": updated_state.project_id,
            "workspace_path": updated_state.workspace_path,
            "calculations": calculations.model_dump(),
            "simulation": simulation.model_dump(),
            "suggestions": suggestions_payload,
            "reasoning": reasoning.model_dump(),
            "state": updated_state.model_dump(),
        }

    def _resolve_calculations(self, project_state) -> CalculationBundle:
        stored = project_state.latest_results.get("calculations")
        if stored:
            return CalculationBundle.model_validate(stored)
        return build_with_estimative_sweep(
            self.calculation_engine, project_state.current_parameters,
        )
