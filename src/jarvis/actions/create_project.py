from __future__ import annotations

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.state_manager import StateManager
from jarvis.knowledge.library import ComponentLibrary, default_library
from jarvis.schemas.action_schema import ActionName, CreateProjectParams
from jarvis.schemas.state_schema import HistoryEntry
from jarvis.simulation.simulator import FlightSimulator
from jarvis.suggestions.suggestion_engine import SuggestionEngine
from jarvis.workspace.workspace_manager import WorkspaceManager

_DEFAULT_MATERIAL = "aluminio"


class CreateProjectAction:
    def __init__(
        self,
        workspace_manager: WorkspaceManager,
        state_manager: StateManager,
        simulator: FlightSimulator,
        calculation_engine: CalculationEngine,
        suggestion_engine: SuggestionEngine,
    ) -> None:
        self.workspace_manager = workspace_manager
        self.state_manager = state_manager
        self.simulator = simulator
        self.calculation_engine = calculation_engine
        self.suggestion_engine = suggestion_engine
        self.library: ComponentLibrary = default_library

    def run(self, parameters: dict) -> dict:
        params = CreateProjectParams.model_validate(parameters)
        project_path, state = self.workspace_manager.create_project_workspace(params)
        # Validate default material exists in library — hard error on init failure
        try:
            material_spec = self.library.get_material(_DEFAULT_MATERIAL)
        except KeyError as exc:
            raise RuntimeError(
                f"Error de inicialización: el material por defecto '{_DEFAULT_MATERIAL}' "
                f"no está en la biblioteca. Revisa library/materiales/_datos.json."
            ) from exc
        state.design_properties.structure.material = material_spec.name
        state.design_properties.structure.density = material_spec.density_kg_m3
        state.design_properties.structure.volume = 1.0
        calculations = self.calculation_engine.build(state.current_parameters)
        autonomy_threshold = state.parsed_constraints.get("autonomy_min")
        simulation = self.simulator.evaluate(calculations, autonomy_threshold=autonomy_threshold)
        suggestions = self.suggestion_engine.generate_suggestions(simulation, calculations)

        simulation_path = self.workspace_manager.save_simulation(
            project_path,
            0,
            simulation.model_dump(),
        )
        iteration_path = self.workspace_manager.save_iteration_snapshot(
            project_path,
            0,
            {
                "iteration_id": 0,
                "event": "create_project",
                "objective": params.objective,
                "vehicle_type": params.vehicle_type,
                "restrictions": params.restrictions,
                "detail_level": params.detail_level,
                "calculations": calculations.model_dump(),
                "simulation": simulation.model_dump(),
                "design_properties": state.design_properties.model_dump(),
                "current_parameters": state.current_parameters,
            },
        )

        history_entry = HistoryEntry(
            action=ActionName.CREATE_PROJECT,
            summary="Proyecto creado con cálculo base y simulación inicial.",
            artifacts={
                "simulation": str(simulation_path),
                "iteration": str(iteration_path),
            },
        )
        seeded_state = state.model_copy(update={"current_parameters": state.current_parameters})
        updated_state = self.state_manager.record_action(
            state=seeded_state,
            action=history_entry,
            latest_results={
                "calculations": calculations.model_dump(),
                "simulation": simulation.model_dump(),
            },
            increment_iteration=True,
        )
        self.workspace_manager.save_state(updated_state)
        self.workspace_manager.append_event(
            project_path,
            "create_project",
            {"project_id": updated_state.project_id, "objective": params.objective},
        )
        self.workspace_manager.render_views(project_path, updated_state)

        return {
            "status": "ok",
            "action": ActionName.CREATE_PROJECT.value,
            "project_id": updated_state.project_id,
            "workspace_path": str(project_path),
            "state": updated_state.model_dump(),
            "calculations": calculations.model_dump(),
            "simulation": simulation.model_dump(),
            "suggestions": [suggestion.model_dump() for suggestion in suggestions],
        }
