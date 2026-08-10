"""
Aerial domain — component inference rules for multi-rotor aircraft (drones, UAVs).

This module defines:
  - Property extractors for aerial components (motors, propellers, ESCs)
  - Completeness evaluators for each component type
  - A ComponentRuleRegistry pre-loaded with aerial rules

Import ``aerial_registry`` to use these rules in component_inference.py, or
pass a custom registry to ``infer_component()`` to override the domain.
"""
from __future__ import annotations

import re

from jarvis.core.component_rules import ComponentRule, ComponentRuleRegistry
from jarvis.schemas.action_schema import PropertyValue


# ── Motor property extractor ─────────────────────────────────────────────────

def extract_motor_properties(normalized: str) -> dict[str, PropertyValue]:
    """Extract structured PropertyValue entries from a motor specification text."""
    props: dict[str, PropertyValue] = {}

    # motor_count: "4 motores", "4x motors", "4x 920KV", "cuatro motores"
    count_match = re.search(r"\b(\d+)\s*(?:x\s*\d|\s*motores?\b)", normalized)
    if not count_match:
        count_match = re.search(r"\b(\d+)\s*x\b", normalized)
    if count_match:
        props["motor_count"] = PropertyValue(
            value=int(count_match.group(1)),
            unit=None,
            confidence=0.9,
            source="declared",
        )

    # kv_rating: "920KV", "920 kv"
    kv_match = re.search(r"\b(\d+(?:\.\d+)?)\s*kv\b", normalized, re.IGNORECASE)
    if kv_match:
        props["kv_rating"] = PropertyValue(
            value=float(kv_match.group(1)),
            unit="KV",
            confidence=0.9,
            source="declared",
        )

    # thrust_n: "15N", "15 N", "15N de empuje"
    thrust_match = re.search(
        r"\b(\d+(?:\.\d+)?)\s*n\b(?!\s*(?:de\s+)?(?:kv|w|a))", normalized, re.IGNORECASE
    )
    if thrust_match:
        props["thrust_n"] = PropertyValue(
            value=float(thrust_match.group(1)),
            unit="N",
            confidence=0.9,
            source="declared",
        )

    # watts / power_w: "100W" — stored as both 'watts' (legacy) and 'power_w' (canonical Fase 4)
    watts_match = re.search(r"\b(\d+(?:\.\d+)?)\s*w\b", normalized, re.IGNORECASE)
    if watts_match:
        pw = float(watts_match.group(1))
        props["watts"] = PropertyValue(value=pw, unit="W", confidence=0.85, source="declared")
        # Fase 4: canonical key for Single Write Point → mirror in current_parameters
        props["power_w"] = PropertyValue(value=pw, unit="W", confidence=0.85, source="declared")

    # model: "MN3510", "T-Motor MN3510", "EMAX 2207"
    model_match = re.search(
        r"\b([A-Z]{1,6}\d{4}|[Tt]-[Mm]otor\s+\w+|[Ee][Mm][Aa][Xx]\s+\d+)\b", normalized
    )
    if model_match:
        props["model"] = PropertyValue(
            value=model_match.group(0).strip(), unit=None, confidence=0.85, source="declared"
        )

    return props


def _motor_completeness(props: dict) -> tuple[str, list[str]]:
    has_thrust = "thrust_n" in props
    has_count = "motor_count" in props
    has_kv = "kv_rating" in props
    has_power = "power_w" in props or "watts" in props  # Fase 4: power_w es canónico
    missing: list[str] = []
    if not has_thrust and not has_kv and not has_power:
        missing.append("empuje por motor, KV o potencia (W)")
    if not has_count:
        missing.append("número de motores")
    if (has_thrust or has_power) and (has_count or has_kv):
        return "high", missing
    if props:
        return "medium", missing
    return "low", missing


# ── Propeller property extractor ─────────────────────────────────────────────

