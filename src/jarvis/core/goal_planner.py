"""Goal Planner — detección determinista de objetivos de diseño y catálogo de estrategias.

Flujo:
    user_input → detect_goal() → goal_key | None
    goal_key   → format_goal_plan()       → bloque de texto fijo para display
    goal_key   → get_goal_context_for_llm() → JSON de estrategias para inyectar al LLM
"""

from __future__ import annotations

import json
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
}

# ── Tabla de detección de objetivos ───────────────────────────────────────────
# Cada entry: (goal_key, [(keyword_normalizada, ...)])
# Las keywords deben estar normalizadas (minúsculas, sin diacríticos).

_GOAL_KEYWORDS: list[tuple[str, list[str]]] = [
    (
        "aumentar_payload",
        [
            "carga util", "carga utile", "payload",
            "levantar mas", "levantar peso", "mas carga",
            "mejorar carga", "aumentar carga", "incrementar carga",
            "subir carga", "mas peso util", "peso util",
        ],
    ),
    (
        "mejorar_autonomia",
        [
            "autonomia", "duracion vuelo", "vuelo mas largo", "mas tiempo",
            "mejorar autonomia", "aumentar autonomia", "mas autonomia",
            "bateria", "duracion bateria", "mas vuelo",
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
        ],
    ),
]


def _normalize(text: str) -> str:
    """Minúsculas + eliminación de diacríticos."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def detect_goal(user_input: str) -> Optional[str]:
    """Detecta el goal de diseño del usuario.

    Returns:
        goal_key si se detecta un objetivo reconocido, None en caso contrario.
    """
    normalized = _normalize(user_input)
    for goal_key, keywords in _GOAL_KEYWORDS:
        for kw in keywords:
            if kw in normalized:
                return goal_key
    return None


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
