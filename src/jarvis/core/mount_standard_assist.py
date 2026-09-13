"""Mount standard assist B1 — deterministic, suggest-only checklist for the
already-expressible standard drone mount graph (investigation_report_
board_drone_default_layout_b0.md §B/§D).

Discoverability only, never new physics: every edge here is already
declarable via the existing `mounted_on_declare_assist.parse_mounted_on_
declare` grammar — this module never widens that vocabulary (`frame_arm`,
`power_connector`, `signal_harness` stay non-subjects, exactly as locked
there) and never writes anything itself. It only lists which in-scope
edges are still undeclared on THIS project and the exact Continuity
phrase that would declare each one — the user still types (or retypes)
that phrase; `_try_handle_mounted_on_declare` (the existing, unchanged
IDLE bridge) is what actually calls the writer.

Locked in-scope graph (IC §0 lock #2/#4 — never widened without a new ★):
  propellers -> motors
  motors -> frame_arm            (only when frame_arm is itself declared)
  esc / flight_controller / battery / sensors -> the airframe (a single
    frame_plate* when exactly one exists, else bare `frame`, else no
    suggestion at all — 2+ plates is AMBIGUOUS, never guessed)

Out of scope, forever without a separate ★: frame_arm/kit-hardware as
mount SUBJECTS, any pose/Δmm, any plate L×W invention.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from jarvis.core.motor_catalog_assist import _normalize_help
from jarvis.domains.aerial import is_frame_plate_key

# Locked trigger phrases (IC §0 lock #5 — "pick 1-2 ... document them"):
# "montajes estándar" (literal, specific) and "qué falta montar"
# (conversational). Accent/case-insensitive via _normalize_help, same as
# every other IDLE phrase gate in this codebase (motor/catalog assists).
# Mount tip/parse align B1 (lock #4): "montaje" singular also triggers —
# thin, one-character widening (`montajes?`), never a new gate concept.
_TRIGGER_RE = re.compile(r"montajes?\s+estandar|que\s+falta\s+montar")


def is_mount_standard_assist_trigger(user_input: str) -> bool:
    """True when *user_input* asks for the standard-mount checklist."""
    return bool(_TRIGGER_RE.search(_normalize_help(user_input)))


@dataclass(frozen=True)
class MountSuggestion:
    """One checklist row. ``kind == "suggested"`` carries a ready-to-type
    ``example_phrase``; ``kind == "ambiguous"`` carries ``candidates``
    instead (2+ declared plates — never guessed which one)."""

    subject: str
    kind: str  # "suggested" | "ambiguous"
    target: str | None = None
    example_phrase: str | None = None
    reason: str = ""
    candidates: tuple[str, ...] = field(default_factory=tuple)


# Spanish subject noun + gender agreement for the example phrase — mirrors
# the exact wording the Conn B1 smoke already validated as parseable
# (`engineer_smoke_connect_remaining_mounted_on_b1.md`: "hélices montadas
# en los motores", "sensor montado en el esc"), never a new alias table.
_STACK_SUBJECTS: tuple[tuple[str, str, str], ...] = (
    ("esc", "esc", "montado"),
    ("flight_controller", "controladora", "montada"),
    ("battery", "batería", "montada"),
    ("sensors", "sensor", "montado"),
)


def _mounted_on(components: dict[str, Any], key: str) -> str | None:
    spec = components.get(key)
    return getattr(spec, "mounted_on", None) if spec is not None else None


def _plate_target(components: dict[str, Any]) -> str | tuple[str, ...] | None:
    """A single `frame_plate*` key when exactly one is declared; a tuple
    of 2+ keys when ambiguous (never guessed which one); `None` when zero
    plates are declared."""
    plate_keys = tuple(sorted(k for k in components if is_frame_plate_key(k)))
    if len(plate_keys) == 1:
        return plate_keys[0]
    if len(plate_keys) >= 2:
        return plate_keys
    return None


def build_mount_standard_checklist(components: dict[str, Any]) -> list[MountSuggestion]:
    """Undeclared, in-scope standard mounts for *components* — pure,
    read-only, mutates nothing and calls no writer. Order: propellers ->
    motors, motors -> frame_arm (only if frame_arm exists), then each
    stack component -> the airframe.
    """
    suggestions: list[MountSuggestion] = []

    if "propellers" in components and "motors" in components:
        if _mounted_on(components, "propellers") != "motors":
            suggestions.append(MountSuggestion(
                subject="propellers", kind="suggested", target="motors",
                example_phrase="hélices montadas en los motores",
                reason="hélice sobre motor",
            ))

    if "motors" in components and "frame_arm" in components:
        if _mounted_on(components, "motors") != "frame_arm":
            suggestions.append(MountSuggestion(
                subject="motors", kind="suggested", target="frame_arm",
                example_phrase="motor montado en el brazo",
                reason="motor sobre brazo",
            ))

    plate = _plate_target(components)
    for key, noun, participle in _STACK_SUBJECTS:
        if key not in components:
            continue
        current = _mounted_on(components, key)

        if isinstance(plate, tuple):
            # 2+ plates declared — ambiguous target, never guessed. Only
            # worth surfacing when the subject has NO mount at all yet; a
            # subject already mounted on anything is not "undeclared."
            if current is None:
                # Mount tip/parse align B1 (lock #2): the retype tip uses
                # the parseable Spanish noun+participle (same table as the
                # "suggested" branch below), never the bare component key —
                # "flight_controller"/"sensors" typed literally used to
                # silently fail _resolve_subject's noun-only table.
                suggestions.append(MountSuggestion(
                    subject=key, kind="ambiguous", candidates=plate,
                    example_phrase=f"{noun} {participle} en <clave>",
                    reason="aviónica sobre placa — varias placas declaradas",
                ))
            continue

        target = plate or ("frame" if "frame" in components else None)
        if target is None or current is not None:
            continue
        target_phrase = "la placa" if target != "frame" else "el frame"
        suggestions.append(MountSuggestion(
            subject=key, kind="suggested", target=target,
            example_phrase=f"{noun} {participle} en {target_phrase}",
            reason="aviónica sobre placa/frame",
        ))

    return suggestions


def format_mount_standard_checklist(suggestions: list[MountSuggestion]) -> str:
    """Locked Spanish copy — numbered list + exact phrase per row, or the
    honest 'nothing left' message. Never claims a pose, never claims the
    plate is the assembly root, never says "ensamblado"/"cabe"/VERIFIED."""
    if not suggestions:
        return (
            "Montajes estándar: no queda ninguno de los declarables hoy "
            "(hélices→motores, motor→brazo, aviónica→placa/frame) sin "
            "declarar. Esto no es ASSEMBLY READY ni una pose."
        )
    lines = ["Montajes estándar pendientes (declarables hoy, no inventa nada nuevo):"]
    for i, s in enumerate(suggestions, start=1):
        if s.kind == "ambiguous":
            lines.append(
                f"  {i}. {s.subject}: hay varias placas declaradas "
                f"({', '.join(s.candidates)}) — indica cuál con "
                f"'{s.example_phrase}'."
            )
        else:
            lines.append(f"  {i}. {s.subject} → {s.target}: escribe \"{s.example_phrase}\"")
    lines.append("Escribe la frase para confirmar — nada se declara solo.")
    return "\n".join(lines)
