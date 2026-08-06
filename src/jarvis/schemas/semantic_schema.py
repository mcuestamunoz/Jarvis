from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SlotValue(BaseModel):
    value: str | None = None
    confidence: float = 0.0
    source: Literal["explicit", "inferred", "confirmed"] = "inferred"


class SemanticState(BaseModel):
    """Estado semántico de runtime. NUNCA se persiste en state.json."""

    intent: str | None = None
    intent_confidence: float = 0.0
    slots: dict[str, SlotValue] = Field(default_factory=dict)
    missing_slots: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    history: list[str] = Field(default_factory=list)
    clarification_round: int = 0
    forced: bool = False
    focus: str | None = None
    entities: list[str] = Field(default_factory=list)
    active_intent: str | None = None

    def get_slot_value(self, name: str) -> str | None:
        slot = self.slots.get(name)
        return slot.value if slot else None

    def get_slot_confidence(self, name: str) -> float:
        slot = self.slots.get(name)
        return slot.confidence if slot else 0.0
