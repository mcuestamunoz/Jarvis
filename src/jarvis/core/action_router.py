from __future__ import annotations

from jarvis.actions.calculate import CalculateAction
from jarvis.actions.create_project import CreateProjectAction
from jarvis.actions.iterate import IterateAction
from jarvis.actions.simulate import SimulateAction
from jarvis.schemas.action_schema import ActionName


class ActionRouter:
    def __init__(
        self,
        create_project_action: CreateProjectAction,
        iterate_action: IterateAction,
        calculate_action: CalculateAction,
        simulate_action: SimulateAction,
    ) -> None:
        self._routes = {
            ActionName.CREATE_PROJECT: create_project_action,
            ActionName.CALCULATE: calculate_action,
            ActionName.SIMULATE: simulate_action,
            ActionName.ITERATE: iterate_action,
        }

    def resolve(self, action_name: ActionName):
        try:
            return self._routes[action_name]
        except KeyError as error:
            raise ValueError(f"Acción no soportada: {action_name}") from error
