from __future__ import annotations

from jarvis.core.parameter_requirements import PARAMETER_REQUIREMENTS
from jarvis.llm.errors import LLMResponseValidationError
from jarvis.schemas.action_schema import (
    ActionName,
    LLMActionRequest,
    LLMRequestMode,
    OrchestratorMode,
)
from jarvis.schemas.state_schema import RuntimeState


class ActionPolicy:
    ALLOWED_ACTIONS = {
        ActionName.CREATE_PROJECT,
        ActionName.ITERATE,
        ActionName.CALCULATE,
        ActionName.SIMULATE,
    }

    ALLOWED_IN_SESSION = {
        OrchestratorMode.CREATE_PROJECT_INTERACTIVE: {ActionName.CREATE_PROJECT},
        OrchestratorMode.ITERATE_INTERACTIVE: {ActionName.ITERATE},
    }

    REQUIRES_INTERACTIVE_MODE = {
        OrchestratorMode.CREATE_PROJECT_INTERACTIVE: {ActionName.CREATE_PROJECT},
        OrchestratorMode.ITERATE_INTERACTIVE: {ActionName.ITERATE},
    }

    MIN_REQUIRED_FIELDS = {
        ActionName.CREATE_PROJECT: set(),
        ActionName.ITERATE: set(),
        ActionName.CALCULATE: set(),
        ActionName.SIMULATE: set(),
    }

    def validate(self, request: LLMActionRequest, runtime_state: RuntimeState) -> LLMActionRequest:
        self._validate_allowed_action(request)
        self._validate_required_project(request, runtime_state)
        self._validate_min_required_fields(request)
        self._validate_session_rules(request, runtime_state)
        self._validate_iterate_variable(request)
        return request

    def _validate_allowed_action(self, request: LLMActionRequest) -> None:
        if request.action not in self.ALLOWED_ACTIONS:
            raise LLMResponseValidationError(f"Acción no soportada por la policy: {request.action.value}")

    def _validate_required_project(self, request: LLMActionRequest, runtime_state: RuntimeState) -> None:
        # Project resolution is the orchestrator's responsibility, not the policy's.
        # The orchestrator resolves the active project before opening any interactive
        # session, so by the time validate() runs, the project context is already set.
        return

    def _validate_min_required_fields(self, request: LLMActionRequest) -> None:
        required_fields = self.MIN_REQUIRED_FIELDS.get(request.action, set())
        missing = [field for field in required_fields if not self._has_field(request, field)]
        if missing:
            raise LLMResponseValidationError(
                f"Faltan campos mínimos para {request.action.value}: {', '.join(missing)}."
            )

    def _validate_session_rules(self, request: LLMActionRequest, runtime_state: RuntimeState) -> None:
        session_mode = runtime_state.session.mode
        if session_mode == OrchestratorMode.IDLE:
            return

        allowed_actions = self.ALLOWED_IN_SESSION.get(session_mode, set())
        if request.action not in allowed_actions:
            raise LLMResponseValidationError(
                f"Hay una sesión activa en modo {session_mode.value}; "
                f"solo se permite {', '.join(action.value for action in allowed_actions)}."
            )

        requires_interactive = self.REQUIRES_INTERACTIVE_MODE.get(session_mode, set())
        if request.action in requires_interactive and request.mode != LLMRequestMode.INTERACTIVE:
            raise LLMResponseValidationError(
                f"La acción {request.action.value} requiere mode=interactive dentro de la sesión activa."
            )

        if not request.raw_user_input and "answer" not in request.parameters:
            raise LLMResponseValidationError(
                "Con una sesión activa, el LLM debe responder dentro del flujo actual "
                "usando raw_user_input o parameters.answer."
            )

    def _has_field(self, request: LLMActionRequest, field_name: str) -> bool:
        direct_value = getattr(request, field_name, None)
        if direct_value not in (None, "", {}):
            return True
        return field_name in request.parameters and request.parameters[field_name] not in (None, "", {})

    def _validate_iterate_variable(self, request: LLMActionRequest) -> None:
        """When action=iterate and parameters.variable is present, reject unknown variables.

        Derived variables pass here — the SemanticIntentAdapter handles them with a
        richer message.  This layer only rejects variables that do not exist at all
        in the registry, catching LLM hallucinations before they reach the wizard.
        """
        if request.action != ActionName.ITERATE:
            return
        variable = request.parameters.get("variable")
        if not variable:
            return
        if variable not in PARAMETER_REQUIREMENTS:
            raise LLMResponseValidationError(
                f"Variable '{variable}' no existe en el Action Space. "
                "Usa solo variables del registro de parámetros."
            )
