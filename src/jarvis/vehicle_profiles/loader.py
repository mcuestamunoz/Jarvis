"""Fase C · C3 — vehicle profile loader. Reads checked-in JSON only, no
network, no craft workspace/BOM binding."""

from __future__ import annotations

import json
from pathlib import Path

from jarvis.vehicle_profiles.schemas import VehicleProfile

_DATA_DIR = Path(__file__).parent / "data"


def load_profile(profile_id: str) -> VehicleProfile:
    path = _DATA_DIR / f"{profile_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"vehicle profile '{profile_id}' not found")
    data = json.loads(path.read_text(encoding="utf-8"))
    return VehicleProfile.model_validate(data)


def load_smoke_profile() -> VehicleProfile:
    return load_profile("smoke_quad_hal_imu")


def load_this_quad_profile() -> VehicleProfile:
    """Fase C · C43 — loads the checked-in `this_quad` fixture (a plain,
    unbound `VehicleProfile`, same C3 shape as `smoke_quad_hal_imu`).
    Binding it to craft identity is a separate, explicit step — see
    `jarvis.vehicle_profiles.bind.bind_profile_to_craft_identity`."""
    return load_profile("this_quad")
