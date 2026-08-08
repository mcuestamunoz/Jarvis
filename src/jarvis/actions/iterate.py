from __future__ import annotations

from pathlib import Path

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.component_resolver import resolve_propulsion_parameters
from jarvis.core.mutation_engine import MutationEngine
from jarvis.core.parameter_requirements import (
    MISSING_PROPELLER_PARAMETERS,
    PARAMETER_REQUIREMENTS,
    REQUIREMENT_REASONS,
)
from jarvis.core.reasoning_layer import ReasoningLayer
from jarvis.core.state_manager import StateManager
from jarvis.schemas.action_schema import ActionName, IterationDraft, IterationOperation
from jarvis.schemas.state_schema import DesignProperties, HistoryEntry
from jarvis.schemas.tool_schema import CalculationBundle, SimulationResult
from jarvis.simulation.simulator import FlightSimulator
from jarvis.suggestions.suggestion_engine import SuggestionEngine
from jarvis.workspace.workspace_manager import WorkspaceManager


def _propulsion_passive_hint(draft: IterationDraft, current_parameters: dict | None = None) -> str | None:
    """Return a next-step hint when a propulsion_passive component has been defined.

    The message is built from the parameter catalog so the hint stays in sync
    with any future changes to labels or examples — no hardcoded strings.
    Returns None when the draft does not contain a propulsion_passive component,
    or when all required propeller parameters are already present in current_parameters.
    """
    patch = draft.component_patch or {}
    has_propulsion_passive = any(
        spec.component_type == "propulsion_passive"
        for spec in patch.values()
    )
    if not has_propulsion_passive:
        return None

    reason = REQUIREMENT_REASONS.get(MISSING_PROPELLER_PARAMETERS)
    if reason is None:
        return None

    # Suppress hint if all required params are already defined
    params = current_parameters or {}
    missing = [p for p in reason.required_params if p not in params]
    if not missing:
        return None

    param_lines: list[str] = []
    for param_name in missing:
        req = PARAMETER_REQUIREMENTS.get(param_name)
        if req:
            param_lines.append(f"  • {param_name} ({req.hint})")
        else:
            param_lines.append(f"  • {param_name}")

    lines = [
        "Para conectar esta hélice al modelo físico necesito:",
        *param_lines,
        "Di 'definir parámetros de hélice' cuando estés listo.",
    ]
    return "\n".join(lines)


