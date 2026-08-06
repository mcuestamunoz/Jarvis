from __future__ import annotations

import re as _re
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from jarvis.schemas.action_schema import ActionName, ComponentSpec, InteractiveSessionState

# Used exclusively for deriving parsed_constraints from free-text restrictions strings.
_AUTONOMY_CONSTRAINT_RE = _re.compile(r"(\d+(?:\.\d+)?)\s*min", _re.IGNORECASE)
# U5: restricción de peso máximo — soporta "peso máximo 5kg", "masa máx: 3kg", "weight max 2.5kg"
_WEIGHT_CONSTRAINT_RE = _re.compile(
    r"(?:peso|masa|weight)\s+m[aá]x(?:imo)?\s*[:\s]\s*(\d+(?:\.\d+)?)\s*kg",
    _re.IGNORECASE,
)


def _parse_constraints(current_parameters: dict) -> dict[str, float]:
    """Derive parsed_constraints from current_parameters["restrictions"].

    Returns a dict with any subset of {"autonomy_min", "max_weight_kg"}.
    Extracted here as a module-level helper so both the @model_validator and
    the model_copy override can call the same logic without duplication.
    """
    restrictions = current_parameters.get("restrictions")
    result: dict[str, float] = {}
    if restrictions:
        m = _AUTONOMY_CONSTRAINT_RE.search(restrictions)
        if m:
            result["autonomy_min"] = float(m.group(1))
        w = _WEIGHT_CONSTRAINT_RE.search(restrictions)
        if w:
            result["max_weight_kg"] = float(w.group(1))
    return result


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class HistoryEntry(BaseModel):
    timestamp: str = Field(default_factory=utc_now_iso)
    action: ActionName
    summary: str
    artifacts: dict[str, str] = Field(default_factory=dict)


class ConflictRecord(BaseModel):
    timestamp: str = Field(default_factory=utc_now_iso)
    conflict_type: str
    initial_objective: str | None = None
    initial_operation: str | None = None
    conflicting_operation: str | None = None
    resolution: str


class ProjectMemory(BaseModel):
    preferences: dict[str, bool] = Field(default_factory=dict)
    conflict_history: list[ConflictRecord] = Field(default_factory=list)


class StructureProperties(BaseModel):
    material: str | None = None
    density: float | None = None
    volume: float | None = None
    structural_fraction: float = 0.25  # fraction of total mass that is structural
    notes: str | None = None

    @field_validator("structural_fraction")
    @classmethod
    def validate_structural_fraction(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(
                f"structural_fraction debe estar entre 0.0 y 1.0, recibido: {v}"
            )
        return v


class DesignProperties(BaseModel):
    structure: StructureProperties = Field(default_factory=StructureProperties)
    components: dict[str, ComponentSpec] = Field(default_factory=dict)
    system_defined: bool = False
    system_blocks: list[str] = Field(default_factory=list)
    system_priority: list[str] = Field(default_factory=list)


class ProjectState(BaseModel):
    """Persistent project state.

    Two-layer constraint representation (Bug 17):
    - ``current_parameters["restrictions"]`` — the raw user-facing string (e.g.
      "vuelo mínimo 20 min").  This is the single source of truth written by the
      user and stored in state.json.
    - ``parsed_constraints`` — the canonical machine-readable form (e.g.
      ``{"autonomy_min": 20.0}``).  This is always derived from the restrictions
      string by ``_derive_parsed_constraints_from_restrictions`` and must never be
      mutated directly.  It is NOT persisted independently; it is re-computed on
      every model instantiation including ``model_copy``.

    Material representation (Fase 3 — Single Read Point):
    - ``components["frame"].properties["material"]`` es la fuente canónica.
    - Lectura vía ``get_frame_material(design_properties)`` en ``jarvis/utils/design_utils.py``.
    - ``design_properties.structure.material`` es un campo legacy (Bug 16) — sigue existiendo
      para compatibilidad con state.json existente, pero ya no es la fuente canónica.
    - ``current_parameters`` must NOT contain a ``"material"`` key in new projects.
    """
    project_id: str
    project_slug: str
    objective: str
    workspace_path: str
    active_iteration: int = 0
    current_parameters: dict[str, Any] = Field(default_factory=dict)
    parsed_constraints: dict[str, float] = Field(default_factory=dict)
    design_properties: DesignProperties = Field(default_factory=DesignProperties)
    latest_results: dict[str, Any] = Field(default_factory=dict)
    # Transient physical output separated from persistent state.
    # Extracted from calculation results by record_action and stored here
    # so that _build_mutable_state can read it directly without coupling
    # to the structure of latest_results.
    last_total_mass_kg: float | None = None
    history: list[HistoryEntry] = Field(default_factory=list)
    memory: ProjectMemory = Field(default_factory=ProjectMemory)

    @model_validator(mode="after")
    def _derive_parsed_constraints_from_restrictions(self) -> "ProjectState":
        """Always re-derive parsed_constraints from the restrictions string.

        Runs during __init__ / model_validate.  For model_copy() calls — which
        bypass validators in Pydantic v2 — see the model_copy override below.

        Design note: current_parameters["restrictions"] is the user-facing string
        and is the single source of truth.  parsed_constraints is the canonical
        machine-readable form and must be derived, never manually mutated.
        """
        self.parsed_constraints = _parse_constraints(self.current_parameters)
        return self

    def model_copy(self, *, update: dict | None = None, deep: bool = False, **kwargs) -> "ProjectState":
        """Override to re-derive parsed_constraints when current_parameters changes.

        Pydantic v2 model_copy() bypasses @model_validator, so we re-derive
        parsed_constraints here explicitly whenever current_parameters is part of
        the update dict.  For all other copies the value is carried over unchanged.
        """
        new = super().model_copy(update=update, deep=deep, **kwargs)
        if update and "current_parameters" in update:
            new.parsed_constraints = _parse_constraints(update["current_parameters"] or {})
        return new


class ConversationTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class RuntimeState(BaseModel):
    session: InteractiveSessionState = Field(default_factory=InteractiveSessionState)
    conversation_history: list[ConversationTurn] = Field(default_factory=list)
