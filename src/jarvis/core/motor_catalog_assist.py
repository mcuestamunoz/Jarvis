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
    max_watts: float | None
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
# FN-009: per_motor_max_thrust_n joins motor_power_w — a single catalog pick
# resolves both coherently (same physical motor), so both are "assisted".
ASSISTED_MOTOR_PARAMS: frozenset[str] = frozenset({"motor_power_w", "per_motor_max_thrust_n"})

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


# Continuity Hardening ★5 (G15): deterministic list-motors escape, mirrors
# G10 ★8's list-materials pattern shape. Narrow on purpose — must not steal
# a bare numeric thrust/watts answer or a real motor model string.
_LIST_MOTORS_PATTERNS: tuple[str, ...] = (
    r"\bque\s+motores\b",
    r"\bmotores\s+(?:disponibles|tenemos|hay)\b",
    r"\bcatalogo\s+de\s+motores\b",
    r"\blista(?:r)?\s+(?:de\s+)?motores\b",
)
_LIST_MOTORS_RE = tuple(re.compile(p) for p in _LIST_MOTORS_PATTERNS)


def is_list_motors_phrase(user_input: str) -> bool:
    """G15 ★5: does *user_input* ask what motors are in the catalog?

    Deliberately narrow — same shape as G10 ★8's ``LIST_MATERIALS_PATTERNS``
    (`intent_resolver.py`) — so it never collides with a genuine numeric
    thrust/watts answer or a catalog model string.
    """
    normalized = _normalize_help(user_input)
    return any(rx.search(normalized) for rx in _LIST_MOTORS_RE)


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


def derive_kv_prop_filters(project_state: Any, *, kv: int | None = None) -> tuple[int | None, float | None]:
    """Extract (kv_hint, prop_inch) from *project_state* — the same design-space
    filters ``build_motor_catalog_suggestions`` uses. Factored out (Continuity
    Hardening ★6) so a caller that already got zero candidates from a filtered
    search can compute a "catalog max" using those SAME filters, instead of
    silently falling back to an unfiltered full-catalog max that can
    contradict the filtered "no candidates" verdict (investigation A10/A11).
    """
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
    return kv_hint, prop_inch


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
    kv_hint, prop_inch = derive_kv_prop_filters(project_state, kv=kv)

    if min_thrust is None and kv_hint is None and prop_inch is None:
        # Fall back: list a few motors near a light aerial thrust band
        matches = lib.find_motors_for_requirements(min_thrust_n=4.0)
    else:
        # G22: no KV-only fallback when the strict thrust/kv/prop search comes
        # back empty. The old fallback (find_motors_by_kv, ignoring the
        # thrust/prop miss) made this function disagree with
        # resolve_motor_catalog_surface's honest "no tengo un motor" gap —
        # list_motors would show candidates the gap said didn't exist. Empty
        # strict search now means empty everywhere, consistently.
        matches = lib.find_motors_for_requirements(
            min_thrust_n=min_thrust,
            kv=kv_hint,
            prop_inch=prop_inch,
        )

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


def format_motor_catalog_suggestions(
    suggestions: list[MotorSuggestion], *, param: str = "motor_power_w", include_cta: bool = True
) -> str:
    """``param`` selects the trailing instruction's unit/copy: W for
    motor_power_w (default, unchanged), N/combo for per_motor_max_thrust_n.
    Callers that don't pass ``param`` keep the original W-copy verbatim.

    G16-B: ``include_cta`` lets a caller that builds its own separate
    "how to answer" ``question`` (e.g. ``_offer_catalog_help``) suppress this
    trailing "Elige un número..." line from ``message`` — otherwise the same
    instruction is shown twice (once in message, once in question). Default
    True keeps every other existing caller's output byte-for-byte unchanged.
    """
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
    if include_cta:
        if param == "per_motor_max_thrust_n":
            lines.append(
                "Elige un número, indica empuje en N (de una combinación motor-hélice), "
                "o di 'no' para omitir."
            )
        else:
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


def assisted_motor_thrust_question(
    suggestions: list[MotorSuggestion] | None = None,
    *,
    thrust_hint_n: float | None = None,
) -> str:
    """FN-009: prompt for per-motor thrust — three paths, optional inline candidates.

    The computed requirement is framed as a provisional minimum: total mass
    (and therefore required thrust) still grows once the battery and other
    components are declared, so this is a floor, not a target. Manual N entry
    is described as the measured/declared thrust of a real motor-propeller
    combo — never presented as a value Jarvis expects the user to invent.
    """
    lines: list[str] = []
    if thrust_hint_n is not None:
        lines.append(
            f"Necesito el empuje máximo por motor. Mínimo provisional para este "
            f"diseño: ≥ {thrust_hint_n:.1f} N/motor (puede subir al declarar la "
            f"batería y otros componentes)."
        )
    else:
        lines.append("Necesito el empuje máximo que puede dar cada motor.")
    lines.append("")
    lines.append("Puedes:")
    lines.append("  • Indicar un motor del catálogo (nombre exacto)")
    lines.append("  • Indicar el empuje medido/declarado en N de tu combo motor-hélice (ej: 15)")
    lines.append("  • Escribir 'ayúdame a elegir' para ver candidatos numerados")
    if suggestions:
        lines.append("")
        lines.append("Candidatos rápidos (responde con el número):")
        for s in suggestions[:3]:
            lines.append(_format_candidate_line(s, detailed=False))
    return "\n".join(lines)


def format_no_thrust_candidate_message(
    *,
    required_n: float | None = None,
    library: ComponentLibrary | None = None,
    kv: int | None = None,
    prop_inch: float | None = None,
) -> str:
    """FN-009: deterministic, honest response when no catalog motor covers the
    computed thrust requirement.

    Names the requirement, what the catalog actually covers, and concrete
    options the user can act on. Never invents a SKU and never mutates
    motor_count automatically.

    Continuity Hardening ★6 (G15): when *kv*/*prop_inch* are given (the same
    filters the search that produced zero candidates already used), the
    quoted "máximo cubierto" is computed over that SAME filtered set — not
    the unfiltered full catalog, which could quote a number no motor in
    range actually offers (investigation A10/A11: "no motor ≥37.7 N" next to
    an unrelated "máximo ~55 N" from a KV-incompatible motor). With no
    filters given (bare thrust-only search), the full-catalog max is still
    the correct, honest figure — unchanged from before this fix.
    """
    lib = library or default_library
    filtered = kv is not None or prop_inch is not None
    if filtered:
        motors = lib.find_motors_for_requirements(kv=kv, prop_inch=prop_inch)
    else:
        motors = lib.list_motors()
    max_available_n = max((m.max_thrust_n for m in motors), default=0.0)
    if required_n is not None:
        line = f"No tengo un motor en el catálogo que cubra ≥ {required_n:.1f} N/motor"
    else:
        line = "No tengo un motor en el catálogo que cubra este requisito de empuje"
    filter_note = " compatible con tu KV/hélice" if filtered else ""
    line += (
        f" (máximo{filter_note} cubierto por el catálogo: ~{max_available_n:.1f} N/motor)."
        if max_available_n > 0
        else "."
    )
    return "\n".join([
        line,
        "Opciones:",
        "  • Añadir más motores para repartir la carga entre más unidades.",
        "  • Usar un motor-hélice fuera de catálogo con datos medidos (empuje real declarado).",
        "  • Revisar el objetivo o la masa del sistema si el requisito es muy alto.",
        "No voy a inventar un modelo de catálogo que no cubra este requisito.",
    ])


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
