"""IDLE catalog rebind — resolve which family the user named.

B2 shipped frame-only (``is_frame_rebind_phrase``). B3 extends the same
bridge to motors / propellers / battery. Bare ``"ayúdame a elegir"`` (no
family noun) returns ``None`` so FN-005's motor→propeller→battery triage
stays unchanged.

Phrases that name a SKU/value after the family (e.g. ``"definir bateria
lipo_6s_10000mah"``) also return ``None`` — those keep the existing
free-text / SKU-token bind paths.
"""
from __future__ import annotations

import re
from typing import Literal

from jarvis.core.motor_catalog_assist import _normalize_help

CatalogRebindKey = Literal["frame", "motors", "propellers", "battery"]

_REBIND_VERB_RE = re.compile(r"\b(?:cambiar|cambia|definir|define|modificar|modifica)\b")
_HELP_CHOOSE_SOFT_RE = re.compile(r"\bayudame\b.*\b(?:elegir|escoger)\b")

# Priority when multiple nouns appear (pathological): frame > motors >
# propellers > battery. Normal user phrases name exactly one family.
_FAMILY_NOUN_PATTERNS: tuple[tuple[CatalogRebindKey, re.Pattern[str]], ...] = (
    ("frame", re.compile(r"\b(?:frame|chasis)\b")),
    ("motors", re.compile(r"\b(?:motores|motor)\b")),
    ("propellers", re.compile(r"\b(?:helices|helice|propellers|propeller)\b")),
    ("battery", re.compile(r"\b(?:baterias|bateria|batteries|battery)\b")),
)

# Tokens stripped when checking that the phrase is a pure reopen request
# (no trailing SKU / "a lipo_…" payload).
_PURE_PHRASE_STRIP_RE = re.compile(
    r"\b(?:ayudame|elegir|escoger|cambiar|cambia|definir|define|modificar|modifica|"
    r"el|la|los|las|de|del|un|una|al|a|"
    r"frame|chasis|motores|motor|helices|helice|propellers|propeller|"
    r"baterias|bateria|batteries|battery)\b"
)


def _is_pure_rebind_phrase(normalized: str) -> bool:
    residual = _PURE_PHRASE_STRIP_RE.sub(" ", normalized)
    residual = re.sub(r"\s+", " ", residual).strip()
    return residual == ""


def resolve_idle_catalog_rebind(user_input: str) -> CatalogRebindKey | None:
    """Return the catalog family to re-offer, or None if not a named rebind."""
    normalized = _normalize_help(user_input)
    if not (
        _HELP_CHOOSE_SOFT_RE.search(normalized) or _REBIND_VERB_RE.search(normalized)
    ):
        return None
    if not _is_pure_rebind_phrase(normalized):
        return None
    for key, pattern in _FAMILY_NOUN_PATTERNS:
        if pattern.search(normalized):
            return key
    return None


def is_frame_rebind_phrase(user_input: str) -> bool:
    """B2 compatibility wrapper — True iff the named rebind target is frame."""
    return resolve_idle_catalog_rebind(user_input) == "frame"
