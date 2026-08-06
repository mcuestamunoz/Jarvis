from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Any


MISSING_TRANSMISSION_PARAMETERS = "missing_transmission_parameters"
MISSING_PROPULSION_PARAMETERS = "missing_propulsion_parameters"
MISSING_ENERGY_PARAMETERS = "missing_energy_parameters"
MISSING_PROPELLER_PARAMETERS = "missing_propeller_parameters"
MISSING_COMPONENT_DEFINITION = "missing_component_definition"

DEFAULT_MISSING_FORCE_REASON = MISSING_TRANSMISSION_PARAMETERS
MISSING_FORCE_REASONS: frozenset[str] = frozenset(
    {
        MISSING_TRANSMISSION_PARAMETERS,
        MISSING_PROPULSION_PARAMETERS,
        MISSING_PROPELLER_PARAMETERS,
    }
)


class VariableType(str, Enum):
    NUMERIC_DIRECT    = "numeric_direct"    # parámetro numérico settable directamente
    SEMANTIC_MUTATION = "semantic_mutation" # mutación conceptual (reducir/aumentar, no set-to-value)
    NUMERIC           = "numeric"           # genérico numérico (para variables derivadas)
    # futuro: CATEGORICAL, COMPONENT_DEFINE, STRUCTURAL, COMPUTED, LATENT


@dataclass(frozen=True)
class ParameterRequirement:
    name: str
    label: str
    unit: str
    example: str
    keywords: tuple[str, ...]
    # --- naturaleza + política (todos con default → las 7 entradas existentes no cambian) ---
    variable_type: VariableType = VariableType.NUMERIC_DIRECT
    # naturaleza funcional de la variable (no política de uso)
    aliases: tuple[str, ...] = ()
    # user-facing display-name aliases → canonical key (reemplaza _PARAM_DISPLAY_ALIASES)
    concept_aliases: tuple[str, ...] = ()
    # concept words que resuelven A esta clave canónica (reemplaza _VARIABLE_NORMALIZATION)
    display_name: str | None = None
    # label humano para semantic_mutation en wizard (reemplaza _SEMANTIC_MUTATION_DISPLAY)
    is_derived: bool = False
    # True → variable no-settable directamente; se intercepta en step 1 del wizard
    derived_message: str | None = None
    # mensaje de redirección cuando el usuario intenta modificar esta variable
    description: str | None = None
    # consumido por build_action_space() para el LLM

    @property
    def hint(self) -> str:
        unit_text = f" en {self.unit}" if self.unit else ""
        return f"({self.label}{unit_text}, ej: {self.example})"


@dataclass(frozen=True)
class RequirementReason:
    code: str
    required_params: tuple[str, ...]
    domain_label: str
    hint: str | None = None


