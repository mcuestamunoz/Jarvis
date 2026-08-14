"""Goal Planner — detección determinista de objetivos de diseño y catálogo de estrategias.

Flujo:
    user_input → detect_goal() → goal_key | None
    goal_key   → format_goal_plan()       → bloque de texto fijo para display
    goal_key   → get_goal_context_for_llm() → JSON de estrategias para inyectar al LLM
"""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Optional


# ── Catálogo de estrategias ────────────────────────────────────────────────────

GOAL_STRATEGIES: dict[str, list[dict[str, str]]] = {
    "aumentar_payload": [
        {
            "action": "Aumentar empuje disponible",
            "description": "Incrementar el número de motores o usar motores con mayor empuje nominal.",
            "lever": "per_motor_max_thrust_n / motors",
        },
        {
            "action": "Reducir masa estructural",
            "description": "Bajar el factor de masa estructural o cambiar a materiales más ligeros.",
            "lever": "structure_mass_factor / material",
        },
        {
            "action": "Optimizar hélices",
            "description": "Aumentar el diámetro de las hélices para mayor empuje por watt.",
            "lever": "propeller_diameter_in / propeller_rpm",
        },
    ],
    "mejorar_autonomia": [
        {
            "action": "Aumentar capacidad de batería",
            "description": "Incrementar la energía disponible aumentando Wh de la batería.",
            "lever": "battery_capacity_wh",
        },
        {
            "action": "Reducir consumo total",
            "description": "Bajar la potencia consumida optimizando número o tipo de motores.",
            "lever": "total_power_w / motors",
        },
        {
            "action": "Reducir masa total del sistema",
            "description": "Menos masa = menos empuje necesario = menor consumo energético.",
            "lever": "structure_mass_factor / payload_kg",
        },
    ],
    "reducir_masa": [
        {
            "action": "Cambiar material estructural",
            "description": "Usar materiales con menor densidad (fibra de carbono, aluminio 6061).",
            "lever": "material",
        },
        {
            "action": "Ajustar factor de estructura",
            "description": "Reducir el factor multiplicador de masa estructural si el diseño lo permite.",
            "lever": "structure_mass_factor",
        },
    ],
    "mejorar_estabilidad": [
        {
            "action": "Aumentar margen de seguridad de empuje",
            "description": "Subir la relación thrust/weight por encima de 1.5 para mayor margen.",
            "lever": "per_motor_max_thrust_n / motors",
        },
        {
            "action": "Ajustar safety factor",
            "description": "Incrementar el safety_factor para que el sistema acepte menos riesgo estructural.",
            "lever": "safety_factor",
        },
    ],
    # F-1: direction-mirrored counterpart of aumentar_payload — same
    # architecture (dict of action/description/lever), vehicle-agnostic
    # wording (no drone-specific concepts). Strategy 3 uses a lever that is
    # not universal (motor_count) — see the Engineer lock note on
    # _prioritize_strategies below; it stays in the catalog but is never
    # promoted for architectures where motor_count is unknown.
    "reducir_payload": [
        {
            "action": "Reducir requisito de carga útil",
            "description": "Bajar directamente el payload objetivo del sistema.",
            "lever": "payload_kg",
        },
        {
            "action": "Aligerar estructura si está sobredimensionada",
            "description": "Con menos carga que soportar, el factor de masa estructural o el material pueden reducirse sin perder margen.",
            "lever": "structure_mass_factor / material",
        },
        {
            "action": "Reducir actuadores si el payload baja",
            "description": "Menos payload puede permitir reducir el número de motores/actuadores manteniendo margen (solo cuando el diseño tiene actuadores configurados).",
            "lever": "motors / motor_count",
        },
    ],
}

# ── Tabla de detección de objetivos ───────────────────────────────────────────
# Cada entry: (goal_key, [(keyword_normalizada, ...)])
# Las keywords deben estar normalizadas (minúsculas, sin diacríticos).

