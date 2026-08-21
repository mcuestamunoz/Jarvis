"""
acquisition_brief
===================
FN-018 — thin, deterministic "Acquisition Brief" for component-key acquisition
targets (Step C of Acquisition Guided Engineering).

Composes Core facts already available elsewhere (BLOCK_TO_COMPONENTS,
derive_physical_requirements) into a short guidance block: what we're
defining, what Jarvis already knows about this project, why it matters (only
when a requirement number is cheaply available), and how to answer
(COMPONENT_PROMPTS, unchanged from FN-017). One function, called from every
entry point that currently shows a component-key question (FN-013 reprompt,
Phase A open, low-completeness re-prompt). G23: no longer called from a
"pending-help" entry point — that acquisition-help feature (FN-015) was
removed entirely; the anti-LLM confusion gate that survives it returns a
one-line re-ask, not this Brief.

Not a dialogue manager, not LLM-authored, not a new subsystem: no state is
kept here and no new calculation is introduced — the "why" line reuses
project_closure.derive_physical_requirements(), the same source
motor_catalog_assist/param_definition_session already read.
"""
from __future__ import annotations

from typing import Any

from jarvis.core.acquisition_target import COMPONENT_PROMPTS
from jarvis.core.system_architecture_catalog import BLOCK_TO_COMPONENTS

_BRIEF_TOPIC: dict[str, str] = {
    "propellers": "las hélices",
    "motors": "los motores",
    "battery": "la batería",
    "frame": "el frame",
}

_BRIEF_BLURB: dict[str, str] = {
    "propellers": "Las hélices convierten la potencia de los motores en empuje.",
    "motors": "Los motores generan el empuje necesario para volar.",
    "battery": "La batería determina la energía disponible y la autonomía.",
    "frame": "El frame es la estructura que soporta el resto de componentes.",
}

_BRIEF_LABEL: dict[str, str] = {
    "propellers": "Hélices",
    "motors": "Motores",
    "battery": "Batería",
    "frame": "Frame",
    "flight_controller": "Controladora de vuelo",
    "sensors": "Sensores/GPS",
}

# Keys with a full Brief (blurb + facts + why). Any other component key
# degrades to COMPONENT_PROMPTS-only — identical to FN-017 behavior.
_BRIEF_KEYS: frozenset[str] = frozenset(_BRIEF_BLURB)


def build_acquisition_brief(key: str, project_state: Any | None) -> dict[str, str]:
    """Compose the thin Acquisition Brief for a component-key acquisition target.

    Returns ``{"message": str, "question": str}``. ``message`` is ``""`` when
    ``key`` has no Brief blurb, or when ``project_state`` is unavailable —
    callers show only ``question`` in that case (no crash, same shape as
    pre-FN-018 COMPONENT_PROMPTS-only behavior).
    """
    question = COMPONENT_PROMPTS.get(key, "")
    if key not in _BRIEF_KEYS or project_state is None:
        return {"message": "", "question": question}

    lines = [f"Vamos a definir {_BRIEF_TOPIC[key]}.", "", _BRIEF_BLURB[key]]

    fact = _known_fact(key, project_state)
    if fact:
        lines.append(fact)

    why = _why_line(key, project_state)
    if why:
        lines.append(why)

    lines.append("")
    lines.append("Puedes:")
    lines.append(f"  • {question}")
    if key in ("motors", "propellers"):
        # G21 ★4 / Prop-6: motors and propellers are the component-sub-mode
        # keys with a live catalog bind entry point (Impl B + Prop-3) —
        # advertise it here, not on battery/frame, which still have no bind
        # path to point to yet.
        lines.append(
            "  • decir 'ayúdame a elegir' para ver candidatos numerados del catálogo"
        )

    return {"message": "\n".join(lines), "question": question}


def _known_fact(key: str, project_state: Any) -> str | None:
    """Deterministic 'what Jarvis already knows' line — sibling components in
    the same architecture block that are already declared. Never invents a
    fact; returns None (line omitted) when nothing is true yet."""
    components = getattr(project_state.design_properties, "components", None) or {}
    owning_block = next(
        (block for block, keys in BLOCK_TO_COMPONENTS.items() if key in keys), None
    )
    if owning_block is None:
        return None
    siblings = [k for k in BLOCK_TO_COMPONENTS[owning_block] if k != key]
    declared = [
        k for k in siblings
        if components.get(k) is not None
        and (getattr(components[k], "completeness", "low") or "low") != "low"
    ]
    if not declared:
        return None
    labels = ", ".join(_BRIEF_LABEL.get(k, k) for k in declared)
    return f"Para este proyecto: {labels} ya declarado(s); gap activo = {key}."


def _why_line(key: str, project_state: Any) -> str | None:
    """Optional 1-line requirement, only when cheaply available. Reuses
    derive_physical_requirements() (already used by motor catalog help) — no
    new calculation. Propellers/motors only: no other key has a cheap
    per-unit requirement today."""
    if key not in ("propellers", "motors"):
        return None
    from jarvis.core.project_closure import derive_physical_requirements

    thrust = derive_physical_requirements(project_state).get("thrust_per_motor_needed_n")
    if thrust is None:
        return None
    return f"Requisito orientativo: ≥ {thrust:.2f} N/motor."