PARAMETER_REQUIREMENTS: dict[str, ParameterRequirement] = {
    "wheel_radius_m": ParameterRequirement(
        name="wheel_radius_m",
        label="radio de rueda",
        unit="metros",
        example="0.15",
        keywords=("radio de rueda", "radio rueda", "radio", "wheel radius", "wheel_radius"),
        description="Radio de la rueda del sistema terrestre. Necesario para la conversión torque → fuerza de tracción.",
    ),
    "gear_ratio": ParameterRequirement(
        name="gear_ratio",
        label="relación de transmisión",
        unit="",
        example="10",
        keywords=("relación de transmisión", "transmisión", "gear_ratio", "engranaje", "gear"),
        description="Relación de transmisión entre motor y rueda. Necesario para la conversión torque → fuerza de tracción.",
    ),
    "battery_capacity_wh": ParameterRequirement(
        name="battery_capacity_wh",
        label="capacidad de batería",
        unit="Wh",
        example="2000",
        keywords=("capacidad de batería", "batería", "battery_capacity", "battery", "capacidad"),
        aliases=(
            # Una forma por clave normalizada (el normalizador aplana tildes)
            "batería",              # normaliza → bateria
            "capacidad_batería",    # normaliza → capacidad_bateria
            "capacidad de batería", # normaliza → capacidad de bateria
            "capacidad bateria",    # sin variante tildada distinta
        ),
        description="Capacidad total de la batería del sistema.",
    ),
    "motor_power_w": ParameterRequirement(
        name="motor_power_w",
        label="potencia por motor",
        unit="W",
        example="50",
        keywords=("potencia por motor", "potencia", "motor_power", "power"),
        aliases=("potencia_motor", "potencia_motores", "potencia motores", "potencia por motor"),
        description="Potencia nominal de cada motor del sistema.",
    ),
    "motor_count": ParameterRequirement(
        name="motor_count",
        label="número de motores",
        unit="",
        example="4",
        keywords=("motores", "numero de motores", "número de motores", "motors", "actuadores", "wheels"),
        aliases=("motores", "num_motores", "motors"),
        description="Número de motores o actuadores del sistema.",
    ),
    "per_motor_max_thrust_n": ParameterRequirement(
        name="per_motor_max_thrust_n",
        label="empuje máximo por motor",
        unit="N",
        example="20",
        keywords=("empuje por motor", "empuje máximo por motor", "thrust", "empuje"),
        aliases=("empuje_max_por_motor",),
        description="Empuje máximo que puede generar cada motor individualmente.",
    ),
    "per_actuator_torque_nm": ParameterRequirement(
        name="per_actuator_torque_nm",
        label="par de torsión por actuador",
        unit="N*m",
        example="1.5",
        keywords=("par de torsión", "par motor", "par máximo", "torque por motor", "torque", "par"),
        description="Par de torsión máximo por actuador. Magnitud de salida para sistemas de tracción terrestre.",
    ),
    # --- Nuevas entradas (Fase 2 — Domain Registry refactor) ---
    "structure_mass_factor": ParameterRequirement(
        name="structure_mass_factor",
        label="factor de masa estructural",
        unit="",
        example="1.3",
        keywords=("factor estructura", "estructura", "factor_estructura", "structure_mass_factor"),
        aliases=("factor_estructura",),
        description="Factor multiplicador sobre la masa de componentes para estimar masa estructural total.",
    ),
    "safety_factor": ParameterRequirement(
        name="safety_factor",
        label="factor de seguridad",
        unit="",
        example="1.5",
        keywords=("factor seguridad", "seguridad", "factor_seguridad", "safety_factor"),
        aliases=("factor_seguridad",),
        description="Factor de seguridad aplicado sobre los cálculos de empuje y carga.",
    ),
    "payload_kg": ParameterRequirement(
        name="payload_kg",
        label="payload (carga útil)",
        unit="kg",
        example="2.0",
        keywords=("payload", "carga", "carga util", "carga útil", "payload_kg"),
        variable_type=VariableType.SEMANTIC_MUTATION,
        concept_aliases=(
            # Una forma por clave normalizada
            "carga",      # normaliza → carga
            "payload",    # normaliza → payload
            "carga útil", # normaliza → carga util (cubre "carga util" también)
        ),
        display_name="el payload (carga útil)",
        description="Carga útil que el sistema debe transportar o levantar.",
    ),
    "autonomia": ParameterRequirement(
        name="autonomia",
        label="autonomía",
        unit="min",
        example="30",
        keywords=("autonomia", "autonomía", "tiempo de vuelo", "endurance"),
        variable_type=VariableType.NUMERIC,
        is_derived=True,
        derived_message=(
            "La autonomía es un resultado derivado — no se puede modificar directamente. "
            "Para mejorarla, modifica 'battery_capacity_wh' (capacidad de batería) "
            "o 'motor_power_w' (potencia de motores)."
        ),
        description="Tiempo de operación estimado. Variable derivada, no settable directamente.",
    ),
    "empuje": ParameterRequirement(
        name="empuje",
        label="empuje",
        unit="N",
        example="60",
        keywords=("empuje", "thrust", "fuerza de empuje", "empuje total"),
        aliases=("thrust", "fuerza de empuje", "empuje total"),
        concept_aliases=("empuje",),
        variable_type=VariableType.NUMERIC,
        is_derived=True,
        derived_message=(
            "El empuje es un resultado derivado — no se puede modificar directamente. "
            "Para modificarlo, ajusta 'motor_count' (número de motores) "
            "o 'per_actuator_torque_nm' (torque por actuador)."
        ),
        description="Fuerza de empuje total. Variable derivada, no settable directamente.",
    ),
    "propeller_diameter_in": ParameterRequirement(
        name="propeller_diameter_in",
        label="diámetro de hélice",
        unit="pulgadas",
        example="10",
        keywords=("helice", "hélice", "diametro helice", "diámetro hélice", "propeller_diameter", "diámetro", "diametro", "pulgadas", "propeller"),
        description="Diámetro de la hélice en pulgadas. Alias de entrada; internamente se convierte a propeller_diameter_m.",
    ),
    "propeller_rpm": ParameterRequirement(
        name="propeller_rpm",
        label="RPM del motor",
        unit="rpm",
        example="8000",
        keywords=("rpm", "revoluciones", "rotaciones", "propeller_rpm", "velocidad motor"),
        description="Velocidad de rotación del motor en RPM para inferencia aerodinámica.",
    ),
}