_GOAL_KEYWORDS: list[tuple[str, list[str]]] = [
    # F-1: payload is no longer a bare-keyword entry here — bare tokens like
    # "payload"/"carga util" carry no direction, which was the root cause of
    # "reducir payload" resolving to aumentar_payload (substring match on the
    # bare dimension word). Payload is now resolved by _detect_payload_goal
    # (dimension + direction), checked before this table in detect_goal().
    (
        "mejorar_autonomia",
        [
            "autonomia", "duracion vuelo", "vuelo mas largo", "mas tiempo",
            "mejorar autonomia", "aumentar autonomia", "mas autonomia",
            "bateria", "duracion bateria", "mas vuelo",
            # FN-022: fill natural-intention gaps.
            "volar mas tiempo", "volar mas", "mayor autonomia",
            "aumentar el tiempo de vuelo", "mas duracion",
        ],
    ),
    (
        "reducir_masa",
        [
            "reducir masa", "menos peso", "aligerar", "bajar peso",
            "reducir peso", "masa menor", "peso menor", "mas ligero",
            "mas liviano",
            # Bug 65 fix: verb+article+noun forms and "minimiza" variants.
            # _normalize strips diacritics so only unaccented forms needed here.
            "reducir la masa", "reducir el peso",
            "minimiza masa", "minimiza la masa",
            "minimiza peso", "minimiza el peso",
            "minimizar masa", "minimizar la masa",
            "minimizar peso", "minimizar el peso",
            # Calibración 2026-08-05: "optimiza para masa/peso" (explore verb, not reducir).
            "para masa", "para peso",
            "optimiza masa", "optimiza peso",
            "optimizar masa", "optimizar peso",
        ],
    ),
    (
        "mejorar_estabilidad",
        [
            "estabilidad", "mas estable", "mejorar estabilidad",
            "aumentar estabilidad", "estabilizar", "vuelo estable",
            "margen de seguridad", "margen seguridad", "safety margin",
            # FN-022: primary mapping for thrust/empuje-as-intention — this
            # goal's strategies already lead with thrust/margin levers
            # (per_motor_max_thrust_n / safety_factor), so "aumentar empuje"
            # style phrases land here rather than creating a fifth goal.
            # Documented in FN-022 report §3.
            "margen", "poco margen", "margen bajo", "margen justo",
            "empuje", "mas empuje", "aumentar empuje", "subir empuje",
            "mas thrust", "aumentar thrust", "thrust",
            "relacion empuje peso", "relacion empuje/peso", "ratio empuje peso",
            "thrust to weight", "thrust/weight",
        ],
    ),
]


