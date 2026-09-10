"""Assisted ESC acquisition — catalog suggestions for IDLE ESC rebind
(geometry ESC visor rebind B1).

Thin glue over ``ComponentLibrary.list_escs()`` — no ranking, no "best ESC
for my motor", no Conversation Engine.

``is_help_choose_phrase`` / ``match_suggestion_by_input`` are imported (not
duplicated) from ``motor_catalog_assist`` — same ★2 discipline the
battery/frame/kit assists already established.

Honesty lock: picking a catalog ESC SKU means identity + the cited
electrical fields + the cited box envelope. This module only builds/formats
the list; it makes no fit/"cabe" claim. Continuity offer is IDLE singleton
``expected_keys == ["esc"]`` only — never the propulsion composite wizard.
"""
from __future__ import annotations

from typing import TypedDict

from jarvis.core.motor_catalog_assist import is_help_choose_phrase, match_suggestion_by_input
from jarvis.knowledge.library import ComponentLibrary, EscSpec, default_library

__all__ = [
    "EscSuggestion",
    "build_esc_catalog_suggestions",
    "format_esc_catalog_suggestions",
    "esc_spec_to_suggestion",
    "is_help_choose_phrase",
    "match_suggestion_by_input",
]


class EscSuggestion(TypedDict):
    """Catalog candidate shown during IDLE ESC rebind."""

    idx: int
    name: str
    manufacturer: str | None
    model: str | None
    part_number: str | None
    continuous_current_a: float
    length_mm: float | None
    width_mm: float | None
    height_mm: float | None


def esc_spec_to_suggestion(spec: EscSpec, idx: int = 1) -> EscSuggestion:
    return {
        "idx": idx,
        "name": spec.name,
        "manufacturer": spec.manufacturer,
        "model": spec.model,
        "part_number": spec.part_number,
        "continuous_current_a": spec.continuous_current_a,
        "length_mm": spec.length_mm,
        "width_mm": spec.width_mm,
        "height_mm": spec.height_mm,
    }


def build_esc_catalog_suggestions(
    *,
    library: ComponentLibrary | None = None,
    limit: int = 10,
) -> list[EscSuggestion]:
    """Catalog ESC candidates — full ``list_escs()`` capped at *limit*,
    no ranking, no hardcoded SKU."""
    lib = library or default_library
    matches = lib.list_escs()
    return [
        esc_spec_to_suggestion(spec, idx=i + 1)
        for i, spec in enumerate(matches[:limit])
    ]


def _format_candidate_line(s: EscSuggestion) -> str:
    identity_bits = [b for b in (s.get("manufacturer"), s.get("model")) if b]
    identity = " ".join(identity_bits) if identity_bits else s["name"]
    part_bit = f" (PN {s['part_number']})" if s.get("part_number") else ""
    amps = s["continuous_current_a"]
    amps_bit = f"{int(amps)}A" if amps == int(amps) else f"{amps}A"
    dims = ""
    if (
        s.get("length_mm") is not None
        and s.get("width_mm") is not None
        and s.get("height_mm") is not None
    ):
        dims = f", {s['length_mm']:g}×{s['width_mm']:g}×{s['height_mm']:g} mm"
    return f"  {s['idx']}. {identity}{part_bit}  →  {amps_bit}{dims}"


def format_esc_catalog_suggestions(
    suggestions: list[EscSuggestion], *, include_cta: bool = True
) -> str:
    if not suggestions:
        return (
            "No tengo ESC en el catálogo ahora mismo. "
            "Descríbelo a mano (ej. 'ESC 40A')."
        )
    lines = ["ESC del catálogo:"]
    for s in suggestions:
        lines.append(_format_candidate_line(s))
    if include_cta:
        lines.append("Elige un número, descríbelo a mano, o di 'no' para dejarlo pendiente.")
    return "\n".join(lines)
