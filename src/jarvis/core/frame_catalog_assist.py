"""Assisted frame acquisition — catalog suggestions for the structure
component wizard (Structure Catalog Foundation IC-3, battery-class UX).

Thin glue over ``ComponentLibrary.list_frames()`` — no new library code, no
ranking, no "best frame for my prop" scoring, no Conversation Engine.

``is_help_choose_phrase`` / ``match_suggestion_by_input`` are imported (not
duplicated) from ``motor_catalog_assist`` — same ★2 discipline
``propeller_catalog_assist``/``battery_catalog_assist`` already established:
they are already generic enough to work on a frame suggestion list
unmodified.

Honesty lock (Structure Catalog Foundation IC-1/IC-2, unchanged here):
picking a catalog frame means identity + declared mass/class from the
catalog — never "estructura validada", never "la hélice cabe", never
ASSEMBLY_READY. This module only builds/formats the list; it makes no
engineering claim itself.
"""
from __future__ import annotations

from typing import Any, TypedDict

from jarvis.core.catalog_rebind_assist import is_frame_rebind_phrase
from jarvis.core.motor_catalog_assist import is_help_choose_phrase, match_suggestion_by_input
from jarvis.knowledge.library import ComponentLibrary, FrameSpec, default_library

__all__ = [
    "FrameSuggestion",
    "build_frame_catalog_suggestions",
    "format_frame_catalog_suggestions",
    "frame_spec_to_suggestion",
    "is_help_choose_phrase",
    "is_frame_rebind_phrase",
    "match_suggestion_by_input",
]

# is_frame_rebind_phrase: B2 API preserved; implementation lives in
# catalog_rebind_assist (B3 shared resolver).


class FrameSuggestion(TypedDict):
    """Catalog candidate shown to the user during assisted frame acquisition."""

    idx: int
    name: str
    manufacturer: str | None
    model: str | None
    mass_g: float
    size_class_inch: float
    material: str | None


def frame_spec_to_suggestion(frame: FrameSpec, idx: int = 1) -> FrameSuggestion:
    return {
        "idx": idx,
        "name": frame.name,
        "manufacturer": frame.manufacturer,
        "model": frame.model,
        "mass_g": frame.mass_g,
        "size_class_inch": frame.size_class_inch,
        "material": frame.material,
    }


def build_frame_catalog_suggestions(
    project_state: Any,
    *,
    library: ComponentLibrary | None = None,
    limit: int = 10,
) -> list[FrameSuggestion]:
    """Catalog frame candidates — no ranking, no filtering.

    Mirrors ``build_battery_catalog_suggestions``'s Option A shape (the full
    v1 seed, capped at ``limit``): frame has no derived requirement to filter
    against the way motors/propellers do (no thrust/KV band), so a full,
    honest, unfiltered list is the only defensible default — same
    "Acceptable default" reasoning the battery assist investigation already
    used. *project_state* is accepted (unused today) for call-site symmetry
    with the other three families' builders.
    """
    lib = library or default_library
    matches = lib.list_frames()
    return [
        frame_spec_to_suggestion(f, idx=i + 1)
        for i, f in enumerate(matches[:limit])
    ]


def _format_candidate_line(s: FrameSuggestion) -> str:
    identity_bits = [b for b in (s.get("manufacturer"), s.get("model")) if b]
    identity = " ".join(identity_bits) if identity_bits else s["name"]
    material_bit = f", {s['material']}" if s.get("material") else ""
    return (
        f"  {s['idx']}. {identity}  →  {s['size_class_inch']:g}\", "
        f"{s['mass_g']:g}g{material_bit}"
    )


def format_frame_catalog_suggestions(
    suggestions: list[FrameSuggestion], *, include_cta: bool = True
) -> str:
    if not suggestions:
        # Defensive — list_frames() always returns the IC-1 seed today, but
        # never silently fall back to a fabricated/invented row if the
        # library were ever empty.
        return (
            "No tengo frames en el catálogo ahora mismo. "
            "Indica masa, material y clase a mano (ej. 'fibra de carbono 450g 5 pulgadas')."
        )
    lines = ["Frames del catálogo:"]
    for s in suggestions:
        lines.append(_format_candidate_line(s))
    if include_cta:
        lines.append("Elige un número, indica el frame a mano, o di 'no' para omitir.")
    return "\n".join(lines)