class IterateAction:
    def __init__(
        self,
        workspace_manager: WorkspaceManager,
        state_manager: StateManager,
        simulator: FlightSimulator,
        calculation_engine: CalculationEngine,
        mutation_engine: MutationEngine,
        suggestion_engine: SuggestionEngine,
        reasoning_layer: ReasoningLayer,
    ) -> None:
        self.workspace_manager = workspace_manager
        self.state_manager = state_manager
        self.simulator = simulator
        self.calculation_engine = calculation_engine
        self.mutation_engine = mutation_engine
        self.suggestion_engine = suggestion_engine
        self.reasoning_layer = reasoning_layer

    def run(self, parameters: dict) -> dict:
        draft = IterationDraft.model_validate(parameters["iteration_draft"])
        project_state = self.state_manager.load_active_project(
            self.workspace_manager,
            project_id=draft.project_id,
            workspace_path=draft.workspace_path,
            project_slug=draft.project_slug,
        )

        mutable_state = self._build_mutable_state(project_state)

        # ── Pre-execution validation (Bug 25 guard) ────────────────────────────
        # A physical (non-DEFINE) draft that cannot be routed to a deterministic
        # mutation strategy must be caught here — before any state mutation or
        # calculation occurs — and degraded to a clarification request.
        if draft.operation != IterationOperation.DEFINE and not self.mutation_engine.is_physically_actionable(draft):
            return {
                "status": "definition",
                "action": ActionName.ITERATE.value,
                "project_id": project_state.project_id,
                "workspace_path": project_state.workspace_path,
                "message": (
                    "No se encontró una estrategia de mutación física para la iteración solicitada. "
                    "Especifica qué variable concreta quieres modificar "
                    "(material, dimensiones, carga útil, etc.)."
                ),
                "iteration_draft": draft.model_dump(),
            }
        # ──────────────────────────────────────────────────────────────────────

        # ── Bug 1/2 guard: volume strategy without a concrete value ───────────
        # apply_volume_mutation applies a fixed arbitrary factor (−10%) whenever
        # the strategy resolves to "volumen". Without a user-specified value there
        # is no physical model to justify that number. Degrade to declarative here
        # so the user can either provide a concrete parameter or confirm the intent
        # as a design note.
        #
        # Material: excluded — apply_material_mutation already hard-gates on value.
        # Payload:  excluded — only needs operation direction (reduce/increase).
        # Numeric:  excluded — wizard sets draft.value explicitly before routing.
        if draft.operation != IterationOperation.DEFINE and self.mutation_engine.needs_concrete_value(draft):
            return {
                "status": "definition",
                "action": ActionName.ITERATE.value,
                "project_id": project_state.project_id,
                "workspace_path": project_state.workspace_path,
                "message": (
                    "La iteración estructural no especifica un valor concreto. "
                    "Se requiere un parámetro numérico explícito para calcular impacto físico "
                    "(ej: 'factor de estructura 0.4'). "
                    "Puedes registrar esta intención como declarativa si confirmas."
                ),
                "iteration_draft": draft.model_dump(),
            }
        # ──────────────────────────────────────────────────────────────────────

        mutated_state, impact = self.mutation_engine.apply_mutation(mutable_state, draft)

        if draft.operation == IterationOperation.DEFINE:
            return self._run_declarative_iteration(project_state, draft, mutated_state, impact)

        updated_parameters = self._apply_mutation_to_parameters(project_state.current_parameters, mutated_state)
        updated_design_properties = self._apply_design_property_mutation(project_state.design_properties, mutated_state)

        # FN-004: substituting defined motor_count requires explicit Sí/No
        if not parameters.get("structural_confirmed"):
            from jarvis.core.param_definition_session import (
                begin_structural_confirm,
                structural_confirm_needed,
            )

            needed = structural_confirm_needed(
                project_state.current_parameters,
                updated_parameters.get("motor_count"),
            )
            if needed:
                old_f, new_f = needed
                margin = None
                sim = (project_state.latest_results or {}).get("simulation") or {}
                if isinstance(sim, dict) and sim.get("safety_margin_ratio") is not None:
                    margin = float(sim["safety_margin_ratio"])
                impact_note = ""
                if margin is not None:
                    impact_note = f" Margen de seguridad actual: {margin:.2f}."
                return begin_structural_confirm(
                    self.state_manager,
                    param="motor_count",
                    from_value=old_f,
                    to_value=new_f,
                    updates={"motor_count": new_f},
                    impact_note=impact_note,
                    resume_kind="iterate",
                    resume_iteration_draft=draft.model_dump(),
                )

        # Resolve propulsion overrides from declarative component specs (ephemeral — not persisted)
        propulsion_override = resolve_propulsion_parameters(
            {k: v.model_dump() for k, v in project_state.design_properties.components.items()}
        )
        updated_parameters = propulsion_override.apply_to(updated_parameters)

        calculations = self.calculation_engine.build(updated_parameters)
        autonomy_threshold = project_state.parsed_constraints.get("autonomy_min")
        simulation = self.simulator.evaluate(calculations, autonomy_threshold=autonomy_threshold)
        suggestions = self.suggestion_engine.generate_suggestions(simulation, calculations)
        suggestions_payload = [suggestion.model_dump() for suggestion in suggestions]
        reasoning = self.reasoning_layer.build(
            {
                "objective": project_state.objective,
                "current_parameters": updated_parameters,
                "design_properties": updated_design_properties.model_dump(),
                "last_calculation": calculations.model_dump(),
                "last_simulation": simulation.model_dump(),
                "memory": project_state.memory.model_dump(),
                "last_mutation": {"mode": "physical"},
                "mutation_mode": "physical",
            },
            suggestions=suggestions_payload,
        )

        workspace_path = Path(project_state.workspace_path)
        iteration_index = project_state.active_iteration
        iteration_path = self.workspace_manager.save_iteration_snapshot(
            workspace_path,
            iteration_index,
            {
                "iteration_id": iteration_index,
                "event": "iterate",
                "change": {
                    "objective": draft.objective,
                    "variable": draft.variable,
                    "operation": draft.operation.value if hasattr(draft.operation, "value") else draft.operation,
                    "strategy": draft.strategy,
                    "restrictions": draft.restrictions,
                },
                "mutation": mutated_state,
                "impact": impact,
                "calculations": calculations.model_dump(),
                "simulation": simulation.model_dump(),
                "design_properties": updated_design_properties.model_dump(),
                "current_parameters": updated_parameters,
            },
        )

        history_entry = HistoryEntry(
            action=ActionName.ITERATE,
            summary=f"Iteración aplicada sobre {draft.variable or draft.strategy or draft.objective}.",
            artifacts={"iteration": str(iteration_path)},
        )
        updated_state = self.state_manager.record_action(
            state=project_state.model_copy(update={
                "current_parameters": updated_parameters,
                "design_properties": updated_design_properties,
            }),
            action=history_entry,
            latest_results={
                "mutation": {
                    "state_patch": mutated_state,
                    "impact": impact,
                    "draft": draft.model_dump(),
                },
                "calculations": calculations.model_dump(),
                "simulation": simulation.model_dump(),
            },
            increment_iteration=True,
        )
        self.workspace_manager.save_state(updated_state)
        self.workspace_manager.append_event(
            workspace_path,
            "iterate",
            {"iteration_id": iteration_index, "variable": draft.variable, "operation": draft.operation.value if hasattr(draft.operation, "value") else draft.operation},
        )
        self.workspace_manager.render_views(workspace_path, updated_state, reasoning.model_dump())

        return {
            "status": "ok",
            "action": ActionName.ITERATE.value,
            "project_id": updated_state.project_id,
            "workspace_path": updated_state.workspace_path,
            "iteration_draft": draft.model_dump(),
            "mutation": {
                "state_patch": mutated_state,
                "impact": impact,
            },
            "calculations": calculations.model_dump(),
            "simulation": simulation.model_dump(),
            "suggestions": suggestions_payload,
            "reasoning": reasoning.model_dump(),
            "propulsion_override_trace": propulsion_override.trace if propulsion_override.has_any else None,
            "state": updated_state.model_dump(),
        }

    def _run_declarative_iteration(self, project_state, draft: IterationDraft, mutated_state: dict, impact: dict) -> dict:
        workspace_path = Path(project_state.workspace_path)
        iteration_index = project_state.active_iteration
        updated_design_properties = self._apply_design_property_mutation(project_state.design_properties, mutated_state)
        calculations = self._resolve_existing_calculations(project_state)
        simulation = self._resolve_existing_simulation(project_state)
        suggestions = []
        suggestion_context_note = "No se generan sugerencias físicas automáticas en iteraciones declarativas."
        declarative_mutation = {
            "mode": "declarative",
            "state_patch": mutated_state,
            "impact": impact,
            "draft": draft.model_dump(),
        }
        reasoning = self.reasoning_layer.build(
            {
                "objective": project_state.objective,
                "current_parameters": project_state.current_parameters,
                "design_properties": updated_design_properties.model_dump(),
                "last_calculation": calculations.model_dump() if calculations is not None else None,
                "last_simulation": simulation.model_dump() if simulation is not None else None,
                "memory": project_state.memory.model_dump(),
                "last_mutation": declarative_mutation,
                "mutation_mode": "declarative",
            },
            suggestions=suggestions,
        )

        iteration_path = self.workspace_manager.save_iteration_snapshot(
            workspace_path,
            iteration_index,
            {
                "iteration_id": iteration_index,
                "event": "iterate_declarative",
                "change": {
                    "objective": draft.objective,
                    "variable": draft.variable,
                    "operation": draft.operation.value if hasattr(draft.operation, "value") else draft.operation,
                    "value": draft.value,
                    "restrictions": draft.restrictions,
                },
                "mutation": mutated_state,
                "design_properties": updated_design_properties.model_dump(),
                "current_parameters": project_state.current_parameters,
            },
        )

        history_entry = HistoryEntry(
            action=ActionName.ITERATE,
            summary=f"Propiedad de diseño definida sobre {draft.variable or draft.objective}.",
            artifacts={"iteration": str(iteration_path)},
        )
        latest_results = dict(project_state.latest_results)
        latest_results["mutation"] = declarative_mutation
        updated_state = self.state_manager.record_action(
            state=project_state.model_copy(update={"design_properties": updated_design_properties}),
            action=history_entry,
            latest_results=latest_results,
            increment_iteration=True,
        )
        self.workspace_manager.save_state(updated_state)
        self.workspace_manager.append_event(
            workspace_path,
            "iterate_declarative",
            {"iteration_id": iteration_index, "variable": draft.variable},
        )
        self.workspace_manager.render_views(workspace_path, updated_state, reasoning.model_dump())

        return {
            "status": "ok",
            "action": ActionName.ITERATE.value,
            "project_id": updated_state.project_id,
            "workspace_path": updated_state.workspace_path,
            "iteration_draft": draft.model_dump(),
            "mutation": {
                "state_patch": mutated_state,
                "impact": impact,
            },
            "message": "Propiedad del diseño definida. No se recalcula impacto físico en esta versión.",
            "next_step_hint": _propulsion_passive_hint(draft, project_state.current_parameters),
            "calculations": calculations.model_dump() if calculations is not None else None,
            "simulation": simulation.model_dump() if simulation is not None else None,
            "suggestions": suggestions,
            "suggestion_context_note": suggestion_context_note,
            "reasoning": reasoning.model_dump(),
            "state": updated_state.model_dump(),
        }

    def _build_mutable_state(self, project_state) -> dict:
        current = project_state.current_parameters
        structure = project_state.design_properties.structure
        payload_kg = float(current["payload_kg"])
        # Read the clean scalar field instead of digging into latest_results.
        # Falls back to payload_kg for projects that pre-date this field.
        total_mass_kg = float(project_state.last_total_mass_kg or payload_kg)

        # Fase 3 — Single Read Point: leer material de components["frame"] via getter canónico.
        # structure.material era el mirror legacy — ya no se usa aquí.
        from jarvis.utils.design_utils import get_frame_material
        material = get_frame_material(project_state.design_properties)
        densidad = float(structure.density or 1000.0)
        volumen = float(structure.volume or 1.0)

        return {
            "vehicle_type": current.get("vehicle_type", ""),
            "material": material,
            "densidad": densidad,
            "volumen": volumen,
            "payload_kg": payload_kg,
            "payload": payload_kg,
            "total_mass_kg": total_mass_kg,
            "masa_total": total_mass_kg,
            "design_properties": project_state.design_properties.model_dump(),
        }

    def _apply_mutation_to_parameters(self, current_parameters: dict, mutated_state: dict) -> dict:
        updated = dict(current_parameters)

        if "payload_kg" in mutated_state:
            updated["payload_kg"] = mutated_state["payload_kg"]
        elif "payload" in mutated_state:
            updated["payload_kg"] = mutated_state["payload"]

        total_mass = mutated_state.get("total_mass_kg", mutated_state.get("masa_total"))
        if total_mass is not None:
            payload_kg = float(updated["payload_kg"])
            updated["structure_mass_override_kg"] = round(max(float(total_mass) - payload_kg, 0.0), 4)

        # Direct current_parameters patch (e.g. from numeric param mutation)
        for key, val in mutated_state.get("current_parameters", {}).items():
            updated[key] = val
            # Patching structure_mass_factor makes the mass override stale — remove it
            if key == "structure_mass_factor" and "structure_mass_override_kg" in updated:
                del updated["structure_mass_override_kg"]

        return updated

    def _apply_design_property_mutation(self, current_design_properties: DesignProperties, mutated_state: dict) -> DesignProperties:
        updated = current_design_properties.model_dump()
        design_patch = mutated_state.get("design_properties", {})
        if "structure" in design_patch:
            updated.setdefault("structure", {}).update(design_patch["structure"])
        if "components" in design_patch:
            updated.setdefault("components", {}).update(design_patch["components"])
        # Route flat mutation keys to their canonical structure locations
        if "material" in mutated_state:
            updated.setdefault("structure", {})["material"] = mutated_state["material"]
        if "densidad" in mutated_state:
            updated.setdefault("structure", {})["density"] = mutated_state["densidad"]
        if "volumen" in mutated_state:
            updated.setdefault("structure", {})["volume"] = mutated_state["volumen"]
        return DesignProperties.model_validate(updated)

    def _resolve_existing_calculations(self, project_state) -> CalculationBundle | None:
        stored = project_state.latest_results.get("calculations")
        if stored is None:
            return None
        return CalculationBundle.model_validate(stored)

    def _resolve_existing_simulation(self, project_state) -> SimulationResult | None:
        stored = project_state.latest_results.get("simulation")
        if stored is None:
            return None
        return SimulationResult.model_validate(stored)
