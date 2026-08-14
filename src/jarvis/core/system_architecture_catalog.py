"""
system_architecture_catalog
============================
Módulo de datos puros. No crea objetos de dominio.

Regla absoluta: este módulo NO importa nada de jarvis.schemas.
               Devuelve strings, listas y dicts primitivos únicamente.
               No conoce completeness, source ni ComponentSpec.
               Esa semántica vive en SystemDefinitionSession.
"""
from __future__ import annotations

import unicodedata


def _normalize(text: str) -> str:
    """Lowercase + strip diacritics (NFD). Función canónica compartida por los catálogos.

    Equivalente a _strip_diacritics en param_definition_session.py pero incluye
    lowercase y strip previos. Los callers que necesiten solo diacríticos sin lowercase
    deben aplicar .lower() por separado antes de su lógica específica.
    """
    nfd = unicodedata.normalize("NFD", text.strip().lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


# ── Arquitecturas base por dominio ────────────────────────────────────────────
# Cada entrada contiene:
#   blocks: lista ordenada de bloques canónicos
#   block_labels: etiquetas humanas para cada bloque
# El orden de inicio se deriva de system_dependency_graph + priority_engine.

SYSTEM_ARCHITECTURES: dict[str, dict] = {
    "dron": {
        "blocks": ["propulsion", "energy", "structure", "control"],
        "block_labels": {
            "propulsion": "Propulsión (motores + hélices)",
            "energy":     "Energía (batería)",
            "structure":  "Estructura (frame)",
            "control":    "Control (controladora + sensores)",
        },
    },
    "uav": {
        "blocks": ["propulsion", "energy", "structure", "control"],
        "block_labels": {
            "propulsion": "Propulsión (motores + hélices)",
            "energy":     "Energía (batería)",
            "structure":  "Estructura (frame)",
            "control":    "Control (controladora + sensores)",
        },
    },
    "robot": {
        "blocks": ["actuation", "transmission", "energy", "control"],
        "block_labels": {
            "actuation":    "Actuación (motores + ruedas)",
            "transmission": "Transmisión",
            "energy":       "Energía",
            "control":      "Control",
        },
    },
    "coche": {
        "blocks": ["actuation", "transmission", "energy", "control"],
        "block_labels": {
            "actuation":    "Actuación (motores + ruedas)",
            "transmission": "Transmisión",
            "energy":       "Energía",
            "control":      "Control",
        },
    },
    "rover": {
        "blocks": ["actuation", "transmission", "energy", "control"],
        "block_labels": {
            "actuation":    "Actuación (motores + ruedas)",
            "transmission": "Transmisión",
            "energy":       "Energía",
            "control":      "Control",
        },
    },
}

# ── Tipo de bloque: cómo se completa ─────────────────────────────────────────
# "param"     → completion driven por current_parameters (valores numéricos)
# "component" → completion driven por components[key].completeness
# "composite" → requiere AMBOS: params OK y componentes OK
#
# Fase 4: "energy" migró a "composite". Fase 6: "propulsion" también.
# DA1 resuelta (23 abril 2026): motors = component-driven → propulsion = composite en Fase 4.

# SYSTEM RULE — Composite block semantics (AND-strict)
# ─────────────────────────────────────────────────────────────────────────────
# Composite blocks use AND-strict semantics:
#   block_complete = params_ok AND components_ok
#
# Neither condition alone is sufficient:
#   params_ok  only → "in_progress" (components still missing)
#   components_ok only → "in_progress" (params still missing)
#   both False         → "not_started"
#   both True          → "complete"
#
# This prevents partial satisfaction from being read as completion.
# Do NOT relax to OR semantics without a documented architectural decision.
# ─────────────────────────────────────────────────────────────────────────────

BLOCK_TYPE: dict[str, str] = {
    "propulsion":    "composite",   # Fase 6: motors (component) + propellers (component) + params
    "actuation":     "param",
    "energy":        "composite",   # Fase 4: battery (component) + param_reason coherente
    "structure":     "component",
    "control":       "component",
    "transmission":  "param",
    "perception":    "component",
    "communication": "component",
    "payload":       "component",
    "manipulation":  "component",
}

# Fallback para bloques custom no registrados: tratar como component-driven.
_BLOCK_TYPE_DEFAULT = "component"


def get_block_type(block: str) -> str:
    """Devuelve el tipo del bloque: 'param', 'component', o 'composite'.
    Fallback: 'component' para bloques custom no registrados.
    """
    return BLOCK_TYPE.get(block, _BLOCK_TYPE_DEFAULT)


# ── Bloque → component keys (strings primitivos) ─────────────────────────────
# Solo se expanden a componentes bloques conocidos en este catálogo.
# Los bloques custom (modo B sin alias) se guardan en system_blocks pero
# NO generan component keys — evita componentes inválidos silenciosos.

# SYSTEM RULE — Blocks as functional views, not ownership boundaries
# ─────────────────────────────────────────────────────────────────────────────
# A single component may satisfy multiple blocks simultaneously.
# Blocks represent functional views; components represent physical entities.
#
#   1 component → N blocks   ✔
#   1 block → exclusive component set   ✗
#
# This means: defining components["motors"] can advance BOTH propulsion AND
# energy at the same time. This is correct — it is the same physical object.
# Do NOT attempt to "deduplicate" a component that appears in multiple blocks.
# ─────────────────────────────────────────────────────────────────────────────

BLOCK_TO_COMPONENTS: dict[str, list[str]] = {
    # DA-MOTORS (23 abril 2026): "motors" aparece en TRES bloques intencionalmente.
    # No es duplicación incorrecta — es intersección de dominios físicos:
    #   propulsion → motors como generador de empuje (thrust_n, kv_rating)
    #   energy     → motors como consumidor de energía (power_w)
    #   actuation  → motors como actuadores (torque_nm, wheels)
    #
    # Fase 6 (27 abril 2026): propulsion ya es "composite" → motors se evalúa
    # como criterio de completitud en AMBOS bloques (propulsion + energy).
    # Decisión DA-MOTORS-2 implementada: Opción B (dependencia compartida).
    #   → Completar motors avanza propulsion Y energy simultáneamente.
    #   → actuation=param → _block_progress_status ignora su component_keys.
    "propulsion":    ["motors", "propellers"],
    "energy":        ["battery", "motors"],
    "structure":     ["frame"],
    "control":       ["flight_controller", "sensors"],
    "actuation":     ["motors", "wheels"],
    "transmission":  ["gearbox"],
    "perception":    ["cameras", "lidar"],
    "communication": ["radio_module"],
    "payload":       ["payload_bay"],
    "manipulation":  ["arm"],
}

# ── vehicle_type → clave canónica del catálogo ────────────────────────────────
VEHICLE_TYPE_ALIASES: dict[str, str] = {
    "dron":       "dron",   "drone":      "dron",
    "uav":        "uav",    "quadcopter": "dron",
    "multirotor": "dron",   "hexacopter": "dron",
    "octocopter": "dron",   "fixed_wing": "uav",
    "robot":      "robot",  "ugv":        "robot",
    "coche":      "coche",  "car":        "coche",
    "rover":      "rover",  "vehicle":    "rover",
}

# ── Alias modo B — texto de usuario → bloque canónico ────────────────────────
# Normalización previa obligatoria: _normalize() antes de lookup.
# Regla: exact match primero; luego contains con \b para evitar falsos positivos.

BLOCK_ALIASES: dict[str, str] = {
    "vision":               "perception",
    "vision artificial":    "perception",
    "camaras":              "perception",
    "camara":               "perception",
    "lidar":                "perception",
    "sensores vision":      "perception",
    "comunicacion":         "communication",
    "telemetria":           "communication",
    "radio":                "communication",
    "payload":              "payload",
    "carga util":           "payload",
    "carga utl":            "payload",
    "manipulador":          "manipulation",
    "brazo":                "manipulation",
    "arm":                  "manipulation",
    "propulsion":           "propulsion",
    "energia":              "energy",
    "bateria":              "energy",
    "estructura":           "structure",
    "frame":                "structure",
    "control":              "control",
    "actuacion":            "actuation",
    "transmision":          "transmission",
}

# ── Bloque → reason code de parameter_requirements ───────────────────────────
# Usado por SystemDefinitionSession para el bridge paramétrico.
# Fuente de verdad: no duplicar aquí la lógica de reason; solo el mapeo.

BLOCK_TO_PARAM_REASON: dict[str, str] = {
    "propulsion": "missing_propulsion_parameters",
    "actuation":  "missing_transmission_parameters",
    # Energy block is param-driven: battery_capacity_wh + motor_power_w are
    # the canonical completion signal (same reason code used by build_startup_context).
    "energy":     "missing_energy_parameters",
}

# SYSTEM RULE — Mirrored parameters
# ──────────────────────────────────────────────────────────────────────────────
# These current_parameters keys are MIRRORS of canonical values stored in
# components[*].properties. They exist solely as the interface to the
# calculation engine (which reads from current_parameters).
#
# INVARIANT: Mirrored params MUST NEVER be written directly to current_parameters.
#            They may ONLY be written via their designated component helper:
#
#   battery_capacity_wh  →  _set_battery_component()
#   battery_mass_kg      →  _set_battery_component() (derived from capacity)
#   motor_power_w        →  _set_motor_component()
#
# Writing them directly bypasses the component spec and breaks the single
# source of truth. Future enforcement: guard in a set_param() gatekeeper (Fase 6+).
# ──────────────────────────────────────────────────────────────────────────────
COMPONENT_MIRRORED_PARAMS: frozenset[str] = frozenset({
    "battery_capacity_wh",      # canónico: components["battery"].properties["battery_capacity_wh"]
    "battery_mass_kg",          # derivado: estimate_battery_mass_kg(battery_capacity_wh) — o
                                 # mass_g/1000 de la SKU cuando components["battery"].catalog_ref
                                 # está fijado (Catalog v1, Impl B, 4A)
    "battery_cell_count",       # canónico: components["battery"].properties["cell_count"]  (U2)
    "motor_power_w",            # canónico: components["motors"].properties["power_w"]
    "motor_kv_rating",          # canónico: components["motors"].properties["kv_rating"]    (U2)
    "motor_mass_kg",            # derivado: (weight_g/1000) * motor_count — SOLO cuando
                                 # components["motors"].catalog_ref está fijado (Catalog v1,
                                 # Impl B, 2A); ausente para motores declarados en texto libre.
    # motor_count NO entra aquí — se puede fijar tanto por componente como por wizard.
    # El invariante "user input beats component inference" requiere que no esté bloqueado.
    "propeller_diameter_in",    # canónico: components["propellers"].properties["diameter_in"]
    "propeller_pitch_in",       # canónico: components["propellers"].properties["pitch_in"] (U2)
})


# ── Public API ────────────────────────────────────────────────────────────────

def get_domain_architecture(vehicle_type: str) -> dict | None:
    """Devuelve la arquitectura del catálogo para el dominio, o None si es desconocido."""
    key = VEHICLE_TYPE_ALIASES.get(_normalize(vehicle_type))
    return SYSTEM_ARCHITECTURES.get(key) if key else None


def blocks_to_component_keys(blocks: list[str]) -> list[str]:
    """
    Expande lista de bloques canónicos a lista deduplicada de component keys.
    Bloques no conocidos en BLOCK_TO_COMPONENTS son ignorados silenciosamente
    (los custom blocks de modo B se almacenan en system_blocks, no aquí).
    """
    seen: set[str] = set()
    keys: list[str] = []
    for block in blocks:
        for key in BLOCK_TO_COMPONENTS.get(block, []):
            if key not in seen:
                seen.add(key)
                keys.append(key)
    return keys


def normalize_block_alias(user_text: str) -> str | None:
    """
    Mapea texto del usuario a un bloque canónico via BLOCK_ALIASES.
    Exact match primero; luego substring solo con _normalize aplicado a ambos lados.
    Devuelve None si no hay match.
    """
    normalized = _normalize(user_text)
    # 1. Exact match
    if normalized in BLOCK_ALIASES:
        return BLOCK_ALIASES[normalized]
    # 2. Substring: alias completo debe estar contenido en el texto normalizado
    #    Se usa la alias como término completo (no fragmento de palabra)
    for alias, block in BLOCK_ALIASES.items():
        if len(alias) >= 4 and alias in normalized:
            return block
    return None


def get_param_reason_for_block(block: str) -> str | None:
    """Devuelve el reason code de parameter_requirements para el bloque dado, o None."""
    return BLOCK_TO_PARAM_REASON.get(block)