def extract_propeller_properties(normalized: str) -> dict[str, PropertyValue]:
    props: dict[str, PropertyValue] = {}
    size_match = re.search(r"\b(\d+)\s*x\s*(\d+(?:\.\d+)?)\b", normalized)
    if size_match:
        props["diameter_in"] = PropertyValue(
            value=float(size_match.group(1)), unit="in", confidence=0.9, source="declared"
        )
        props["pitch_in"] = PropertyValue(
            value=float(size_match.group(2)), unit="in", confidence=0.9, source="declared"
        )
    # Count must be an integer OUTSIDE the NxP size span. A naive \b(\d+)\b
    # otherwise steals pitch decimals ("10x4.5" → count=5) or diameter digits
    # ("10 x 4.5" → count=10). Explicit counts like "6 hélices 15x5" still match.
    if "diameter_in" in props:
        size_span = size_match.span() if size_match else None
        for count_match in re.finditer(r"\b(\d+)\b", normalized):
            if size_span is not None and size_span[0] <= count_match.start() < size_span[1]:
                continue
            props["count"] = PropertyValue(
                value=int(count_match.group(1)), unit=None, confidence=0.8, source="declared"
            )
            break
    return props


def _propeller_completeness(props: dict) -> tuple[str, list[str]]:
    missing: list[str] = []
    if "diameter_in" not in props:
        missing.append("diámetro/paso")
    if not props or "diameter_in" not in props:
        return "low", missing
    return "high", []


# ── ESC property extractor ───────────────────────────────────────────────────

def extract_esc_properties(normalized: str) -> dict[str, PropertyValue]:
    props: dict[str, PropertyValue] = {}
    amps_match = re.search(r"\b(\d+(?:\.\d+)?)\s*a\b", normalized, re.IGNORECASE)
    if amps_match:
        props["current_a"] = PropertyValue(
            value=float(amps_match.group(1)), unit="A", confidence=0.9, source="declared"
        )
    return props


def _esc_completeness(props: dict) -> tuple[str, list[str]]:
    if "current_a" not in props:
        return "medium", ["corriente nominal"]
    return "high", []


# ── Battery property extractor ──────────────────────────────────────────────

def extract_battery_properties(normalized: str) -> dict[str, PropertyValue]:
    props: dict[str, PropertyValue] = {}

    # cell count first: "4s", "6s" — needed to correctly convert mAh → Wh
    cell_match = re.search(r"\b(\d+)s\b", normalized, re.IGNORECASE)
    if cell_match:
        props["cell_count"] = PropertyValue(
            value=int(cell_match.group(1)), unit="S", confidence=0.9, source="declared"
        )

    # capacity: "5000mah", "5000 mah"
    # With cell_count: wh = mAh/1000 * cells * 3.7V (nominal LiPo)
    # Without cell_count: assume 1S (rough estimate, low confidence)
    mah_match = re.search(r"\b(\d+(?:\.\d+)?)\s*mah\b", normalized, re.IGNORECASE)
    if mah_match:
        mah = float(mah_match.group(1))
        cells = int(props["cell_count"].value) if "cell_count" in props else 1
        wh = round(mah / 1000 * cells * 3.7, 2)
        confidence = 0.9 if "cell_count" in props else 0.5
        props["battery_capacity_wh"] = PropertyValue(
            value=wh, unit="Wh", confidence=confidence, source="inferred"
        )

    # capacity in Wh: "100wh", "100 wh" — direct declaration takes priority
    wh_match = re.search(r"\b(\d+(?:\.\d+)?)\s*wh\b", normalized, re.IGNORECASE)
    if wh_match:
        props["battery_capacity_wh"] = PropertyValue(
            value=float(wh_match.group(1)), unit="Wh", confidence=0.9, source="declared"
        )

    return props


def _battery_completeness(props: dict) -> tuple[str, list[str]]:
    missing: list[str] = []
    if "battery_capacity_wh" not in props:
        missing.append("capacidad (Wh o mAh)")
    if not props:
        return "low", missing
    if "battery_capacity_wh" in props:
        return "medium", missing
    return "low", missing


# ── Frame property extractor ─────────────────────────────────────────────────

