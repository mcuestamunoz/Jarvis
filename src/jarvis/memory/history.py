from __future__ import annotations

from jarvis.schemas.state_schema import ConflictRecord, ProjectMemory


def build_conflict_type(initial_objective: str | None, initial_operation: str | None) -> str:
    if initial_objective == "peso":
        return "weight_direction_conflict"
    if initial_objective == "carga":
        return "payload_direction_conflict"
    if initial_operation in {"aumentar", "reducir"}:
        return "direction_conflict"
    return "generic_conflict"


def latest_conflict_by_type(memory: ProjectMemory, conflict_type: str) -> ConflictRecord | None:
    for record in reversed(memory.conflict_history):
        if record.conflict_type == conflict_type:
            return record
    return None
