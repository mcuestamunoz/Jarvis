"""Fase C · C4 — autonomy command surface types.

Python scaffold / sim only — production flight_control runtime is C++
(future IC). `AutonomyCommand` and `AutonomySubmissionResult` are pure
data: no actuator field exists here or anywhere else in this rung, and
`AutonomySubmissionResult.execution` can never be `"executed"` on any
shipped path — see `jarvis.flight_software.autonomy.surface`.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from jarvis.capabilities.safety import SafetyDecision


class AutonomyVerb(str, Enum):
    TAKEOFF = "TAKEOFF"
    HOLD = "HOLD"
    GO_TO = "GO_TO"
    FOLLOW = "FOLLOW"
    RETURN_HOME = "RETURN_HOME"
    LAND = "LAND"
    PATROL = "PATROL"


class AutonomyCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    verb: AutonomyVerb
    intent_id: str | None = None
    params: dict[str, str] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


ExecutionState = Literal["not_attempted", "not_implemented"]


class AutonomySubmissionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command_id: str
    verb: AutonomyVerb
    safety: SafetyDecision
    execution: ExecutionState