MATERIAL_MAP: dict[str, str] = {
    "carbono":           "carbon_fiber",
    "fibra de carbono":  "carbon_fiber",
    "carbon":            "carbon_fiber",
    "carbon fiber":      "carbon_fiber",
    "cf":                "carbon_fiber",
    "aluminio":          "aluminum",
    "aluminum":          "aluminum",
    "aluminium":         "aluminum",
    "alu":               "aluminum",
    "plastico":          "plastic",
    "plástico":          "plastic",
    "abs":               "plastic",
    "nylon":             "plastic",
}


def extract_frame_properties(normalized: str) -> dict[str, PropertyValue]:
    """Extract mass_kg and material from a free-text frame description.

    Examples:
        "fibra de carbono 450g"  → {mass_kg: 0.45, material: "carbon_fiber"}
        "aluminio 0.6kg"         → {mass_kg: 0.6,  material: "aluminum"}
        "carbono"                → {material: "carbon_fiber"}
        "500g"                   → {mass_kg: 0.5}
    """
    props: dict[str, PropertyValue] = {}

    # mass: grams ("450g", "500 g") or kg ("0.45kg", "0.45 kg")
    mass_g = re.search(r"\b(\d+(?:\.\d+)?)\s*g\b", normalized, re.IGNORECASE)
    mass_kg = re.search(r"\b(\d+(?:\.\d+)?)\s*kg\b", normalized, re.IGNORECASE)
    if mass_kg:
        props["mass_kg"] = PropertyValue(
            value=float(mass_kg.group(1)), unit="kg", confidence=0.95, source="declared"
        )
    elif mass_g:
        props["mass_kg"] = PropertyValue(
            value=round(float(mass_g.group(1)) / 1000, 4), unit="kg", confidence=0.9, source="declared"
        )

    # material: longest match first to prefer "fibra de carbono" over "carbono"
    found_material: str | None = None
    found_len = 0
    lower = normalized.lower()
    for alias, canonical in MATERIAL_MAP.items():
        if alias in lower and len(alias) > found_len:
            found_material = canonical
            found_len = len(alias)
    if found_material:
        props["material"] = PropertyValue(
            value=found_material, unit=None, confidence=0.9, source="declared"
        )

    return props


def _frame_completeness(props: dict) -> tuple[str, list[str]]:
    """Evaluate completeness of frame properties.

    Returns:
        ("high",   [])              — mass_kg + material present
        ("medium", [...])           — mass_kg present, material missing
        ("low",    [...])           — neither present
    """
    has_mass = "mass_kg" in props
    has_material = "material" in props
    missing: list[str] = []
    if not has_mass:
        missing.append("masa (ej: 450g)")
    if not has_material:
        missing.append("material (ej: fibra de carbono)")
    if has_mass and has_material:
        return "high", []
    if has_mass:
        return "medium", missing
    return "low", missing


# ── Flight Controller property extractor ─────────────────────────────────────

FLIGHT_CONTROLLER_MAP: dict[str, str] = {
    # Longest strings first to ensure longest-match wins
    "pixhawk 6x":     "pixhawk_6x",
    "pixhawk 6c":     "pixhawk_6c",
    "pixhawk 6":      "pixhawk_6",
    "pixhawk 4 mini": "pixhawk_4_mini",
    "pixhawk 4":      "pixhawk_4",
    "pixhawk":        "pixhawk",
    "ardupilot":      "ardupilot",
    "betaflight":     "betaflight",
    "naze32":         "naze32",
    "matek":          "matek",
}


def extract_flight_controller_properties(normalized: str) -> dict[str, PropertyValue]:
    """Extract model from a flight controller description.

    Examples:
        "Pixhawk 4"            → {model: "pixhawk_4",  confidence=0.9}
        "controladora Pixhawk" → {model: "pixhawk",    confidence=0.7}
        "ardupilot"            → {model: "ardupilot",  confidence=0.7}
        "controladora"         → {} (brand not identified)
    """
    props: dict[str, PropertyValue] = {}
    lower = normalized.lower()
    found_model: str | None = None
    found_len = 0
    found_confidence = 0.7

    for alias, canonical in FLIGHT_CONTROLLER_MAP.items():
        if alias in lower and len(alias) > found_len:
            found_model = canonical
            found_len = len(alias)
            # Specific model string (contains digit) → higher confidence
            found_confidence = 0.9 if any(ch.isdigit() for ch in alias) else 0.7

    if found_model:
        props["model"] = PropertyValue(
            value=found_model, unit=None, confidence=found_confidence, source="declared"
        )
    return props


