"""Assisted camera acquisition — catalog suggestions for the perception
singleton wizard and IDLE `cambiar cámara` (First `library/cameras` seed,
`B1-library-cameras-seed`).

Thin glue over ``ComponentLibrary.list_cameras()`` — no ranking, no "best
camera for my craft", no Conversation Engine. Mirrors ``esc_catalog_
assist.py``'s own shape/discipline exactly (§0.2 fork, locked): pick MUST
resolve through ``catalog_bind.bind_camera_from_catalog`` — never a
free-text-only apply that leaves no ``catalog_ref`` (the FC/sensors mistake
this Buy exists to not repeat).

``is_help_choose_phrase`` / ``match_suggestion_by_input`` are imported (not
duplicated) from ``motor_catalog_assist`` — same ★2 discipline every other
catalog assist module already established.

Honesty lock: picking a catalog camera SKU means identity + the cited box
envelope + the cited mass, plus a cited `power_w` when the row states one
(`B1-catalog-camera-power-w`). This module only builds/formats the list;
it makes no fit/"cabe" claim.
"""
from __future__ import annotations

from typing import TypedDict

from jarvis.core.motor_catalog_assist import is_help_choose_phrase, match_suggestion_by_input
from jarvis.knowledge.library import CameraSpec, ComponentLibrary, default_library

__all__ = [
    "CameraSuggestion",
    "build_camera_catalog_suggestions",
    "format_camera_catalog_suggestions",
    "camera_spec_to_suggestion",
    "is_help_choose_phrase",
    "match_suggestion_by_input",
]


class CameraSuggestion(TypedDict):
    """Catalog candidate shown during the perception wizard / camera rebind."""

    idx: int
    name: str
    manufacturer: str | None
    model: str | None
    length_mm: float | None
    width_mm: float | None
    height_mm: float | None
    mass_g: float | None
    power_w: float | None


def camera_spec_to_suggestion(spec: CameraSpec, idx: int = 1) -> CameraSuggestion:
    return {
        "idx": idx,
        "name": spec.name,
        "manufacturer": spec.manufacturer,
        "model": spec.model,
        "length_mm": spec.length_mm,
        "width_mm": spec.width_mm,
        "height_mm": spec.height_mm,
        "mass_g": spec.mass_g,
        "power_w": spec.power_w,
    }


def build_camera_catalog_suggestions(
    *,
    library: ComponentLibrary | None = None,
    limit: int = 10,
) -> list[CameraSuggestion]:
    """Catalog camera candidates — full ``list_cameras()`` capped at
    *limit*, no ranking, no hardcoded SKU."""
    lib = library or default_library
    matches = lib.list_cameras()
    return [
        camera_spec_to_suggestion(spec, idx=i + 1)
        for i, spec in enumerate(matches[:limit])
    ]


def _format_candidate_line(s: CameraSuggestion) -> str:
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
    power = f", {s['power_w']:g} W" if s.get("power_w") is not None else ""
    return f"  {s['idx']}. {identity}{dims}{mass}{power}"


def format_camera_catalog_suggestions(
    suggestions: list[CameraSuggestion], *, include_cta: bool = True
) -> str:
    if not suggestions:
        return (
            "No tengo cámaras en el catálogo ahora mismo. "
            "Descríbela a mano (ej. 'cámara RunCam')."
        )
    lines = ["Cámaras del catálogo:"]
    for s in suggestions:
        lines.append(_format_candidate_line(s))
    if include_cta:
        lines.append("Elige un número, descríbela a mano, o di 'no' para dejarlo pendiente.")
    return "\n".join(lines)
