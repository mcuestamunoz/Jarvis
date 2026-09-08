"""IDLE `mounted_on` declare/clear — pure parse for Continuity B1.

Mirrors ``catalog_rebind_assist``'s thinness: a deterministic phrase parser,
no LLM, no state mutation. The orchestrator calls
``jarvis.core.component_writers.set_component_mounted_on`` with the result —
this module never writes anything and never validates against a live
``ComponentSpec`` beyond reading declared frame-part labels for target
resolution.

Kinds:
  SET               — (component_key, target_key) both resolved, ready to write.
  CLEAR             — (component_key,) — clear the declared mount.
  AMBIGUOUS_TARGET  — component_key resolved, target is not — ``candidates``
                       lists known frame-plate keys/labels when the ambiguity
                       is "which plate" (2+ plates, bare "placa"/"plate");
                       an EMPTY ``candidates`` tuple means the named target
                       token matched nothing declared at all (still surfaced
                       as "ambiguous/unresolved", not silently NONE, so the
                       orchestrator can give an honest message instead of
                       falling through to the LLM on a clearly mount-shaped
                       phrase).
  NONE              — not a mount declare/clear phrase at all (no gate
                       phrase matched, or no recognizable subject noun) —
                       falls through to the caller's normal routing.

Subject resolution never depends on whether the key is actually present in
``components`` — that check is the orchestrator's job (it can then give the
locked "aún no declarado" honest error instead of this module inventing a
component). Target resolution DOES depend on ``components`` — a target must
already exist to be named.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from jarvis.core.motor_catalog_assist import _normalize_help
from jarvis.domains.aerial import is_frame_plate_key


@dataclass(frozen=True)
class MountDeclareResult:
    kind: str  # "SET" | "CLEAR" | "AMBIGUOUS_TARGET" | "NONE"
    component_key: str | None = None
    target_key: str | None = None
    candidates: tuple[tuple[str, str], ...] = field(default_factory=tuple)


_NONE = MountDeclareResult(kind="NONE")

# ── Gate phrases ─────────────────────────────────────────────────────────────

_CLEAR_RE = re.compile(
    r"\bquita(?:r)?\s+(?:el\s+)?montaje\b|\bsin\s+montaje\b|\bdesmonta(?:r)?\b"
)
_SET_DIRECT_RE = re.compile(r"\bmontad[ao]s?\s+en\b|\bmontar\s+en\b")
_SET_VERB_RE = re.compile(r"\bmonta\s+(?:el|la|los|las)\b")
_FIJA_RE = re.compile(r"\bfija(?:r)?\b")
_EN_RE = re.compile(r"\ben\b")

# ── Subject nouns → canonical component key (fixed priority order) ──────────

_SUBJECT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("flight_controller", re.compile(r"\b(?:fc|flight\s*controller|controladora|pixhawk)\b")),
    ("esc", re.compile(r"\besc\b")),
    ("motors", re.compile(r"\b(?:motores|motor)\b")),
    ("battery", re.compile(r"\b(?:baterias|bateria|batteries|battery)\b")),
    ("sensors", re.compile(r"\b(?:sensores|sensor|gps|here3)\b")),
    ("propellers", re.compile(r"\b(?:helices|helice|propellers|propeller)\b")),
)

# ── Target nouns → canonical frame-part key ──────────────────────────────────

_ARM_RE = re.compile(r"\b(?:brazos?|arms?)\b")
_CAGE_RE = re.compile(r"\b(?:jaula|cage)\b")
_STANDOFF_RE = re.compile(r"\b(?:standoff|separadores?)\b")
_FRAME_ROOT_RE = re.compile(r"\b(?:frame|chasis)\b")
_PLATE_BARE_RE = re.compile(r"\b(?:placas?|plates?)\b")


def _resolve_subject(normalized: str) -> str | None:
    for key, pattern in _SUBJECT_PATTERNS:
        if pattern.search(normalized):
            return key
    return None


def _exact_key_match(normalized: str, components: dict) -> str | None:
    for key in components:
        key_norm = _normalize_help(key)
        spaced = key_norm.replace("_", " ")
        if re.search(rf"\b{re.escape(key_norm)}\b", normalized) or re.search(
            rf"\b{re.escape(spaced)}\b", normalized
        ):
            return key
    return None


def _plate_label(components: dict, key: str) -> str:
    spec = components.get(key)
    props = getattr(spec, "properties", None) or {}
    label_prop = props.get("label")
    value = getattr(label_prop, "value", None) if label_prop is not None else None
    return str(value) if value else "—"


def _label_match(normalized: str, components: dict) -> list[str]:
    matches: list[str] = []
    for key in components:
        if not is_frame_plate_key(key):
            continue
        label = _plate_label(components, key)
        if label == "—":
            continue
        label_norm = _normalize_help(label)
        if label_norm and label_norm in normalized:
            matches.append(key)
    return matches


def _resolve_target(normalized: str, components: dict) -> MountDeclareResult | str | None:
    """Returns a resolved target key (str), an AMBIGUOUS_TARGET result, or
    None when no target-shaped token was found at all (caller decides what
    None means at the SET-gate level)."""
    exact = _exact_key_match(normalized, components)
    if exact is not None:
        return exact

    label_matches = _label_match(normalized, components)
    if len(label_matches) == 1:
        return label_matches[0]
    if len(label_matches) > 1:
        return MountDeclareResult(
            kind="AMBIGUOUS_TARGET",
            candidates=tuple(sorted((k, _plate_label(components, k)) for k in label_matches)),
        )

    if _ARM_RE.search(normalized) and "frame_arm" in components:
        return "frame_arm"
    if _CAGE_RE.search(normalized) and "frame_cage" in components:
        return "frame_cage"
    if _STANDOFF_RE.search(normalized) and "frame_standoff" in components:
        return "frame_standoff"
    if _FRAME_ROOT_RE.search(normalized) and "frame" in components:
        return "frame"

    if _PLATE_BARE_RE.search(normalized):
        plate_keys = sorted(k for k in components if is_frame_plate_key(k))
        if len(plate_keys) == 1:
            return plate_keys[0]
        if len(plate_keys) >= 2:
            return MountDeclareResult(
                kind="AMBIGUOUS_TARGET",
                candidates=tuple((k, _plate_label(components, k)) for k in plate_keys),
            )
        # zero plates declared — nothing to resolve to
        return None

    # Conn B1: component-noun aliases (the same fixed-priority table used
    # for subjects, e.g. "motores" -> motors, "esc" -> esc) — scoped to the
    # TARGET segment only, and only when that key already exists in
    # components. Never invents a key. This is what lets "hélices montadas
    # en los motores" resolve a target at all — "motores" is not a frame
    # part noun, it's an electronics/propulsion key phrased in Spanish.
    alias = _resolve_target_component_alias(normalized, components)
    if alias is not None:
        return alias

    return None


def _resolve_target_component_alias(normalized: str, components: dict) -> str | None:
    for key, pattern in _SUBJECT_PATTERNS:
        if pattern.search(normalized) and key in components:
            return key
    return None


def parse_mounted_on_declare(user_input: str, components: dict) -> MountDeclareResult:
    """Pure parse: no state mutation, no LLM. ``components`` is
    ``design_properties.components`` (or an equivalent dict) — used only to
    resolve/validate targets, never to invent a subject."""
    normalized = _normalize_help(user_input)

    if _CLEAR_RE.search(normalized):
        subject = _resolve_subject(normalized)
        if subject is None:
            return _NONE
        return MountDeclareResult(kind="CLEAR", component_key=subject)

    is_set_phrase = bool(
        _SET_DIRECT_RE.search(normalized)
        or (_SET_VERB_RE.search(normalized) and _EN_RE.search(normalized))
        or (_FIJA_RE.search(normalized) and _EN_RE.search(normalized))
    )
    if not is_set_phrase:
        return _NONE

    en_match = _EN_RE.search(normalized)
    # Conn B1: subject resolution is scoped to the text BEFORE the first
    # "en" — the exact mirror of the target-segment discipline below.
    # Without this, "helices montadas en los motores" misresolved "motors"
    # as the subject: "motores" also matches the motors subject pattern,
    # which outranks propellers in the fixed priority table, and the old
    # code scanned the WHOLE phrase for a subject with no positional
    # awareness. Scoping to "before en" means the target segment's own
    # nouns can never leak into subject resolution.
    subject_segment = normalized[:en_match.start()] if en_match else normalized
    subject = _resolve_subject(subject_segment)
    if subject is None:
        return _NONE

    # Target resolution only looks AFTER the first "en" — never at the
    # subject's own text before it — so e.g. "esc montado en frame_plate"
    # can never resolve "esc" itself as its own target.
    target_segment = normalized[en_match.end():] if en_match else ""

    target = _resolve_target(target_segment, components)
    if isinstance(target, MountDeclareResult):
        return MountDeclareResult(
            kind="AMBIGUOUS_TARGET", component_key=subject, candidates=target.candidates
        )
    if target is None:
        return MountDeclareResult(kind="AMBIGUOUS_TARGET", component_key=subject, candidates=())
    return MountDeclareResult(kind="SET", component_key=subject, target_key=target)


# ── Public wrappers (Continuity Declared Box-Local Pose B1) ─────────────────
#
# Thin, behavior-preserving re-exports of this module's own noun-resolution
# internals, so a sibling assist (declared_box_pose_declare_assist.py) can
# reuse the exact same subject/part-noun tables instead of duplicating them.
# Neither wrapper changes what the underlying function returns — they exist
# only so a second module never has to import a private (`_`-prefixed) name.


def resolve_component_subject_noun(normalized: str) -> str | None:
    """Public alias of ``_resolve_subject`` — canonical component key for a
    recognized subject noun (fc/esc/motor(es)/bateria/sensor(es)/helice(s)),
    or ``None``. Does not check whether the key is actually declared."""
    return _resolve_subject(normalized)


def resolve_declared_part_noun(
    normalized: str, components: dict
) -> MountDeclareResult | str | None:
    """Public alias of ``_resolve_target`` — a resolved component key
    (``str``), an ``AMBIGUOUS_TARGET``-kind ``MountDeclareResult`` carrying
    plate candidates, or ``None`` when no target-shaped token was found at
    all. ``components`` is used only to resolve/validate — never to invent
    a key that isn't declared."""
    return _resolve_target(normalized, components)
