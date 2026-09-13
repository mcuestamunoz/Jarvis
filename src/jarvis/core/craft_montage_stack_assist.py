"""Craft montage Path F — pure propose for centered flush stack poses of
box subjects onto a boxed `frame_plate*` origin (`B1-craft-montage-path-f`).

Reopens stack-rule Path F now that a boxed plate is obtainable (cited OR
`estimated_temporary`, per that separate Buy) — Path N (disk motor/
propeller pose origins) stays permanently dead: `set_component_declared_
box_pose`'s own origin-must-be-box gate rejects a disk unconditionally,
and nothing here ever proposes one (motors/propellers are never in
`_STACK_SUBJECTS`).

Project-agnostic by design (lock #10 — zero SKU/project-id branches):
"does this box exist" is answered purely via `_geometry_from_spec`, the
SAME projector `spatial_board.py` already uses for the Board — this module
never inspects a component's name/SKU, only its declared L×W×H properties.
Never writes anything itself — the orchestrator's IDLE bridge is what
calls the existing, unmodified pose writer once the user retypes (or
number-picks) a proposal.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from jarvis.core.motor_catalog_assist import _normalize_help
from jarvis.domains.aerial import is_frame_plate_key

# Locked trigger phrases (IC §0 lock #7 — "pick 1-2 ... document them"):
# "apilar en placa" (literal, specific) and "proponer stack centrado"
# (matches the product-sentence wording). Accent/case-insensitive via
# _normalize_help, same as every other IDLE phrase gate in this codebase.
_TRIGGER_RE = re.compile(r"apilar\s+en\s+placa|proponer\s+stack\s+centrado")


def is_craft_montage_stack_trigger(user_input: str) -> bool:
    """True when *user_input* asks for the Path F stack checklist."""
    return bool(_TRIGGER_RE.search(_normalize_help(user_input)))

# Locked subject scope (lock #4) — never motors/propellers (Visor X/
# wheelbase already cover those separately; Path N stays dead).
_STACK_SUBJECTS: tuple[str, ...] = ("flight_controller", "esc", "battery", "sensors")

# Same Spanish noun table mount_standard_assist.py already validated for
# these exact 4 subjects — reused, not reinvented.
_SUBJECT_NOUNS: dict[str, str] = {
    "esc": "el esc",
    "flight_controller": "la controladora",
    "battery": "la batería",
    "sensors": "el sensor",
}

_BOX_DIM_KEYS = ("length_mm", "width_mm", "height_mm")


@dataclass(frozen=True)
class StackProposal:
    """One Path F checklist row.

    ``kind == "proposed"`` carries a ready-to-type ``example_pose_phrase``.
    ``kind == "ambiguous"`` carries ``candidates`` (2+ boxed plates, never
    guessed which is main) instead, and every other field stays at its
    default. ``kind == "skipped"`` names a declared-but-boxless subject
    (``reason`` explains why), purely informational — never blocks the
    other proposals. ``kind == "done"`` names a subject that already has a
    declared pose — nothing left to propose for it. Distinguishing "done"
    from a bare empty list matters (layout_pack_cited_b1's own N1 finding,
    same bug class): an entirely empty ``propose_path_f_stack`` result
    must only ever mean "no plate box exists at all" — never "every
    subject already succeeded", which is a much happier case that gets
    its own explicit row instead of silently vanishing.
    """

    subject: str
    kind: str  # "proposed" | "ambiguous" | "skipped" | "done"
    origin_key: str | None = None
    x_mm: float | None = None
    y_mm: float | None = None
    z_mm: float | None = None
    example_pose_phrase: str | None = None
    reason: str = ""
    candidates: tuple[str, ...] = field(default_factory=tuple)


def _is_estimated_temporary_box(spec: Any) -> bool:
    props = getattr(spec, "properties", None) or {}
    return any(
        (prop := props.get(key)) is not None and getattr(prop, "source", None) == "estimated_temporary"
        for key in _BOX_DIM_KEYS
    )


def _plate_box_origin(components: dict[str, Any]) -> str | tuple[str, ...] | None:
    """A single clear boxed `frame_plate*` key (lock #5 — prefer the one
    unambiguous main plate); a tuple of 2+ keys when multiple plates are
    boxed (AMBIGUOUS, never guessed); `None` when zero plate boxes exist."""
    from jarvis.workspace.spatial_board import _geometry_from_spec

    boxed_plates = tuple(sorted(
        key for key, spec in components.items()
        if is_frame_plate_key(key) and (_geometry_from_spec(spec) or {}).get("shape") == "box"
    ))
    if len(boxed_plates) == 1:
        return boxed_plates[0]
    if len(boxed_plates) >= 2:
        return boxed_plates
    return None


def _fmt(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(round(value, 4))


def flush_centered_z_mm(origin_geometry: dict[str, Any], child_geometry: dict[str, Any]) -> float:
    """The one locked Path F arithmetic (lock #3): flush-centered stack
    height, `plate.height_mm/2 + child.height_mm/2`. Extracted as its own
    function so a NAMED, curated pack (`layout_pack_assist.py`, `B1-
    layout-pack-cited`) can reuse the exact same formula instead of a
    second copy — "same arithmetic as B1-craft-montage-path-f" is that
    Buy's own explicit lock."""
    return origin_geometry["height_mm"] / 2.0 + child_geometry["height_mm"] / 2.0


def propose_path_f_stack(components: dict[str, Any]) -> list[StackProposal]:
    """Undeclared, box-only Path F stack proposals for *components* — pure,
    read-only, mutates nothing and calls no writer.

    Locked arithmetic (lock #3): for each in-scope subject with its own
    `shape: box` geometry, ``x_mm=0``, ``y_mm=0``,
    ``z_mm = plate.height_mm/2 + child.height_mm/2`` (flush centered) —
    never an invented XY offset.
    """
    from jarvis.workspace.spatial_board import _geometry_from_spec

    origin = _plate_box_origin(components)
    if origin is None:
        return []
    if isinstance(origin, tuple):
        return [StackProposal(
            subject="(placa)", kind="ambiguous", candidates=origin,
            reason="varias placas tienen caja declarada — no elijo cuál es la principal",
        )]

    origin_spec = components[origin]
    origin_geometry = _geometry_from_spec(origin_spec)
    origin_estimated = _is_estimated_temporary_box(origin_spec)

    proposals: list[StackProposal] = []
    for subject in _STACK_SUBJECTS:
        spec = components.get(subject)
        if spec is None:
            continue  # not declared at all — nothing to propose

        geometry = _geometry_from_spec(spec)
        if geometry is None or geometry.get("shape") != "box":
            proposals.append(StackProposal(
                subject=subject, kind="skipped",
                reason="sin caja L×W×H declarada todavía",
            ))
            continue

        if getattr(spec, "declared_box_pose", None) is not None:
            proposals.append(StackProposal(
                subject=subject, kind="done", origin_key=origin,
                reason="ya tiene pose declarada — nada que añadir",
            ))
            continue  # never propose a "correction" to an existing pose

        z_mm = flush_centered_z_mm(origin_geometry, geometry)
        noun = _SUBJECT_NOUNS[subject]
        phrase = (
            f"declara {noun} a 0 mm en x, 0 mm en y, {_fmt(z_mm)} mm en z "
            f"respecto a {origin}"
        )
        disclaimer = "apilado centrado (supuesto), no medida / no VERIFICADO"
        if origin_estimated:
            disclaimer += " — placa con geometría ESTIMATED_TEMPORARY, no citada"

        proposals.append(StackProposal(
            subject=subject, kind="proposed", origin_key=origin,
            x_mm=0.0, y_mm=0.0, z_mm=z_mm,
            example_pose_phrase=phrase, reason=disclaimer,
        ))

    return proposals


def format_path_f_stack(proposals: list[StackProposal]) -> str:
    """Locked Spanish copy — numbered list + exact phrase per row, honest
    'nothing to propose' message, mandatory supuesto/estimada disclosure.
    Never says VERIFICADO/CAD/"cabe"/Product B."""
    if not proposals:
        # An entirely empty list only ever means no plate box exists at
        # all — "every subject already has a pose" is represented by
        # "done" rows below, never a bare [] (N1 fix, layout_pack_cited_
        # b1's same finding applied back to this sibling module).
        return (
            "Apilado en placa: no hay una placa con caja declarada todavía "
            "(cita o estimada) — nada que proponer. Prueba primero "
            "'declara frame_plate estimada L x W mm' o una medida real."
        )
    if len(proposals) == 1 and proposals[0].kind == "ambiguous":
        row = proposals[0]
        return (
            f"Hay varias placas con caja declarada ({', '.join(row.candidates)}) "
            "— indica cuál es la principal antes de proponer un apilado."
        )

    lines = ["Apilado propuesto sobre la placa (centrado, supuesto — no medida):"]
    idx = 1
    for row in proposals:
        if row.kind == "skipped":
            lines.append(f"  · {row.subject}: {row.reason}")
            continue
        if row.kind == "done":
            lines.append(f"  ✓ {row.subject} → {row.origin_key}: {row.reason}")
            continue
        lines.append(f"  {idx}. {row.subject} → {row.origin_key}: escribe \"{row.example_pose_phrase}\"")
        lines.append(f"     ({row.reason})")
        idx += 1
    if idx == 1:
        lines.append("  (nada pendiente — todo lo que tiene caja ya tiene pose, o falta caja.)")
    else:
        lines.append("Escribe la frase para confirmar — nada se declara solo.")
    return "\n".join(lines)
