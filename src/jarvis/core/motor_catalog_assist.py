"""Assisted motor acquisition — catalog suggestions for DEFINE + iterate wizards.

Thin glue over D8 ``find_motors_for_requirements``. No Conversation Engine.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, TypedDict

from jarvis.knowledge.library import ComponentLibrary, MotorSpec, default_library


class MotorSuggestion(TypedDict):
    """Ranked catalog candidate shown to the user during assisted acquisition."""

    idx: int
    name: str
    thrust_n: float
    kv_rating: int
    weight_g: float
    max_watts: float
    is_generic: bool

HELP_CHOOSE_PHRASES: frozenset[str] = frozenset({
    "ayudame a elegir",
    "ayúdame a elegir",
    "ayudame a escoger",
    "ayúdame a escoger",
    "busca motores",
    "buscar motores",
    "propon candidatos",
    "propón candidatos",
    "propone candidatos",
    "dame opciones",
    "opciones de motor",
    "no se que motor",
    "no sé qué motor",
    "elige tu",
    "elige por mi",
    "elige por mí",
})

# Params that open the assisted motor menu instead of a bare number prompt.
ASSISTED_MOTOR_PARAMS: frozenset[str] = frozenset({"motor_power_w"})

# Bare watts: "350", "350W", "350 w", "350.5"
_BARE_WATTS_RE = re.compile(
    r"^\s*(\d+(?:[.,]\d+)?)\s*(?:w|watts?|vatios?)?\s*$",
    re.IGNORECASE,
)
# Model-like: has letters and digits (MN3508, sunnysky_x2216, T-Motor 2306…)
_HAS_LETTER = re.compile(r"[a-záéíóúñ]", re.IGNORECASE)
_HAS_DIGIT = re.compile(r"\d")


def _normalize_help(text: str) -> str:
    nfd = unicodedata.normalize("NFD", text.strip().lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def _compact_name(text: str) -> str:
    return re.sub(r"[\s_\-]+", "", _normalize_help(text))


def is_help_choose_phrase(user_input: str) -> bool:
    normalized = _normalize_help(user_input)
    if normalized in {_normalize_help(p) for p in HELP_CHOOSE_PHRASES}:
        return True
    # Soft match: contains "ayudame" + ("elegir" | "escoger" | "motor")
    if "ayudame" in normalized and any(
        tok in normalized for tok in ("elegir", "escoger", "motor", "opcion")
    ):
        return True
    if "busca" in normalized and "motor" in normalized:
        return True
    return False


def is_bare_watts_input(user_input: str) -> bool:
    """True when the whole input is a power number (optional W suffix), not a model string."""
    return _BARE_WATTS_RE.match(user_input.strip()) is not None


def looks_like_motor_model_text(user_input: str) -> bool:
    """True when input looks like a motor model/SKU, not a bare wattage."""
    text = user_input.strip()
    if not text or is_bare_watts_input(text):
        return False
    if is_help_choose_phrase(text):
        return False
    # Keyword+number power phrases are not models
    norm = _normalize_help(text)
    if any(k in norm for k in ("potencia", "watts", " vatios")) and _HAS_DIGIT.search(text):
        if not _HAS_LETTER.search(re.sub(r"potencia|watts?|vatios?|w\b", "", norm, flags=re.I)):
            return False
    # Letters + digits together → model/SKU
    if _HAS_LETTER.search(text) and _HAS_DIGIT.search(text):
        return True
    # Multi-token brand-ish without digits still possible ("sunnysky r2305" has digits usually)
    compact = _compact_name(text)
    if len(compact) >= 8 and _HAS_LETTER.search(compact):
        # Long alpha token without being a help phrase — treat as model attempt
        if _HAS_DIGIT.search(compact):
            return True
    return False


def motor_spec_to_suggestion(motor: MotorSpec, idx: int = 1) -> MotorSuggestion:
    return {
        "idx": idx,
        "name": motor.name,
        "thrust_n": motor.thrust_n,
        "kv_rating": motor.kv_rating,
        "weight_g": motor.weight_g,
        "max_watts": motor.max_watts,
        "is_generic": motor.is_generic,
    }


def resolve_motor_from_text(
    user_input: str,
    *,
    library: ComponentLibrary | None = None,
) -> MotorSuggestion | None:
    """Resolve a catalog motor from free-text model name. Strict — no substring traps.

    Accepts:
      - exact catalog key (normalized)
      - user text whose compact form equals the catalog key
      - user text that contains the full catalog key as a token sequence (len ≥ 6)
    Rejects short fragments like \"motor\".
    """
    lib = library or default_library
    compact = _compact_name(user_input)
    if len(compact) < 4:
        return None
    # Try exact key
    try:
        return motor_spec_to_suggestion(lib.get_motor(user_input.strip()))
    except KeyError:
        pass
    best: MotorSpec | None = None
    best_len = 0
    for motor in lib.list_motors():
        name_c = _compact_name(motor.name)
        if not name_c or len(name_c) < 4:
            continue
        if compact == name_c:
            return motor_spec_to_suggestion(motor)
        # Full catalog key embedded in user text (e.g. "quiero el sunnysky_x2216_11")
        if len(name_c) >= 6 and name_c in compact and len(name_c) > best_len:
            best = motor
            best_len = len(name_c)
        # User typed a longer form that starts with the key or vice versa (min 8 chars)
        if len(compact) >= 8 and len(name_c) >= 8:
            if compact.startswith(name_c) or name_c.startswith(compact):
                if max(len(compact), len(name_c)) > best_len:
                    best = motor
                    best_len = max(len(compact), len(name_c))
    if best is not None:
        return motor_spec_to_suggestion(best)
    return None


def build_motor_catalog_suggestions(
    project_state: Any,
    *,
    library: ComponentLibrary | None = None,
    limit: int = 5,
    kv: int | None = None,
) -> list[MotorSuggestion]:
    """Ranked catalog candidates for the current project's design space."""
    lib = library or default_library
    from jarvis.core.project_closure import derive_physical_requirements

    req = derive_physical_requirements(project_state) if project_state is not None else {}
    min_thrust = req.get("thrust_per_motor_needed_n")
    kv_hint = kv
    if kv_hint is None and project_state is not None:
        motors_comp = getattr(
            getattr(project_state, "design_properties", None), "components", None
        ) or {}
        motors = motors_comp.get("motors")
        if motors is not None:
            kv_prop = (getattr(motors, "properties", None) or {}).get("kv_rating")
            if kv_prop is not None:
                try:
                    kv_hint = int(kv_prop.value)
                except (TypeError, ValueError):
                    kv_hint = None
    prop_inch = None
    params = getattr(project_state, "current_parameters", None) or {} if project_state else {}
    if params.get("propeller_diameter_in") is not None:
        try:
            prop_inch = float(params["propeller_diameter_in"])
        except (TypeError, ValueError):
            prop_inch = None

    if min_thrust is None and kv_hint is None and prop_inch is None:
        # Fall back: list a few motors near a light aerial thrust band
        matches = lib.find_motors_for_requirements(min_thrust_n=4.0)
    else:
        matches = lib.find_motors_for_requirements(
            min_thrust_n=min_thrust,
            kv=kv_hint,
            prop_inch=prop_inch,
        )
        if not matches and kv_hint is not None:
            matches = lib.find_motors_by_kv(kv_hint)

    return [
        motor_spec_to_suggestion(m, idx=i + 1)
        for i, m in enumerate(matches[:limit])
    ]


