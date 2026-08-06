"""Standalone component writer functions.

Cada función es el único punto de escritura para su componente.
Son funciones puras (sin estado externo): reciben un ProjectState y devuelven
un ProjectState nuevo sin persistir — el caller es responsable de guardar.

Extraídas de JarvisOrchestrator en Fase 7 prerequisito para desbloquear DA2:
el DesignExplorer necesita llamar a estos writers sin crear un import circular
(orchestrator → design_explorer → orchestrator).

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║              MIRRORED PARAM CONTRACT (ley del sistema)                 ║
# ╠══════════════════════════════════════════════════════════════════════════╣
# ║ Todo writer que gestione un componente físico DEBE:                    ║
# ║                                                                        ║
# ║  (1) Escribir en design_properties.components[key]   ← canónico       ║
# ║      Fuente única de verdad del componente.                            ║
# ║                                                                        ║
# ║  (2) Escribir en current_parameters[param]           ← bridge físico  ║
# ║      Mirror para que calculation_engine consuma el valor.              ║
# ║                                                                        ║
# ║ Si (2) falta:                                                          ║
# ║  - updated_params NO tendrá el valor                                   ║
# ║  - el engine calculará con datos desactualizados                       ║
# ║  - NO se lanzará ningún error (fallo silencioso)                       ║
# ║                                                                        ║
# ║ Flujo garantizado:                                                     ║
# ║   ComponentSpec → writer → current_parameters → calculation_engine    ║
# ║                                                                        ║
# ║ Enforcement:                                                           ║
# ║  - test_d4_param_gatekeeper.py verifica ambos lados tras save_state   ║
# ║  - Cualquier nuevo mirrored param DEBE añadir su test de contrato      ║
# ║  - Definición canónica: COMPONENT_MIRRORED_PARAMS en                  ║
# ║    core/system_architecture_catalog.py                                 ║
# ╚══════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

from typing import Any

from jarvis.domains.aerial import _frame_completeness
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.tools.electricity import estimate_battery_mass_kg


def set_frame_material(
    project_state: Any,
    mass_kg: float | None,
    material: str | None,
) -> Any:
    """Único punto de escritura para propiedades del frame.

    Escribe en dos lugares de forma atómica:
      1. components["frame"].properties (canónico — fuente única de verdad)
      2. current_parameters["structure_mass_override_kg"] (bypass física existente)

    Fase 3 completada: el mirror legacy structure.material fue eliminado.
    La lectura canónica ahora se hace via get_frame_material() en design_utils.py.

    Returns the updated ProjectState (not persisted — caller must save).
    """
    # ── 1. Build / update components["frame"] ────────────────────────────
    existing = project_state.design_properties.components.get("frame")
    props: dict[str, PropertyValue] = dict(existing.properties) if existing else {}

    if mass_kg is not None:
        props["mass_kg"] = PropertyValue(
            value=mass_kg, unit="kg", confidence=0.95, source="declared"
        )
    if material is not None:
        props["material"] = PropertyValue(
            value=material, unit=None, confidence=0.9, source="declared"
        )

    completeness, missing_fields = _frame_completeness(props)
    frame_spec = ComponentSpec(
        name="frame",
        component_type="structure",
        suggested_key="frame",
        inference_confidence=0.9,
        properties=props,
        completeness=completeness,
        missing_fields=missing_fields,
        source="declared",
    )
    updated_components = {**project_state.design_properties.components, "frame": frame_spec}
    updated_dp = project_state.design_properties.model_copy(update={
        "components": updated_components,
    })

    # ── 2. structure_mass_override_kg in current_parameters ───────────────
    updated_params = dict(project_state.current_parameters or {})
    if mass_kg is not None:
        updated_params["structure_mass_override_kg"] = mass_kg
    else:
        updated_params.pop("structure_mass_override_kg", None)

    return project_state.model_copy(update={
        "design_properties": updated_dp,
        "current_parameters": updated_params,
    })


def set_control_component(project_state: Any, spec: Any) -> Any:
    """Único punto de escritura para componentes del bloque control (FC, sensores).

    Escribe spec directamente en components[spec.suggested_key].
    Sin physics bypass — control no afecta cálculo en Fase 2.5.
    Sin mirror legacy — no hay campo equivalente en design_properties.

    Returns the updated ProjectState (not persisted — caller must save).
    """
    key = spec.suggested_key or spec.component_type or "generic_control"
    updated_components = {**project_state.design_properties.components, key: spec}
    updated_dp = project_state.design_properties.model_copy(update={"components": updated_components})
    return project_state.model_copy(update={"design_properties": updated_dp})


def set_battery_component(
    project_state: Any,
    spec: Any,
    capacity_wh: float | None,
) -> Any:
    """Único punto de escritura para propiedades de la batería.

    Escribe en dos lugares de forma atómica:
      1. components["battery"].properties (canónico)
      2. current_parameters["battery_capacity_wh"] (bridge al calculation engine)

    Sin mirror legacy — no hay campo equivalente en StructureProperties para battery.
    Returns updated ProjectState (not persisted — caller must save).
    """
    updated_components = {**project_state.design_properties.components, "battery": spec}
    updated_dp = project_state.design_properties.model_copy(update={"components": updated_components})

    updated_params = dict(project_state.current_parameters or {})
    if capacity_wh is not None:
        updated_params["battery_capacity_wh"] = capacity_wh
        updated_params["battery_mass_kg"] = estimate_battery_mass_kg(capacity_wh)
    else:
        updated_params.pop("battery_capacity_wh", None)
        updated_params.pop("battery_mass_kg", None)
    # U2: bridge cell_count → battery_cell_count (needed for RPM derivation in engine)
    cell_prop = spec.properties.get("cell_count")
    if cell_prop is not None:
        updated_params["battery_cell_count"] = int(cell_prop.value)
    else:
        updated_params.pop("battery_cell_count", None)

    return project_state.model_copy(update={
        "design_properties": updated_dp,
        "current_parameters": updated_params,
    })


def set_motor_component(
    project_state: Any,
    spec: Any,
    power_w: float | None,
) -> Any:
    """Único punto de escritura para propiedades de los motores.

    Escribe en dos lugares de forma atómica:
      1. components["motors"].properties (canónico)
      2. current_parameters["motor_power_w"] (bridge al calculation engine)

    Bug 78: preserves motor_count from the existing component when the new spec
    does not include it. Prevents double-write scenarios (first write declares count,
    second declares KV+power) from losing the count in component properties.
    The physics (current_parameters["motor_count"]) is always preserved regardless,
    but the component property must also be consistent for reasoning display.

    Returns updated ProjectState (not persisted — caller must save).
    """
    # Bug 78: merge motor_count from existing component if missing from new spec.
    existing_motors = getattr(project_state.design_properties, "components", {}).get("motors")
    if existing_motors is not None and "motor_count" not in (spec.properties or {}):
        old_count = existing_motors.properties.get("motor_count")
        if old_count is not None:
            spec = spec.model_copy(update={"properties": {**spec.properties, "motor_count": old_count}})

    updated_components = {**project_state.design_properties.components, "motors": spec}
    updated_dp = project_state.design_properties.model_copy(update={"components": updated_components})

    updated_params = dict(project_state.current_parameters or {})
    if power_w is not None:
        updated_params["motor_power_w"] = power_w
    else:
        updated_params.pop("motor_power_w", None)
    # U2: bridge motor_count → current_parameters (necesario para calculate_thrust_per_motor)
    count_prop = spec.properties.get("motor_count")
    if count_prop is not None:
        updated_params["motor_count"] = int(count_prop.value)
    # U2: bridge kv_rating → motor_kv_rating (needed for RPM derivation in engine)
    kv_prop = spec.properties.get("kv_rating")
    if kv_prop is not None:
        updated_params["motor_kv_rating"] = float(kv_prop.value)
    else:
        updated_params.pop("motor_kv_rating", None)

    return project_state.model_copy(update={
        "design_properties": updated_dp,
        "current_parameters": updated_params,
    })


def set_propeller_component(project_state: Any, spec: Any) -> Any:
    """Único punto de escritura para propiedades de las hélices.

    Escribe en dos lugares de forma atómica:
      1. components["propellers"].properties (canónico)
      2. current_parameters["propeller_diameter_in"] (bridge al calculation engine)

    El engine usa propeller_diameter_in para calcular thrust via aerodinámica.
    propeller_rpm NO se toca aquí — es un param dinámico de operación (Phase B).
    Returns updated ProjectState (not persisted — caller must save).
    """
    updated_components = {**project_state.design_properties.components, "propellers": spec}
    updated_dp = project_state.design_properties.model_copy(update={"components": updated_components})

    updated_params = dict(project_state.current_parameters or {})
    diameter_prop = spec.properties.get("diameter_in")
    if diameter_prop is not None:
        updated_params["propeller_diameter_in"] = float(diameter_prop.value)
    else:
        updated_params.pop("propeller_diameter_in", None)
    # U2: bridge pitch_in → propeller_pitch_in (informativo; no entra al engine aún)
    pitch_prop = spec.properties.get("pitch_in")
    if pitch_prop is not None:
        updated_params["propeller_pitch_in"] = float(pitch_prop.value)
    else:
        updated_params.pop("propeller_pitch_in", None)

    return project_state.model_copy(update={
        "design_properties": updated_dp,
        "current_parameters": updated_params,
    })


# ── DA2: composite delta applicator ──────────────────────────────────────────

# Canonical write order: each writer may derive params from the previous component.
# frame → battery → motors → propellers → control (everything else).
_APPLY_ORDER = ("frame", "battery", "motors", "propellers")


def apply_components_delta(project_state: Any, components_delta: dict[str, Any]) -> Any:
    """Aplica un dict de ComponentSpec sobre project_state usando los writers canónicos.

    Garantías:
    - Orden determinista: _APPLY_ORDER primero, luego claves extra (control, etc.).
    - Cada writer extrae sus parámetros físicos de spec.properties — nunca de params.
    - Idempotente con delta vacío: devuelve project_state con params re-derivados
      de los componentes ya presentes (normalización de baseline).
    - Puro: no persiste ni dispara efectos secundarios.

    Returns updated ProjectState (not persisted — caller must save).

    # TODO (v2 — refactor semántico): esta función hace dos cosas distintas:
    #   1. Aplicar un delta de componentes (comportamiento esperado).
    #   2. Normalizar el estado re-derivando params desde componentes existentes
    #      cuando delta es {} (baseline normalization en explore()).
    # Separar en:
    #   normalize_state_from_components(state) -> ProjectState
    #   apply_components_delta(state, delta) -> ProjectState
    # Riesgo actual: un caller que pase {} esperando no-op obtendrá recálculo completo.
    # Refactor seguro — no cambiar hasta que haya un segundo caller con expectativa distinta.
    """
    state = project_state

    # Ordered keys first
    for key in _APPLY_ORDER:
        spec = components_delta.get(key)
        if spec is None:
            # No delta for this key — re-apply existing component if present
            # so baseline normalization works correctly (empty delta path).
            design_props = getattr(state, "design_properties", None)
            existing_components = getattr(design_props, "components", None) if design_props is not None else None
            existing = existing_components.get(key) if existing_components is not None else None
            if existing is None:
                continue
            spec = existing

        if key == "frame":
            mass_prop = spec.properties.get("mass_kg")
            material_prop = spec.properties.get("material")
            mass_kg = float(mass_prop.value) if mass_prop is not None and mass_prop.value is not None else None
            material = str(material_prop.value) if material_prop is not None and material_prop.value is not None else None
            state = set_frame_material(state, mass_kg, material)
        elif key == "battery":
            cap_prop = spec.properties.get("battery_capacity_wh")
            capacity_wh = float(cap_prop.value) if cap_prop is not None and cap_prop.value is not None else None
            state = set_battery_component(state, spec, capacity_wh)
        elif key == "motors":
            power_prop = spec.properties.get("power_w")
            power_w = float(power_prop.value) if power_prop is not None and power_prop.value is not None else None
            state = set_motor_component(state, spec, power_w)
        elif key == "propellers":
            state = set_propeller_component(state, spec)

    # Extra keys not in _APPLY_ORDER (flight_controller, sensors, esc, …)
    for key, spec in components_delta.items():
        if key not in _APPLY_ORDER:
            state = set_control_component(state, spec)

    return state
