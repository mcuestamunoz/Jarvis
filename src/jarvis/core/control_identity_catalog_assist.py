"""Assisted FC / GPS identity acquisition — numbered list from
`library/fc/` / `library/sensors/` (Relocate FC + GPS envelopes into
`library/` B1, `B1-library-fc-sensors`).

These two families now live in ``library/`` exactly like every other
catalog family (``ComponentLibrary.list_fcs`` / ``list_sensors``) — this
module never imports a dimension dict from ``jarvis.domains.aerial``
anymore. The pick-application UX is UNCHANGED (IC lock #8): a pick still
maps back to the SAME free-text declare phrase the extractors already
understand — no new ``catalog_ref`` bind wired into this path, no fit
claim. (A separate, explicit catalog-bind path — ``catalog_bind.
bind_flight_controller_from_catalog`` / ``bind_sensor_from_catalog`` —
exists for other callers, but this assist module does not use it.)
"""
from __future__ import annotations

from typing import Literal, TypedDict

from jarvis.core.motor_catalog_assist import is_help_choose_phrase, match_suggestion_by_input
from jarvis.knowledge.library import default_library

__all__ = [
    "ControlIdentitySuggestion",
    "build_flight_controller_identity_suggestions",
    "build_sensor_identity_suggestions",
    "format_control_identity_suggestions",
    "is_help_choose_phrase",
    "match_suggestion_by_input",
]

ControlFamily = Literal["flight_controller", "sensors"]

# Declare phrases that extract_* already resolve to the same canonical
# model id `library/fc|sensors` key off (longest aliases preferred in
# aerial maps — these are the smoke phrases). Kept here (not derived from
# `manufacturer`/`model`) since the extractor's own alias table is the
# actual authority on what text round-trips.
_FC_DECLARE: dict[str, str] = {
    "pixhawk_4": "Pixhawk 4",
    "speedybee_f405_v4": "SpeedyBee F405 V4",
    "skystars_f4_v4": "Skystars F4 V4",
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
    """Sourced FC envelopes from ``library/fc/`` (``ComponentLibrary.
    list_fcs``) — no ranking. Only rows with a full cited box (all of
    length/width/height) are listed, matching this assist's own "con caja
    citada" header."""
    out: list[ControlIdentitySuggestion] = []
    for i, spec in enumerate(default_library.list_fcs()):
        if spec.length_mm is None or spec.width_mm is None or spec.height_mm is None:
            continue
        if len(out) >= limit:
            break
        label = _FC_DECLARE.get(spec.name, spec.name.replace("_", " "))
        out.append(
            {
                "idx": len(out) + 1,
                "name": label,  # match_suggestion_by_input keys off "name"
                "family": "flight_controller",
                "model_key": spec.name,
                "declare_text": label,
                "label": label,
                "length_mm": spec.length_mm,
                "width_mm": spec.width_mm,
                "height_mm": spec.height_mm,
            }
        )
    return out


def build_sensor_identity_suggestions(*, limit: int = 10) -> list[ControlIdentitySuggestion]:
    """Sourced GPS/sensor envelopes from ``library/sensors/``
    (``ComponentLibrary.list_sensors``) — no ranking. Only rows with a
    full cited box are listed."""
    out: list[ControlIdentitySuggestion] = []
    for i, spec in enumerate(default_library.list_sensors()):
        if spec.length_mm is None or spec.width_mm is None or spec.height_mm is None:
            continue
        if len(out) >= limit:
            break
        label = _GPS_DECLARE.get(spec.name, spec.name.replace("_", " "))
        out.append(
            {
                "idx": len(out) + 1,
                "name": label,  # match_suggestion_by_input keys off "name"
                "family": "sensors",
                "model_key": spec.name,
                "declare_text": label,
                "label": label,
                "length_mm": spec.length_mm,
                "width_mm": spec.width_mm,
                "height_mm": spec.height_mm,
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
