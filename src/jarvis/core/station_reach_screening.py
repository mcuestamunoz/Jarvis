"""station_reach_screening
===========================
Disk-station radial reach B1 (`B1-disk-station-reach`) — a NEW, narrowly
named engineering screening for exactly one relation: does the frame's
own declared ``frame_arm.length_mm`` reach the quad-X station radius
derived from ``frame.wheelbase_mm``?

This is deliberately NOT ``pose_envelope_screening.screen_posed_envelope``
widened to accept disks — motors/propellers stay "not a box" there,
unchanged (investigation_report_disk_station_fit_attest_b0.md §A2, §E).
This module's own status vocabulary (``station_reach_*``) can never be
confused with ``overlap``/``no_overlap``/``child_not_box``.

Claim ceiling (IC §0.1): affirms ONLY that the arm's declared length
reaches (or overshoots) the wheelbase-derived station radius — the exact
L vs R comparison the Visor already uses to place the arm box
(``workspace.spatial_board._frame_arm_radial_offsets_mm``), read here via
the SAME functions (never a second copy) so the two can never drift.
Never affirms hub interference, blade clearance, or vertical clearance.
Never a substitute for a physical MEASURE.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from jarvis.schemas.action_schema import ComponentSpec

StationReachStatus = Literal[
    "station_reach_ok",
    "station_reach_over",
    "station_reach_insufficient",
    "station_reach_estimated",
]


@dataclass(frozen=True)
class StationReachScreening:
    status: StationReachStatus


def screen_station_reach(
    child: ComponentSpec, origin_key: str, components: dict[str, ComponentSpec]
) -> StationReachScreening:
    """Screen *child* (e.g. ``motors``) against *origin_key*'s
    (``frame_arm``) declared length reaching the frame's own quad-X
    station radius.

    Fail-closed at every step — never a fallback origin, never an assumed
    axis, never a shrunk length. Required, in order:

    1. ``child.mounted_on == origin_key`` — never inferred. A station-reach
       claim about a component that never declared this mount is not
       honest, even if the geometry alone would pass.
    2. ``frame`` declared with ``configuration == "quad_x"`` and a positive
       ``wheelbase_mm`` — via ``_quad_x_wheelbase_mm``, the SAME gate the
       Visor itself uses (imported, never re-implemented).
    3. *origin_key* declaring a positive box ``length_mm``.

    Any missing/invalid piece -> ``station_reach_insufficient``.

    ``station_reach_estimated`` fires when the arm's own ``length_mm`` OR
    the frame's ``wheelbase_mm`` carries ``source == "estimated_temporary"``
    — checked BEFORE the L<=R comparison, same "screening, no verificado"
    discipline as ``pose_envelope_screening.screen_posed_envelope``'s own
    ``estimated_dims`` gate. The attestation writer refuses any status
    other than ``station_reach_ok``, so this fails closed for attest too.
    """
    from jarvis.workspace.spatial_board import _quad_x_station_points, _quad_x_wheelbase_mm

    if getattr(child, "mounted_on", None) != origin_key:
        return StationReachScreening(status="station_reach_insufficient")

    frame = components.get("frame")
    origin = components.get(origin_key)
    if frame is None or origin is None:
        return StationReachScreening(status="station_reach_insufficient")

    wheelbase_mm = _quad_x_wheelbase_mm(components)
    if wheelbase_mm is None:
        return StationReachScreening(status="station_reach_insufficient")

    length_prop = (origin.properties or {}).get("length_mm")
    if length_prop is None or length_prop.value is None:
        return StationReachScreening(status="station_reach_insufficient")
    try:
        length_mm = float(length_prop.value)
    except (TypeError, ValueError):
        return StationReachScreening(status="station_reach_insufficient")
    if not (length_mm > 0):
        return StationReachScreening(status="station_reach_insufficient")

    wheelbase_prop = (frame.properties or {}).get("wheelbase_mm")
    wheelbase_source = getattr(wheelbase_prop, "source", None) if wheelbase_prop is not None else None
    length_source = getattr(length_prop, "source", None)
    if length_source == "estimated_temporary" or wheelbase_source == "estimated_temporary":
        return StationReachScreening(status="station_reach_estimated")

    station = _quad_x_station_points(wheelbase_mm)[0]
    radius_mm = (station["xMm"] ** 2 + station["yMm"] ** 2) ** 0.5
    if not (radius_mm > 0):
        return StationReachScreening(status="station_reach_insufficient")

    if length_mm <= radius_mm:
        return StationReachScreening(status="station_reach_ok")
    return StationReachScreening(status="station_reach_over")


def format_station_reach(screening: StationReachScreening) -> str:
    """Locked Spanish copy — "alcance de estación" honesty. Never claims
    AABB "cabe", never bare "VERIFIED", never hub/blade clearance."""
    if screening.status == "station_reach_ok":
        return (
            "El brazo declarado alcanza el radio de estación del quad-X — "
            "alcance de estación, no verificado."
        )
    if screening.status == "station_reach_over":
        return (
            "El brazo declarado es más largo que el radio de estación del "
            "quad-X — alcance de estación, no verificado."
        )
    if screening.status == "station_reach_estimated":
        return (
            "Jarvis no verifica ensamblaje físico; al menos una medida "
            "(brazo o wheelbase) es ESTIMATED_TEMPORARY (provisional, sin "
            "evidencia) — no se compara."
        )
    return (
        "Jarvis no verifica alcance de estación; faltan wheelbase quad-X, "
        "longitud de brazo, o el motor no declara montaje en el brazo."
    )
