"""Assisted battery acquisition — catalog suggestions for the energy
component wizard (Bat-2, propeller-class UX for batteries).

Thin glue over ``ComponentLibrary.list_batteries()`` — no new library code,
no Conversation Engine, no SKU-specific special-casing.

``is_help_choose_phrase`` / ``match_suggestion_by_input`` are imported (not
duplicated) from ``motor_catalog_assist`` — same ★2 discipline
``propeller_catalog_assist`` already established: they are already generic
enough to work on a battery suggestion list unmodified.

Scope decision (IC §3, disclosed in implementation report): Option A only
(``list_batteries()`` capped at ``limit`` — the contract's own "Acceptable
default"). Option B (``find_batteries(min_energy_wh=...)`` from a derived
autonomy floor) is explicitly labeled "Optional enhancement" in the
contract and is not implemented here — kept out to avoid the ambiguity of
what an empty filtered result should honestly fall back to, which the
contract does not resolve unambiguously.
"""
from __future__ import annotations

from typing import Any, TypedDict

from jarvis.core.motor_catalog_assist import is_help_choose_phrase, match_suggestion_by_input
from jarvis.knowledge.library import BatterySpec, ComponentLibrary, default_library

__all__ = [
    "BatterySuggestion",
    "build_battery_catalog_suggestions",
    "format_battery_catalog_suggestions",
    "battery_spec_to_suggestion",
    "is_help_choose_phrase",
    "match_suggestion_by_input",
    "detect_battery_sku_token",
]


class BatterySuggestion(TypedDict):
    """Ranked catalog candidate shown to the user during assisted acquisition."""

    idx: int
    name: str
    energy_wh: float
    cells: int | None
    capacity_mah: float | None
    mass_g: float
    chemistry: str


def battery_spec_to_suggestion(battery: BatterySpec, idx: int = 1) -> BatterySuggestion:
    return {
        "idx": idx,
        "name": battery.name,
        "energy_wh": battery.energy_wh,
        "cells": battery.cells,
        "capacity_mah": battery.capacity_mah,
        "mass_g": battery.mass_g,
        "chemistry": battery.chemistry,
    }


def build_battery_catalog_suggestions(
    project_state: Any,
    *,
    library: ComponentLibrary | None = None,
    limit: int = 10,
) -> list[BatterySuggestion]:
    """Ranked catalog battery candidates.

    ★1 (locked, Bat-2): suggestions come only from ``ComponentLibrary.
    list_batteries()`` — the full v1 seed (contract §3 Option A: "capped at
    N — 10 entries — honest full v1 catalog"; ``limit=10`` therefore shows
    every seed battery unfiltered, unlike motors/propellers' narrower
    design-space-filtered ``limit=5``) — never a hardcoded SKU, never
    invented rows. *project_state* is accepted (unused today) for call-site
    symmetry with ``build_motor_catalog_suggestions``/
    ``build_propeller_catalog_suggestions`` and to leave room for a future,
    explicitly-scoped filter without changing every caller's signature.
    """
    lib = library or default_library
    matches = lib.list_batteries()
    return [
        battery_spec_to_suggestion(b, idx=i + 1)
        for i, b in enumerate(matches[:limit])
    ]


def detect_battery_sku_token(user_input: str, *, library: ComponentLibrary | None = None) -> str | None:
    """Block Closure B-PROP-ENERGY IC §2 (battery re-bind prerequisite): does
    free text name a live library battery SKU verbatim, e.g. "definir
    bateria lipo_6s_10000mah" or "cambia la bateria a lipo_6s_10000mah"?

    Distinct from ``match_suggestion_by_input`` (matches a whole reply
    against a pre-offered numbered list, e.g. after "ayúdame a elegir") —
    this scans arbitrary free text for an embedded SKU token, the shape
    ``ParamDefinitionSession.try_ingest`` needs before it ever reaches its
    opportunistic numeric parser (which would otherwise misparse the "6"
    out of "..._6s_..." and destroy an existing ``catalog_ref`` — the
    G27-class failure, on a distinct code path from G27's own wizard-path
    fix). SKU names are snake_case and specific enough (e.g.
    ``lipo_6s_10000mah``) that plain substring containment is safe — no
    normalization beyond lowercasing is needed for these ASCII identifiers.
    """
    lib = library or default_library
    normalized = user_input.lower()
    for spec in lib.list_batteries():
        if spec.name in normalized:
            return spec.name
    return None


def _format_candidate_line(s: BatterySuggestion) -> str:
    cells_bit = f", {s['cells']}S" if s.get("cells") is not None else ""
    mah_bit = f", {int(s['capacity_mah'])}mAh" if s.get("capacity_mah") is not None else ""
    return f"  {s['idx']}. {s['name']}  →  {s['energy_wh']}Wh{cells_bit}{mah_bit}, {s['mass_g']}g"


def format_battery_catalog_suggestions(
    suggestions: list[BatterySuggestion], *, include_cta: bool = True
) -> str:
    if not suggestions:
        # Defensive — list_batteries() always returns the seed catalog
        # today, but never silently fall back to a fabricated/heuristic
        # value (the G27 discipline) if the library were ever empty.
        return (
            "No tengo baterías en el catálogo ahora mismo. "
            "Indica la capacidad a mano (ej. '4S 10000mAh' o directamente en Wh)."
        )
    lines = ["Baterías del catálogo:"]
    for s in suggestions:
        lines.append(_format_candidate_line(s))
    if include_cta:
        lines.append("Elige un número, indica la batería a mano, o di 'no' para omitir.")
    return "\n".join(lines)
