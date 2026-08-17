"""Capa de lectura canónica para propiedades de componentes.

Single Read Point: todos los callers que necesiten leer propiedades de
componentes físicos deben usar estos getters en lugar de acceder directamente
a design_properties.structure.material u otras rutas legacy.

Reglas:
- Siempre leer de components["x"].properties (fuente canónica).
- completeness == "low" → tratar como ausente → aplicar fallback.
- Nunca leer de structure.material (mirror legacy) — ese campo se eliminará
  en el Commit 5 de Fase 3.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from jarvis.domains.materials import LEGACY_MATERIAL_SLUGS

if TYPE_CHECKING:
    from jarvis.schemas.state_schema import DesignProperties


def get_frame_material(design_properties: "DesignProperties") -> str:
    """Lectura canónica del material del frame.

    Returns:
        Material del frame como string canónico — la biblioteca (nombre en
        español, ej. "fibra de carbono", "aluminio"; ver
        ``jarvis.domains.materials``). G10 ★5: si el valor almacenado es un
        slug inglés heredado de acquisitions anteriores a este fix
        (``carbon_fiber``/``aluminum``/``plastic``), se traduce aquí en
        lectura — no requiere migrar archivos de estado existentes.
        Fallback: "aluminio" cuando el frame no está definido o tiene completeness=low.
    """
    frame = design_properties.components.get("frame")
    if (
        frame is not None
        and frame.completeness != "low"
        and "material" in frame.properties
    ):
        value = frame.properties["material"].value
        if not value:
            return "aluminio"
        value = str(value)
        return LEGACY_MATERIAL_SLUGS.get(value, value)
    return "aluminio"


def get_frame_mass_kg(design_properties: "DesignProperties") -> float | None:
    """Lectura canónica de la masa del frame en kg.

    Returns:
        Masa del frame en kg, o None si no está definido o tiene completeness=low.
    """
    frame = design_properties.components.get("frame")
    if (
        frame is not None
        and frame.completeness != "low"
        and "mass_kg" in frame.properties
    ):
        value = frame.properties["mass_kg"].value
        if value is not None:
            return float(value)
    return None


def get_battery_capacity_wh(design_properties: "DesignProperties") -> float | None:
    """Lectura canónica de la capacidad de la batería en Wh.

    Returns:
        Capacidad en Wh, o None si no está definida o tiene completeness=low.
    """
    battery = design_properties.components.get("battery")
    if (
        battery is not None
        and battery.completeness != "low"
        and "battery_capacity_wh" in battery.properties
    ):
        value = battery.properties["battery_capacity_wh"].value
        if value is not None:
            return float(value)
    return None


def get_motor_power_w(design_properties: "DesignProperties") -> float | None:
    """Lectura canónica de la potencia de los motores en W.

    Returns:
        Potencia en W (clave canónica power_w), o None si no está definida o
        tiene completeness=low.
    """
    motors = design_properties.components.get("motors")
    if (
        motors is not None
        and motors.completeness != "low"
        and "power_w" in motors.properties
    ):
        value = motors.properties["power_w"].value
        if value is not None:
            return float(value)
    return None
