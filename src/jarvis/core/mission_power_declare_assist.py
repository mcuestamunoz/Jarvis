"""IDLE mission component power declare — pure parse for Mission `power_w`
→ energy/autonomía (`B1-mission-power-w`).

Scoped EXCLUSIVELY to `cameras`/`radio_module` power — never invents watts
from a model name or from the Phoenix 2 citation's `200mA@5V` note
(mission-payload-identity's own claim ceiling extends here, same discipline
`mission_mass_declare_assist.py` already established for mass). Reuses
`mission_mass_declare_assist.resolve_mission_mass_subject` — the SAME
CAMERA_KEYWORDS/RADIO_KEYWORDS vocabulary the identity ComponentRules and
the mass grammar already use — so "what counts as a camera/radio phrase"
can never drift across the three grammars.

Gate: a recognized subject keyword (camera or radio) + a number + "w"/
"vatio(s)". A recognized subject with no number is INCOMPLETE — never a
guessed watt figure. Mirrors `mission_mass_declare_assist.py`'s own
thinness: deterministic parse only, no LLM, no state mutation — the
orchestrator calls `component_writers.set_mission_component_power` with
the result.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from jarvis.core.mission_mass_declare_assist import resolve_mission_mass_subject
from jarvis.core.motor_catalog_assist import _normalize_help


@dataclass(frozen=True)
class MissionPowerDeclareResult:
    kind: str  # "SET" | "INCOMPLETE" | "NONE"
    component_key: str | None = None
    power_w: float | None = None


_NONE = MissionPowerDeclareResult(kind="NONE")

# Same verbatim single-number convention as mission_mass_declare_assist's
# own grammar.
_NUM = r"(-?\d+(?:[.,]\d+)?)"
_POWER_RE = re.compile(rf"{_NUM}\s*(?:w|vatios?)\b")

# A bare subject mention alone (e.g. "cámara RunCam") must NEVER be
# intercepted by this grammar — that is the identity-declare path
# (extract_camera_properties/extract_radio_properties), untouched by this
# Buy. This module only fires (even as INCOMPLETE) when the phrase ALSO
# carries an explicit power/watt word — otherwise a subject match with no
# number returns NONE, not INCOMPLETE, so it falls through unchanged.
_POWER_WORD_RE = re.compile(r"\b(?:potencia|watt|watts|vatio|vatios)\b")


def _to_float(raw: str) -> float:
    return float(raw.replace(",", "."))


def parse_mission_power_declare(user_input: str) -> MissionPowerDeclareResult:
    """Pure parse: no state mutation, no LLM, no ``components`` lookup
    needed here (the writer itself checks the target is already
    declared).

    A bare subject phrase with neither a number nor a power word (e.g.
    "cámara RunCam") returns NONE — that is the identity-declare grammar's
    territory. INCOMPLETE only fires when a power word is present without
    a resolvable number, so this grammar never swallows a plain identity
    declare.
    """
    normalized = _normalize_help(user_input)

    subject = resolve_mission_mass_subject(normalized)
    if subject is None:
        return _NONE

    match = _POWER_RE.search(normalized)
    if match is not None:
        return MissionPowerDeclareResult(
            kind="SET", component_key=subject, power_w=_to_float(match.group(1))
        )

    if _POWER_WORD_RE.search(normalized):
        return MissionPowerDeclareResult(kind="INCOMPLETE", component_key=subject)

    return _NONE