REQUIREMENT_REASONS: dict[str, RequirementReason] = {
    MISSING_TRANSMISSION_PARAMETERS: RequirementReason(
        code=MISSING_TRANSMISSION_PARAMETERS,
        required_params=("per_actuator_torque_nm", "motor_count", "wheel_radius_m", "gear_ratio"),
        domain_label="transmisión",
        hint='Puedes responder: "1.5 torque, 4 ruedas, 0.15 y 10"',
    ),
    MISSING_PROPULSION_PARAMETERS: RequirementReason(
        code=MISSING_PROPULSION_PARAMETERS,
        required_params=("motor_count", "per_motor_max_thrust_n"),
        domain_label="propulsión",
        hint='Puedes decir "4 motores" y el empuje máximo por motor en N',
    ),
    MISSING_ENERGY_PARAMETERS: RequirementReason(
        code=MISSING_ENERGY_PARAMETERS,
        required_params=("battery_capacity_wh", "motor_power_w"),
        domain_label="energía",
        hint='Puedes responder: "batería 2000 potencia 50"',
    ),
    MISSING_PROPELLER_PARAMETERS: RequirementReason(
        code=MISSING_PROPELLER_PARAMETERS,
        required_params=("propeller_diameter_in", "propeller_rpm"),
        domain_label="hélice",
        hint='Puedes responder: "10 pulgadas 8000 rpm"',
    ),
}


def params_for_reason(reason: str | None) -> tuple[str, ...]:
    requirement = REQUIREMENT_REASONS.get(reason or "")
    return requirement.required_params if requirement else ()


def reason_domain_label(reason: str | None) -> str:
    requirement = REQUIREMENT_REASONS.get(reason or "")
    if requirement:
        return requirement.domain_label
    return "transmisión"


def reason_hint(reason: str | None) -> str | None:
    requirement = REQUIREMENT_REASONS.get(reason or "")
    return requirement.hint if requirement else None


def keywords_for_param(param: str) -> tuple[str, ...]:
    requirement = PARAMETER_REQUIREMENTS.get(param)
    return requirement.keywords if requirement else ()


def all_parameter_names() -> list[str]:
    return list(PARAMETER_REQUIREMENTS.keys())


def param_question(param: str) -> str:
    requirement = PARAMETER_REQUIREMENTS.get(param)
    if requirement is None:
        return f"¿Cuál es el valor de {param}?"
    unit_part = f" en {requirement.unit}" if requirement.unit else ""
    return f"¿Cuál es el {requirement.label} ({param}){unit_part}? (ej: {requirement.example})"


def param_hint(param: str) -> str:
    requirement = PARAMETER_REQUIREMENTS.get(param)
    return requirement.hint if requirement else ""


def missing_params_for_reason(reason: str | None, params: dict[str, Any]) -> list[str]:
    return [param for param in params_for_reason(reason) if params.get(param) is None]


def missing_force_reason_from_warnings(warnings: list[str] | tuple[str, ...]) -> str:
    for warning in warnings:
        if warning in MISSING_FORCE_REASONS:
            return warning
    return DEFAULT_MISSING_FORCE_REASON


def is_known_reason(reason: str | None) -> bool:
    return bool(reason and reason in REQUIREMENT_REASONS)


# ---------------------------------------------------------------------------
# Domain Registry helpers (Fase 3)
# ---------------------------------------------------------------------------

