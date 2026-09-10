"""Assisted kit-hardware acquisition — catalog suggestions for the
power_connector/signal_harness kit single-key wizards (Kit SKUs D B1,
battery/frame-class UX).

Thin glue over ``ComponentLibrary.list_kit_hardware(kit_key=...)`` — no new
library code, no ranking, no "best connector for my battery" scoring, no
Conversation Engine. One shared module/format for BOTH kit holes (not two
near-identical assist modules) — mirrors the single ``KitHardwareSpec``
family: the two rows are structurally thin and near-identical, so unifying
the assist layer too avoids the exact "generic parts dump" duplication this
Buy's own investigation argued against.

``is_help_choose_phrase`` / ``match_suggestion_by_input`` are imported (not
duplicated) from ``motor_catalog_assist`` — same ★2 discipline
``propeller_catalog_assist``/``battery_catalog_assist``/``frame_catalog_assist``
already established: they are already generic enough to work on a kit
hardware suggestion list unmodified.

Honesty lock: picking a catalog kit-hardware SKU means identity + the
cited electrical/physical fields only — never a mass, never a box, never
"cabe"/ASSEMBLY_READY. This module only builds/formats the list; it makes
no engineering claim itself.
"""
from __future__ import annotations

from typing import Any, TypedDict

from jarvis.core.motor_catalog_assist import is_help_choose_phrase, match_suggestion_by_input
from jarvis.knowledge.library import ComponentLibrary, KitHardwareSpec, default_library

__all__ = [
    "KitHardwareSuggestion",
    "build_kit_hardware_catalog_suggestions",
    "format_kit_hardware_catalog_suggestions",
    "kit_hardware_spec_to_suggestion",
    "is_help_choose_phrase",
    "match_suggestion_by_input",
]


class KitHardwareSuggestion(TypedDict):
    """Catalog candidate shown during assisted kit-hardware acquisition."""

    idx: int
    name: str
    kit_key: str
    manufacturer: str | None
    model: str | None
    part_number: str | None


def kit_hardware_spec_to_suggestion(spec: KitHardwareSpec, idx: int = 1) -> KitHardwareSuggestion:
    return {
        "idx": idx,
        "name": spec.name,
        "kit_key": spec.kit_key,
        "manufacturer": spec.manufacturer,
        "model": spec.model,
        "part_number": spec.part_number,
    }


def build_kit_hardware_catalog_suggestions(
    kit_key: str,
    *,
    library: ComponentLibrary | None = None,
    limit: int = 10,
) -> list[KitHardwareSuggestion]:
    """Catalog kit-hardware candidates for exactly one hole — no ranking, no
    filtering beyond ``kit_key`` (the connector wizard must never list the
    harness row and vice versa)."""
    lib = library or default_library
    matches = lib.list_kit_hardware(kit_key=kit_key)
    return [
        kit_hardware_spec_to_suggestion(spec, idx=i + 1)
        for i, spec in enumerate(matches[:limit])
    ]


def _format_candidate_line(s: KitHardwareSuggestion) -> str:
    identity_bits = [b for b in (s.get("manufacturer"), s.get("model")) if b]
    identity = " ".join(identity_bits) if identity_bits else s["name"]
    part_bit = f" (PN {s['part_number']})" if s.get("part_number") else ""
    return f"  {s['idx']}. {identity}{part_bit}"


def format_kit_hardware_catalog_suggestions(
    suggestions: list[KitHardwareSuggestion], *, include_cta: bool = True
) -> str:
    if not suggestions:
        # Defensive — the seed always has one row per key today, but never
        # silently fall back to a fabricated/invented row if the library
        # were ever empty for this kit_key.
        return (
            "No tengo piezas de catálogo para este hueco todavía. "
            "Descríbela a mano (ej. 'XT60') o déjala pendiente."
        )
    lines = ["Catálogo:"]
    for s in suggestions:
        lines.append(_format_candidate_line(s))
    if include_cta:
        lines.append("Elige un número, descríbelo a mano, o di 'no' para dejarlo pendiente.")
    return "\n".join(lines)
