"""IDLE catalog-bound refresh — pure parse for Catalog-bound Property
Freshness B1.

Mirrors ``mounted_on_declare_assist``'s thinness: a deterministic phrase
parser, no LLM, no state mutation. The orchestrator calls
``jarvis.core.component_writers.refresh_component_from_catalog`` with the
resolved key — this module never writes anything and never checks whether
the component is actually catalog-bound (that honesty check, and the
"nothing to refresh" error, belong to the writer).

Gate: "actualiza(r)"/"refresca(r)" (+ optional "desde/del catálogo") plus a
recognized subject noun. A bare status phrase with no subject noun
(e.g. "hay que actualizar algo") stays NONE — no invented target.
"""
from __future__ import annotations

import re

from jarvis.core.motor_catalog_assist import _normalize_help

_GATE_RE = re.compile(r"\b(?:actualiza(?:r)?|refresca(?:r)?)\b")

# Exactly the 5 catalog-bindable families locked by §3.2 — no flight_controller
# (FC has no CatalogRef.family/bind path at all; out of scope per this IC).
_SUBJECT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("esc", re.compile(r"\besc\b")),
    ("motors", re.compile(r"\b(?:motores|motor)\b")),
    ("battery", re.compile(r"\b(?:baterias|bateria|batteries|battery)\b")),
    ("frame", re.compile(r"\b(?:frame|chasis)\b")),
    ("propellers", re.compile(r"\b(?:helices|helice|propellers|propeller)\b")),
)


def resolve_catalog_refresh_component(user_input: str) -> str | None:
    """Return the canonical component key to refresh, or None when the
    phrase isn't a catalog-refresh request at all (no gate verb, or no
    recognized subject noun)."""
    normalized = _normalize_help(user_input)
    if not _GATE_RE.search(normalized):
        return None
    for key, pattern in _SUBJECT_PATTERNS:
        if pattern.search(normalized):
            return key
    return None