def normalize_alias(text: str) -> str:
    """Lowercase + strip diacritics + strip whitespace.

    Shared normalization policy for all alias lookups across the system.
    ``iterate_domain._normalize_variable_input`` is kept as a local alias
    for backward compatibility (verified identical by test CROSS-1).
    """
    nfkd = unicodedata.normalize("NFKD", text.lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def build_alias_map() -> dict[str, str]:
    """Return ``{normalized_alias: canonical_name}`` for all entries with aliases.

    Replaces ``mutation_engine._PARAM_DISPLAY_ALIASES`` as the source of truth.
    All keys are normalized via ``_normalize_alias`` to avoid invisible duplicates.
    """
    result: dict[str, str] = {}
    for canonical, req in PARAMETER_REQUIREMENTS.items():
        for alias in req.aliases:
            result[normalize_alias(alias)] = canonical
    return result


def build_normalization_map() -> dict[str, str]:
    """Return ``{normalized_concept_alias: canonical_name}`` for concept words.

    Replaces ``iterate_domain._VARIABLE_NORMALIZATION`` as the source of truth.
    """
    result: dict[str, str] = {}
    for canonical, req in PARAMETER_REQUIREMENTS.items():
        for concept in req.concept_aliases:
            result[normalize_alias(concept)] = canonical
    return result


def build_semantic_params() -> frozenset[str]:
    """Return canonical names whose ``variable_type`` is ``SEMANTIC_MUTATION``.

    Replaces ``iterate_domain._SEMANTIC_MUTATION_PARAMS``.
    """
    return frozenset(
        name
        for name, req in PARAMETER_REQUIREMENTS.items()
        if req.variable_type == VariableType.SEMANTIC_MUTATION
    )


def build_valid_domain() -> frozenset[str]:
    """Return all terms that are valid step-1 inputs: names + aliases + concept_aliases.

    Replaces the hardcoded portion of ``iterate_domain._VALID_VARIABLE_DOMAIN``.
    ``_STRUCTURAL_TERMS`` (lexical wizard terms) are NOT included here — they are
    added by the caller with a set union.
    """
    terms: set[str] = set()
    for canonical, req in PARAMETER_REQUIREMENTS.items():
        terms.add(normalize_alias(canonical))
        for alias in req.aliases:
            terms.add(normalize_alias(alias))
        for concept in req.concept_aliases:
            terms.add(normalize_alias(concept))
    return frozenset(terms)


def get_derived_message(var_normalised: str) -> str | None:
    """Return the redirect message for a derived variable, or ``None``.

    ``var_normalised`` must already be normalized (lowercase, no diacritics).
    Replaces ``iterate_domain._DERIVED_VARIABLE_MESSAGES``.
    """
    req = PARAMETER_REQUIREMENTS.get(var_normalised)
    if req and req.is_derived:
        return req.derived_message
    return None


def get_display_name(canonical: str) -> str | None:
    """Return the human-readable display name for a ``SEMANTIC_MUTATION`` variable.

    Replaces ``iterate_domain._SEMANTIC_MUTATION_DISPLAY``.
    """
    req = PARAMETER_REQUIREMENTS.get(canonical)
    if req:
        return req.display_name
    return None


def build_action_space() -> dict[str, dict]:
    """Return a structured dict consumable by the LLM.

    Format per entry::

        {
            "type": <VariableType value>,   # naturaleza de la variable
            "settable": <bool>,             # política: not is_derived
            "derived": <bool>,              # True si is_derived
            "description": <str | None>,
            "aliases": [<normalized alias>, ...],
            "display_name": <str | None>,   # solo para SEMANTIC_MUTATION
            "message": <str | None>,        # solo para is_derived
        }
    """
    space: dict[str, dict] = {}
    for canonical, req in PARAMETER_REQUIREMENTS.items():
        entry: dict = {
            "type": req.variable_type.value,
            "settable": not req.is_derived,
            "derived": req.is_derived,
            "description": req.description,
            "aliases": [normalize_alias(a) for a in req.aliases]
                      + [normalize_alias(c) for c in req.concept_aliases],
        }
        if req.display_name is not None:
            entry["display_name"] = req.display_name
        if req.is_derived and req.derived_message is not None:
            entry["message"] = req.derived_message
        space[canonical] = entry
    return space


def validate_registry() -> None:
    """Assert internal consistency of ``PARAMETER_REQUIREMENTS``.

    Called at module level after the dict is defined.  Raises ``ValueError``
    on the first violation found so errors surface at import time, not runtime.

    Checks:
    - No duplicate aliases across entries (after normalization).
    - No ``is_derived=True`` entry without ``derived_message``.
    - No ``SEMANTIC_MUTATION`` entry without ``display_name``.
    - No entry without ``description`` among the new entries (entries with all
      new fields at their defaults are legacy and exempt).
    """
    seen_aliases: dict[str, str] = {}  # normalized_alias → canonical

    for canonical, req in PARAMETER_REQUIREMENTS.items():
        # aliases duplicates
        for alias in req.aliases:
            key = normalize_alias(alias)
            if key in seen_aliases:
                raise ValueError(
                    f"Duplicate alias '{alias}' (normalized: '{key}') found in "
                    f"'{canonical}' and '{seen_aliases[key]}'."
                )
            seen_aliases[key] = canonical

        # concept_aliases duplicates
        for concept in req.concept_aliases:
            key = normalize_alias(concept)
            if key in seen_aliases:
                raise ValueError(
                    f"Duplicate concept_alias '{concept}' (normalized: '{key}') found in "
                    f"'{canonical}' and '{seen_aliases[key]}'."
                )
            seen_aliases[key] = canonical

        # derived without message
        if req.is_derived and not req.derived_message:
            raise ValueError(
                f"Entry '{canonical}' has is_derived=True but no derived_message."
            )

        # semantic_mutation without display_name
        if req.variable_type == VariableType.SEMANTIC_MUTATION and not req.display_name:
            raise ValueError(
                f"Entry '{canonical}' has variable_type=SEMANTIC_MUTATION but no display_name."
            )

        # description required for entries that use new fields
        has_new_fields = (
            req.aliases
            or req.concept_aliases
            or req.display_name is not None
            or req.is_derived
            or req.variable_type != VariableType.NUMERIC_DIRECT
        )
        if has_new_fields and not req.description:
            raise ValueError(
                f"Entry '{canonical}' uses registry fields but has no description."
            )


validate_registry()
