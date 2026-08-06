from __future__ import annotations

from jarvis.memory.history import build_conflict_type, latest_conflict_by_type
from jarvis.schemas.state_schema import ConflictRecord, ProjectMemory, ProjectState


class MemoryManager:
    def apply_conflict_resolution(
        self,
        state: ProjectState,
        *,
        initial_objective: str | None,
        initial_operation: str | None,
        conflicting_operation: str | None,
        resolution: str,
    ) -> ProjectState:
        conflict_type = build_conflict_type(initial_objective, initial_operation)
        record = ConflictRecord(
            conflict_type=conflict_type,
            initial_objective=initial_objective,
            initial_operation=initial_operation,
            conflicting_operation=conflicting_operation,
            resolution=resolution,
        )
        memory = state.memory.model_copy(
            update={
                "preferences": self._updated_preferences(
                    state.memory.preferences,
                    initial_objective=initial_objective,
                    initial_operation=initial_operation,
                    conflicting_operation=conflicting_operation,
                    resolution=resolution,
                ),
                "conflict_history": [*state.memory.conflict_history, record],
            }
        )
        return state.model_copy(update={"memory": memory})

    def latest_conflict_hint(self, memory: ProjectMemory, *, initial_objective: str | None, initial_operation: str | None) -> str | None:
        conflict_type = build_conflict_type(initial_objective, initial_operation)
        previous = latest_conflict_by_type(memory, conflict_type)
        if previous is None:
            return None
        resolution_label = {
            "keep_initial_goal": "mantener el objetivo inicial",
            "apply_new_change": "aplicar el nuevo cambio",
            "cancel_iteration": "cancelar la iteración",
        }.get(previous.resolution, previous.resolution)
        return f"En un conflicto similar anterior elegiste {resolution_label}."

    def _updated_preferences(
        self,
        preferences: dict[str, bool],
        *,
        initial_objective: str | None,
        initial_operation: str | None,
        conflicting_operation: str | None,
        resolution: str,
    ) -> dict[str, bool]:
        updated = dict(preferences)
        if initial_objective == "peso" and resolution == "keep_initial_goal":
            updated["prioritize_weight_reduction"] = True
        if (
            initial_objective == "carga"
            and initial_operation == "aumentar"
            and conflicting_operation == "reducir"
            and resolution == "apply_new_change"
        ):
            updated["rejects_payload_increase"] = True
        return updated
