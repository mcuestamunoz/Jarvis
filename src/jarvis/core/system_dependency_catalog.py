"""
system_dependency_catalog
==========================
Módulo de datos puros. No crea objetos de dominio.

Regla absoluta: este módulo NO importa nada de jarvis.schemas.
               Devuelve strings, listas y dicts primitivos únicamente.

Estructura de SYSTEM_DEPENDENCIES:
  { vehicle_type_canónico: { bloque: [bloques_de_los_que_depende] } }

La normalización de vehicle_type usa VEHICLE_TYPE_ALIASES del catálogo
de arquitectura — misma clave canónica, misma fuente de verdad.
Los bloques custom (modo B sin alias) no están en el catálogo → reciben
dependencias vacías [] al construir el grafo, nunca causan KeyError.
"""
from __future__ import annotations

from jarvis.core.system_architecture_catalog import VEHICLE_TYPE_ALIASES, _normalize


# ── Dependencias por dominio ──────────────────────────────────────────────────
# Cada bloque lista los bloques que deben estar definidos ANTES que él.
# Bloques sin dependencias tienen lista vacía [].
# El grafo es un DAG — no deben introducirse ciclos.

SYSTEM_DEPENDENCIES: dict[str, dict[str, list[str]]] = {
    "dron": {
        "propulsion": [],
        "energy":     ["propulsion"],
        "structure":  ["propulsion", "energy"],
        "control":    ["structure"],
    },
    "uav": {
        "propulsion": [],
        "energy":     ["propulsion"],
        "structure":  ["propulsion", "energy"],
        "control":    ["structure"],
    },
    "robot": {
        "actuation":    [],
        "transmission": ["actuation"],
        "energy":       ["actuation"],
        "control":      ["energy"],
    },
    "coche": {
        "actuation":    [],
        "transmission": ["actuation"],
        "energy":       ["actuation"],
        "control":      ["energy"],
    },
    "rover": {
        "actuation":    [],
        "transmission": ["actuation"],
        "energy":       ["actuation"],
        "control":      ["energy"],
    },
}


# ── Public API ────────────────────────────────────────────────────────────────

def get_domain_dependencies(vehicle_type: str) -> dict[str, list[str]]:
    """Devuelve el mapa de dependencias canónico para el dominio, o {} si desconocido.

    Normaliza vehicle_type mediante VEHICLE_TYPE_ALIASES — misma lógica que
    get_domain_architecture(), garantizando que la clave canónica sea siempre la misma.
    """
    key = VEHICLE_TYPE_ALIASES.get(_normalize(vehicle_type))
    return SYSTEM_DEPENDENCIES.get(key, {}) if key else {}