def _flight_controller_completeness(props: dict) -> tuple[str, list[str]]:
    """Evaluate completeness of flight controller properties.

    Returns:
        ("high",   [])   — specific model identified (confidence >= 0.85)
        ("medium", [])   — category/brand identified (confidence < 0.85)
        ("low",    [...])— nothing recognised
    """
    if "model" not in props:
        return "low", ["modelo de controladora (ej: Pixhawk 4, Betaflight F7)"]
    model_prop = props["model"]
    confidence = model_prop.confidence if isinstance(model_prop, PropertyValue) else 0.0
    if confidence >= 0.85:
        return "high", []
    return "medium", []


# ── GPS / Sensor property extractor ──────────────────────────────────────────

GPS_MAP: dict[str, str] = {
    # Longest strings first
    "here3+": "here3_plus",
    "here3":  "here3",
    "here+":  "here_plus",
    "here2":  "here2",
    "m8n":    "ublox_m8n",
    "m9n":    "ublox_m9n",
    "m10":    "ublox_m10",
    "gps":    "generic_gps",
}

# Bug 66: sensor types beyond GPS (IMU, barometer, compass).
# component_inference.py passes text as text.lower() — diacritics are PRESERVED.
# Both accented and non-accented forms must be present as keys.
# Longest strings first to ensure longest-match wins (e.g. "acelerometro" > "imu").
SENSOR_TYPE_MAP: dict[str, str] = {
    "acelerometro": "imu",
    "acelerómetro": "imu",
    "giroscopio":   "imu",
    "inercial":     "imu",
    "imu":          "imu",
    "magnetometro": "compass",
    "magnetómetro": "compass",
    "brujula":      "compass",
    "brújula":      "compass",
    "compass":      "compass",
    "barometro":    "barometer",
    "barómetro":    "barometer",
    "presion":      "barometer",
    "presión":      "barometer",
}


def extract_sensor_properties(normalized: str) -> dict[str, PropertyValue]:
    """Extract GPS model and/or sensor type from a sensor description.

    The `normalized` argument is expected to be lowercased (diacritics preserved
    since component_inference only calls text.lower()). Both GPS and sensor-type
    searches use longest-match: when multiple aliases are present the longest wins.

    Examples:
        "gps m9n"         → {gps_model: "ublox_m9n",   confidence=0.9}
        "here3"           → {gps_model: "here3",        confidence=0.9}
        "gps generico"    → {gps_model: "generic_gps",  confidence=0.6}
        "sensores imu"    → {sensor_type: "imu",        confidence=0.8}
        "barómetro"       → {sensor_type: "barometer",  confidence=0.8}
        "imu y barómetro" → {sensor_type: "barometer",  confidence=0.8}  (longest-match wins)
    """
    props: dict[str, PropertyValue] = {}
    lower = normalized.lower()

    # ── GPS model (existing logic) ────────────────────────────────────────────
    found_model: str | None = None
    found_len = 0
    found_confidence = 0.6

    for alias, canonical in GPS_MAP.items():
        if alias in lower and len(alias) > found_len:
            found_model = canonical
            found_len = len(alias)
            found_confidence = 0.6 if alias == "gps" else 0.9

    if found_model:
        props["gps_model"] = PropertyValue(
            value=found_model, unit=None, confidence=found_confidence, source="declared"
        )

    # ── Sensor type (Bug 66: IMU, barometer, compass) ─────────────────────────
    # Bug 68: use word-boundary regex instead of plain substring so that 'imu'
    # matches only as a standalone word and not as a substring of 'simula'.
    found_sensor_type: str | None = None
    found_type_len = 0

    for alias, canonical in SENSOR_TYPE_MAP.items():
        if re.search(r'\b' + re.escape(alias) + r'\b', lower) and len(alias) > found_type_len:
            found_sensor_type = canonical
            found_type_len = len(alias)

    if found_sensor_type:
        props["sensor_type"] = PropertyValue(
            value=found_sensor_type, unit=None, confidence=0.8, source="declared"
        )

    return props


