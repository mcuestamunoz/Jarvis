"""Assisted FC / GPS identity acquisition — numbered list from sourced
dimension tables (Geometry #4b), not Class A ``library/`` SKUs.

``FLIGHT_CONTROLLER_DIMENSIONS`` / ``GPS_DIMENSIONS`` are the Engineer-
cited identity envelopes already used by free-text declare. This module
only formats those rows for ``ayúdame a elegir`` and maps a pick back to
the same declare phrase the extractors already understand — no new
``catalog_ref`` family, no bind, no fit claim.
"""
from __future__ import annotations

from typing import Literal, TypedDict

from jarvis.core.motor_catalog_assist import is_help_choose_phrase, match_suggestion_by_input
from jarvis.domains.aerial import FLIGHT_CONTROLLER_DIMENSIONS, GPS_DIMENSIONS

__all__ = [
    "ControlIdentitySuggestion",
    "build_flight_controller_identity_suggestions",
    "build_sensor_identity_suggestions",
    "format_control_identity_suggestions",
    "is_help_choose_phrase",
    "match_suggestion_by_input",
]

ControlFamily = Literal["flight_controller", "sensors"]

# Declare phrases that extract_* already resolve to the dim-table keys
# (longest aliases preferred in aerial maps — these are the smoke phrases).
_FC_DECLARE: dict[str, str] = {
    "pixhawk_4": "Pixhawk 4",
    "speedybee_f405_v4": "SpeedyBee F405 V4",
}

_GPS_DECLARE: dict[str, str] = {
    "holybro_m10": "Holybro M10",
}


class ControlIdentitySuggestion(TypedDict):
    idx: int
    name: str
    family: ControlFamily
    model_key: str
    declare_text: str
    label: str
    length_mm: float
    width_mm: float
    height_mm: float


def build_flight_controller_identity_suggestions(
    *, limit: int = 10
) -> list[ControlIdentitySuggestion]:
    """Sourced FC envelopes from ``FLIGHT_CONTROLLER_DIMENSIONS`` — no ranking."""
    out: list[ControlIdentitySuggestion] = []
    for i, (key, dims) in enumerate(FLIGHT_CONTROLLER_DIMENSIONS.items()):
        if i >= limit:
            break
        label = _FC_DECLARE.get(key, key.replace("_", " "))
        out.append(
            {
                "idx": i + 1,
                "name": label,  # match_suggestion_by_input keys off "name"
                "family": "flight_controller",
                "model_key": key,
                "declare_text": label,
                "label": label,
                "length_mm": float(dims["length_mm"]),  # type: ignore[arg-type]
                "width_mm": float(dims["width_mm"]),  # type: ignore[arg-type]
                "height_mm": float(dims["height_mm"]),  # type: ignore[arg-type]
            }
        )
    return out


def build_sensor_identity_suggestions(*, limit: int = 10) -> list[ControlIdentitySuggestion]:
    """Sourced GPS envelopes from ``GPS_DIMENSIONS`` — no ranking."""
    out: list[ControlIdentitySuggestion] = []
    for i, (key, dims) in enumerate(GPS_DIMENSIONS.items()):
        if i >= limit:
            break
        label = _GPS_DECLARE.get(key, key.replace("_", " "))
        out.append(
            {
                "idx": i + 1,
                "name": label,  # match_suggestion_by_input keys off "name"
                "family": "sensors",
                "model_key": key,
                "declare_text": label,
                "label": label,
                "length_mm": float(dims["length_mm"]),  # type: ignore[arg-type]
                "width_mm": float(dims["width_mm"]),  # type: ignore[arg-type]
                "height_mm": float(dims["height_mm"]),  # type: ignore[arg-type]
            }
        )
    return out


def format_control_identity_suggestions(
    suggestions: list[ControlIdentitySuggestion],
    *,
    family: ControlFamily,
    include_cta: bool = True,
) -> str:
    if not suggestions:
        topic = "controladoras" if family == "flight_controller" else "GPS/sensores"
        return (
            f"No tengo {topic} con caja citada en la tabla de identidades ahora mismo. "
            "Indica el modelo a mano."
        )
    header = (
        "Controladoras con caja citada:"
        if family == "flight_controller"
        else "GPS/sensores con caja citada:"
    )
    lines = [header]
    for s in suggestions:
        lines.append(
            f"  {s['idx']}. {s['label']}  →  "
            f"{s['length_mm']:g}×{s['width_mm']:g}×{s['height_mm']:g} mm"
        )
    if include_cta:
        lines.append("Elige un número, indica el modelo a mano, o di 'no' para omitir.")
    return "\n".join(lines)
