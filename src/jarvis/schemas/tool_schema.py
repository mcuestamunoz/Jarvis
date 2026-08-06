from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    tool_name: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)


class CalculationBundle(BaseModel):
    vehicle_type: str
    payload_kg: float
    structure_mass_kg: float
    total_mass_kg: float
    weight_n: float
    required_thrust_n: float
    motors: int | None
    thrust_per_motor_required_n: float | None
    available_total_thrust_n: float | None
    autonomy_min: float | None = None
    tool_results: list[ToolResult] = Field(default_factory=list)

    # Generic aliases
    @property
    def actuator_count(self) -> int | None:
        return self.motors

    @property
    def required_force_n(self) -> float:
        return self.required_thrust_n

    @property
    def available_total_force_n(self) -> float:
        return self.available_total_thrust_n

    @property
    def force_per_actuator_required_n(self) -> float | None:
        return self.thrust_per_motor_required_n


class SimulationAnalysis(BaseModel):
    available_thrust_n: float | None
    required_thrust_n: float
    weight_n: float
    per_motor_load_ratio: float


PhysicsStatus = Literal["valid", "missing_parameters"]
EnergyStatus = Literal["valid", "missing_energy_parameters"]
PropellerStatus = Literal["valid", "missing_propeller_parameters"]


class SimulationResult(BaseModel):
    physics_status: PhysicsStatus = "valid"
    energy_status: EnergyStatus = "valid"
    propeller_status: PropellerStatus = "valid"
    status: str
    can_fly: bool
    quality: str
    safety_margin_ratio: float
    thrust_to_weight_ratio: float
    autonomy_min: float | None = None
    propeller_thrust_inferred: bool = False
    warnings: list[str] = Field(default_factory=list)
    analysis: SimulationAnalysis
    summary: str

    # Generic aliases
    @property
    def constraints_satisfied(self) -> bool:
        return self.can_fly

    @property
    def force_to_weight_ratio(self) -> float:
        return self.thrust_to_weight_ratio


SuggestionType = Literal[
    "reduce_weight",
    "increase_payload",
    "improve_efficiency",
    "increase_thrust",
    "increase_force",  # generic alias
    "improve_autonomy",
]


class Suggestion(BaseModel):
    type: SuggestionType
    reason: str
    expected_effect: str
    priority: float | None = None


ReasoningActionType = Literal[
    "create_project",
    "iterate",
    "calculate",
    "simulate",
    "analyze",
]


class ReasoningSuggestion(BaseModel):
    action: ReasoningActionType
    label: str
    reason: str
    priority: float | None = None
    blocked: bool = False
    is_critical: bool = False
    action_type: str | None = None  # semantic type (e.g. "increase_payload"), distinct from action routing
    block_reason: str | None = None  # why this action is blocked (from CONFLICT_RULES)


class ReasoningOutput(BaseModel):
    explanation: str
    insights: list[str] = Field(default_factory=list)
    tradeoffs: list[str] = Field(default_factory=list)
    suggested_actions: list[ReasoningSuggestion] = Field(default_factory=list)
    signals: dict[str, bool] = Field(default_factory=dict)
