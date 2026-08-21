from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from jarvis.schemas.semantic_schema import SemanticState


class ActionName(str, Enum):
    CREATE_PROJECT = "create_project"
    CALCULATE = "calculate"
    SIMULATE = "simulate"
    ITERATE = "iterate"


class ActionRequest(BaseModel):
    action: ActionName
    parameters: dict[str, Any] = Field(default_factory=dict)
    raw_user_input: str | None = None


class LLMRequestMode(str, Enum):
    INTERACTIVE = "interactive"


class LLMActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: ActionName
    project_id: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    mode: LLMRequestMode | None = None
    raw_user_input: str | None = None


class ExecutionType(str, Enum):
    SINGLE = "single"
    SEQUENCE = "sequence"


class PlanStepStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    DONE = "done"


class PlanStep(BaseModel):
    step_id: str
    action: ActionName
    description: str
    status: PlanStepStatus = PlanStepStatus.PENDING


class ExecutionPlan(BaseModel):
    goal: str
    project_id: str | None = None
    execution_type: ExecutionType
    steps: list[PlanStep] = Field(default_factory=list)


class CreateProjectParams(BaseModel):
    objective: str
    project_slug: str | None = None
    payload_kg: float = Field(gt=0)
    vehicle_type: str
    restrictions: str
    detail_level: str
    motors: int | None = Field(default=None, ge=1)
    per_motor_max_thrust_n: float | None = Field(default=None, gt=0)
    structure_mass_factor: float = Field(ge=0)
    safety_factor: float = Field(gt=1)
    propeller_diameter_in: float | None = Field(default=None, gt=0)
    propeller_rpm: float | None = Field(default=None, gt=0)
    per_actuator_torque_nm: float | None = Field(default=None, gt=0)
    max_force_per_actuator_n: float | None = Field(default=None, gt=0)

    @field_validator("project_slug")
    @classmethod
    def normalize_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip().replace(" ", "-").lower()

    @field_validator("vehicle_type", "detail_level", "restrictions")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        return value.strip()


class OrchestratorMode(str, Enum):
    IDLE = "idle"
    CREATE_PROJECT_INTERACTIVE = "create_project_interactive"
    ITERATE_INTERACTIVE = "iterate_interactive"
    DEFINE_MISSING_PARAMETERS = "define_missing_params"
    SYSTEM_DEFINITION = "system_definition"


class ProjectDraft(BaseModel):
    vehicle_type: str | None = None
    objective: str | None = None
    payload_kg: float | None = None
    restrictions: str | None = None
    detail_level: str | None = None
    motors: int | None = None
    per_motor_max_thrust_n: float | None = None
    structure_mass_factor: float | None = None
    safety_factor: float | None = None
    propeller_diameter_in: float | None = None
    propeller_rpm: float | None = None
    per_actuator_torque_nm: float | None = None
    max_force_per_actuator_n: float | None = None


class ImpactEstimate(BaseModel):
    weight_change_percent: float | None = None
    thrust_impact: str | None = None
    stability_impact: str | None = None
    summary: str | None = None


class PropertyValue(BaseModel):
    value: str | float | int | None = None
    unit: str | None = None
    confidence: float = 0.0
    source: Literal["declared", "inferred", "calculated"] = "inferred"


class CatalogRef(BaseModel):
    """Physical Component Catalog v1 (Impl A) — identity placeholder.

    Points a ComponentSpec at a specific `library/**/_datos.json` SKU. Additive
    and optional: introduced by Impl A's schema, but no writer, assisted pick,
    or Continuity path populates it yet — that is Impl B's Bind step. See
    docs/PHYSICAL_COMPONENT_CATALOG_V1.md, decision 1A.
    """

    family: Literal["motor", "battery", "propeller"]
    sku: str


