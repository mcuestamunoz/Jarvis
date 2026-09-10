"""IDLE `declared_box_pose` declare/clear — pure parse for Continuity
Declared Box-Local Pose B1, extended by Pose Continuity subject: plates B1,
Pose Continuity subject: kit keys B1, and Loose structure/kit envelopes +
pose subjects B1.

Subject resolution (both SET and CLEAR), fixed precedence: (1) the
electronics subject table (``resolve_component_subject_noun``); (2) a
frame-plate noun, via ``declared_envelope_declare_assist.
resolve_plate_subject_noun`` — the SAME noun set the envelope grammar
already recognizes (exact key, label substring, "placa principal"/"main
plate", "placa lipo"/"top lipo", bare "placa"/"plate"); (3) a presence-
gated loose-structure noun, via ``declared_envelope_declare_assist.
resolve_loose_structure_subject_noun`` (prop_adapter/frame_standoff/
frame_cage/frame_caps); (4) a presence-gated kit noun, via
``declared_envelope_declare_assist.resolve_kit_subject_noun`` (conector/
xt60/power_connector, harness/"cable de señal"/signal_harness). Never a
second/third/fourth noun table. This lets a plate (e.g. ``frame_plate_2``),
a kit component, or a loose structure part be posed relative to another
box the exact same way an electronics component already could.

Mirrors ``mounted_on_declare_assist``'s thinness: a deterministic phrase
parser, no LLM, no state mutation. The orchestrator calls
``jarvis.core.component_writers.set_component_declared_box_pose`` with the
result — this module never writes anything and never checks whether an
origin is actually a declared ``geometry: box`` (that honesty check, and
the "not a box" error, belong to the writer — see its own docstring).

Kinds:
  SET               — component_key, origin_key, and at least one of
                       x_mm/y_mm/z_mm resolved, ready to write. The writer
                       REPLACES the whole DeclaredBoxPose per call, so a
                       single SET always carries every axis this one
                       utterance names — omitted axes are None, not a merge
                       with any previously-declared pose.
  CLEAR             — component_key — clear the declared pose.
  AMBIGUOUS_ORIGIN  — component_key and at least one axis resolved, but the
                       origin noun is not uniquely resolved. ``candidates``
                       lists known frame-plate keys/labels for the "which
                       plate" ambiguity (2+ plates, bare "placa"/"plate");
                       an EMPTY ``candidates`` tuple means the named origin
                       token matched nothing declared at all.
  INCOMPLETE        — the SET gate fired (declara + mm + respecto all
                       present) but no recognized subject noun or no axis
                       clause was found. Deliberately NOT ``NONE`` — a
                       phrase this gate-shaped must not silently fall
                       through to the LLM/FN-014 just because it's missing
                       a piece.
  NONE              — not a pose declare/clear phrase at all (gate didn't
                       fire, or a CLEAR phrase named no recognizable
                       subject) — falls through to the caller's normal
                       routing, e.g. so "declarar el esc" (no mm/respecto)
                       still reaches FN-014's acquisition flow.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from jarvis.core.declared_envelope_declare_assist import (
    resolve_kit_subject_noun,
    resolve_loose_structure_subject_noun,
    resolve_plate_subject_noun,
)
from jarvis.core.motor_catalog_assist import _normalize_help
from jarvis.core.mounted_on_declare_assist import (
    MountDeclareResult,
    resolve_component_subject_noun,
    resolve_declared_part_noun,
)


@dataclass(frozen=True)
class PoseDeclareResult:
    kind: str  # "SET" | "CLEAR" | "AMBIGUOUS_ORIGIN" | "INCOMPLETE" | "NONE"
    component_key: str | None = None
    origin_key: str | None = None
    x_mm: float | None = None
    y_mm: float | None = None
    z_mm: float | None = None
    candidates: tuple[tuple[str, str], ...] = field(default_factory=tuple)


_NONE = PoseDeclareResult(kind="NONE")

# ── Gate phrases ─────────────────────────────────────────────────────────────
# SET requires ALL THREE — never "fija" (already claimed by mounted_on
# for "fija ... en" mount phrases; a pose gate must never collide with it).
_DECLARA_RE = re.compile(r"\bdeclara(?:r)?\b")
_MM_RE = re.compile(r"\bmm\b")
_RESPECTO_RE = re.compile(r"\brespecto\b")
_CLEAR_RE = re.compile(r"\bquita(?:r)?\s+(?:la\s+)?pose\b")

# ── Axis tokens — bare letters or length/width/height words ONLY. No
# directional/gravity synonyms (adelante/atras/arriba/abajo/izquierda/
# derecha/morro/gravedad) are ever accepted here.
_AXIS_TO_FIELD: dict[str, str] = {
    "x": "x_mm", "largo": "x_mm",
    "y": "y_mm", "ancho": "y_mm",
    "z": "z_mm", "alto": "z_mm",
}
_AXIS_MM_RE = re.compile(
    r"(-?\d+(?:[.,]\d+)?)\s*mm\s+en\s+(x|y|z|largo|ancho|alto)\b"
)


def _resolve_pose_subject(segment: str, components: dict) -> str | None:
    """Pose Continuity subject: plates B1 / kit keys B1 / Loose
    structure/kit envelopes + pose subjects B1 — fixed precedence:
    (1) electronics subject table (``resolve_component_subject_noun`` —
    unchanged, byte-identical: "declara el esc..." must keep resolving
    ``esc``, never a plate/kit/loose-structure key); (2) plate noun
    (``resolve_plate_subject_noun`` — the SAME noun set the envelope
    grammar already recognizes: exact key, label, "placa principal", "placa
    lipo"/"top lipo", bare "placa" — no second noun table); (3) loose
    structure/kit noun (``resolve_loose_structure_subject_noun`` —
    prop_adapter/frame_standoff/frame_cage/frame_caps, presence-gated);
    (4) kit noun (``resolve_kit_subject_noun`` — conector/xt60/
    power_connector, harness/"cable de señal"/signal_harness —
    presence-gated). Every presence-gated tier resolves to ``None`` here
    when the matching noun has no such key declared, never invented. A
    plate match that resolves to 2+ candidates (bare "placa" with several
    plates declared) has no dedicated result kind in this grammar yet — it
    is treated as "no subject" (``None``), same as any other unresolved
    reference, rather than inventing a new ``PoseDeclareResult`` kind for
    an ambiguity no test in any parent IC exercises."""
    subject = resolve_component_subject_noun(segment)
    if subject is not None:
        return subject
    plate_subject = resolve_plate_subject_noun(segment, components)
    if isinstance(plate_subject, MountDeclareResult):
        return None
    if plate_subject is not None:
        return plate_subject
    loose_subject = resolve_loose_structure_subject_noun(segment, components)
    if loose_subject is not None:
        return loose_subject
    return resolve_kit_subject_noun(segment, components)


def _parse_axes(segment: str) -> dict[str, float]:
    """All (value, axis) matches in *segment*, later occurrences of the same
    axis winning — never merged with anything outside this one phrase."""
    axes: dict[str, float] = {}
    for match in _AXIS_MM_RE.finditer(segment):
        raw_value, axis_token = match.group(1), match.group(2)
        field_name = _AXIS_TO_FIELD[axis_token]
        axes[field_name] = float(raw_value.replace(",", "."))
    return axes


def parse_declared_box_pose_declare(user_input: str, components: dict) -> PoseDeclareResult:
    """Pure parse: no state mutation, no LLM. ``components`` is
    ``design_properties.components`` (or an equivalent dict) — used only to
    resolve/validate the origin noun, never to invent a subject."""
    normalized = _normalize_help(user_input)

    if _CLEAR_RE.search(normalized):
        subject = _resolve_pose_subject(normalized, components)
        if subject is None:
            return _NONE
        return PoseDeclareResult(kind="CLEAR", component_key=subject)

    is_set_phrase = bool(
        _DECLARA_RE.search(normalized)
        and _MM_RE.search(normalized)
        and _RESPECTO_RE.search(normalized)
    )
    if not is_set_phrase:
        return _NONE

    respecto_match = _RESPECTO_RE.search(normalized)
    subject_segment = normalized[: respecto_match.start()]
    origin_segment = normalized[respecto_match.end() :]

    subject = _resolve_pose_subject(subject_segment, components)
    axes = _parse_axes(subject_segment)
    if subject is None or not axes:
        return PoseDeclareResult(kind="INCOMPLETE", component_key=subject)

    origin = resolve_declared_part_noun(origin_segment, components)
    if isinstance(origin, MountDeclareResult) or origin is None:
        # Pose Continuity subject: plates B1: `resolve_declared_part_noun`
        # alone has no "placa principal"/"placa lipo" canonical-noun
        # awareness — only exact key, label substring, and bare "placa"
        # (which is genuinely ambiguous with 2+ plates). Retry with the
        # SAME plate noun set the subject side just used
        # (`resolve_plate_subject_noun`) so "respecto a la placa
        # principal"/"...la placa lipo" resolves to that ONE plate instead
        # of surfacing a spurious "which plate" ambiguity. A still-genuine
        # ambiguity (bare "placa" with no principal/lipo keyword) or an
        # unmatched origin falls straight back through unchanged.
        plate_origin = resolve_plate_subject_noun(origin_segment, components)
        if plate_origin is not None:
            origin = plate_origin
    if isinstance(origin, MountDeclareResult):
        return PoseDeclareResult(
            kind="AMBIGUOUS_ORIGIN", component_key=subject, candidates=origin.candidates
        )
    if origin is None:
        return PoseDeclareResult(kind="AMBIGUOUS_ORIGIN", component_key=subject, candidates=())

    return PoseDeclareResult(kind="SET", component_key=subject, origin_key=origin, **axes)
