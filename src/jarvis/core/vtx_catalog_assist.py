"""Assisted VTX acquisition — catalog suggestions for the video_link
singleton wizard and IDLE `cambiar vtx` (First `library/vtx` seed,
`B1-mission-vtx-identity`).

Thin glue over ``ComponentLibrary.list_vtx()`` — no ranking, no "best VTX
for my craft", no Conversation Engine. Mirrors ``camera_catalog_assist.py``'s
own shape/discipline exactly (§0.2 fork, locked): pick MUST resolve through
``catalog_bind.bind_vtx_from_catalog`` — never a free-text-only apply that
leaves no ``catalog_ref``.

``is_help_choose_phrase`` / ``match_suggestion_by_input`` are imported (not
duplicated) from ``motor_catalog_assist`` — same ★2 discipline every other
catalog assist module already established.

Honesty lock: picking a catalog VTX SKU means identity + the cited box
envelope + the cited mass — never a projected ``power_w`` (a VTX's cited
spec is RF output in milliwatts, a different physical quantity from the
electrical DC draw the mission energy model sums). This module only
builds/formats the list; it makes no fit/"cabe" claim.
"""
from __future__ import annotations

from typing import TypedDict

from jarvis.core.motor_catalog_assist import is_help_choose_phrase, match_suggestion_by_input
from jarvis.knowledge.library import ComponentLibrary, VtxSpec, default_library

__all__ = [
    "VtxSuggestion",
    "build_vtx_catalog_suggestions",
    "format_vtx_catalog_suggestions",
    "vtx_spec_to_suggestion",
    "is_help_choose_phrase",
    "match_suggestion_by_input",
]


class VtxSuggestion(TypedDict):
    """Catalog candidate shown during the video_link wizard / VTX rebind."""

    idx: int
    name: str
    manufacturer: str | None
    model: str | None
    length_mm: float | None
    width_mm: float | None
    height_mm: float | None
    mass_g: float | None


def vtx_spec_to_suggestion(spec: VtxSpec, idx: int = 1) -> VtxSuggestion:
    return {
        "idx": idx,
        "name": spec.name,
        "manufacturer": spec.manufacturer,
        "model": spec.model,
        "length_mm": spec.length_mm,
        "width_mm": spec.width_mm,
        "height_mm": spec.height_mm,
        "mass_g": spec.mass_g,
    }


def build_vtx_catalog_suggestions(
    *,
    library: ComponentLibrary | None = None,
    limit: int = 10,
) -> list[VtxSuggestion]:
    """Catalog VTX candidates — full ``list_vtx()`` capped at *limit*, no
    ranking, no hardcoded SKU."""
    lib = library or default_library
    matches = lib.list_vtx()
    return [
        vtx_spec_to_suggestion(spec, idx=i + 1)
        for i, spec in enumerate(matches[:limit])
    ]


def _format_candidate_line(s: VtxSuggestion) -> str:
    identity_bits = [b for b in (s.get("manufacturer"), s.get("model")) if b]
    identity = " ".join(identity_bits) if identity_bits else s["name"]
    dims = ""
    if (
        s.get("length_mm") is not None
        and s.get("width_mm") is not None
        and s.get("height_mm") is not None
    ):
        dims = f", {s['length_mm']:g}×{s['width_mm']:g}×{s['height_mm']:g} mm"
    mass = f", {s['mass_g']:g} g" if s.get("mass_g") is not None else ""
    return f"  {s['idx']}. {identity}{dims}{mass}"


def format_vtx_catalog_suggestions(
    suggestions: list[VtxSuggestion], *, include_cta: bool = True
) -> str:
    if not suggestions:
        return (
            "No tengo VTX en el catálogo ahora mismo. "
            "Descríbelo a mano (ej. 'vtx HGLRC')."
        )
    lines = ["VTX del catálogo:"]
    for s in suggestions:
        lines.append(_format_candidate_line(s))
    if include_cta:
        lines.append("Elige un número, descríbelo a mano, o di 'no' para dejarlo pendiente.")
    return "\n".join(lines)
