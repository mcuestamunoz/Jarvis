"""IDLE mission component mass declare — pure parse for Mission mass → AUW
+ Continuity ladder (`B1-mission-mass-energy`).

Scoped EXCLUSIVELY to `cameras`/`radio_module` mass — never invents grams
from a model name (mission-payload-identity's own claim ceiling extends
here: `extract_camera_properties`/`extract_radio_properties` never read a
digit from the message for mass, and this module is the ONLY path that
ever sets `mass_g`). Reuses `aerial.CAMERA_KEYWORDS`/`RADIO_KEYWORDS` — the
SAME vocabulary the identity ComponentRules already use — so this grammar
and "what counts as a camera/radio phrase" can never drift apart.

Gate: a recognized subject keyword (camera or radio) + a number + "g"/
"gramos". A recognized subject with no number is INCOMPLETE — never a
guessed mass. Mirrors `estimated_temporary_esc_assist.py`'s own thinness:
deterministic parse only, no LLM, no state mutation — the orchestrator
calls `component_writers.set_mission_component_mass` with the result.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from jarvis.core.motor_catalog_assist import _normalize_help
from jarvis.domains.aerial import CAMERA_KEYWORDS, RADIO_KEYWORDS


@dataclass(frozen=True)
class MissionMassDeclareResult:
    kind: str  # "SET" | "INCOMPLETE" | "NONE"
    component_key: str | None = None
    mass_g: float | None = None


_NONE = MissionMassDeclareResult(kind="NONE")

# Same verbatim single-number convention as estimated_temporary_esc_assist's
# own dims grammar.
_NUM = r"(-?\d+(?:[.,]\d+)?)"
_MASS_RE = re.compile(rf"{_NUM}\s*(?:g|gramos?)\b")

# A bare subject mention alone (e.g. "cámara RunCam") must NEVER be
# intercepted by this grammar — that is the identity-declare path
# (extract_camera_properties/extract_radio_properties), untouched by this
# Buy. This module only fires (even as INCOMPLETE) when the phrase ALSO
# carries an explicit mass/weight word — otherwise a subject match with no
# number returns NONE, not INCOMPLETE, so it falls through unchanged.
_MASS_WORD_RE = re.compile(r"\b(?:masa|peso|pesa|mass|weight)\b")


def _to_float(raw: str) -> float:
    return float(raw.replace(",", "."))


def resolve_mission_mass_subject(normalized: str) -> str | None:
    """Longest-keyword-wins subject resolution — camera vs radio. Mirrors
    `aerial.py`'s own `ComponentRule` keyword tuples exactly (no second
    list). ``normalized`` is expected to already be accent-stripped
    (``_normalize_help``) — the accented keyword variants in the shared
    tuples simply never match against an accent-stripped string, which is
    harmless (the unaccented variant always covers the same ground)."""
    found_key: str | None = None
    found_len = 0
    for kw in CAMERA_KEYWORDS:
        if kw in normalized and len(kw) > found_len:
            found_key, found_len = "cameras", len(kw)
    for kw in RADIO_KEYWORDS:
        if kw in normalized and len(kw) > found_len:
            found_key, found_len = "radio_module", len(kw)
    return found_key


def parse_mission_mass_declare(user_input: str) -> MissionMassDeclareResult:
    """Pure parse: no state mutation, no LLM, no ``components`` lookup
    needed here (the writer itself checks the target is already
    declared — lock #7c's honest refuse).

    A bare subject phrase with neither a number nor a mass word (e.g.
    "cámara RunCam") returns NONE — that is the identity-declare grammar's
    territory, never this module's. INCOMPLETE only fires when a mass
    word is present without a resolvable number (e.g. "cuánto pesa la
    cámara"), so this grammar never swallows a plain identity declare.
    """
    normalized = _normalize_help(user_input)

    subject = resolve_mission_mass_subject(normalized)
    if subject is None:
        return _NONE

    match = _MASS_RE.search(normalized)
    if match is not None:
        return MissionMassDeclareResult(
            kind="SET", component_key=subject, mass_g=_to_float(match.group(1))
        )

    if _MASS_WORD_RE.search(normalized):
        return MissionMassDeclareResult(kind="INCOMPLETE", component_key=subject)

    return _NONE
