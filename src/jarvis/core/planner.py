from __future__ import annotations

from typing import Any

from jarvis.schemas.action_schema import (
    ActionName,
    ExecutionPlan,
    ExecutionType,
    PlanStep,
)


class PlanValidationError(ValueError):
    """Raised when a generated plan is inconsistent with the execution context."""


def requires_planning(goal: str | ActionName) -> bool:
    normalized_goal = goal.value if isinstance(goal, ActionName) else goal
    return normalized_goal in Planner.COMPOSITE_GOALS


class Planner:
    COMPOSITE_GOALS = {
        "create_and_simulate",
        "recalculate_and_simulate",
        "iterate_and_validate",
    }

    def requires_planning(self, goal: str | ActionName) -> bool:
        return requires_planning(goal)

    def generate(self, goal: str | ActionName, context: dict[str, Any] | None = None) -> ExecutionPlan:
        normalized_goal = goal.value if isinstance(goal, ActionName) else goal
        build_context = context or {}

        if normalized_goal == "create_and_simulate":
            plan = ExecutionPlan(
                goal=normalized_goal,
                project_id=build_context.get("project_id"),
                execution_type=ExecutionType.SEQUENCE,
                steps=[
                    PlanStep(
                        step_id="step_1",
                        action=ActionName.CREATE_PROJECT,
                        description="Crear el proyecto base.",
                    ),
                    PlanStep(
                        step_id="step_2",
                        action=ActionName.SIMULATE,
                        description="Simular el proyecto creado.",
                    ),
                ],
            )
        elif normalized_goal == "recalculate_and_simulate":
            plan = ExecutionPlan(
                goal=normalized_goal,
                project_id=build_context.get("project_id"),
                execution_type=ExecutionType.SEQUENCE,
                steps=[
                    PlanStep(
                        step_id="step_1",
                        action=ActionName.CALCULATE,
                        description="Recalcular el estado actual del proyecto.",
                    ),
                    PlanStep(
                        step_id="step_2",
                        action=ActionName.SIMULATE,
                        description="Simular el proyecto tras el recálculo.",
                    ),
                ],
            )
        elif normalized_goal == "iterate_and_validate":
            plan = self._single_step_plan(ActionName.ITERATE, build_context, goal=normalized_goal)
        else:
            if normalized_goal in {action.value for action in ActionName}:
                raise PlanValidationError(
                    f"El planner v0 solo se usa para objetivos compuestos. "
                    f"'{normalized_goal}' debe ejecutarse directamente."
                )
            raise PlanValidationError(f"Goal compuesto no soportado por el planner v0: {normalized_goal}")

        self.validate_plan(plan, build_context)
        return plan

    def validate_plan(self, plan: ExecutionPlan, context: dict[str, Any] | None = None) -> ExecutionPlan:
        validation_context = context or {}
        has_project = bool(plan.project_id or validation_context.get("project_id"))
        creates_project_in_plan = any(step.action == ActionName.CREATE_PROJECT for step in plan.steps)

        for step in plan.steps:
            if step.action in {ActionName.CALCULATE, ActionName.SIMULATE, ActionName.ITERATE}:
                if not has_project and not creates_project_in_plan:
                    raise PlanValidationError(
                        f"La acción {step.action.value} requiere un proyecto activo en el contexto o en el plan."
                    )
            if step.action == ActionName.SIMULATE and plan.execution_type == ExecutionType.SINGLE and not has_project:
                raise PlanValidationError("No se puede simular sin project_id en un plan single.")

        return plan

    def _single_step_plan(
        self,
        action: ActionName,
        context: dict[str, Any],
        goal: str | None = None,
    ) -> ExecutionPlan:
        descriptions = {
            ActionName.CREATE_PROJECT: "Ejecutar create_project.",
            ActionName.CALCULATE: "Ejecutar calculate sobre el proyecto actual.",
            ActionName.SIMULATE: "Ejecutar simulate sobre el proyecto actual.",
            ActionName.ITERATE: "Ejecutar iterate como pipeline único del sistema.",
        }
        return ExecutionPlan(
            goal=goal or action.value,
            project_id=context.get("project_id"),
            execution_type=ExecutionType.SINGLE,
            steps=[
                PlanStep(
                    step_id="step_1",
                    action=action,
                    description=descriptions[action],
                )
            ],
        )
