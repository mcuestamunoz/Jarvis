"""
acquisition_target
===================
FN-014 — unified block ∪ component mention resolution for the IDLE acquisition
gate.
FN-015 — generic "help me define the pending value" phrase detection, added
here (rather than motor_catalog_assist.py) because it needs to cross-check
against the same block-alias/declare-verb machinery this module already
owns, and it is not motor-specific.
FN-016 — navigation-back phrase detection ("atrás"/"volver"), added here for
the same reason: this module is already the shared phrase-classification
helper consumed by both orchestrator.py and param_definition_session.py, so
adding a third detector here avoids a new module. The word list itself lives
in jarvis.config (NAVIGATION_BACK_WORDS) — single source of truth, same
pattern as ESCAPE_WORDS/NEW_PROJECT_WORDS.

Resolves free text ("definir propellers", "definir propulsión") to a canonical
architecture block OR component key belonging to a block, without introducing
a second inference engine:

- Block mentions reuse ``system_architecture_catalog.normalize_block_alias``
  (the same table SystemDefinitionSession already uses).
- Component mentions use a small explicit token/alias table
  (``COMPONENT_TERM_ALIASES``) — naming the gap, not parsing a free-text spec.
  ``infer_component()`` (component_inference.py) is a different concern: it
  extracts properties from a full description like "4 motores 920kv", not
  "is this word a component name".

Module rule (same as system_architecture_catalog.py): no imports from
jarvis.schemas — this module returns plain dicts/strings only and reads
ProjectState-shaped objects via duck typing (getattr), so it stays usable from
tests with SimpleNamespace fixtures too.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Literal, TypedDict

from jarvis.config import NAVIGATION_BACK_WORDS
from jarvis.core.intent_resolver import IntentResolver
from jarvis.core.system_architecture_catalog import BLOCK_TO_COMPONENTS, normalize_block_alias

# Reuses IntentResolver.DECLARE_BLOCK_VERB_PATTERNS as the single source of
# truth for "this text explicitly requests declaring/completing something"
# (declarar/completar/definir/configurar/especificar) — no duplicated verb
# list, no change to intent_resolver.py. Without this gate, a plain
# description that happens to contain a block/component word (e.g.
# "estructura de fibra de carbono", a material spec for the frame component)
# would be misread as a declare-request instead of falling through to the
# component-description intercept that actually parses it.
_DECLARE_VERB_RE = tuple(
    re.compile(p) for p in IntentResolver.DECLARE_BLOCK_VERB_PATTERNS
)


def _has_declare_verb(user_input: str) -> bool:
    lowered = user_input.strip().lower()
    return any(rx.search(lowered) for rx in _DECLARE_VERB_RE)


def _normalize(text: str) -> str:
    """Lowercase + strip diacritics (NFD). Same policy as the catalog module."""
    nfd = unicodedata.normalize("NFD", text.strip().lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


# Free-text token (post-normalize) → canonical component key.
# Token/alias lookup only — matched against whole words, never substrings, so
# "motor" cannot fire inside "motorizacion" and "helice" cannot fire inside a
# longer unrelated word. Extend this table, never call infer_component() here.
COMPONENT_TERM_ALIASES: dict[str, str] = {
    "propellers": "propellers",
    "propeller": "propellers",
    "helices": "propellers",
    "helice": "propellers",
    "palas": "propellers",
    "motors": "motors",
    "motores": "motors",
    "motor": "motors",
    "battery": "battery",
    "bateria": "battery",
    "frame": "frame",
    "chasis": "frame",
    "flight_controller": "flight_controller",
    "controladora": "flight_controller",
    "sensors": "sensors",
    "sensores": "sensors",
}

# FN-017 B1/B5: moved here (from orchestrator.py) so both orchestrator.py and
# param_definition_session.py can import the SAME dict without a circular
# import (orchestrator.py already imports param_definition_session.py at
# module load time, so the reverse import is not possible). Single source of
# truth for the concrete "describe this component" prompt per key — used by
# _handle_component_description's follow-ups AND ParamDefinitionSession.start()'s
# opening question for a component-definition wizard.
COMPONENT_PROMPTS: dict[str, str] = {
    "frame":             "Describe el frame del dron (material y masa). Ej: 'fibra de carbono 450g'",
    "flight_controller": "Describe la controladora de vuelo. Ej: 'Pixhawk 4' o 'Betaflight F7'",
    "sensors":           "Describe el GPS/sensores. Ej: 'GPS M9N' o 'Here3'",
    "battery":           "Describe la batería. Ej: 'LiPo 6S 5000mAh' o '100Wh'",
    "motors":            "Describe los motores. Ej: '4x 2306 2400KV 50W'",
    "propellers":        "Describe las hélices. Ej: '10x4.5' o 'hélices de carbono'",
}


class AcquisitionMention(TypedDict):
    kind: Literal["block", "component"]
    key: str
    block_key: str


def resolve_acquisition_mention(
    user_input: str,
    project_state: Any,
    *,
    pending_block_key: str | None = None,
) -> AcquisitionMention | None:
    """Resolve free text to a block or component mention, deterministically.

    Requires an explicit declare/complete-style verb (same gate FN-011 already
    applied via IntentResolver.DECLARE_BLOCK_VERB_PATTERNS) — a bare mention of
    a block/component word with no such verb is NOT a declare-request and must
    return None, so richer free-text component descriptions (e.g. "estructura
    de fibra de carbono", a material spec for the frame component) keep
    falling through to the component-description intercept that actually
    parses them, instead of being swallowed here as a vague "declare frame".

    Resolution order:
      1. ``normalize_block_alias(user_input)`` → block mention.
      2. Whole-word lookup in ``COMPONENT_TERM_ALIASES`` → component mention;
         owning block is the block in ``system_priority`` that lists the key
         in ``BLOCK_TO_COMPONENTS`` — preferring ``pending_block_key`` when it
         qualifies (a component can belong to more than one block, e.g.
         "motors" in both propulsion and energy), else the first qualifying
         block in priority order.
      3. ``None`` — no verb, or no known term mentioned.

    Never invents block membership: a component with no qualifying block in
    ``system_priority`` resolves to ``None``.
    """
    if not _has_declare_verb(user_input):
        return None

    block = normalize_block_alias(user_input)
    if block is not None:
        return {"kind": "block", "key": block, "block_key": block}

    normalized = _normalize(user_input)
    for token in normalized.split():
        component_key = COMPONENT_TERM_ALIASES.get(token)
        if component_key is None:
            continue
        owning_block = _owning_block_for_component(
            component_key, project_state, pending_block_key=pending_block_key
        )
        if owning_block is None:
            continue
        return {"kind": "component", "key": component_key, "block_key": owning_block}
    return None


def _owning_block_for_component(
    component_key: str,
    project_state: Any,
    *,
    pending_block_key: str | None,
) -> str | None:
    priority = list(getattr(project_state.design_properties, "system_priority", None) or [])
    candidates = [b for b in priority if component_key in BLOCK_TO_COMPONENTS.get(b, [])]
    if not candidates:
        return None
    if pending_block_key is not None and pending_block_key in candidates:
        return pending_block_key
    return candidates[0]


def is_mention_on_active_gap(
    mention: AcquisitionMention,
    pending_block_key: str | None,
    project_state: Any,
) -> bool:
    """True iff the mention refers to the block that is genuinely the current
    pending gap (caller-supplied, from ``_next_pending_block``) — never a
    cross-block jump, and never invented.

    For a component mention, additionally requires the component to still be
    missing/low on that block — the exact Phase-A criterion already used by
    ``_set_pending_next_block`` (``spec is None or spec.completeness == "low"``).
    """
    if pending_block_key is None:
        return False
    if mention["block_key"] != pending_block_key:
        return False
    if mention["kind"] == "block":
        return True
    components = project_state.design_properties.components
    spec = components.get(mention["key"])
    if spec is None:
        return True
    return (getattr(spec, "completeness", "low") or "low") == "low"


# FN-015: fixed catch-phrases that mean "help me define the pending value"
# on their own, with no "ayudame" prefix required.
_EXACT_HELP_DEFINE_PHRASES: frozenset[str] = frozenset({
    "como lo defino",
    "no se que poner",
})

# FN-015: markers that, combined with "ayudame", mean generic define-help
# (not a real analysis/explanation question). Deliberately narrow — see
# is_help_define_pending_phrase for the full gate.
_HELP_DEFINE_MARKERS: tuple[str, ...] = ("definir", "valor", "poner")


def is_help_define_pending_phrase(user_input: str) -> bool:
    """FN-015: generic "help me define the current pending value" phrase —
    no named block/component/model. Distinct from:

    - FN-005 ``is_help_choose_phrase`` (motor catalog help: "elegir"/
      "escoger"/"motor"/"opcion") — explicitly excluded first.
    - FN-011/013/014 named-target declare requests ("ayúdame a declarar
      propulsión") — excluded when the text both has a declare verb AND
      resolves to a real block via ``normalize_block_alias``; that is
      FN-013/014's territory, right block or wrong. Component-only mentions
      (e.g. "definir propellers" with no "ayudame") are NOT excluded here —
      nothing else currently handles a bare component name inside an active
      DEFINE_MISSING wizard, and the outcome (help for that pending item) is
      identical to the generic pending-help path anyway.
    - Real analysis/explanation questions ("analiza el margen de
      seguridad") — never match (no "ayudame", not a fixed catch-phrase).
    """
    from jarvis.core.motor_catalog_assist import is_help_choose_phrase

    if is_help_choose_phrase(user_input):
        return False
    if _has_declare_verb(user_input) and normalize_block_alias(user_input) is not None:
        return False

    normalized = _normalize(user_input)
    if normalized in _EXACT_HELP_DEFINE_PHRASES:
        return True
    if "ayudame" not in normalized:
        return False
    return any(marker in normalized for marker in _HELP_DEFINE_MARKERS)


def is_navigation_back_phrase(user_input: str) -> bool:
    """FN-016: exact-match navigation word ("atrás"/"volver"/"vuelve") — never
    a value, never a skip, never help. Whole normalized input must equal one
    of NAVIGATION_BACK_WORDS (jarvis.config) — not a substring/token match, so
    it never fires inside a real description or a longer sentence.

    Deliberately NOT merged into ESCAPE_WORDS: this is scoped to acquisition
    wizards by the caller (DEFINE_MISSING_PARAMETERS / ParamDefinitionSession),
    not a global command.
    """
    return _normalize(user_input) in NAVIGATION_BACK_WORDS