class ComponentSpec(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = ""
    component_type: str | None = None
    suggested_key: str | None = None
    inference_confidence: float = 0.0
    properties: dict[str, PropertyValue] = Field(default_factory=dict)
    completeness: Literal["low", "medium", "high"] = "low"
    missing_fields: list[str] = Field(default_factory=list)
    hints: list[str] = Field(default_factory=list)
    source: Literal["declared", "inferred"] = "declared"
    # output_magnitude: the property key that this component's rule uses as its
    # primary physical output (e.g. "thrust_n", "torque_nm").  Set by
    # component_inference from the matching ComponentRule.  The resolver reads
    # this instead of hardcoding domain-specific property names.
    output_magnitude: str | None = None
    # Catalog v1 (Impl A) — optional identity placeholder. Default None means
    # "declared/inferred, not catalog-bound" (today's only behavior). No
    # production code path sets this in Impl A — see CatalogRef docstring.
    catalog_ref: CatalogRef | None = None


class IterationOperation(str, Enum):
    REDUCE = "reducir"
    INCREASE = "aumentar"
    IMPROVE = "mejorar"
    OPTIMIZE = "optimizar"
    DEFINE = "define"


class IterationConflict(BaseModel):
    initial_objective: str | None = None
    initial_operation: str | None = None
    conflicting_operation: str | None = None
    conflicting_input: str


class IterationDraft(BaseModel):
    project_id: str | None = None
    project_slug: str | None = None
    workspace_path: str | None = None
    objective: str | None = None
    variable: str | None = None
    operation: IterationOperation | None = None
    restrictions: str | None = None
    strategy: str | None = None
    value: str | None = None
    impact_estimate: ImpactEstimate | None = None
    conflict: IterationConflict | None = None
    component_patch: dict[str, ComponentSpec] | None = None

    @field_validator("operation", mode="before")
    @classmethod
    def _coerce_operation(cls, v: object) -> object:
        """Silently discard unrecognised operation values from the LLM instead of crashing."""
        if v is None:
            return v
        valid = {op.value for op in IterationOperation}
        if isinstance(v, str) and v not in valid:
            return None
        return v


class HandoffContext(BaseModel):
    """FN-024 (H1): operation-scoped Handoff Context — a temporary, runtime-only
    bridge between a Goal Plan just shown (goal_planner.format_goal_plan) and
    the turn(s) that follow it (bare "explora opciones" → DSE; a named lever →
    future H4 iterate preseed).

    Deliberately NOT a sticky `last_engineering_goal` string: it is capability-
    scoped (dse_capability/iterate_capability track what has and hasn't been
    consumed for THIS operation) and project-scoped (project_id guards every
    read — see orchestrator._handle_explore) so it can never be read across a
    project boundary or reused after DSE already ran for it.

    Never added to state_manager._PERSISTED_SESSION_FIELDS — same tier as
    last_exploration_result: runtime-only, never written to state.json, never
    restored from a snapshot.
    """
    goal_key: str
    levers: list[str] = Field(default_factory=list)
    origin: Literal["engineering_intent"] = "engineering_intent"
    dse_capability: Literal["active", "consumed"] = "active"
    iterate_capability: Literal["active"] = "active"
    project_id: str


class InteractiveSessionState(BaseModel):
    mode: OrchestratorMode = OrchestratorMode.IDLE
    step: int = 0
    project_draft: ProjectDraft | None = None
    iteration_draft: IterationDraft | None = None
    memory_context: dict[str, Any] | None = None
    semantic_state: SemanticState | None = None
    pending_entities: list[str] = Field(default_factory=list)
    motor_suggestions: list[dict] = Field(default_factory=list)
    # Prop-1: symmetric with motor_suggestions — runtime-only (see
    # state_manager._PERSISTED_SESSION_FIELDS comment), not persisted.
    propeller_suggestions: list[dict] = Field(default_factory=list)
    pending_param_definitions: list[str] = Field(default_factory=list)
    collected_params: dict[str, float] = Field(default_factory=dict)
    param_definition_reason: str = ""
    # Bug 54: pending affirmative confirmation to start define_missing_params wizard
    pending_define_missing: bool = False
    pending_missing_params: list[str] = Field(default_factory=list)
    pending_missing_reason: str = ""
    # Bug 49: dismissed suggestion labels (session-scoped, not persisted to state.json)
    dismissed_suggestions: list[str] = Field(default_factory=list)
    last_suggested_action: str | None = None
    # DSE v1.1: último ExplorationResult en memoria para poder aplicarlo sin repetir exploración.
    # Typed as Any para evitar ciclo de importación (design_explorer → calculation_engine → ...).
    last_exploration_result: Any | None = None
    # FN-004: pending structural substitution (e.g. motor_count 6→4) awaiting sí/no
    pending_structural_change: dict[str, Any] | None = None
    # FN-024 (H1): operation-scoped Handoff Context — runtime-only, never
    # persisted (not in state_manager._PERSISTED_SESSION_FIELDS). See
    # HandoffContext's own docstring.
    handoff_context: HandoffContext | None = None