def _normalize(text: str) -> str:
    """Minúsculas + eliminación de diacríticos."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ── F-1: direction-aware dimension resolution ─────────────────────────────────
# A goal is (engineering dimension, direction). Bare dimension words alone
# ("payload", "carga util") are not sufficient evidence of direction — that
# was the root cause of "reducir payload" resolving to aumentar_payload
# (naive substring match on a direction-less token). This is a small, reusable
# pattern; F-1 migrates ONLY payload to it. Other dimensions (autonomía,
# thrust, masa, safety margin) keep their existing single-direction keyword
# lists and are explicitly out of scope here — future contracts (F-1b) may
# migrate them the same way.
_INCREASE_WORDS: tuple[str, ...] = ("aument", "subir", "sube", "increment", "mejorar", "levantar")
_DECREASE_WORDS: tuple[str, ...] = ("reduc", "bajar", "disminu", "menos", "aligerar")


def _direction_of(normalized: str) -> Optional[str]:
    """Return "increase" | "decrease" | None (absent, or both present — ambiguous)."""
    has_increase = any(w in normalized for w in _INCREASE_WORDS)
    has_decrease = any(w in normalized for w in _DECREASE_WORDS)
    if has_increase and not has_decrease:
        return "increase"
    if has_decrease and not has_increase:
        return "decrease"
    return None


# Bare payload-dimension terms — name the dimension without encoding a
# direction on their own. Never matched alone as evidence of a specific
# direction; always paired with _direction_of() below.
_PAYLOAD_DIMENSION_TERMS: tuple[str, ...] = (
    "carga util", "carga utile", "payload", "capacidad de carga",
)

# Phrases that already bake BOTH dimension and direction into the words
# themselves — safe to match directly regardless of _direction_of(), and kept
# verbatim from the pre-F-1 keyword list so existing intent stays compatible.
_PAYLOAD_INCREASE_PHRASES: tuple[str, ...] = (
    "levantar mas", "levantar peso", "mas carga",
    "mejorar carga", "aumentar carga", "incrementar carga",
    "subir carga", "mas peso util",
    "aumentar payload", "subir payload", "incrementar payload",
    "mas capacidad de carga", "transportar mas peso", "transportar mas carga",
    "cargar mas",
)
# New F-1 mirror — only the phrasing that needs context beyond a bare
# dimension term + direction word (the "transportar" framing distinguishes
# payload reduction from generic structural mass reduction, which already
# owns bare "menos peso"/"bajar peso" in reducir_masa's keyword list).
_PAYLOAD_DECREASE_PHRASES: tuple[str, ...] = (
    "transportar menos peso", "transportar menos carga",
)


def _detect_payload_goal(normalized: str) -> Optional[str]:
    """Direction-aware payload detection (F-1). Checked before the generic
    _GOAL_KEYWORDS loop in detect_goal(). Returns "aumentar_payload",
    "reducir_payload", or None (no payload dimension mentioned at all).
    """
    if any(p in normalized for p in _PAYLOAD_DECREASE_PHRASES):
        return "reducir_payload"
    if any(p in normalized for p in _PAYLOAD_INCREASE_PHRASES):
        return "aumentar_payload"
    if any(t in normalized for t in _PAYLOAD_DIMENSION_TERMS):
        # Bare dimension term with an explicit decrease word ("reducir",
        # "bajar", ...) anywhere in the phrase → reducir_payload. Otherwise
        # (explicit increase word, or no direction word at all) defaults to
        # aumentar_payload — the same default bare "payload"/"carga util"
        # already had pre-F-1, now only reachable when no decrease word is
        # present, closing the "reducir payload" inversion bug.
        if _direction_of(normalized) == "decrease":
            return "reducir_payload"
        return "aumentar_payload"
    return None


def detect_goal(user_input: str) -> Optional[str]:
    """Detecta el goal de diseño del usuario.

    Returns:
        goal_key si se detecta un objetivo reconocido, None en caso contrario.
    """
    normalized = _normalize(user_input)
    payload_goal = _detect_payload_goal(normalized)
    if payload_goal is not None:
        return payload_goal
    for goal_key, keywords in _GOAL_KEYWORDS:
        for kw in keywords:
            if kw in normalized:
                return goal_key
    return None


# FN-022: any digit means the user already gave a concrete target value
# (bare number, "a 15 N", "en 2 kg", ...) — deliberately conservative, no
# unit/format parsing. A numeric value always means iterate/define_params
# owns the turn, never the intention-only goal plan.
_HAS_DIGIT_RE = re.compile(r"\d")


def looks_like_numeric_mutate(user_input: str) -> bool:
    """True when the input already carries a concrete numeric target."""
    return bool(_HAS_DIGIT_RE.search(user_input))


def is_engineering_intention(user_input: str) -> Optional[str]:
    """FN-022: detect a bare engineering intention ("aumentar el empuje",
    "mejorar la autonomía", ...) with no concrete target value yet.

    Returns the goal_key when detect_goal() recognizes a goal AND the input
    does not already carry a numeric value (looks_like_numeric_mutate) —
    None otherwise, so a phrase like "sube el empuje a 15N" is left alone
    for the existing iterate/define_params path. Generic over every goal in
    GOAL_STRATEGIES — no goal-specific branching here.
    """
    key = detect_goal(user_input)
    if key is None:
        return None
    if looks_like_numeric_mutate(user_input):
        return None
    return key


def _prioritize_strategies(
    goal_key: str,
    strategies: list[dict[str, str]],
    sim_context: dict | None,
) -> list[dict[str, str]]:
    """Reordena estrategias según el estado actual de simulación.

    Reglas por goal basadas en safety_margin_ratio:
      - aumentar_payload:
          margin < 1.15  → empuje primero (urgencia real de thrust)
          margin > 1.5   → payload directo primero (hay margen, aprovéchalo)
      - reducir_payload:
          margin < 1.15  → reducir payload_kg directamente primero (F-1)
          la palanca de actuadores nunca se promueve — ver nota architecture-
          conditional más abajo
      - mejorar_autonomia:
          sin batería (warnings contienen 'energy') → batería primero
      - reducir_masa / mejorar_estabilidad → orden por defecto
    """
    if sim_context is None:
        return strategies

    margin: float | None = sim_context.get("safety_margin_ratio")
    warnings: list = sim_context.get("warnings") or []
    warnings_str = " ".join(str(w) for w in warnings).lower()

    ordered = list(strategies)  # copia para no mutar el catálogo

    if goal_key == "aumentar_payload" and margin is not None:
        if margin < 1.15:
            # Margen crítico: lo primero es conseguir más empuje
            ordered.sort(key=lambda s: 0 if "thrust" in s["lever"] or "motor" in s["lever"].lower() else 1)
        elif margin > 1.5:
            # Margen holgado: se puede aumentar carga directamente sin tocar motores
            ordered.sort(key=lambda s: 0 if "payload" in s["lever"].lower() or "factor" in s["lever"].lower() else 1)

    elif goal_key == "reducir_payload":
        if margin is not None and margin < 1.15:
            # Margen crítico: reducir el payload objetivo es la palanca más
            # directa e inmediata (contract F-1: "if margin is low,
            # prioritizing payload_kg reduction is appropriate").
            ordered.sort(key=lambda s: 0 if "payload" in s["lever"].lower() else 1)
        # Engineer lock (F-1): motor_count is architecture-conditional, not
        # universal — sim_context (last_simulation-shaped) never carries it
        # today, so the actuator/motor lever is always pushed last here
        # rather than promoted. It stays in GOAL_STRATEGIES (Handoff/H4 may
        # still reference it when the user names it explicitly) — this only
        # controls display/priority order, never invents motor_count.
        if sim_context.get("motor_count") is None:
            ordered.sort(key=lambda s: 1 if "motor" in s["lever"].lower() else 0)

    elif goal_key == "mejorar_autonomia":
        if "energy" in warnings_str or "bateria" in warnings_str or "battery" in warnings_str:
            # Sin batería definida: batería es el primer paso obligatorio
            ordered.sort(key=lambda s: 0 if "battery" in s["lever"].lower() or "wh" in s["lever"].lower() else 1)

    return ordered


def format_goal_plan(goal_key: str, sim_context: dict | None = None) -> str:
    """Genera el bloque determinista de opciones estratégicas para display.

    Cuando se pasa ``sim_context`` (resultado de ``last_simulation``), las
    estrategias se reordenan por relevancia al estado actual del proyecto.
    """
    strategies = GOAL_STRATEGIES.get(goal_key, [])
    if not strategies:
        return ""

    prioritized = _prioritize_strategies(goal_key, strategies, sim_context)

    goal_labels = {
        "aumentar_payload": "Aumentar carga útil",
        "reducir_payload": "Reducir carga útil",
        "mejorar_autonomia": "Mejorar autonomía",
        "reducir_masa": "Reducir masa",
        "mejorar_estabilidad": "Mejorar estabilidad",
    }
    label = goal_labels.get(goal_key, goal_key.replace("_", " ").title())

    lines = [f"Plan estratégico — {label}:", ""]
    for i, s in enumerate(prioritized, start=1):
        lines.append(f"{i}. {s['action']}")
        lines.append(f"   {s['description']}")
        lines.append(f"   Palanca: {s['lever']}")
        if i < len(prioritized):
            lines.append("")

    return "\n".join(lines)


def get_goal_context_for_llm(goal_key: str) -> str:
    """Serializa las estrategias del goal como JSON compacto para inyectar al LLM."""
    strategies = GOAL_STRATEGIES.get(goal_key, [])
    return json.dumps(
        {"goal": goal_key, "strategies": strategies},
        ensure_ascii=False,
        indent=2,
    )
