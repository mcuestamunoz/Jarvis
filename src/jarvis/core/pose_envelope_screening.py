"""pose_envelope_screening
=========================
Geometry assembly fit B1-min — backend-only AABB screening of one posed
child box against its own pose-origin box, in the DECLARED millimetre
frame (L→+X, W→+Y, H→+Z — see ``spatial_board.POSE_AXES_HONESTY_LABEL``).

This is deliberately NOT the CSS/pixel frame ``ui/spatial-board/src/
scene3dLayout.ts`` uses for rendering (which applies its own Y↔Z swap and
a top-left-anchored wrapper correction for a purely presentational
purpose, and treats an omitted axis as ``0`` for *display* only). Reusing
that frame or that "omitted → 0" convention for a physical claim would
silently launder a rendering choice into an engineering verdict — this
module never imports from ``ui/`` and never treats a missing axis as
zero: a missing axis is UNKNOWN, not "at the origin."

A screening fact only — never "cabe" / "no cabe" / "VERIFIED" /
"ensamblado" / "misfit geométrico". Never composes origin chains (single
level only, matching the pose writer's own honesty scope). Never reads
``mounted_on`` — a pose's own declared origin key is the only relationship
compared here, independent of where the part is physically attached.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from jarvis.schemas.action_schema import ComponentSpec

ScreeningStatus = Literal[
    "no_pose",
    "origin_unusable",
    "child_not_box",
    "pose_incomplete",
    "overlap",
    "no_overlap",
]

_AXIS_NAMES = ("x", "y", "z")


@dataclass(frozen=True)
class Screening:
    status: ScreeningStatus
    missing_axes: tuple[str, ...] = ()


def screen_posed_envelope(
    child: ComponentSpec, components: dict[str, ComponentSpec]
) -> Screening:
    """Screen *child* against its own ``declared_box_pose`` origin.

    Fail-closed at every step — never a fallback origin, never an assumed
    axis, never a cylinder from a disk. Local import of
    ``_geometry_from_spec`` avoids a circular import with
    ``spatial_board.py`` (which imports this module for ``_fields``) —
    same pattern ``component_writers.py`` already uses for the same pair
    of modules.
    """
    from jarvis.workspace.spatial_board import _geometry_from_spec

    pose = child.declared_box_pose
    if pose is None:
        return Screening(status="no_pose")

    origin = components.get(pose.origin_key)
    origin_geometry = _geometry_from_spec(origin) if origin is not None else None
    if origin_geometry is None or origin_geometry.get("shape") != "box":
        return Screening(status="origin_unusable")

    child_geometry = _geometry_from_spec(child)
    if child_geometry is None or child_geometry.get("shape") != "box":
        return Screening(status="child_not_box")

    axis_values = (pose.x_mm, pose.y_mm, pose.z_mm)
    missing = tuple(name for name, value in zip(_AXIS_NAMES, axis_values) if value is None)
    if missing:
        return Screening(status="pose_incomplete", missing_axes=missing)

    # AABB, declared mm frame, center-to-center, single-level. Origin box
    # centered at (0,0,0); child box centered at (x_mm, y_mm, z_mm) — the
    # pose's own declared offset, verbatim, never defaulted.
    origin_half = (
        origin_geometry["length_mm"] / 2.0,
        origin_geometry["width_mm"] / 2.0,
        origin_geometry["height_mm"] / 2.0,
    )
    child_half = (
        child_geometry["length_mm"] / 2.0,
        child_geometry["width_mm"] / 2.0,
        child_geometry["height_mm"] / 2.0,
    )
    overlaps = all(
        abs(axis_values[i]) <= child_half[i] + origin_half[i]
        for i in range(3)
    )
    return Screening(status="overlap" if overlaps else "no_overlap")


def format_screening(screening: Screening) -> str:
    """Locked Spanish copy — no forbidden tokens ever ("cabe", "no cabe",
    "VERIFIED", "ensamblado", "misfit geométrico"). Every geometric verdict
    (overlap/no_overlap/pose_incomplete) explicitly names itself
    "screening, no verificado" so it can never be read as a fit proof.
    """
    if screening.status == "pose_incomplete":
        axes = ", ".join(screening.missing_axes)
        return (
            f"Pose incompleta (faltan {axes}); no se compara — "
            "screening, no verificado."
        )
    if screening.status == "overlap":
        return "Los sobres se solapan en los ejes declarados — screening, no verificado."
    if screening.status == "no_overlap":
        return "Los sobres no se solapan en los ejes declarados — screening, no verificado."
    if screening.status == "origin_unusable":
        return (
            "Jarvis no verifica ensamblaje físico; el origen de la pose "
            "no es una caja declarada."
        )
    if screening.status == "child_not_box":
        return (
            "Jarvis no verifica ensamblaje físico; este componente no es "
            "una caja declarada."
        )
    return "Jarvis no verifica ensamblaje físico; falta pose declarada entre dos cajas."
