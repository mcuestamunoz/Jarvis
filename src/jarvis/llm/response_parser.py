from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from jarvis.llm.action_policy import ActionPolicy
from jarvis.llm.errors import LLMResponseValidationError
from jarvis.schemas.action_schema import (
    LLMActionRequest,
)
from jarvis.schemas.state_schema import RuntimeState


class LLMResponseParser:
    def __init__(self, action_policy: ActionPolicy | None = None) -> None:
        self.action_policy = action_policy or ActionPolicy()

    def parse(self, payload: str | dict[str, Any]) -> LLMActionRequest:
        try:
            normalized = json.loads(payload) if isinstance(payload, str) else payload
            return LLMActionRequest.model_validate(normalized)
        except json.JSONDecodeError as error:
            raise LLMResponseValidationError("La salida del LLM no es JSON válido.") from error
        except ValidationError as error:
            raise LLMResponseValidationError(f"Salida del LLM inválida: {error}") from error

    def validate_for_runtime(
        self,
        request: LLMActionRequest,
        runtime_state: RuntimeState,
    ) -> LLMActionRequest:
        return self.action_policy.validate(request, runtime_state)

    def to_action_request(self, request: LLMActionRequest) -> dict[str, Any]:
        parameters = dict(request.parameters)
        if request.project_id and "project_id" not in parameters:
            parameters["project_id"] = request.project_id
        return {
            "action": request.action.value,
            "parameters": parameters,
            "raw_user_input": request.raw_user_input,
        }
