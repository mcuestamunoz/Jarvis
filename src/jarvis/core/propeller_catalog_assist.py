"""Assisted propeller acquisition — catalog suggestions for the propulsion
component wizard (Prop-2, G21-class UX for propellers).

Thin glue over ``ComponentLibrary.match_motor_propeller`` (ERF-2's existing
motor<->propeller compatibility predicate) — no new library code, no
Conversation Engine, no SKU-specific special-casing.

``is_help_choose_phrase`` / ``match_suggestion_by_input`` are imported (not
duplicated) from ``motor_catalog_assist`` — ★2: they are already generic
enough to work on a propeller suggestion list unmodified.
"""
from __future__ import annotations

from typing import Any, TypedDict

from jarvis.core.motor_catalog_assist import is_help_choose_phrase, match_suggestion_by_input
from jarvis.knowledge.library import ComponentLibrary, PropellerSpec, default_library

__all__ = [
    "PropellerSuggestion",
    "build_propeller_catalog_suggestions",
    "format_propeller_catalog_suggestions",
    "propeller_spec_to_suggestion",
    "is_help_choose_phrase",
    "match_suggestion_by_input",
]


class PropellerSuggestion(TypedDict):
    """Ranked catalog candidate shown to the user during assisted acquisition."""

    idx: int
    name: str
    diameter_in: float
    pitch_in: float
    mass_g: float | None


def propeller_spec_to_suggestion(prop: PropellerSpec, idx: int = 1) -> PropellerSuggestion:
    return {
        "idx": idx,
        "name": prop.name,
        "diameter_in": prop.diameter_in,
        "pitch_in": prop.pitch_in,
        "mass_g": prop.mass_g,
    }


def _bound_motor_sku(project_state: Any) -> str | None:
    components = getattr(getattr(project_state, "design_properties", None), "components", None) or {}
    motors = components.get("motors")
    catalog_ref = getattr(motors, "catalog_ref", None) if motors is not None else None
    if catalog_ref is not None and getattr(catalog_ref, "family", None) == "motor":
        return catalog_ref.sku
    return None


def build_propeller_catalog_suggestions(
    project_state: Any,
    *,
    library: ComponentLibrary | None = None,
    limit: int = 5,
) -> list[PropellerSuggestion]:
    """Ranked catalog propeller candidates compatible with the bound motor.

    ★1 (locked): filters via the existing ``ComponentLibrary.match_motor_propeller``
    predicate only — no new library predicate, no per-SKU special-casing.

    Returns ``[]`` when no motor is catalog-bound yet — this is deliberate,
    not a bug: dumping the full propeller catalog with nothing to filter
    against would repeat the exact honesty mistake G22 already fixed for
    motors (a list that disagrees with what a gap/predicate can actually
    justify). The caller shows an honest "bind a motor first" message
    instead (``format_propeller_catalog_suggestions`` on an empty list).
    """
    lib = library or default_library
    motor_sku = _bound_motor_sku(project_state) if project_state is not None else None
    if motor_sku is None:
        return []
    matches = [
        p for p in lib.list_propellers()
        if lib.match_motor_propeller(motor_sku, p.name)
    ]
    return [
        propeller_spec_to_suggestion(p, idx=i + 1)
        for i, p in enumerate(matches[:limit])
    ]


def _format_candidate_line(s: PropellerSuggestion) -> str:
    mass = s.get("mass_g")
    mass_bit = f", {mass}g" if mass is not None else ""
    return f"  {s['idx']}. {s['name']}  →  {s['diameter_in']}x{s['pitch_in']}{mass_bit}"


def format_propeller_catalog_suggestions(
    suggestions: list[PropellerSuggestion], *, include_cta: bool = True
) -> str:
    if not suggestions:
        return (
            "Primero elige un motor del catálogo para poder filtrar hélices "
            "compatibles — di 'ayúdame a elegir' para motores, o indica la "
            "hélice a mano (ej. '5x4.5')."
        )
    lines = ["Hélices del catálogo compatibles con el motor elegido:"]
    for s in suggestions:
        lines.append(_format_candidate_line(s))
    if include_cta:
        lines.append("Elige un número, indica la hélice a mano, o di 'no' para omitir.")
    return "\n".join(lines)
