"""IDLE estimated-temporary plate envelope declare — pure parse for
Estimated-temporary plate envelope B1 (`B1-estimated-temporary-plate`).

Scoped EXCLUSIVELY to a frame-plate subject (`is_frame_plate_key`, via the
SAME noun table `declared_envelope_declare_assist.resolve_plate_subject_noun`
already uses for the plain declare grammar — no second plate-noun table).
Never battery/sensors/kit/frame_arm/motors/etc — this Buy's own lock #2
keeps every other family `declared`-only, unchanged.

Gate requires BOTH the existing envelope-declare shape (declara + A×B[×C]
mm) AND an explicit provisional keyword (estimada/estimado/temporal/
provisional) — a plain "declara la placa principal 100x100 mm" without
that keyword returns NONE here and falls through unchanged to
`declared_envelope_declare_assist`'s own bridge (`source="declared"`, no
behavior change for that phrase family or any non-plate subject).

Mirrors `mounted_on_declare_assist`'s thinness: deterministic parse only,
no LLM, no state mutation. The orchestrator calls
`component_writers.set_estimated_temporary_plate_envelope` with the
result — this module never writes anything and never invents a fallback
height (a two-number phrase leaves `height_mm=None`; the orchestrator
resolves it from that plate's own cited `thickness_mm`, same convention
`declared_envelope_declare_assist`'s own bridge already uses).

Kinds:
  SET             — a plate subject and length_mm/width_mm resolved
                     (height_mm resolved too, or None for the orchestrator
                     to fill from thickness_mm).
  AMBIGUOUS_PLATE — a plate-shaped reference (bare "placa"/"plate", or a
                     label match) resolved to 2+ candidates.
  INCOMPLETE      — the gate fired (declara + provisional keyword + dims)
                     but no plate-shaped subject was found at all.
  NONE            — not this grammar at all: no gate phrase, no dims, or
                     no provisional keyword (a plain declare belongs to
                     `declared_envelope_declare_assist`, never this
                     module).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from jarvis.core.declared_envelope_declare_assist import resolve_plate_subject_noun
from jarvis.core.motor_catalog_assist import _normalize_help
from jarvis.core.mounted_on_declare_assist import MountDeclareResult, resolve_component_subject_noun


@dataclass(frozen=True)
class EstimatedPlateDeclareResult:
    kind: str  # "SET" | "AMBIGUOUS_PLATE" | "INCOMPLETE" | "NONE"
    component_key: str | None = None
    length_mm: float | None = None
    width_mm: float | None = None
    height_mm: float | None = None
    candidates: tuple[tuple[str, str], ...] = field(default_factory=tuple)


_NONE = EstimatedPlateDeclareResult(kind="NONE")

_DECLARA_RE = re.compile(r"\bdeclara(?:r)?\b")
_PROVISIONAL_RE = re.compile(r"\b(?:estimad[ao]s?|temporal(?:es)?|provisional(?:es)?)\b")

# Same verbatim-print-order convention as declared_envelope_declare_assist's
# own dims grammar — deliberately duplicated (a 4-line regex pair) rather
# than importing that module's private `_parse_dims`/`_TRIPLE_RE`/`_PAIR_RE`,
# matching this codebase's own established convention of never reaching
# into another module's `_`-prefixed internals.
_NUM = r"(-?\d+(?:[.,]\d+)?)"
_SEP = r"\s*(?:x|×|por)\s*"
_TRIPLE_RE = re.compile(rf"{_NUM}{_SEP}{_NUM}{_SEP}{_NUM}\s*mm\b")
_PAIR_RE = re.compile(rf"{_NUM}{_SEP}{_NUM}\s*mm\b")


def _to_float(raw: str) -> float:
    return float(raw.replace(",", "."))


def _parse_dims(normalized: str) -> tuple[float, float, float | None]:
    triple = _TRIPLE_RE.search(normalized)
    if triple:
        return _to_float(triple.group(1)), _to_float(triple.group(2)), _to_float(triple.group(3))
    pair = _PAIR_RE.search(normalized)
    return _to_float(pair.group(1)), _to_float(pair.group(2)), None


def parse_estimated_temporary_plate_declare(user_input: str, components: dict) -> EstimatedPlateDeclareResult:
    """Pure parse: no state mutation, no LLM. ``components`` is
    ``design_properties.components`` (or an equivalent dict) — used only
    to resolve/validate the plate subject, never to invent a key."""
    normalized = _normalize_help(user_input)

    is_set_phrase = bool(
        _DECLARA_RE.search(normalized)
        and _PROVISIONAL_RE.search(normalized)
        and (_TRIPLE_RE.search(normalized) or _PAIR_RE.search(normalized))
    )
    if not is_set_phrase:
        return _NONE

    subject = resolve_plate_subject_noun(normalized, components)
    if isinstance(subject, MountDeclareResult):
        return EstimatedPlateDeclareResult(kind="AMBIGUOUS_PLATE", candidates=subject.candidates)
    if subject is None:
        # No plate-shaped noun matched — but if the phrase actually names a
        # DIFFERENT recognized subject (battery/sensors/esc/fc/motors/
        # propellers — this Buy's own lock #2 "not in this Buy" list),
        # this isn't a plate phrase at all: defer entirely (NONE) rather
        # than surfacing a confusing "which plate?" prompt for a battery
        # utterance. Only a genuinely subject-less provisional phrase
        # (e.g. "declara estimada 120x55mm") is INCOMPLETE.
        if resolve_component_subject_noun(normalized) is not None:
            return _NONE
        return EstimatedPlateDeclareResult(kind="INCOMPLETE")

    length_mm, width_mm, height_mm = _parse_dims(normalized)  # never None — the gate above required it
    return EstimatedPlateDeclareResult(
        kind="SET", component_key=subject,
        length_mm=length_mm, width_mm=width_mm, height_mm=height_mm,
    )
