"""IDLE estimated-temporary ESC height declare — pure parse for
Estimated-temporary ESC height (Skystars KO50A II) B1
(`B1-estimated-temporary-esc-skystars`).

Scoped EXCLUSIVELY to the ESC subject — never battery/sensors/plate/
frame_arm/motors/fc/propellers. This is a HYBRID completion, not a full
provisional envelope: unlike `estimated_temporary_plate_assist` (which
sets all three axes at once, since a plate has no prior cited fact), an
ESC bound to catalog already has cited `length_mm`/`width_mm` — this
grammar only ever supplies the ONE axis catalog evidence never covered
(H), never re-stating or overwriting the cited L/W.

Gate requires ALL of: "declara(r)", a provisional keyword (estimada/
estimado/temporal/provisional), the ESC subject noun specifically
(reuses `mounted_on_declare_assist.resolve_component_subject_noun`'s own
table — no second alias table; a DIFFERENT subject, e.g. "declara la
bateria estimada...", defers to NONE so it never steals a phrase this
module has no business answering), and exactly one "<N> mm" number. A
recognized ESC-provisional phrase with no number is INCOMPLETE, never a
guessed height.

Mirrors `mounted_on_declare_assist`/`estimated_temporary_plate_assist`'s
own thinness: deterministic parse only, no LLM, no state mutation. The
orchestrator calls `component_writers.set_estimated_temporary_esc_height`
with the result.

Kinds:
  SET         — height_mm resolved (component_key is always "esc").
  INCOMPLETE  — the gate fired (declara + provisional + esc noun) but no
                "<N> mm" number was found.
  NONE        — not this grammar at all: no gate phrase, no provisional
                keyword, or the named subject isn't ESC (a different
                recognized subject, or none) — falls through unchanged.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from jarvis.core.motor_catalog_assist import _normalize_help
from jarvis.core.mounted_on_declare_assist import resolve_component_subject_noun


@dataclass(frozen=True)
class EstimatedEscHeightDeclareResult:
    kind: str  # "SET" | "INCOMPLETE" | "NONE"
    component_key: str | None = None
    height_mm: float | None = None


_NONE = EstimatedEscHeightDeclareResult(kind="NONE")

_DECLARA_RE = re.compile(r"\bdeclara(?:r)?\b")
_PROVISIONAL_RE = re.compile(r"\b(?:estimad[ao]s?|temporal(?:es)?|provisional(?:es)?)\b")

# Same verbatim-print-order single-number convention as
# estimated_temporary_plate_assist's own dims grammar — deliberately
# duplicated (one line) rather than importing that module's private
# `_NUM`, matching this codebase's own established convention of never
# reaching into another module's `_`-prefixed internals.
_NUM = r"(-?\d+(?:[.,]\d+)?)"
_HEIGHT_RE = re.compile(rf"{_NUM}\s*mm\b")


def _to_float(raw: str) -> float:
    return float(raw.replace(",", "."))


def parse_estimated_temporary_esc_height_declare(user_input: str) -> EstimatedEscHeightDeclareResult:
    """Pure parse: no state mutation, no LLM, no ``components`` lookup
    needed (the subject is always the literal ``"esc"`` key — the writer
    itself, not this parser, is what checks the ESC is actually declared
    and already has cited L×W)."""
    normalized = _normalize_help(user_input)

    is_gate = bool(_DECLARA_RE.search(normalized) and _PROVISIONAL_RE.search(normalized))
    if not is_gate:
        return _NONE

    subject = resolve_component_subject_noun(normalized)
    if subject != "esc":
        # Not an ESC phrase at all (a different recognized subject, or
        # none) — never this module's business; falls through unchanged
        # (e.g. to estimated_temporary_plate_assist for a plate phrase).
        return _NONE

    match = _HEIGHT_RE.search(normalized)
    if match is None:
        return EstimatedEscHeightDeclareResult(kind="INCOMPLETE", component_key="esc")

    return EstimatedEscHeightDeclareResult(
        kind="SET", component_key="esc", height_mm=_to_float(match.group(1))
    )