def _sensor_completeness(props: dict) -> tuple[str, list[str]]:
    """Evaluate completeness of sensor properties.

    Returns:
        ("medium", []) — gps_model or sensor_type present
        ("low",    [...])— nothing recognised
    """
    if "gps_model" not in props and "sensor_type" not in props:
        return "low", ["modelo GPS (ej: M9N, Here3) o tipo de sensor (ej: IMU, barómetro)"]
    return "medium", []


# ── Rule registry for aerial domain ─────────────────────────────────────────

aerial_registry = ComponentRuleRegistry([
    ComponentRule(
        keywords=("helice", "hélice", "propeller", "props"),
        component_type="propulsion_passive",
        suggested_key="propellers",
        inference_confidence=0.6,
        property_extractor=extract_propeller_properties,
        completeness_evaluator=_propeller_completeness,
        missing_field_hints=("Define tamaño de hélice (ej: 10x4.5)",),
    ),
    ComponentRule(
        keywords=("motor",),
        component_type="propulsion_active",
        suggested_key="motors",
        inference_confidence=0.75,
        property_extractor=extract_motor_properties,
        completeness_evaluator=_motor_completeness,
        missing_field_hints=("Incluye cantidad y especificación (ej: 4x 920KV)",),
        output_magnitude="thrust_n",
    ),
    ComponentRule(
        keywords=("esc",),
        component_type="power_control",
        suggested_key="esc",
        inference_confidence=0.7,
        property_extractor=extract_esc_properties,
        completeness_evaluator=_esc_completeness,
        missing_field_hints=("Añade corriente nominal (ej: 30A)",),
    ),
    ComponentRule(
        keywords=("bateria", "batería", "battery", "lipo", "lipoly", "celda", "acumulador", "pack"),
        component_type="energy_storage",
        suggested_key="battery",
        inference_confidence=0.8,
        property_extractor=extract_battery_properties,
        completeness_evaluator=_battery_completeness,
        missing_field_hints=("Define battery_capacity_wh (Wh) y motor_power_w (W) para calcular autonomía",),
    ),
    ComponentRule(
        keywords=("frame", "chasis", "estructura", "armazon", "armazón", "carbon", "carbono", "aluminio"),
        component_type="structure",
        suggested_key="frame",
        inference_confidence=0.8,
        property_extractor=extract_frame_properties,
        completeness_evaluator=_frame_completeness,
        missing_field_hints=("Describe material y masa del frame. Ej: 'fibra de carbono 450g'",),
    ),
    ComponentRule(
        keywords=("pixhawk", "controladora", "flight controller", "ardupilot", "betaflight", "naze32", "matek"),
        component_type="flight_controller",
        suggested_key="flight_controller",
        inference_confidence=0.85,
        property_extractor=extract_flight_controller_properties,
        completeness_evaluator=_flight_controller_completeness,
        missing_field_hints=("Indica el modelo exacto. Ej: 'Pixhawk 4' o 'Betaflight F7'",),
    ),
    ComponentRule(
        keywords=("gps", "m8n", "m9n", "m10", "here3", "here+", "here2", "gnss",
                  "imu", "inercial", "barometro", "barómetro", "sensor", "sensores",
                  "magnetometro", "magnetómetro", "brujula", "brújula", "giroscopio"),
        component_type="sensors",
        suggested_key="sensors",
        inference_confidence=0.8,
        property_extractor=extract_sensor_properties,
        completeness_evaluator=_sensor_completeness,
        missing_field_hints=("Indica el modelo GPS o tipo de sensor. Ej: 'GPS M9N', 'IMU', 'barómetro'",),
    ),
])
