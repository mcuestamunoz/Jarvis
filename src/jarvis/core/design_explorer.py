"""Design Space Explorer — exploración automática de configuraciones óptimas.

Flujo:
    project_state + goal_key → DesignExplorer.explore() → ExplorationResult

Garantías:
    - Operación 100% en memoria: no escribe en disco, no llama a record_action ni save_state.
    - No muta project_state ni ningún parámetro de entrada.
    - Candidatos inviables (can_fly=False) se separan antes del ranking.
    - Candidatos con parámetros requeridos ausentes se omiten sin excepción.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from jarvis.core.calculation_engine import CalculationEngine
from jarvis.core.component_writers import apply_components_delta
from jarvis.core.system_architecture_catalog import COMPONENT_MIRRORED_PARAMS
from jarvis.schemas.action_schema import ComponentSpec, PropertyValue
from jarvis.schemas.tool_schema import CalculationBundle, SimulationResult
from jarvis.simulation.simulator import FeasibilitySimulator
from jarvis.tools.electricity import estimate_battery_mass_kg


# ── Labels de objetivo ────────────────────────────────────────────────────────

GOAL_LABELS: dict[str, str] = {
    "mejorar_autonomia": "maximizar autonomía",
    "aumentar_payload": "maximizar carga útil",
    "reducir_payload": "minimizar carga útil",
    "reducir_masa": "minimizar masa total",
    "mejorar_estabilidad": "maximizar margen de seguridad",
}


# ── Grids de exploración ──────────────────────────────────────────────────────
# Cada entry es un dict de deltas a aplicar sobre current_parameters.
#
# Convención de claves:
#   {param}_factor  → multiplica el valor actual por el factor (float)
#   {param}_delta   → suma un entero al valor actual (útil para motors)
#   {param}_value   → fija un valor absoluto
#
# Los candidatos cuyo parámetro base no exista en current_parameters se omiten
# automáticamente en _apply_delta() — nunca se usan defaults inventados.

EXPLORATION_GRIDS: dict[str, list[dict[str, Any]]] = {
    "mejorar_autonomia": [
        # ── Batería más grande ────────────────────────────────────────────────
        {"battery_capacity_wh_factor": 1.5},
        {"battery_capacity_wh_factor": 2.0},
        {"battery_capacity_wh_factor": 2.5},
        # ── Reducción de actuadores (menos consumo) ───────────────────────────
        {"motor_count_delta": -1},
        {"motor_count_delta": -2},
        {"battery_capacity_wh_factor": 1.5, "motor_count_delta": -1},
        {"battery_capacity_wh_factor": 2.0, "motor_count_delta": -1},
        # ── Motores más eficientes (menor consumo) ────────────────────────────
        {"motor_power_w_factor": 0.75},
        {"battery_capacity_wh_factor": 2.0, "motor_power_w_factor": 0.75},
        # ── U3: Estructura más ligera (domain-agnostic: factor relativo al baseline)
        # Funciona para dron (300g frame), rover (3kg), robot arm (1kg), etc.
        # Si structure_mass_override_kg no existe en base_params, el candidato
        # se omite automáticamente (_apply_delta devuelve None).
        {"structure_mass_override_kg_factor": 0.6},
        {"structure_mass_override_kg_factor": 0.75},
        {"structure_mass_override_kg_factor": 0.6,  "battery_capacity_wh_factor": 1.5},
        # ── U3: Motores más eficientes combinados con frame ligero ─────────────
        {"motor_power_w_factor": 0.65},
        {"motor_power_w_factor": 0.65, "structure_mass_override_kg_factor": 0.75},
    ],
    "aumentar_payload": [
        {"payload_kg_factor": 1.2},
        {"payload_kg_factor": 1.5},
        {"payload_kg_factor": 2.0},
        {"per_motor_max_thrust_n_factor": 1.5},
        {"per_motor_max_thrust_n_factor": 2.0},
        {"motor_count_delta": 2},
        {"motor_count_delta": 4},
        {"motor_count_delta": 2, "per_motor_max_thrust_n_factor": 1.5},
        {"payload_kg_factor": 1.2, "motor_count_delta": 2},
    ],
    "reducir_masa": [
        {"structure_mass_factor_factor": 0.7},
        {"structure_mass_factor_factor": 0.5},
        {"structure_mass_factor_factor": 0.4},
        {"payload_kg_factor": 0.8},
        {"structure_mass_factor_factor": 0.7, "payload_kg_factor": 0.8},
    ],
    # F-1: direction-mirrored counterpart of aumentar_payload — factors below
    # 1.0 only, so candidates always explore LOWER payload than the current
    # value, never accidentally reusing the increase direction. motor_count_delta
    # stays architecture-conditional by construction: _apply_delta() already
    # omits any candidate whose referenced param is absent from base_params
    # (no motor_count on this project → that candidate is silently skipped,
    # same mechanism every other goal's motor_count_delta entries already rely on).
    "reducir_payload": [
        {"payload_kg_factor": 0.85},
        {"payload_kg_factor": 0.7},
        {"payload_kg_factor": 0.5},
        {"structure_mass_factor_factor": 0.85, "payload_kg_factor": 0.85},
        {"motor_count_delta": -1, "payload_kg_factor": 0.85},
    ],
    "mejorar_estabilidad": [
        {"motor_count_delta": 2},
        {"motor_count_delta": 4},
        {"per_motor_max_thrust_n_factor": 1.5},
        {"per_motor_max_thrust_n_factor": 2.0},
        {"per_motor_max_thrust_n_factor": 1.5, "motor_count_delta": 2},
        {"safety_factor_factor": 1.25},
        {"safety_factor_factor": 1.5},
    ],
}

# Máximo de candidatos viables devueltos en ExplorationResult.viable
MAX_VIABLE = 5


# ── Component spec helpers ────────────────────────────────────────────────────

def _build_component_spec(
    component_key: str,
    component_type: str,
    property_name: str,
    unit: str | None,
    value: Any,
) -> ComponentSpec:
    """Builds a minimal ComponentSpec for a single-property DSE variation.

    Domain-agnostic: any component_key that apply_components_delta knows how to
    route will be correctly evaluated. Components not in _APPLY_ORDER fall through
    to set_control_component (declarative storage, no physics derivation).
    """
    return ComponentSpec(
        name=f"{component_key}_{property_name}_{value}",
        component_type=component_type,
        suggested_key=component_key,
        inference_confidence=0.9,
        completeness="medium",
        source="declared",
        properties={
            property_name: PropertyValue(value=value, unit=unit, confidence=0.95, source="declared")
        },
    )


def _battery_spec(capacity_wh: float) -> ComponentSpec:
    """Battery ComponentSpec for test convenience. Wraps _build_component_spec."""
    return _build_component_spec("battery", "energy_storage", "battery_capacity_wh", "Wh", capacity_wh)


def _motor_spec(power_w: float) -> ComponentSpec:
    """Motor ComponentSpec for test convenience. Wraps _build_component_spec."""
    return _build_component_spec("motors", "propulsion_active", "power_w", "W", power_w)


def _frame_spec(mass_kg: float) -> ComponentSpec:
    """Frame ComponentSpec for test convenience. Wraps _build_component_spec."""
    return _build_component_spec("frame", "structure", "mass_kg", "kg", mass_kg)


# ── Component variation rules ─────────────────────────────────────────────────
# Declarative table: for each exploration goal, which component properties to
# vary and with which absolute values. Adding a new component type or goal only
# requires adding an entry here — no logic changes needed.
#
# Rule schema (each entry is a plain dict):
#   component_key  str        — key in components dict (routed by apply_components_delta)
#   component_type str        — ComponentSpec.component_type (passed to writer routing)
#   property_name  str        — property key in ComponentSpec.properties
#   unit           str|None   — unit for PropertyValue
#   values         list[Any]  — concrete values; one candidate is generated per value

COMPONENT_VARIATION_RULES: dict[str, list[dict]] = {
    "mejorar_autonomia": [
        {
            "component_key": "battery", "component_type": "energy_storage",
            "property_name": "battery_capacity_wh", "unit": "Wh",
            "values": [300.0, 500.0, 800.0, 1200.0],
        },
    ],
    "aumentar_payload": [
        {
            "component_key": "motors", "component_type": "propulsion_active",
            "property_name": "power_w", "unit": "W",
            "values": [150.0, 200.0, 300.0, 400.0],
        },
    ],
    "reducir_masa": [
        {
            "component_key": "frame", "component_type": "structure",
            "property_name": "mass_kg", "unit": "kg",
            "values": [0.280, 0.350, 0.450],
        },
    ],
    "mejorar_estabilidad": [
        {
            "component_key": "frame", "component_type": "structure",
            "property_name": "mass_kg", "unit": "kg",
            "values": [0.500, 0.700],
        },
    ],
}


def _build_component_candidates_for_goal(goal_key: str) -> list[dict[str, ComponentSpec]]:
    """Generates component grid entries for a goal from COMPONENT_VARIATION_RULES.

    Returns one dict[component_key → ComponentSpec] per value per rule.
    Adding new component types or goals only requires updating
    COMPONENT_VARIATION_RULES — this function never needs to change.
    """
    entries: list[dict[str, ComponentSpec]] = []
    for rule in COMPONENT_VARIATION_RULES.get(goal_key, []):
        for value in rule["values"]:
            spec = _build_component_spec(
                component_key=rule["component_key"],
                component_type=rule["component_type"],
                property_name=rule["property_name"],
                unit=rule.get("unit"),
                value=value,
            )
            entries.append({rule["component_key"]: spec})
    return entries


# ── Schemas ───────────────────────────────────────────────────────────────────

class ExplorationCandidate(BaseModel):
    params_delta: dict[str, Any] = Field(default_factory=dict)
    components_delta: dict[str, ComponentSpec] = Field(default_factory=dict)
    # generation_metadata: reserved for v2 generative path
    generation_metadata: dict[str, Any] | None = None
    calculations: CalculationBundle
    simulation: SimulationResult
    score: float
    label: str
    improvement: float = 0.0


class ExplorationResult(BaseModel):
    goal_key: str
    goal_label: str
    baseline_score: float
    baseline_calculations: CalculationBundle
    baseline_simulation: SimulationResult
    candidates: list[ExplorationCandidate] = Field(default_factory=list)
    viable: list[ExplorationCandidate] = Field(default_factory=list)


# ── Scoring ───────────────────────────────────────────────────────────────────

def _score_candidate(
    sim: SimulationResult,
    calc: CalculationBundle,
    goal_key: str,
) -> float:
    """Devuelve un score escalar para el candidato. Mayor = mejor para todos los goals.

    Para reducir_masa se niega total_mass_kg para que sort descendente funcione.
    """
    if goal_key == "mejorar_autonomia":
        return sim.autonomy_min or 0.0
    if goal_key == "aumentar_payload":
        return sim.safety_margin_ratio * calc.payload_kg
    if goal_key == "reducir_payload":
        # Mirrors reducir_masa's shape (pure-reduction goal): lower payload_kg
        # scores higher so descending sort favors bigger reductions.
        return -calc.payload_kg
    if goal_key == "reducir_masa":
        return -calc.total_mass_kg
    if goal_key == "mejorar_estabilidad":
        return sim.safety_margin_ratio
    return 0.0


# ── Label generation ──────────────────────────────────────────────────────────

_DELTA_PARAM_LABELS: dict[str, str] = {
    "battery_capacity_wh": "batería (Wh)",
    "motor_power_w": "potencia/motor (W)",
    "payload_kg": "carga útil (kg)",
    "per_motor_max_thrust_n": "empuje/motor (N)",
    "structure_mass_factor": "factor masa estructural",
    "safety_factor": "safety factor",
    "motor_count": "motores",
}


def _build_label(delta: dict[str, Any], applied: dict[str, Any]) -> str:
    """Genera una etiqueta legible para un candidato params-driven."""
    parts = []
    for key, value in delta.items():
        if key.endswith("_factor"):
            param_name = key[: -len("_factor")]
            human = _DELTA_PARAM_LABELS.get(param_name, param_name)
            new_val = applied.get(param_name)
            if new_val is not None:
                formatted = int(new_val) if isinstance(new_val, float) and new_val == int(new_val) else round(new_val, 1)
                parts.append(f"{human}={formatted}")
        elif key.endswith("_delta"):
            param_name = key[: -len("_delta")]
            human = _DELTA_PARAM_LABELS.get(param_name, param_name)
            new_val = applied.get(param_name)
            if new_val is not None:
                parts.append(f"{human}={new_val}")
        elif key.endswith("_value"):
            param_name = key[: -len("_value")]
            human = _DELTA_PARAM_LABELS.get(param_name, param_name)
            parts.append(f"{human}={value}")
        else:
            parts.append(f"{key}={value}")
    return ", ".join(parts) if parts else str(delta)


def _build_label_components(components_delta: dict[str, Any]) -> str:
    """Genera una etiqueta legible para un candidato component-driven."""
    parts = []
    for comp_key, spec in components_delta.items():
        if not spec.properties:
            parts.append(comp_key)
            continue
        prop_summary = ", ".join(
            f"{k}={v.value}" for k, v in spec.properties.items() if v.value is not None
        )
        parts.append(f"{comp_key}: {prop_summary}" if prop_summary else comp_key)
    return " | ".join(parts) if parts else str(components_delta)


# ── Delta application ─────────────────────────────────────────────────────────

def _apply_delta(
    base_params: dict[str, Any],
    delta: dict[str, Any],
) -> dict[str, Any] | None:
    """Aplica un delta sobre base_params y devuelve un nuevo dict de parámetros.

    Devuelve None si algún parámetro referenciado no existe en base_params,
    lo que provoca que el candidato se omita sin error.
    """
    # DA2-prep (D4): mirrored params come from components_delta, not params_delta
    delta = {k: v for k, v in delta.items() if k not in COMPONENT_MIRRORED_PARAMS}
    result = dict(base_params)
    for key, value in delta.items():
        if key.endswith("_factor"):
            param_name = key[: -len("_factor")]
            base_value = base_params.get(param_name)
            if base_value is None:
                return None  # parámetro ausente — omitir candidato
            result[param_name] = round(float(base_value) * float(value), 4)
        elif key.endswith("_delta"):
            param_name = key[: -len("_delta")]
            base_value = base_params.get(param_name)
            if base_value is None:
                return None
            new_val = int(round(float(base_value))) + int(value)
            result[param_name] = max(1, new_val)  # discreta: mínimo 1
        elif key.endswith("_value"):
            param_name = key[: -len("_value")]
            result[param_name] = value
        else:
            result[key] = value

    # U1: keep battery_mass_kg in sync when battery_capacity_wh changes via delta.
    if "battery_capacity_wh" in result:
        result["battery_mass_kg"] = estimate_battery_mass_kg(result["battery_capacity_wh"])

    return result


# ── Explorer ──────────────────────────────────────────────────────────────────

class DesignExplorer:
    """Explora el espacio de diseño para un objetivo dado.

    Es una operación de solo lectura: nunca modifica el estado del proyecto
    ni escribe en disco. Usa calculation_engine y simulator como funciones puras.
    """

    def __init__(
        self,
        calculation_engine: CalculationEngine,
        simulator: FeasibilitySimulator,
    ) -> None:
        self._engine = calculation_engine
        self._simulator = simulator

    def explore(self, project_state: Any, goal_key: str) -> ExplorationResult:
        """Explora variaciones del diseño para el objetivo indicado.

        Args:
            project_state: ProjectState con current_parameters como punto de partida.
            goal_key: una de las claves de EXPLORATION_GRIDS / COMPONENT_VARIATION_RULES.

        Returns:
            ExplorationResult con baseline, todos los candidatos evaluados y
            los viables (can_fly=True) ordenados por score descendente (top MAX_VIABLE).
        """
        # ── Baseline normalizado ──────────────────────────────────────────────
        # apply_components_delta con delta vacío re-deriva params desde los
        # componentes ya presentes — garantiza que baseline y candidatos sean
        # comparables (mismo pipeline de derivación).
        normalized_state = apply_components_delta(project_state, {})
        base_params = dict(normalized_state.current_parameters or {})
        goal_label = GOAL_LABELS.get(goal_key, goal_key)

        baseline_calc = self._engine.build(base_params)
        baseline_sim = self._simulator.evaluate(baseline_calc)
        baseline_score = _score_candidate(baseline_sim, baseline_calc, goal_key)

        candidates: list[ExplorationCandidate] = []
        viable: list[ExplorationCandidate] = []

        # ── Simple param-hash cache: avoid re-evaluating identical params ────
        _cache: dict[frozenset, tuple] = {}

        def _evaluate(params: dict[str, Any]) -> tuple:
            # Cache por hash de params derivados.
            # TODO (v2): esta es una aproximación — el cache asume que el mapping
            # componente→params es inyectivo. Si dos ComponentSpecs distintos
            # derivan los mismos current_parameters (ej. motor A + hélice X =
            # motor B + hélice Y = 10N de thrust), producirán la misma clave y
            # el segundo candidato reutilizará el resultado del primero.
            # Impacto actual: bajo (grids con valores muy distintos).
            # Solución futura: incluir identidad de componentes en la clave de cache.
            key = frozenset(params.items())
            if key not in _cache:
                calc_ = self._engine.build(params)
                sim_ = self._simulator.evaluate(calc_)
                _cache[key] = (calc_, sim_)
            return _cache[key]

        # ── Params-only grid ─────────────────────────────────────────────────
        for delta in EXPLORATION_GRIDS.get(goal_key, []):
            # Guard: mixed deltas not supported yet (DA2 keeps them separate)
            applied = _apply_delta(base_params, delta)
            if applied is None:
                continue

            try:
                calc, sim = _evaluate(applied)
            except Exception:
                continue

            score = _score_candidate(sim, calc, goal_key)
            improvement = round(score - baseline_score, 4)
            candidate = ExplorationCandidate(
                params_delta=delta,
                components_delta={},
                calculations=calc,
                simulation=sim,
                score=score,
                label=_build_label(delta, applied),
                improvement=improvement,
            )
            candidates.append(candidate)
            if sim.can_fly:
                viable.append(candidate)

        # ── Component grid ───────────────────────────────────────────────────
        for comp_delta in _build_component_candidates_for_goal(goal_key):
            if not comp_delta:
                continue  # skip empty (vacío no aporta)

            try:
                temp_state = apply_components_delta(normalized_state, comp_delta)
                applied = dict(temp_state.current_parameters or {})
                calc, sim = _evaluate(applied)
            except Exception:
                continue

            score = _score_candidate(sim, calc, goal_key)
            improvement = round(score - baseline_score, 4)
            candidate = ExplorationCandidate(
                params_delta={},
                components_delta=comp_delta,
                calculations=calc,
                simulation=sim,
                score=score,
                label=_build_label_components(comp_delta),
                improvement=improvement,
            )
            candidates.append(candidate)
            if sim.can_fly:
                viable.append(candidate)

        viable.sort(key=lambda c: c.score, reverse=True)

        return ExplorationResult(
            goal_key=goal_key,
            goal_label=goal_label,
            baseline_score=baseline_score,
            baseline_calculations=baseline_calc,
            baseline_simulation=baseline_sim,
            candidates=candidates,
            viable=viable[:MAX_VIABLE],
        )
