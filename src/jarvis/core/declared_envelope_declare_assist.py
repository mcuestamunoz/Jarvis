"""IDLE declared box-envelope declare/clear — pure parse for Declared
battery envelope + Main Plate L×W B1, extended by Declared sensors + kit
envelope B1, Top LiPo plate (`frame_plate_2`) envelope noun B1, Frame arm
envelope + visor X copies B1, and Loose structure/kit envelopes + pose
subjects B1 (`prop_adapter`/`frame_standoff`/`frame_cage`/`frame_caps`).

Mirrors ``declared_box_pose_declare_assist``'s thinness: a deterministic
phrase parser, no LLM, no state mutation. The orchestrator calls
``jarvis.core.component_writers.set_component_declared_box_envelope`` with
the result — this module never writes anything.

Scope: ``battery``, ``sensors`` (existing subject-noun table — resolves
regardless of whether the key is declared, same as ``battery``; the
orchestrator gives the "aún no declarado" error), any frame-plate key
(``is_frame_plate_key``), and exactly two kit keys — ``power_connector``/
``signal_harness`` (resolved from acquisition-style nouns — conector/xt60/
harness/"cable de señal" — but ONLY when that key already exists in
``components``; a matching noun with no such key present is treated as "no
subject", same as zero plates declared for a bare "placa"). Never ``frame``
root, arms, cage, standoff, motors, ESC, FC, or propellers. Reuses
``mounted_on_declare_assist``'s public wrappers
(``resolve_component_subject_noun``/``resolve_declared_part_noun``) for noun
resolution rather than duplicating those tables — never imports their
private (``_``-prefixed) internals.

Kinds:
  SET             — component_key + length_mm/width_mm resolved, and either
                     height_mm resolved (three numbers named) or ``None``
                     (two numbers named, plate path ONLY — the ORCHESTRATOR
                     fills the third axis from that spec's own
                     ``thickness_mm`` at apply time; this parser never
                     invents a number). Battery/sensors/kit never get a
                     thickness fallback — they always require all three.
  CLEAR           — component_key — clear the declared envelope.
  AMBIGUOUS_PLATE — a plate-shaped subject reference (bare "placa"/"plate",
                     or a label match) resolved to 2+ candidates.
                     ``candidates`` lists (key, label) pairs.
  INCOMPLETE      — the SET/CLEAR gate fired but no recognized subject was
                     found (SET-shaped only — a CLEAR with no subject is
                     ``NONE``, mirroring the mount-declare precedent), or a
                     battery/sensors/kit phrase named only two numbers (a
                     box needs all three for those families — height is
                     never inferred), or a plate phrase named two numbers
                     and that plate has no ``thickness_mm`` to fall back on.
  NONE            — not an envelope declare/clear phrase at all (no gate
                     phrase, no A×B[×C] mm shape, or ``respecto`` present —
                     that grammar belongs to
                     ``declared_box_pose_declare_assist``, never this
                     module) — falls through to the caller's normal routing.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from jarvis.core.motor_catalog_assist import _normalize_help
from jarvis.core.mounted_on_declare_assist import (
    MountDeclareResult,
    resolve_component_subject_noun,
    resolve_declared_part_noun,
)
from jarvis.domains.aerial import is_frame_plate_key


@dataclass(frozen=True)
class EnvelopeDeclareResult:
    kind: str  # "SET" | "CLEAR" | "AMBIGUOUS_PLATE" | "INCOMPLETE" | "NONE"
    component_key: str | None = None
    length_mm: float | None = None
    width_mm: float | None = None
    height_mm: float | None = None
    candidates: tuple[tuple[str, str], ...] = field(default_factory=tuple)


_NONE = EnvelopeDeclareResult(kind="NONE")

# ── Gate phrases ─────────────────────────────────────────────────────────────
_DECLARA_RE = re.compile(r"\bdeclara(?:r)?\b")
_RESPECTO_RE = re.compile(r"\brespecto\b")
_CLEAR_RE = re.compile(
    r"\bquita(?:r)?\s+(?:el\s+)?sobre\b|\bquita(?:r)?\s+(?:las\s+)?cotas\b"
)
_MAIN_PLATE_RE = re.compile(r"\bplaca\s+principal\b|\bmain\s+plate\b")

# Top LiPo plate envelope noun B1 — mirrors `_MAIN_PLATE_RE`/`_resolve_main_plate`
# exactly: a dedicated noun that resolves by the plate's OWN label (live
# Rooster `frame_plate_2`, label "Top (LiPo) plate"), independent of the
# generic label-substring match (which requires the literal English text in
# the utterance — "placa lipo" never contains "top (lipo) plate").
_TOP_LIPO_PLATE_RE = re.compile(r"\bplaca\s+(?:top\s+)?lipo\b|\btop\s+lipo(?:\s+plate)?\b")

# Declared sensors + kit envelope B1 — kit-key nouns, reusing the same
# acquisition-style words the kit-hardware assist already recognizes
# (conector/xt60 for power_connector; harness/"cable de señal" for
# signal_harness), plus each key's own literal (underscore or spaced) name.
# Presence-gated below (`_resolve_kit_key`) — unlike battery/sensors, a
# matching noun with no such key declared is "no subject", never invented.
_KIT_KEY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("power_connector", re.compile(r"\b(?:conector(?:es)?|xt60|power[_ ]?connector)\b")),
    ("signal_harness", re.compile(r"\b(?:harness|cable\s+de\s+senal|signal[_ ]?harness)\b")),
)

# Loose structure/kit envelopes + pose subjects B1 — `prop_adapter` and
# `frame_caps` have no existing noun anywhere else in the codebase (unlike
# `frame_cage`/`frame_standoff`, which `resolve_declared_part_noun` already
# resolves for the mount-declare grammar) — a small presence-gated pattern
# table, same shape as `_KIT_KEY_PATTERNS`, is the honest minimum here
# instead of stretching an unrelated module's noun table across a module
# boundary. Presence-gated below (`_resolve_loose_key`).
_LOOSE_KEY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("prop_adapter", re.compile(r"\b(?:adaptador(?:es)?|adapters?|collets?|prop[_ ]?adapter)\b")),
    ("frame_caps", re.compile(r"\b(?:caps|tapas?|frame[_ ]?caps)\b")),
)

# ── Number-triple/pair — verbatim print order (same N2a convention the
# catalog envelope itself already uses), "x"/"×"/"por" separators, comma
# decimals. Triple checked first so "A x B x C mm" never short-circuits to
# a pair reading of its own first two numbers.
_NUM = r"(-?\d+(?:[.,]\d+)?)"
_SEP = r"\s*(?:x|×|por)\s*"
_TRIPLE_RE = re.compile(rf"{_NUM}{_SEP}{_NUM}{_SEP}{_NUM}\s*mm\b")
_PAIR_RE = re.compile(rf"{_NUM}{_SEP}{_NUM}\s*mm\b")


def _to_float(raw: str) -> float:
    return float(raw.replace(",", "."))


def _parse_dims(normalized: str) -> tuple[float, float, float | None] | None:
    triple = _TRIPLE_RE.search(normalized)
    if triple:
        return _to_float(triple.group(1)), _to_float(triple.group(2)), _to_float(triple.group(3))
    pair = _PAIR_RE.search(normalized)
    if pair:
        return _to_float(pair.group(1)), _to_float(pair.group(2)), None
    return None


def _label_of(components: dict, key: str) -> str:
    spec = components.get(key)
    props = getattr(spec, "properties", None) or {}
    label_prop = props.get("label")
    value = getattr(label_prop, "value", None) if label_prop is not None else None
    return str(value) if value else "—"


def _plates_by_normalized_label(components: dict, normalized_label: str) -> list[str]:
    """Plates whose OWN label normalizes to exactly *normalized_label* —
    shared by `"placa principal"`/`"main plate"` (-> ``"main plate"``) and
    `"placa lipo"`/`"top lipo"` (-> ``"top (lipo) plate"``). Independent of
    the generic label-substring match (``resolve_declared_part_noun``'s own
    ``_label_match``), which requires the label TEXT itself to appear in
    the utterance — neither noun literally contains its target's English
    label."""
    return [
        key
        for key in components
        if is_frame_plate_key(key) and _normalize_help(_label_of(components, key)) == normalized_label
    ]


def _resolve_main_plate(components: dict) -> list[str]:
    return _plates_by_normalized_label(components, "main plate")


def _resolve_top_lipo_plate(components: dict) -> list[str]:
    return _plates_by_normalized_label(components, "top (lipo) plate")


def _resolve_from_matches(components: dict, matches: list[str]) -> str | MountDeclareResult | None:
    """Shared single/ambiguous/none reduction for a labeled-plate noun
    match list — one plate resolves directly, 2+ becomes AMBIGUOUS_TARGET
    (candidates sorted (key, label)), 0 is "no subject" (falls through to
    the caller's own INCOMPLETE/NONE handling, never invented)."""
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return MountDeclareResult(
            kind="AMBIGUOUS_TARGET",
            candidates=tuple(sorted((k, _label_of(components, k)) for k in matches)),
        )
    return None


def resolve_kit_subject_noun(normalized: str, components: dict) -> str | None:
    """Public: resolve a kit noun (conector/xt60/power_connector,
    harness/"cable de señal"/signal_harness) to that exact key, ONLY if it
    already exists in ``components`` — unlike battery/sensors (which
    resolve regardless of presence, deferring the "aún no declarado"
    honesty check to the orchestrator), a kit noun with no matching
    declared key is treated as no subject at all, never an invented
    component.

    Extracted from the envelope grammar's own subject resolution (Declared
    sensors + kit envelope B1) so a sibling grammar (Pose Continuity
    subject: kit keys B1) can pose a kit component with the EXACT SAME
    noun set, instead of a second noun table."""
    for key, pattern in _KIT_KEY_PATTERNS:
        if pattern.search(normalized) and key in components:
            return key
    return None


def resolve_frame_arm_subject_noun(normalized: str, components: dict) -> str | None:
    """Public: resolve the frame arm noun (``"brazo"``/``"brazos"``,
    ``"arm"``/``"arms"``, or the exact key ``frame_arm``) to that ONE fixed
    key — never the four-siblings shape plates use, so no ordinal/label
    resolution is needed here. Reuses ``resolve_declared_part_noun``'s own
    existing arm-noun handling (the same bare "brazo"/"arm" regex the
    mount-declare grammar already ships, itself gated on ``"frame_arm" in
    components`` — never an invented component) rather than a new regex
    table; only accepts the result when it's specifically ``"frame_arm"``,
    since that function can also resolve unrelated nouns (cage, standoff,
    motors, …)."""
    target = resolve_declared_part_noun(normalized, components)
    return target if target == "frame_arm" else None


def _resolve_loose_key(normalized: str, components: dict) -> str | None:
    for key, pattern in _LOOSE_KEY_PATTERNS:
        if pattern.search(normalized) and key in components:
            return key
    return None


def resolve_loose_structure_subject_noun(normalized: str, components: dict) -> str | None:
    """Public: resolve ``prop_adapter``/``frame_caps`` (a small presence-
    gated pattern table — adaptador/adapter/collet, caps/tapas — no noun
    for either exists anywhere else) OR ``frame_cage``/``frame_standoff``
    (via ``resolve_declared_part_noun``'s existing jaula/cage,
    standoff/separador(es) nouns, filtered to just those two keys). ALL
    FOUR are presence-gated — a matching noun with no such key declared is
    "no subject", never invented, same discipline as
    ``resolve_kit_subject_noun``.

    Extracted as one public entry point (mirrors ``resolve_kit_subject_noun``/
    ``resolve_frame_arm_subject_noun``) so a sibling grammar (pose) can
    reuse the EXACT SAME noun set — Loose structure/kit envelopes + pose
    subjects B1."""
    loose_key = _resolve_loose_key(normalized, components)
    if loose_key is not None:
        return loose_key
    target = resolve_declared_part_noun(normalized, components)
    if isinstance(target, str) and target in ("frame_cage", "frame_standoff"):
        return target
    return None


def resolve_plate_subject_noun(normalized: str, components: dict) -> str | MountDeclareResult | None:
    """Public: resolve a frame-plate noun to a single plate key, an
    ``AMBIGUOUS_TARGET``-kind ``MountDeclareResult`` (2+ candidates), or
    ``None`` (no plate-shaped match at all). Tries, in order: Main Plate
    (``"placa principal"``/``"main plate"``), Top LiPo plate (``"placa
    lipo"``/``"top lipo"``/…), then any other plate via exact key/label
    substring/bare ``"placa"``/``"plate"`` (``resolve_declared_part_noun``,
    filtered to ``is_frame_plate_key`` results only — that function can
    also resolve frame root/arm/cage/standoff/motor/esc/fc/sensor/propeller
    nouns for the mount-declare grammar; none of those are plates, so they
    are never returned here).

    Extracted from the envelope grammar's own subject resolution (Declared
    battery envelope + Main Plate L×W B1 / Top LiPo plate envelope noun B1)
    so a sibling grammar (Pose Continuity subject: plates B1) can pose a
    plate with the EXACT SAME noun set, instead of a second noun table."""
    if _MAIN_PLATE_RE.search(normalized):
        return _resolve_from_matches(components, _resolve_main_plate(components))

    if _TOP_LIPO_PLATE_RE.search(normalized):
        return _resolve_from_matches(components, _resolve_top_lipo_plate(components))

    target = resolve_declared_part_noun(normalized, components)
    if isinstance(target, MountDeclareResult):
        # AMBIGUOUS_TARGET from resolve_declared_part_noun only ever fires
        # from a plate-shaped match (bare "placa"/"plate" or a plate label
        # substring) — its candidates are always plate candidates here.
        return target
    if isinstance(target, str) and is_frame_plate_key(target):
        return target
    return None


def _resolve_subject(normalized: str, components: dict) -> str | MountDeclareResult | None:
    """``battery``/``sensors`` (existing subject table), a present kit key
    (``power_connector``/``signal_harness``), the present ``frame_arm`` key,
    a present loose-structure key (``prop_adapter``/``frame_standoff``/
    ``frame_cage``/``frame_caps``), or any frame-plate key
    (``resolve_plate_subject_noun``) — never frame root/motors/esc/fc/
    propellers."""
    subject = resolve_component_subject_noun(normalized)
    if subject in ("battery", "sensors"):
        return subject

    kit_key = resolve_kit_subject_noun(normalized, components)
    if kit_key is not None:
        return kit_key

    arm_key = resolve_frame_arm_subject_noun(normalized, components)
    if arm_key is not None:
        return arm_key

    loose_key = resolve_loose_structure_subject_noun(normalized, components)
    if loose_key is not None:
        return loose_key

    return resolve_plate_subject_noun(normalized, components)


# battery/sensors/kit/frame_arm/loose-structure keys always require all
# three declared numbers — only a frame-plate key (checked via
# `is_frame_plate_key` at each call site below, since plate keys are
# open-ended/ordinal, not a fixed set) may fall back to a cited
# `thickness_mm` for the third axis. Some of these DO carry their own
# `thickness_mm` (e.g. the Rooster's `arm_thickness_mm` seed), but every IC
# in this family explicitly forbids borrowing it as a height fallback — a
# declared box for any of these always needs all three Engineer-typed
# numbers, never two numbers plus an inferred thickness.
_NO_THICKNESS_FALLBACK_KEYS = frozenset({
    "battery", "sensors", "power_connector", "signal_harness", "frame_arm",
    "prop_adapter", "frame_standoff", "frame_cage", "frame_caps",
})


def _thickness_mm(components: dict, key: str) -> float | None:
    spec = components.get(key)
    props = getattr(spec, "properties", None) or {}
    prop = props.get("thickness_mm")
    return prop.value if prop is not None else None


def parse_declared_envelope_declare(user_input: str, components: dict) -> EnvelopeDeclareResult:
    """Pure parse: no state mutation, no LLM. ``components`` is
    ``design_properties.components`` (or an equivalent dict) — used only to
    resolve/validate the subject, never to invent a key."""
    normalized = _normalize_help(user_input)

    if _RESPECTO_RE.search(normalized):
        return _NONE

    if _CLEAR_RE.search(normalized):
        subject = _resolve_subject(normalized, components)
        if isinstance(subject, MountDeclareResult):
            return EnvelopeDeclareResult(kind="AMBIGUOUS_PLATE", candidates=subject.candidates)
        if subject is None:
            return _NONE
        return EnvelopeDeclareResult(kind="CLEAR", component_key=subject)

    is_set_phrase = bool(
        _DECLARA_RE.search(normalized) and (_TRIPLE_RE.search(normalized) or _PAIR_RE.search(normalized))
    )
    if not is_set_phrase:
        return _NONE

    dims = _parse_dims(normalized)
    subject = _resolve_subject(normalized, components)
    if isinstance(subject, MountDeclareResult):
        return EnvelopeDeclareResult(kind="AMBIGUOUS_PLATE", candidates=subject.candidates)
    if subject is None:
        return EnvelopeDeclareResult(kind="INCOMPLETE")

    length_mm, width_mm, height_mm = dims  # dims is never None — the gate above required it

    if subject in _NO_THICKNESS_FALLBACK_KEYS:
        if height_mm is None:
            return EnvelopeDeclareResult(kind="INCOMPLETE", component_key=subject)
        return EnvelopeDeclareResult(
            kind="SET", component_key=subject,
            length_mm=length_mm, width_mm=width_mm, height_mm=height_mm,
        )

    # Plate path — height_mm stays None here for the two-number case; the
    # orchestrator reads thickness_mm at apply time. This parser only
    # decides INCOMPLETE-vs-SET by checking thickness PRESENCE, never its
    # value, and never writes a number itself.
    if height_mm is None and _thickness_mm(components, subject) is None:
        return EnvelopeDeclareResult(kind="INCOMPLETE", component_key=subject)
    return EnvelopeDeclareResult(
        kind="SET", component_key=subject,
        length_mm=length_mm, width_mm=width_mm, height_mm=height_mm,
    )