def _format_candidate_line(s: MotorSuggestion, *, detailed: bool) -> str:
    """Shared candidate-line formatting for the full list and the inline quick menu."""
    tag = " [genérico]" if s.get("is_generic") else ""
    watts = s.get("max_watts")
    watts_bit = f", ~{int(watts)}W" if watts is not None else ""
    if detailed:
        body = f"{s['thrust_n']}N, {s['weight_g']}g, {s['kv_rating']}KV{watts_bit}"
    else:
        body = f"{s['thrust_n']}N{watts_bit}"
    return f"  {s['idx']}. {s['name']}{tag}  →  {body}"


def format_motor_catalog_suggestions(suggestions: list[MotorSuggestion]) -> str:
    if not suggestions:
        return (
            "No tengo un motor en el catálogo que cubra este espacio de diseño. "
            "Indica la potencia aproximada en W, o un modelo concreto del catálogo."
        )
    lines = [
        "Candidatos del catálogo para este espacio de diseño:",
    ]
    for s in suggestions:
        lines.append(_format_candidate_line(s, detailed=True))
    lines.append("Elige un número, indica W a mano, o di 'no' para omitir.")
    return "\n".join(lines)


def assisted_motor_power_question(
    suggestions: list[MotorSuggestion] | None = None,
    *,
    thrust_hint_n: float | None = None,
) -> str:
    """Human-first prompt for motor power — three paths, optional inline candidates.

    Menu options are bullets (not numbers) so they never collide with catalog picks 1..N.
    """
    lines: list[str] = []
    if thrust_hint_n is not None:
        lines.append(
            f"Para ~{thrust_hint_n:.1f} N/motor necesito la potencia nominal de cada motor."
        )
    else:
        lines.append("Necesito la potencia nominal de cada motor.")
    lines.append("")
    lines.append("Puedes:")
    lines.append("  • Indicar un motor del catálogo (nombre exacto)")
    lines.append("  • Indicar la potencia aproximada en W (ej: 350)")
    lines.append("  • Escribir 'ayúdame a elegir' para ver candidatos numerados")
    if suggestions:
        lines.append("")
        lines.append("Candidatos rápidos (responde con el número):")
        for s in suggestions[:3]:
            lines.append(_format_candidate_line(s, detailed=False))
    return "\n".join(lines)


def match_suggestion_by_input(
    user_input: str, suggestions: list[MotorSuggestion]
) -> MotorSuggestion | None:
    """Match a numbered pick or an exact catalog name in the suggestion list.

    Strict: no substring traps (\"motor\" must not match \"t-motor_…\").
    """
    normalized = user_input.strip().lower()
    # Pure index only
    if re.fullmatch(r"\d+", normalized):
        for s in suggestions:
            if normalized == str(s["idx"]):
                return s
        return None
    compact = _compact_name(user_input)
    if len(compact) < 4:
        return None
    for s in suggestions:
        name_compact = _compact_name(str(s.get("name") or ""))
        if not name_compact:
            continue
        if compact == name_compact:
            return s
        if len(compact) >= 6 and len(name_compact) >= 6:
            if compact.startswith(name_compact) or name_compact.startswith(compact):
                return s
    return None
