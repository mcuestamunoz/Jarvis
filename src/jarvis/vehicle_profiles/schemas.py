"""Fase C · C3 — `VehicleProfile`: which physical/hardware configuration a
system needs (see `docs/PLATFORM_CAPABILITY_VISION.md` §4). Minimal record
only — no BOM bind, no geometry, no catalog SKUs required in C3.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class VehicleProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    display_name: str | None = None
    vehicle_class: str = "unspecified"
    rung: Literal["hal_imu"]
    notes: str | None = None
